frappe.query_reports["Employee Timesheet Submissions by Status"] = {
  filters: [
    {
      fieldname: "year",
      label: __("Year"),
      fieldtype: "Select",
      options: ["2024", "2025", "2026", "2027", "2028"],
      default: String(new Date().getFullYear()),
      reqd: 1,
    },
  ],
};
