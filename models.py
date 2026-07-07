from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)  # index=True để .filter() tận dụng B-Tree
    shipment_code = Column(String(50), unique=True, nullable=False)
    status_delivery = Column(String(30), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    