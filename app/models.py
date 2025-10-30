from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Text, Boolean, func, UniqueConstraint
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(128), unique=True, nullable=True)          # optional
    title = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    product_metadata = Column(JSON, nullable=True)   # product-specific specs extracted by PhotoAI
    images = Column(JSON, nullable=True)     # list of image URLs
    source = Column(String(128), nullable=True)   # e.g., 'pallet', 'supplier', 'ebay'
    price = Column(Integer, nullable=True)    # stored as cents
    cost = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "sku": self.sku,
            "title": self.title,
            "description": self.description,
            "metadata": self.product_metadata,
            "images": self.images,
            "source": self.source,
            "price": self.price,
            "cost": self.cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    response_status = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    # Optionally store expiration, or cleanup older entries via background job
