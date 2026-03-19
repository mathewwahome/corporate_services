import React, { useEffect, useState } from "react";

function EmployeeDetail({ employee, onBack, onViewReport }) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    frappe.call({
      method:
        "corporate_services.icl_corporate_services.page.timesheet_workflow.timesheet_workflow.get_timesheet_submissions_by_employee",
      args: { employee_name: employee.employee_name },
      callback: (r) => {
        setSubmissions(r.message || []);
        setLoading(false);
      },
    });
  }, [employee]);

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-5">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <button className="btn btn-secondary" onClick={onBack}>
          <i className="fa fa-arrow-left"></i> Back to Employees
        </button>
        <button className="btn btn-success" onClick={() => onViewReport(employee)}>
          <i className="fa fa-chart-bar"></i> View Detailed Report
        </button>
      </div>

      {/* Employee Info Card */}
      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h4 className="mb-0">
            <i className="fa fa-user"></i> {employee.employee_name || employee.name}
          </h4>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-4">
              <p className="mb-2">
                <strong>Employee ID:</strong> {employee.name}
              </p>
            </div>
            <div className="col-md-4">
              <p className="mb-2">
                <strong>Department:</strong> {employee.department || "-"}
              </p>
            </div>
            <div className="col-md-4">
              <p className="mb-2">
                <strong>Designation:</strong> {employee.designation || "-"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Submissions Section */}
      <div className="card">
        <div className="card-header bg-secondary text-white">
          <h5 className="mb-0">Timesheet Submissions</h5>
        </div>
        <div className="card-body">
          {submissions.length === 0 ? (
            // Empty State
            <div className="text-center py-5">
              <i
                className="fa fa-inbox text-muted"
                style={{ fontSize: "4rem" }}
              ></i>
              <h4 className="mt-3 text-muted">No Timesheet Submissions</h4>
              <p className="text-muted">
                This employee has not submitted any timesheets yet.
              </p>
            </div>
          ) : (
            // Submissions Table
            <div className="table-responsive">
              <table className="table table-striped table-bordered">
                <thead className="table-dark">
                  <tr>
                    <th>#</th>
                    <th>Month</th>
                    <th>Total Hours</th>
                    <th>Status</th>
                    <th>Submitted On</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((ts, index) => (
                    <tr key={ts.name}>
                      <td>{index + 1}</td>
                      <td>{ts.month_year}</td>
                      <td>{ts.total_working_hours}</td>
                      <td>
                        <span
                          className={`badge ${
                            ts.status === "Approved"
                              ? "bg-success"
                              : ts.status === "Rejected"
                              ? "bg-danger"
                              : ts.status === "Cancelled"
                              ? "bg-secondary"
                              : "bg-warning"
                          }`}
                        >
                          {ts.status}
                        </span>
                      </td>
                      <td>{new Date(ts.creation).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default EmployeeDetail;