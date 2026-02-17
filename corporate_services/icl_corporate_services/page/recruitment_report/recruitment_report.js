frappe.pages["recruitment_report"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Recruitment Report",
    single_column: true,
  });

  frappe.require("https://cdn.jsdelivr.net/npm/chart.js", () => {
    frappe.require(
      "/assets/corporate_services/js/recruitment_report.js",
      () => {
        if (window.initTimesheetWorkflow) {
          window.initTimesheetWorkflow(page);
        } else {
          console.error("React bundle loaded but init function missing");
        }
      },
    );
  });
};
