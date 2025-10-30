from sqlalchemy.exc import IntegrityError
from app.models import IdempotencyKey
from sqlalchemy.orm import Session

def check_idempotency(session: Session, key: str):
    existing = session.query(IdempotencyKey).filter_by(idempotency_key=key).one_or_none()
    return existing

def store_idempotency_response(session: Session, key: str, status: int, body: dict):
    rec = IdempotencyKey(idempotency_key=key, response_status=status, response_body=body)
    try:
        session.add(rec)
        session.commit()
    except IntegrityError:
        session.rollback()
    return rec
