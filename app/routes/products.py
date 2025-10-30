from flask import Blueprint, request, jsonify, current_app
from app.schemas import ProductPayloadSchema
from app.utils import SessionLocal
from app.models import Product
from app.services.idempotency import check_idempotency, store_idempotency_response
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import ValidationError

bp = Blueprint("products", __name__, url_prefix="/api/v1/products")

@bp.route("/upsert", methods=["POST"])
def upsert_product():
    # 1) payload size check
    if request.content_length and request.content_length > current_app.config.get("MAX_PAYLOAD_BYTES", 2*1024*1024):
        return jsonify({"error": "payload_too_large"}), 413

    json_data = request.get_json(force=True, silent=True)
    if not json_data:
        return jsonify({"error": "invalid_json"}), 400

    schema = ProductPayloadSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "messages": e.messages}), 400

    idempotency_key = data.get("idempotency_key")
    session = SessionLocal()
    try:
        existing = check_idempotency(session, idempotency_key)
        if existing:
            # Return stored response
            return jsonify({"idempotent": True, "cached_response": existing.response_body}), existing.response_status or 200

        # Upsert logic by SKU if present, otherwise match on strong title+metadata signature
        product = None
        sku = data.get("sku")
        if sku:
            product = session.query(Product).filter_by(sku=sku).one_or_none()

        if not product:
            title = data.get("title")
            # simple heuristic: try find by exact title + source
            product = session.query(Product).filter_by(title=title, source=data.get("source")).one_or_none()

        if product:
            # update fields
            product.description = data.get("description") or product.description
            product.product_metadata = data.get("metadata") or product.product_metadata
            product.images = data.get("images") or product.images
            if data.get("price") is not None:
                product.price = data.get("price")
            if data.get("cost") is not None:
                product.cost = data.get("cost")
        else:
            product = Product(
                sku=sku,
                title=data["title"],
                description=data.get("description"),
                product_metadata=data.get("metadata"),
                images=data.get("images"),
                source=data.get("source"),
                price=data.get("price"),
                cost=data.get("cost")
            )
            session.add(product)

        session.commit()
        response_body = {"status": "ok", "product": product.to_dict()}
        store_idempotency_response(session, idempotency_key, 200, response_body)
        return jsonify(response_body), 200

    except SQLAlchemyError as e:
        session.rollback()
        err = {"error": "db_error", "message": str(e)}
        try:
            store_idempotency_response(session, idempotency_key, 500, err)
        except Exception:
            pass
        return jsonify(err), 500
    finally:
        session.close()
