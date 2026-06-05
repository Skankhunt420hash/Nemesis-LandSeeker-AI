import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import "leaflet/dist/leaflet.css";

if ("serviceWorker" in navigator && !window.Capacitor?.isNativePlatform?.()) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => null);
  });
}

createRoot(document.getElementById("root")).render(<App />);
