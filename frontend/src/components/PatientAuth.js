import React, { useState } from "react";

function PatientAuth({ setPatientId, onBack }) {
  const [isRegister, setIsRegister] = useState(true);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: ""
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    const url = isRegister
      ? "http://127.0.0.1:8000/patient/register"
      : "http://127.0.0.1:8000/patient/login";

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(form)
      });

      const data = await response.json();

      if (response.ok) {
        if (data.patient_code) {
          alert(
            `${data.message}\n\nYour Patient Code: ${data.patient_code}\n\nPlease save this code carefully.\nDoctors will need it to access your records.`
          );
        } else {
          alert(data.message);
        }

        localStorage.setItem("patientId", data.patient_id);
        localStorage.setItem("patientCode", data.patient_code);
        localStorage.setItem("role", "patient");

        setPatientId(data.patient_id);
      } else {
        alert(data.detail || "Something went wrong");
      }
    } catch (error) {
      console.error(error);
      alert("Server error. Please try again.");
    }
  };

  return (
    <div className="patient-auth-bg">
      <div style={{ textAlign: "center", position: "relative" }}>
        
        {/* BACK BUTTON */}
        <button className="back-btn" onClick={onBack}>
          ← Back
        </button>

        <h2>{isRegister ? "Patient Registration" : "Patient Login"}</h2>

        {isRegister && (
          <>
            <input
              name="name"
              placeholder="Name"
              value={form.name}
              onChange={handleChange}
            />
            <br />
            <br />
          </>
        )}

        <input
          name="email"
          placeholder="Email"
          value={form.email}
          onChange={handleChange}
        />
        <br />
        <br />

        <input
          type="password"
          name="password"
          placeholder="Password"
          value={form.password}
          onChange={handleChange}
        />
        <br />
        <br />

        <button onClick={handleSubmit}>
          {isRegister ? "Register" : "Login"}
        </button>

        <p
          style={{ cursor: "pointer", color: "blue", marginTop: "10px" }}
          onClick={() => setIsRegister(!isRegister)}
        >
          {isRegister
            ? "Already have an account? Login"
            : "New patient? Register"}
        </p>
      </div>
    </div>
  );
}

export default PatientAuth;
