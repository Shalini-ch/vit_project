import React, { useEffect, useState } from "react";

function DoctorDashboard({ onLogout }) {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientCode, setPatientCode] = useState("");
  const [verified, setVerified] = useState(false);
  const [records, setRecords] = useState([]);

  // Load all patients
  useEffect(() => {
    fetch("http://127.0.0.1:8000/doctor/patients")
      .then((res) => res.json())
      .then((data) => setPatients(data.patients))
      .catch((err) => console.error(err));
  }, []);

  // Verify patient
  const handleVerify = async () => {
    if (!selectedPatient) {
      alert("Please select a patient first.");
      return;
    }

    if (!patientCode || patientCode.trim().length !== 5) {
      alert("Please enter a valid 5-digit patient code.");
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/doctor/verify-patient", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: selectedPatient.id,
          patient_code: patientCode.trim(),
        }),
      });

      const data = await res.json();

      if (res.ok) {
        alert("Patient verified successfully");
        setVerified(true);
        fetchPatientRecords(selectedPatient.id);
      } else {
        alert(data.detail || "Invalid patient code");
        setVerified(false);
        setRecords([]);
      }
    } catch (err) {
      console.error(err);
      alert("Server error while verifying patient");
    }
  };

  // Fetch patient records
  const fetchPatientRecords = async (patientId) => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/doctor/patient/${patientId}/records`
      );

      if (!res.ok) throw new Error("Failed to fetch records");

      const data = await res.json();
      setRecords(data.records || []);
    } catch (err) {
      console.error(err);
      alert("Failed to load patient records");
    }
  };

  return (
    /* 🔥 Added wrapper only for background */
    <div className="dashboard-bg">
      <div style={{ textAlign: "center", width: "100%" }}>
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "10px 40px",
          }}
        >
          <h2>Doctor Dashboard</h2>
          <button onClick={onLogout} className="logout-btn">
            Logout
          </button>
        </div>

        {/* Select Patient */}
        <h4>Select Patient Name</h4>
        <select
          value={selectedPatient ? selectedPatient.id : ""}
          onChange={(e) => {
            const patient = patients.find(
              (p) => p.id === parseInt(e.target.value)
            );
            setSelectedPatient(patient);
            setVerified(false);
            setRecords([]);
            setPatientCode("");
          }}
        >
          <option value="">-- Select Patient --</option>
          {patients.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>

        {/* Enter Patient Code */}
        {selectedPatient && (
          <div style={{ marginTop: "30px" }}>
            <h4>Enter 5-digit Patient Code</h4>
            <input
              type="text"
              maxLength="5"
              value={patientCode}
              placeholder="Patient Code"
              onChange={(e) => setPatientCode(e.target.value)}
            />
            <br />
            <br />
            <button onClick={handleVerify}>Verify Patient</button>
          </div>
        )}

        {/* Patient Records */}
        {verified && (
          <div style={{ marginTop: "40px" }}>
            <h3>Patient X-ray Records</h3>

            {records.length === 0 ? (
              <p>No records found.</p>
            ) : (
              records.map((r, i) => (
                <div key={i} className="record-card">
                  <p>
                    <b>Disease:</b> {r.disease}
                  </p>
                  <p>
                    <b>Confidence:</b> {(r.confidence * 100).toFixed(2)}%
                  </p>
                  <p>
                    <b>Date:</b> {r.date}
                  </p>

                  <img src={r.image} alt="X-ray" />
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default DoctorDashboard;
