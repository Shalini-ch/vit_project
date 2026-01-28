import React, { useState } from "react";

function DoctorLogin({ setDoctorLoggedIn, onBack }) {
  const [form, setForm] = useState({
    username: "",
    password: ""
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/doctor/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(form)
      });

      const data = await res.json();

      if (res.ok) {
        alert(data.message);
        setDoctorLoggedIn(true); // move to doctor dashboard
      } else {
        alert(data.detail || "Login failed");
      }
    } catch (err) {
      console.error(err);
      alert("Server error");
    }
  };

  return (
    /* ONLY THIS WRAPPER IS ADDED */
    <div className="patient-auth-bg">
      <div style={{ textAlign: "center", position: "relative" }}>
        
        {/* BACK BUTTON */}
        <button className="back-btn" onClick={onBack}>
          ← Back
        </button>

        <h2>Doctor Login</h2>

        <input
          type="text"
          name="username"
          placeholder="Doctor Username"
          value={form.username}
          onChange={handleChange}
        />
        <br /><br />

        <input
          type="password"
          name="password"
          placeholder="Password"
          value={form.password}
          onChange={handleChange}
        />
        <br /><br />

        <button onClick={handleLogin}>
          Login
        </button>
      </div>
    </div>
  );
}

export default DoctorLogin;
