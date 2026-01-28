import React from "react";

function RoleSelect({ setRole }) {
  return (
    // 🔥 Add this wrapper class for background
    <div className="role-background" style={containerStyle}>
      
      {/* 🔥 Add this class for the card (keeps your inline styles too) */}
      <div className="role-card" style={cardStyle}>
        <h1 style={titleStyle}>Virtual Clinic</h1>
        <p style={subtitleStyle}>Select your role to continue</p>

        <div style={buttonContainer}>
          <button onClick={() => setRole("patient")} style={btnStyle}>
            Patient
          </button>
          <button onClick={() => setRole("doctor")} style={btnStyle}>
            Doctor
          </button>
          <button onClick={() => setRole("admin")} style={btnStyle}>
            Admin
          </button>
        </div>
      </div>
    </div>
  );
}

const containerStyle = {
  height: "100vh",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
};

const cardStyle = {
  width: "420px",
  padding: "40px",
  borderRadius: "12px",
  background: "white",
  boxShadow: "0 10px 25px rgba(0,0,0,0.15)",
  textAlign: "center",
};

const titleStyle = {
  fontSize: "28px",
  marginBottom: "8px",
};

const subtitleStyle = {
  fontSize: "14px",
  marginBottom: "30px",
  opacity: 0.7,
};

const buttonContainer = {
  display: "flex",
  justifyContent: "space-between",
  gap: "12px",
};

const btnStyle = {
  flex: 1,
  padding: "12px 0",
  fontSize: "16px",
  cursor: "pointer",
  borderRadius: "6px",
  border: "1px solid #ccc",
  background: "white",
  transition: "0.2s",
};

export default RoleSelect;
