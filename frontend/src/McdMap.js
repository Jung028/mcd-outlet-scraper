import { useEffect, useState, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const getDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371;
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
};


const McdMap = () => {
    const [outlets, setOutlets] = useState([]);
    const [intersectingOutlets, setIntersectingOutlets] = useState(new Set());
    const mapRef = useRef(null); // Store the map instance

    useEffect(() => {
        fetch("https://mindhive-assessment.onrender.com/scrape")
            .then((response) => response.json())
            .then((data) => {
                setOutlets(data.outlets);
                findIntersections(data.outlets);
            })
            .catch((error) => console.error("Error fetching outlets:", error));
    }, []);

    const findIntersections = (outlets) => {
        const intersectingSet = new Set();
        for (let i = 0; i < outlets.length; i++) {
            for (let j = i + 1; j < outlets.length; j++) {
                const d = getDistance(
                    outlets[i].geo.latitude, outlets[i].geo.longitude,
                    outlets[j].geo.latitude, outlets[j].geo.longitude
                );
                if (d <= 5) {
                    intersectingSet.add(outlets[i].name);
                    intersectingSet.add(outlets[j].name);
                }
            }
        }
        setIntersectingOutlets(intersectingSet);
    };

    useEffect(() => {
        if (!outlets.length) return; // Avoid initializing map with empty data

        if (mapRef.current) {
            mapRef.current.remove(); // Destroy the old map before reinitializing
        }

        const map = L.map("map").setView([3.146847, 101.710931], 12);
        mapRef.current = map; // Store map instance

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

        const normalIcon = L.icon({
            iconUrl: "/mcd-icon.webp",
            iconSize: [38, 38],
            iconAnchor: [19, 38],
            popupAnchor: [0, -38]
        });

        const intersectIcon = L.icon({
            iconUrl: "/mcd-intersect.webp",
            iconSize: [38, 38],
            iconAnchor: [19, 38],
            popupAnchor: [0, -38]
        });

        outlets.forEach(outlet => {
            const { latitude, longitude } = outlet.geo;
            const isIntersecting = intersectingOutlets.has(outlet.name);
            const markerIcon = isIntersecting ?  normalIcon : intersectIcon;
            const servicesList = outlet.services ? outlet.services.join(", ") : "N/A";

            const popupContent = `
                <div style="text-align:center;">
                    <b>${outlet.name}</b><br/>
                    <img src="${outlet.image[0]}" alt="McDonald's Logo" width="100"/><br/>
                    <b>Address:</b> ${outlet.address}<br/>
                    <b>Phone:</b> ${outlet.telephone}<br/>
                    <b>Info:</b> ${outlet.info || "N/A"}<br/>
                    <b>Services:</b> ${servicesList}<br/>
                    <b>Menu:</b> <a href="${outlet.menu}" target="_blank">View Menu</a><br/>
                    <b>More Info:</b> <a href="${outlet.url}" target="_blank">Visit Site</a>
                </div>
            `;


            L.marker([latitude, longitude], { icon: markerIcon })
                .addTo(map)
                .bindPopup(popupContent);

            L.circle([latitude, longitude], {
                color: isIntersecting ? "red" : "blue",
                fillColor: isIntersecting ? "#9999ff" : "#ff9999", // Softer colors
                fillOpacity: 0,
                radius: 5000,
                dashArray: "3, 3", // Creates a dashed circle border
                weight: 1.5, // Thinner stroke width


            }).addTo(map);
        });

        return () => {
            map.remove(); // Cleanup map when component unmounts
        };
    }, [outlets, intersectingOutlets]);

    return <div id="map" style={{ height: "500px", width: "100%" }} />;
};

export default McdMap;
