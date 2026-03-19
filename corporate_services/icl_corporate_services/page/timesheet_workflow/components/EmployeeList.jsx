import React from "react";

function EmployeeList({
  employees,
  onViewAllSubmissions,
  onViewEmployee,
  onViewEmployeeReport,
}) {
  return (
    <div className="container py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Employee Timesheet Workflow</h1>
        <button className="btn btn-primary" onClick={onViewAllSubmissions}>
          View All Timesheet Submissions
        </button>
      </div>

      <div className="card">
        <div className="card-header bg-primary text-white">
          <h5 className="mb-0">All Employees</h5>
        </div>
        <div className="card-body p-0">
          <div className="table-responsive">
            <table className="table table-hover table-striped mb-0">
              <thead className="table-dark">
                <tr>
                  <th>#</th>
                  <th>Employee Name</th>
                  <th>Department</th>
                  <th>Designation</th>
                  <th className="text-center">Actions</th>
                </tr>
              </thead>
              <tbody>
                {employees.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center text-muted py-4">
                      No employees found
                    </td>
                  </tr>
                ) : (
                  employees.map((emp, index) => (
                    <tr key={emp.name}>
                      <td>{index + 1}</td>
                      <td>
                        <strong>{emp.employee_name || emp.name}</strong>
                      </td>
                      <td>{emp.department || "-"}</td>
                      <td>{emp.designation || "-"}</td>
                      <td className="text-center">
                        <div className="btn-group" role="group">
                          <button
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => onViewEmployee(emp)}
                            title="View Submissions"
                          >
                            <i className="fa fa-list"></i> Submissions
                          </button>
                          <button
                            className="btn btn-sm btn-outline-success"
                            onClick={() => onViewEmployeeReport(emp)}
                            title="View Detailed Report"
                          >
                            <i className="fa fa-chart-bar"></i> Report
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EmployeeList;