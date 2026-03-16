import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Register cytoscape extensions
import cytoscape from "cytoscape";
import coseBilkent from "cytoscape-cose-bilkent";
cytoscape.use(coseBilkent);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
