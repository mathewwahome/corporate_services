import React from "react";
import { createRoot } from "react-dom/client";
import RecruitmenstDashboard from "./RecruitmenstDashboard";

window.initRecruitmentDashboard = function (page) {
    const container = document.createElement("div");
    container.id = "react-root";
    page.main[0].appendChild(container);

    const root = createRoot(container);
    root.render(<RecruitmenstDashboard />);
};
