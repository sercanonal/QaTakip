import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Remove external badges
const removeBadges = () => {
  const selectors = [
    '#emergent-badge',
    '[href*="emergent"]',
    'a[style*="position: fixed"]',
    'a[style*="bottom: 20px"]'
  ];
  selectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => el.remove());
  });
};

// Run on load and periodically
setInterval(removeBadges, 500);
document.addEventListener('DOMContentLoaded', removeBadges);

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
