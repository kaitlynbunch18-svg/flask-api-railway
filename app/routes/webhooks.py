from flask import Blueprint, request, jsonify
from app.utils import SessionLocal
from app.models import IdempotencyKey
import json
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint("webhooks", __name__, url_prefix="/api/v1/webhooks")

@bp.route("/make", methods=["POST"])
def make_webhook_ingest():
    """
    Simple endpoint to accept forwarded webhooks or failed payloads from Make.com.
    Should store the raw payload for inspection and allow later replay.
    Body: { "idempotency_key": "...", "source": "supplier_email", "payload": { ... } }
    """
    json_data = request.get_json(force=True, silent=True)
    if not json_data:
        return jsonify({"error": "invalid_json"}), 400
    session = SessionLocal()
    try:
        key = json_data.get("idempotency_key")
        if key:
            # store idempotency row if not exists
            existing = session.query(IdempotencyKey).filter_by(idempotency_key=key).one_or_none()
            if existing:
                return jsonify({"status": "duplicate"}), 200
            rec = IdempotencyKey(idempotency_key=key, response_status=202, response_body=json_data)
            session.add(rec)
            session.commit()
        # optionally push to internal processing queue (left for you)
        return jsonify({"status": "accepted"}), 202
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "db_error", "message": str(e)}), 500
    finally:
        session.close()
