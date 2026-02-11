import React, { useEffect, useState } from "react";

function EmployeeTimesheetReport({ employee, onBack, onBackToHome }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    frappe.call({
      method:
        "corporate_services.icl_corporate_services.page.timesheet_workflow.timesheet_workflow.get_employee_timesheet_report",
      args: { employee_name: employee.name },
      callback: (r) => {
        setReportData(r.message || {});
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

  const {
    total_hours = 0,
    projects = [],
    tasks = [],
    monthly_hours = [],
    timesheets = [],
  } = reportData;

  return (
    <div className="container py-5">
      {/* Navigation */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <button className="btn btn-secondary" onClick={onBack}>
          <i className="fa fa-arrow-left"></i> Back to Employee
        </button>
        <button className="btn btn-outline-secondary" onClick={onBackToHome}>
          <i className="fa fa-home"></i> Home
        </button>
      </div>

      {/* Employee Header */}
      <div className="card mb-4">
        <div className="card-header bg-success text-white">
          <h3 className="mb-0">
            <i className="fa fa-chart-line"></i> Timesheet Report:{" "}
            {employee.employee_name}
          </h3>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="row mb-4">
        <div className="col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <h6 className="text-muted">Total Hours Worked</h6>
              <h2 className="text-primary">{total_hours.toFixed(1)}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <h6 className="text-muted">Projects Worked On</h6>
              <h2 className="text-info">{projects.length}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <h6 className="text-muted">Tasks Completed</h6>
              <h2 className="text-success">{tasks.length}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <h6 className="text-muted">Total Entries</h6>
              <h2 className="text-warning">{timesheets.length}</h2>
            </div>
          </div>
        </div>
      </div>

      {/* Projects Breakdown */}
      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h5 className="mb-0">
            <i className="fa fa-project-diagram"></i> Hours by Project
          </h5>
        </div>
        <div className="card-body">
          {projects.length === 0 ? (
            <div className="text-center py-4 text-muted">
              <i className="fa fa-inbox" style={{ fontSize: "3rem" }}></i>
              <p className="mt-2">No project data available</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped table-bordered">
                <thead className="table-dark">
                  <tr>
                    <th>#</th>
                    <th>Project</th>
                    <th>Total Hours</th>
                    <th>Percentage</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((project, index) => (
                    <tr key={index}>
                      <td>{index + 1}</td>
                      <td>{project.project || "-"}</td>
                      <td>{project.hours.toFixed(2)}</td>
                      <td>
                        <div className="progress">
                          <div
                            className="progress-bar bg-primary"
                            role="progressbar"
                            style={{
                              width: `${(project.hours / total_hours) * 100}%`,
                            }}
                          >
                            {((project.hours / total_hours) * 100).toFixed(1)}%
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Tasks Breakdown */}
      <div className="card mb-4">
        <div className="card-header bg-info text-white">
          <h5 className="mb-0">
            <i className="fa fa-tasks"></i> Hours by Task
          </h5>
        </div>
        <div className="card-body">
          {tasks.length === 0 ? (
            <div className="text-center py-4 text-muted">
              <i className="fa fa-inbox" style={{ fontSize: "3rem" }}></i>
              <p className="mt-2">No task data available</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped table-bordered">
                <thead className="table-dark">
                  <tr>
                    <th>#</th>
                    <th>Task</th>
                    <th>Project</th>
                    <th>Total Hours</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task, index) => (
                    <tr key={index}>
                      <td>{index + 1}</td>
                      <td>{task.task || "-"}</td>
                      <td>{task.project || "-"}</td>
                      <td>{task.hours.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Monthly Breakdown */}
      <div className="card mb-4">
        <div className="card-header bg-success text-white">
          <h5 className="mb-0">
            <i className="fa fa-calendar"></i> Monthly Hours
          </h5>
        </div>
        <div className="card-body">
          {monthly_hours.length === 0 ? (
            <div className="text-center py-4 text-muted">
              <i className="fa fa-inbox" style={{ fontSize: "3rem" }}></i>
              <p className="mt-2">No monthly data available</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped table-bordered">
                <thead className="table-dark">
                  <tr>
                    <th>#</th>
                    <th>Month</th>
                    <th>Total Hours</th>
                  </tr>
                </thead>
                <tbody>
                  {monthly_hours.map((month, index) => (
                    <tr key={index}>
                      <td>{index + 1}</td>
                      <td>{month.month}</td>
                      <td>{month.hours.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* All Timesheet Entries */}
      <div className="card">
        <div className="card-header bg-dark text-white">
          <h5 className="mb-0">
            <i className="fa fa-list"></i> All Timesheet Entries
          </h5>
        </div>
        <div className="card-body">
          {timesheets.length === 0 ? (
            <div className="text-center py-4 text-muted">
              <i className="fa fa-inbox" style={{ fontSize: "3rem" }}></i>
              <p className="mt-2">No timesheet entries found</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped table-bordered table-sm">
                <thead className="table-dark">
                  <tr>
                    <th>#</th>
                    <th>Date</th>
                    <th>Project</th>
                    <th>Task</th>
                    <th>Activity</th>
                    <th>Hours</th>
                  </tr>
                </thead>
                <tbody>
                  {timesheets.map((ts, index) => (
                    <tr key={index}>
                      <td>{index + 1}</td>
                      <td>{ts.from_time || "-"}</td>
                      <td>{ts.project || "-"}</td>
                      <td>{ts.task || "-"}</td>
                      <td>{ts.activity_type || "-"}</td>
                      <td>{ts.hours.toFixed(2)}</td>
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

export default EmployeeTimesheetReport;