import React, { useState, useEffect } from "react";
import RoleSelect from "./components/RoleSelect";
import PatientAuth from "./components/PatientAuth";
import XrayUpload from "./components/XrayUpload";
import DoctorLogin from "./components/DoctorLogin";
import DoctorDashboard from "./components/DoctorDashboard";
import "./App.css";   // make sure this is imported

function App() {
  const [role, setRole] = useState(null);
  const [patientId, setPatientId] = useState(null);
  const [doctorLoggedIn, setDoctorLoggedIn] = useState(false);

  // 🔁 Restore session
  useEffect(() => {
    const savedRole = localStorage.getItem("role");
    const savedPatientId = localStorage.getItem("patientId");
    const savedDoctor = localStorage.getItem("doctorLoggedIn");

    if (savedRole) setRole(savedRole);
    if (savedRole === "patient" && savedPatientId) setPatientId(savedPatientId);
    if (savedRole === "doctor" && savedDoctor === "true") setDoctorLoggedIn(true);
  }, []);

  // 🔥 Full logout (clears everything)
  const handleLogout = () => {
    localStorage.clear();
    setRole(null);
    setPatientId(null);
    setDoctorLoggedIn(false);
  };

  // 🔙 Go back to Role Selection only
  const goBackToRole = () => {
    localStorage.removeItem("role");
    localStorage.removeItem("patientId");
    localStorage.removeItem("doctorLoggedIn");

    setRole(null);
    setPatientId(null);
    setDoctorLoggedIn(false);
  };

  let content = null;

  // ---------------------------
  // Role selection
  // ---------------------------
  if (!role) {
    content = (
      <RoleSelect
        setRole={(r) => {
          localStorage.setItem("role", r);
          setRole(r);
        }}
      />
    );
  }

  // ---------------------------
  // Patient Flow
  // ---------------------------
  else if (role === "patient" && !patientId) {
    content = (
      <PatientAuth
        setPatientId={(id) => {
          localStorage.setItem("patientId", id);
          setPatientId(id);
        }}
        onBack={goBackToRole}
      />
    );
  }

  else if (role === "patient" && patientId) {
    content = (
      <XrayUpload
        patientId={patientId}
        onLogout={handleLogout}
      />
    );
  }

  // ---------------------------
  // Doctor Flow
  // ---------------------------
  else if (role === "doctor" && !doctorLoggedIn) {
    content = (
      <DoctorLogin
        setDoctorLoggedIn={() => {
          localStorage.setItem("doctorLoggedIn", "true");
          setDoctorLoggedIn(true);
        }}
        onBack={goBackToRole}
      />
    );
  }

  else if (role === "doctor" && doctorLoggedIn) {
    content = <DoctorDashboard onLogout={handleLogout} />;
  }

  // ---------------------------
  // Admin Placeholder
  // ---------------------------
  else if (role === "admin") {
    content = (
      <div style={{ textAlign: "center", marginTop: "50px" }}>
        <h2>Admin Login</h2>
        <p>Admin UI will be added later</p>
        <button onClick={goBackToRole}>Back</button>
      </div>
    );
  }

  return (
    <div className="app-background">
      <div className="app-container">
        {content}
      </div>
    </div>
  );
}

export default App;
