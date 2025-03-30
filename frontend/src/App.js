import React from "react";
import McdMap from "./McdMap";
import Chatbot from "./Chatbot";

function App() {
  return (
    <div className="relative h-screen w-screen flex flex-col bg-gray-100">
      {/* Chatbot at the top with a sticky header */}
      <div className="fixed top-0 w-full z-10 bg-white shadow-md p-4">
        <h1 className="text-xl font-bold text-center">McDonald's Outlets Map</h1>
        <McdMap />
      </div>

      {/* Map takes full space below the chatbot */}
      <div className="flex-grow mt-24">
        <Chatbot />
      </div>
    </div>
  );
}

export default App;
