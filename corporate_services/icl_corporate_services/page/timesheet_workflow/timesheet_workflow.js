frappe.pages["timesheet_workflow"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Timesheet Submissions Reports",
    });

    frappe.require("/assets/corporate_services/css/timesheet_workflow.css");

    function buildSidebar(wrapper) {
        const sidebarEl = wrapper.querySelector(".layout-side-section");
        if (!sidebarEl) return;

        const workspaces = frappe.boot.allowed_workspaces || [];

        const parents = workspaces.filter((ws) => !ws.parent_page);
        const childMap = {};
        workspaces.filter((ws) => ws.parent_page).forEach((ws) => {
            if (!childMap[ws.parent_page]) childMap[ws.parent_page] = [];
            childMap[ws.parent_page].push(ws);
        });

        const groups = {};
        parents.forEach((ws) => {
            const g = ws.public ? "PUBLIC" : "PRIVATE";
            if (!groups[g]) groups[g] = [];
            groups[g].push(ws);
        });

        function renderIcon(iconName, title) {
            if (iconName) {
                try {
                    const svg = frappe.utils.icon(iconName, "sm");
                    if (svg) return `<span class="ts-item-icon">${svg}</span>`;
                } catch (e) { 

                }
            }
            const letter = (title || "?")[0].toUpperCase();
            return `<span class="ts-item-icon" style="
                width:18px;height:18px;border-radius:4px;
                background:var(--primary,#5e64ff);color:#fff;
                font-size:10px;font-weight:700;
                display:inline-flex;align-items:center;justify-content:center;
                margin-right:9px;flex-shrink:0;opacity:1;
            ">${letter}</span>`;
        }

        let html = `<div class="ts-sidebar-nav">`;
        const groupKeys = Object.keys(groups);

        groupKeys.forEach((groupName, gi) => {
            if (gi > 0) html += `<div class="ts-sidebar-divider"></div>`;

            html += `
                <div class="ts-sidebar-group" data-group="${groupName}">
                    <div class="ts-sidebar-group-label" data-group="${groupName}">
                        ${groupName}
                        <span class="ts-chevron">▾</span>
                    </div>
                    <div class="ts-sidebar-group-items">
            `;

            groups[groupName].forEach((ws) => {
                const children = childMap[ws.name] || [];
                const hasChildren = children.length > 0;
                const iconHtml = renderIcon(ws.icon, ws.title || ws.name);

                html += `
                    <a class="ts-sidebar-item"
                       data-name="${ws.name}"
                       data-has-children="${hasChildren}"
                       href="/app/Workspaces/${encodeURIComponent(ws.name)}">
                        ${iconHtml}
                        <span class="ts-item-label">${ws.title || ws.name}</span>
                        ${hasChildren ? `<span class="ts-item-arrow">›</span>` : ""}
                    </a>
                `;

                if (hasChildren) {
                    html += `<div class="ts-sidebar-children" data-parent="${ws.name}" style="max-height:0;">`;
                    children.forEach((child) => {
                        const childIcon = renderIcon(child.icon, child.title || child.name);
                        html += `
                            <a class="ts-sidebar-item ts-child-item"
                               data-name="${child.name}"
                               href="/app/Workspaces/${encodeURIComponent(child.name)}">
                                ${childIcon}
                                <span class="ts-item-label">${child.title || child.name}</span>
                            </a>
                        `;
                    });
                    html += `</div>`;
                }
            });

            html += `</div></div>`;
        });

        html += `</div>`;
        sidebarEl.innerHTML = html;

        function setActive() {
            const route = frappe.get_route() || [];
            const currentName = route[1] ? decodeURIComponent(route[1]) : "";

            sidebarEl.querySelectorAll(".ts-sidebar-item").forEach((el) => {
                el.classList.remove("active");
            });

            if (currentName) {
                const match = sidebarEl.querySelector(
                    `.ts-sidebar-item[data-name="${currentName}"]`
                );
                if (match) {
                    match.classList.add("active");
                    const childContainer = match.closest(".ts-sidebar-children");
                    if (childContainer) {
                        const parentName = childContainer.dataset.parent;
                        const parentEl = sidebarEl.querySelector(
                            `.ts-sidebar-item[data-name="${parentName}"]`
                        );
                        if (parentEl) {
                            parentEl.classList.add("open");
                            childContainer.style.maxHeight = childContainer.scrollHeight + "px";
                        }
                    }
                }
            }
        }

        setActive();

        sidebarEl.querySelectorAll(".ts-sidebar-item").forEach((el) => {
            el.addEventListener("click", (e) => {
                e.preventDefault();
                const name = el.dataset.name;
                const hasChildren = el.dataset.hasChildren === "true";

                if (hasChildren) {
                    const childContainer = sidebarEl.querySelector(
                        `.ts-sidebar-children[data-parent="${name}"]`
                    );
                    const isOpen = el.classList.contains("open");
                    el.classList.toggle("open", !isOpen);
                    childContainer.style.maxHeight = isOpen
                        ? "0"
                        : childContainer.scrollHeight + "px";
                } else {
                    frappe.set_route("Workspaces", name);
                    setActive();
                }
            });
        });

        sidebarEl.querySelectorAll(".ts-sidebar-group-label").forEach((label) => {
            label.addEventListener("click", () => {
                const groupName = label.dataset.group;
                const itemsEl = sidebarEl.querySelector(
                    `.ts-sidebar-group[data-group="${groupName}"] .ts-sidebar-group-items`
                );
                const isCollapsed = label.classList.toggle("collapsed");
                itemsEl.style.display = isCollapsed ? "none" : "block";
            });
        });

        frappe.router.on("change", setActive);
    }

    buildSidebar(wrapper);

    frappe.require(
        "https://cdn.jsdelivr.net/npm/chart.js",
        () => {
            frappe.require(
                "/assets/corporate_services/js/timesheet_workflow.js",
                () => {
                    if (window.initTimesheetWorkflow) {
                        window.initTimesheetWorkflow(page);
                    } else {
                        console.error("React bundle loaded but init function missing");
                    }
                }
            );
        }
    );
};

frappe.pages["timesheet_workflow"].on_page_show = function (wrapper) {
    setTimeout(() => {
        const sidebar = wrapper.querySelector(".layout-side-section");
        if (sidebar) {
            sidebar.style.display = "block";
            sidebar.style.minWidth = "220px";
            sidebar.style.width = "220px";
        }
    }, 50);
};