frappe.pages["timesheet_workflow"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Timesheet Workflow",
        single_column: true,
    });

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
