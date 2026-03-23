from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import re, os, random
from datetime import datetime
from pydantic import BaseModel

from real_model import predict
from database import engine, SessionLocal, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================
# Request Models
# ============================
class PatientRegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class PatientLoginRequest(BaseModel):
    email: str
    password: str


class DoctorVerifyRequest(BaseModel):
    patient_id: int
    patient_code: str


class DoctorLoginRequest(BaseModel):
    username: str
    password: str


# ============================
# Helpers
# ============================
def validate_email(email: str):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)


def validate_password(password: str):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


@app.get("/")
def home():
    return {"message": "Backend is running"}


# ============================
# Patient Register
# ============================
@app.post("/patient/register")
def register_patient(data: PatientRegisterRequest, db: Session = Depends(get_db)):
    if not validate_email(data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    if not validate_password(data.password):
        raise HTTPException(status_code=400, detail="Weak password")

    while True:
        patient_code = str(random.randint(10000, 99999))
        if not db.query(models.Patient).filter(models.Patient.patient_code == patient_code).first():
            break

    new_patient = models.Patient(
        name=data.name.strip(),
        email=data.email.strip(),
        password=data.password,
        patient_code=patient_code
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return {
        "message": "Patient registered successfully",
        "patient_id": new_patient.id,
        "patient_code": patient_code
    }


# ============================
# Patient Login
# ============================
@app.post("/patient/login")
def login_patient(data: PatientLoginRequest, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(
        models.Patient.email == data.email,
        models.Patient.password == data.password
    ).first()

    if not patient:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "patient_id": patient.id,
        "name": patient.name,
        "patient_code": patient.patient_code
    }


# ============================
# Doctor Login
# ============================
@app.post("/doctor/login")
def doctor_login(data: DoctorLoginRequest):
    if data.username == "doctor" and data.password == "doctor123":
        return {"message": "Doctor login successful"}
    raise HTTPException(status_code=401, detail="Invalid doctor credentials")


# ============================
# Doctor: Get Patients
# ============================
@app.get("/doctor/patients")
def get_all_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    return {"patients": [{"id": p.id, "name": p.name} for p in patients]}


# ============================
# Doctor: Verify Patient Code
# ============================
@app.post("/doctor/verify-patient")
def verify_patient_code(data: DoctorVerifyRequest, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == data.patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient.patient_code != data.patient_code:
        raise HTTPException(status_code=401, detail="Invalid code. Please check and try again.")

    return {"message": "Patient verified successfully"}


# ============================
# Doctor: Get Patient Records
# ============================
@app.get("/doctor/patient/{patient_id}/records")
def doctor_get_patient_records(patient_id: int, db: Session = Depends(get_db)):
    records = db.query(models.Record).filter(models.Record.patient_id == patient_id).all()
    return {
        "records": [
            {
                "id": r.id,   # 🔥 Needed for delete feature
                "image": f"http://127.0.0.1:8000/{r.image_path.replace(os.sep,'/')}",
                "disease": r.disease,
                "confidence": r.confidence,
                "date": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in records
        ]
    }



# ============================
# 🔥 Patient Upload & Predict
# ============================
@app.post("/patient/upload")
def upload_xray(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        disease, confidence = predict(file_path)

        new_record = models.Record(
            patient_id=patient_id,
            image_path=file_path,
            disease=disease,
            confidence=confidence
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return {
            "message": "Prediction successful",
            "disease": disease,
            "confidence": confidence,
            "image_path": file_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================
# Delete Record
# ============================
@app.delete("/record/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.Record).filter(models.Record.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Delete image file from disk
    if os.path.exists(record.image_path):
        os.remove(record.image_path)

    db.delete(record)
    db.commit()

    return {"message": "Record deleted successfully"}

# ============================
# Patient: Get Own Records
# ============================
@app.get("/patient/{patient_id}/records")
def get_patient_records(patient_id: int, db: Session = Depends(get_db)):
    records = db.query(models.Record).filter(models.Record.patient_id == patient_id).all()

    return {
        "records": [
            {
                "id": r.id,
                "image_path": r.image_path,
                "disease": r.disease,
                "confidence": r.confidence,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in records
        ]
    }
