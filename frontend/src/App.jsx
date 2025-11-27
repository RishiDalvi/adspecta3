import React, { useState, useEffect } from "react";

// -----------------------------
// CONFIG: BACKEND API URL
// -----------------------------
// If Vercel provides an environment variable, use it.
// If not, fallback to your deployed Railway backend.
const API =
    import.meta.env.VITE_API_URL ||
    "https://adspecta3-production.up.railway.app";

export default function App() {
    const [budget, setBudget] = useState(60000);

    // Audience inputs
    const [audienceType, setAudienceType] = useState("general");
    const [ageMin, setAgeMin] = useState(18);
    const [ageMax, setAgeMax] = useState(60);

    const [results, setResults] = useState([]);
    const [statusMsg, setStatusMsg] = useState("");
    const [lastError, setLastError] = useState("");

    useEffect(() => {
        console.log("🔵 FRONTEND LOADED");
        console.log("🔗 Backend URL:", API);

        setStatusMsg("Frontend loaded. Ready to request backend.");
    }, []);

    // -----------------------------
    // MAIN FUNCTION: API CALL
    // -----------------------------
    async function getRecommendations() {
        setStatusMsg("Sending request...");
        setLastError("");

        const payload = {
            lat: 18.5204,
            lng: 73.8567,
            budget: Number(budget),
            audience_age_min: Number(ageMin),
            audience_age_max: Number(ageMax),
            audience_type: audienceType
        };

        console.log("📤 Sending Payload:", payload);

        try {
            const res = await fetch(`${API}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            console.log("📥 Response status:", res.status);

            // If backend returns non-JSON error
            let data;
            try {
                data = await res.json();
            } catch (err) {
                const rawText = await res.text();
                throw new Error("JSON parse failed: " + rawText);
            }

            console.log("📥 Parsed JSON:", data);

            if (Array.isArray(data) && data.length > 0) {
                setResults(data);
                setStatusMsg(`Found ${data.length} results`);
            } else {
                setResults([]);
                setStatusMsg("No results returned");
            }
        } catch (err) {
            console.error("❌ API ERROR:", err);
            setLastError(err.message);
            setStatusMsg("Request failed");
        }
    }

    // -----------------------------
    // RENDER UI
    // -----------------------------
    return ( <
        div style = {
            { padding: "20px", fontFamily: "Arial" }
        } >
        <
        h1 > AdSpecta– Smart AdSpace Recommendation < /h1>

        { /* FILTERS */ } <
        div style = {
            { marginBottom: 20 }
        } >

        <
        label style = {
            { marginRight: 10 }
        } > Budget(₹): < /label> <
        input type = "number"
        value = { budget }
        onChange = {
            (e) => setBudget(e.target.value)
        }
        style = {
            { marginRight: 20 }
        }
        />

        <
        label style = {
            { marginRight: 10 }
        } > Audience Type: < /label> <
        select value = { audienceType }
        onChange = {
            (e) => setAudienceType(e.target.value)
        }
        style = {
            { marginRight: 20 }
        } >
        <
        option value = "general" > General < /option> <
        option value = "students" > Students < /option> <
        option value = "it_workers" > IT Workers < /option> <
        option value = "shoppers" > Shoppers < /option> <
        option value = "residents" > Residents < /option> <
        option value = "tourists" > Tourists < /option> < /
        select >

        <
        br / > < br / >

        <
        label style = {
            { marginRight: 10 }
        } > Age Min: < /label> <
        input type = "number"
        value = { ageMin }
        onChange = {
            (e) => setAgeMin(e.target.value)
        }
        style = {
            { width: 60, marginRight: 20 }
        }
        />

        <
        label style = {
            { marginRight: 10 }
        } > Age Max: < /label> <
        input type = "number"
        value = { ageMax }
        onChange = {
            (e) => setAgeMax(e.target.value)
        }
        style = {
            { width: 60, marginRight: 20 }
        }
        />

        <
        button onClick = { getRecommendations } > Get Recommendations < /button> < /
        div >

        { /* STATUS */ } {
            statusMsg && ( <
                div style = {
                    { marginBottom: 10 }
                } >
                <
                strong > Status: < /strong> {statusMsg} < /
                div >
            )
        }

        {
            lastError && ( <
                div style = {
                    { color: "red", marginBottom: 10 }
                } >
                <
                strong > Error: < /strong> {lastError} < /
                div >
            )
        }

        { /* RESULTS */ } <
        div > {
            results.length === 0 && < div > No results to show. < /div>}

            {
                results.map((r) => ( <
                    div key = { r.id }
                    style = {
                        {
                            border: "1px solid #ccc",
                            padding: 12,
                            borderRadius: 6,
                            marginBottom: 12
                        }
                    } >
                    <
                    h3 > { r.name } < /h3>

                    <
                    p > < strong > Type: < /strong> {r.type}</p >
                    <
                    p > < strong > Price: < /strong> ₹{r.price_per_month}</p >

                    <
                    p > < strong > Predicted Impressions: < /strong> {r.predicted_impressions}</p >
                    <
                    p > < strong > Audience Match: < /strong> {r.audience_match?.toFixed(2)}</p >
                    <
                    p > < strong > Final Score: < /strong> {r.final_score?.toFixed(2)}</p >
                    <
                    /div>
                ))
            } <
            /div> < /
            div >
        );
    }