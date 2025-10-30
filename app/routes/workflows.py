from flask import Blueprint, request, jsonify, current_app
from app.utils import SessionLocal
from app.services.idempotency import check_idempotency, store_idempotency_response
import uuid
import requests
from flask import abort

bp = Blueprint("workflows", __name__, url_prefix="/api/v1/workflows")

@bp.route("/run", methods=["POST"])
def run_workflow():
    """
    Start a workflow. Expect body:
    {
      "idempotency_key": "...",
      "workflow_name": "supplier_ingest",
      "payload": { ... },
      "callback_url": "https://..."
    }
    """
    json_data = request.get_json(force=True, silent=True)
    if not json_data:
        return jsonify({"error": "invalid_json"}), 400

    idempotency_key = json_data.get("idempotency_key")
    if not idempotency_key:
        return jsonify({"error": "missing_idempotency_key"}), 400

    session = SessionLocal()
    try:
        existing = check_idempotency(session, idempotency_key)
        if existing:
            return jsonify({"idempotent": True, "cached_response": existing.response_body}), existing.response_status or 200

        # Minimal permissions/auth check via header token (optional)
        token = request.headers.get("X-Workflow-Token")
        expected = current_app.config.get("WORKFLOW_AUTH_TOKEN")
        if expected and token != expected:
            abort(401)

        workflow_name = json_data.get("workflow_name")
        payload = json_data.get("payload", {})
        callback_url = json_data.get("callback_url")

        # Enqueue: For now we trigger a simple HTTP POST to your Make webhook (or internal job)
        # In production, you might push to a queue like SQS, Redis, or start an async job.
        # We'll call callback_url synchronously (if provided) and return the response.

        if callback_url:
            try:
                r = requests.post(callback_url, json={"workflow_name": workflow_name, "payload": payload}, timeout=20)
                body = {"status": "callback_sent", "workflow_name": workflow_name, "callback_status": r.status_code}
                store_idempotency_response(session, idempotency_key, r.status_code, body)
                return jsonify(body), r.status_code
            except requests.RequestException as e:
                body = {"status": "callback_failed", "error": str(e)}
                store_idempotency_response(session, idempotency_key, 500, body)
                return jsonify(body), 500
        else:
            # No callback: just store as queued (simple response)
            body = {"status": "queued", "workflow_name": workflow_name}
            store_idempotency_response(session, idempotency_key, 202, body)
            return jsonify(body), 202

    except Exception as e:
        session.rollback()
        err = {"error": "server_error", "message": str(e)}
        try:
            store_idempotency_response(session, idempotency_key, 500, err)
        except Exception:
            pass
        return jsonify(err), 500
    finally:
        session.close()
