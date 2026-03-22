frappe.pages["survey_manager"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Survey Manager",
    single_column: true,
  });

  const $wrapper = $(page.body);
  $wrapper
    .empty()
    .append(`<div id="survey-manager-root" class="survey-manager"></div>`);

  frappe.require("/assets/corporate_services/js/survey_admin.js", () => {
    if (globalThis.initSurveyManager) {
      globalThis.initSurveyManager(page);
    } else {
      console.error("Survey Manager bundle loaded but init function missing");
    }
  });
};

