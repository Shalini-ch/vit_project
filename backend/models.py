from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    # 🔐 Random 5-digit patient code (used by doctor for access)
    patient_code = Column(String(5), unique=True, index=True, nullable=False)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    # Relationship with records
    records = relationship(
        "Record",
        back_populates="patient",
        cascade="all, delete"
    )


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    image_path = Column(String, nullable=False)
    disease = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to patient
    patient = relationship("Patient", back_populates="records")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
