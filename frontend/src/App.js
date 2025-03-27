import React from "react";
import MapComponent from "./MapComponent";

function App() {
  return (
    <div style={{ textAlign: "center", fontFamily: "Arial, sans-serif" }}>
      <h1>McDonald's Outlets Map</h1>
      <p>Displaying outlets with 5KM radius catchment areas.</p>
      <MapComponent />
    </div>
  );
}

export default App;
