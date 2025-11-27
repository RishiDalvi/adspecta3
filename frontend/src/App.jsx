import React, { useState, useEffect } from "react";

export default function App() {
  const [budget, setBudget] = useState(60000);

  // 🎯 NEW: Audience filters
  const [audience, setAudience] = useState("general");
  const [ageMin, setAgeMin] = useState(18);
  const [ageMax, setAgeMax] = useState(60);

  const [results, setResults] = useState([]);
  const [statusMsg, setStatusMsg] = useState("");
  const [lastError, setLastError] = useState(null);

  useEffect(() => {
    console.log("[App] frontend mounted");
    setStatusMsg("Frontend loaded. Backend must run at http://127.0.0.1:8000");
  }, []);

  async function getRecommendations() {
    console.log("=== Sending Request to Backend ===");
    console.log("Budget:", budget);
    console.log("Audience Type:", audience);
    console.log("Age Range:", ageMin, ageMax);

    setStatusMsg("Sending request...");
    setLastError(null);

    try {
      const payload = {
        lat: 18.5204,
        lng: 73.8567,
        budget: Number(budget),
        audience_age_min: Number(ageMin),
        audience_age_max: Number(ageMax),
        audience_type: audience
      };

      console.log("[Payload]", payload);

      const res = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      console.log("[Response Status]", res.status, res.statusText);

      let data;
      try {
        data = await res.json();
      } catch (e) {
        const text = await res.text();
        throw new Error(`JSON parsing failed. Body: ${text}`);
      }

      console.log("[Response JSON]", data);

      if (!Array.isArray(data) || data.length === 0) {
        setStatusMsg("No results found for selected filters.");
      } else {
        setStatusMsg(`Found ${data.length} matching adspaces.`);
      }

      setResults(data);

    } catch (err) {
      console.error("[ERROR]", err);
      setLastError(String(err));
      setStatusMsg("Request failed. Check console.");
      setResults([]);
    }
  }

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>AdSpecta Targeted Recommendation</h1>

      {/* -------------------- INPUTS -------------------- */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ marginRight: 8 }}>Budget (₹):</label>
        <input
          type="number"
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
          style={{ marginRight: 20 }}
        />

        <label style={{ marginRight: 8 }}>Audience Type:</label>
        <select
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          style={{ marginRight: 20 }}
        >
          <option value="general">General</option>
          <option value="students">Students</option>
          <option value="it_workers">IT Workers</option>
          <option value="shoppers">Shoppers</option>
          <option value="residents">Residents</option>
          <option value="tourists">Tourists</option>
        </select>

        <br /><br />

        <label style={{ marginRight: 8 }}>Age Min:</label>
        <input
          type="number"
          value={ageMin}
          onChange={(e) => setAgeMin(e.target.value)}
          style={{ width: 60, marginRight: 20 }}
        />

        <label style={{ marginRight: 8 }}>Age Max:</label>
        <input
          type="number"
          value={ageMax}
          onChange={(e) => setAgeMax(e.target.value)}
          style={{ width: 60, marginRight: 20 }}
        />

        <button onClick={getRecommendations}>Get Recommendations</button>
      </div>

      {/* -------------------- STATUS -------------------- */}
      <div style={{ marginBottom: 12 }}>
        <strong>Status:</strong> {statusMsg}
      </div>

      {lastError && (
        <div style={{ color: "red", marginBottom: 12 }}>
          <strong>Error:</strong> {lastError}
        </div>
      )}

      {/* -------------------- RESULTS -------------------- */}
      <div>
        {results.length === 0 && <div>No results to show.</div>}

        {results.map((r, index) => (
          <div
            key={r.id || index}
            style={{
              border: "1px solid #ccc",
              padding: "12px",
              marginBottom: "12px",
              borderRadius: "6px"
            }}
          >
            <h3>
              {r.name}
            </h3>

            <p><strong>Type:</strong> {r.type}</p>
            <p><strong>Price:</strong> ₹{r.price_per_month}</p>

            <p>
              <strong>Predicted Impressions:</strong> {r.predicted_impressions}
            </p>

            <p>
              <strong>Audience Match Score:</strong> {r.audience_match?.toFixed(2)}
            </p>

            <p>
              <strong>Final Score:</strong> {r.final_score?.toFixed(2)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
