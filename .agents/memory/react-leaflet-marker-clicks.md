---
name: react-leaflet marker clicks
description: Why Leaflet CircleMarker eventHandlers.click silently fails in this app, and the proven fix
---

# react-leaflet CircleMarker click handlers don't fire reliably

In this frontend (react-leaflet v5 + React 19 + StrictMode), a `<CircleMarker eventHandlers={{ click: ... }}>` does **not** fire on user click — no handler runs, no error, no network request. Clicking the same record from a plain React `onClick` (list rows, cards) works fine.

**Why:** react-leaflet's Leaflet-native event binding does not survive this version/StrictMode combo; React's own synthetic `onClick` is unaffected. The map still renders and positions markers correctly — only the Leaflet click event is dead.

**How to apply:** Do NOT rely on `eventHandlers.click` alone for opening detail views from a map marker. Mirror the working maps in this codebase (`AirLogisticsMap.jsx`, `CorridorMap.jsx`): give each marker a `<Popup>` containing a button with a real React `onClick={() => handler(item)}`. The maritime `LogisticsMap.jsx` was the odd one out (hover `<Tooltip>` + bare `eventHandlers.click`, no Popup button) which is exactly why its port-details modal never opened from the map. Keeping the (non-firing) `eventHandlers.click` is harmless; the Popup button is what actually works.
