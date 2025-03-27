import React, { useState, useEffect } from "react";
import axios from "axios";
import { GoogleMap, LoadScript, Circle } from "@react-google-maps/api";

const MapComponent = () => {
  const [outlets, setOutlets] = useState([]);
  const [intersections, setIntersections] = useState(new Set());

  // API Key from Environment Variables
  const googleMapsApiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

  // Map Container Style
  const mapContainerStyle = {
    width: "100vw",
    height: "100vh",
  };

  // Default Map Center (Malaysia)
  const defaultCenter = {
    lat: 3.139,
    lng: 101.6869,
  };

  // Fetch Outlets from Backend API
  useEffect(() => {
    const fetchOutlets = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/outlets");
        console.log("Fetched Outlets:", response.data);
        setOutlets(response.data);
      } catch (error) {
        console.error("Error fetching outlets:", error);
      }
    };

    fetchOutlets();
  }, []);

  // Check for Intersecting Circles
  useEffect(() => {
    if (outlets.length > 0) {
      findIntersections(outlets);
    }
  }, [outlets]);

  const findIntersections = (outlets) => {
    const intersectingOutlets = new Set();
    const radius = 5000; // 5KM in meters

    for (let i = 0; i < outlets.length; i++) {
      for (let j = i + 1; j < outlets.length; j++) {
        const outletA = outlets[i];
        const outletB = outlets[j];

        const distance = haversineDistance(
          { lat: outletA.latitude, lng: outletA.longitude },
          { lat: outletB.latitude, lng: outletB.longitude }
        );

        if (distance < radius / 1000) {
          intersectingOutlets.add(outletA.id);
          intersectingOutlets.add(outletB.id);
        }
      }
    }

    setIntersections(intersectingOutlets);
  };

  // Haversine Formula to Calculate Distance (KM)
  const haversineDistance = (coords1, coords2) => {
    const R = 6371; // Earth radius in KM
    const dLat = (coords2.lat - coords1.lat) * (Math.PI / 180);
    const dLng = (coords2.lng - coords1.lng) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(coords1.lat * (Math.PI / 180)) *
        Math.cos(coords2.lat * (Math.PI / 180)) *
        Math.sin(dLng / 2) *
        Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in KM
  };

  return (
    <LoadScript googleMapsApiKey={googleMapsApiKey}>
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={defaultCenter}
        zoom={10}
      >
        {outlets.map((outlet) => (
          <Circle
            key={outlet.id}
            center={{ lat: outlet.latitude, lng: outlet.longitude }}
            radius={5000} // 5KM Radius
            options={{
              strokeColor: intersections.has(outlet.id) ? "red" : "blue",
              strokeOpacity: 0.8,
              strokeWeight: 2,
              fillColor: intersections.has(outlet.id) ? "red" : "blue",
              fillOpacity: 0.35,
            }}
          />
        ))}
      </GoogleMap>
    </LoadScript>
  );
};

export default MapComponent;
