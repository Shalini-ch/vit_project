import React, { useState, useEffect } from "react";
import PatientRecords from "./PatientRecords";

function XrayUpload({ patientId, onLogout }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshHistory, setRefreshHistory] = useState(false); // 🔥 force reload

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    setFile(selected);
    setPreview(selected ? URL.createObjectURL(selected) : null);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select an X-ray image first");
      return;
    }

    const formData = new FormData();
    formData.append("patient_id", patientId);
    formData.append("file", file);

    try {
      setLoading(true);

      const res = await fetch("http://127.0.0.1:8000/patient/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.detail || "Prediction failed");
        return;
      }

      setResult(data);

      // 🔥 Always show and refresh history after prediction
      setShowHistory(true);
      setRefreshHistory((prev) => !prev);

      setFile(null);
      setPreview(null);
    } catch (err) {
      console.error(err);
      alert("Prediction failed. Check backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-bg">
      <div style={{ textAlign: "center", position: "relative", width: "100%" }}>

        {/* Logout Button */}
        <button className="logout-btn" onClick={onLogout}>
          Logout
        </button>

        <h1>X-ray Upload</h1>
        <h3>Patient ID: {patientId}</h3>

        <input type="file" accept="image/*" onChange={handleFileChange} />
        <br /><br />

        {preview && (
          <div>
            <h3>Preview</h3>
            <img
              src={preview}
              alt="Preview"
              style={{
                width: "250px",
                border: "2px solid #333",
                borderRadius: "8px",
                marginBottom: "20px",
              }}
            />
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={loading}
          style={{
            padding: "10px 20px",
            borderRadius: "6px",
            background: "#2c3e50",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}
        >
          {loading ? "Predicting..." : "Upload & Predict"}
        </button>

        {result && (
          <div style={{ marginTop: "30px" }}>
            <h2>Prediction Result</h2>
            <p><b>Disease:</b> {result.disease}</p>
            <p><b>Confidence:</b> {(result.confidence * 100).toFixed(2)}%</p>

            <button
              onClick={() => setShowHistory(!showHistory)}
              style={{
                marginTop: "10px",
                padding: "6px 12px",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              {showHistory ? "Hide History" : "View History"}
            </button>
          </div>
        )}

        {showHistory && (
          <PatientRecords
            patientId={patientId}
            refresh={refreshHistory}   // 🔥 important
          />
        )}
      </div>
    </div>
  );
}

export default XrayUpload;
