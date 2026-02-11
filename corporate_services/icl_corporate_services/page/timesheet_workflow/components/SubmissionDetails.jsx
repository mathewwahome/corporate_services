import React, { useEffect, useState } from "react";

function SubmissionDetails({ submission, employee, onBack }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    frappe.call({
      method:
        "corporate_services.icl_corporate_services.page.timesheet_workflow.timesheet_workflow.get_timesheet_submission_details",
      args: { submission_name: submission.name },
      callback: (r) => {
        setDetails(r.message);
        setLoading(false);
      },
    });
  }, [submission]);

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger">
          Failed to load submission details
        </div>
        <button className="btn btn-secondary" onClick={onBack}>
          ← Back
        </button>
      </div>
    );
  }

  const {
    submission: sub,
    projects,
    tasks,
    timesheets,
    total_entries,
  } = details;

  return (
    <div className="container py-5">
      <button className="btn btn-secondary mb-4" onClick={onBack}>
        <i className="fa fa-arrow-left"></i> Back to Submissions
      </button>

      <div className="card mb-4">
        <div className="card-body">
          <div className="row">
            <div className="col-md-3">
              <p>
                <strong>Employee:</strong> {sub.employee_name}
              </p>
            </div>
            <div className="col-md-3">
              <p>
                <strong>Month:</strong> {sub.month_year}
              </p>
            </div>
            <div className="col-md-3">
              <p>
                <strong>Total Hours:</strong> {sub.total_working_hours}
              </p>
            </div>
            <div className="col-md-3">
              <p>
                <strong>Status:</strong>{" "}
                <span
                  className={`badge ${
                    sub.status === "Approved"
                      ? "bg-success"
                      : sub.status === "Rejected"
                        ? "bg-danger"
                        : sub.status === "Cancelled"
                          ? "bg-secondary"
                          : "bg-warning"
                  }`}
                >
                  {sub.status}
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="row mb-4">
        <div className="col-md-4">
          <div className="card text-center">
            <div className="card-body">
              <h6 className="text-muted">Total tasks</h6>
              <h2 className="text-primary">{total_entries}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card text-center">
            <div className="card-body">
              <h6 className="text-muted">Projects Worked On</h6>
              <h2 className="text-info">{projects.length}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card text-center">
            <div className="card-body">
              <h6 className="text-muted">Tasks Completed</h6>
              <h2 className="text-success">{tasks.length}</h2>
            </div>
          </div>
        </div>
      </div>

      {/* Projects Breakdown */}
      <div className="card mb-4">
        <div className="card-header bg-info text-white">
          <h5 className="mb-0">
            <i className="fa fa-project-diagram"></i> Hours by Project
          </h5>
        </div>
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-striped table-bordered">
              <thead className="table-dark">
                <tr>
                  <th>#</th>
                  <th>Project</th>
                  <th>Total Hours</th>
                  <th>Tasks</th>
                  <th>Entries</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project, index) => (
                  <tr key={index}>
                    <td>{index + 1}</td>
                    <td>{project.project}</td>
                    <td>{project.hours.toFixed(2)}</td>
                    <td>{project.task_count}</td>
                    <td>{project.entries}</td>
                    <td>
                      <div className="progress">
                        <div
                          className="progress-bar bg-info"
                          role="progressbar"
                          style={{
                            width: `${(project.hours / sub.total_working_hours) * 100}%`,
                          }}
                        >
                          {(
                            (project.hours / sub.total_working_hours) *
                            100
                          ).toFixed(1)}
                          %
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Tasks Breakdown */}
      <div className="card mb-4">
        <div className="card-header bg-success text-white">
          <h5 className="mb-0">
            <i className="fa fa-tasks"></i> Hours by Task
          </h5>
        </div>
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-striped table-bordered">
              <thead className="table-dark">
                <tr>
                  <th>#</th>
                  <th>Task</th>
                  <th>Project</th>
                  <th>Total Hours</th>
                  <th>Entries</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task, index) => (
                  <tr key={index}>
                    <td>{index + 1}</td>
                    <td>{task.task}</td>
                    <td>{task.project}</td>
                    <td>{task.hours.toFixed(2)}</td>
                    <td>{task.entries}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
                    <td>{ts.date}</td>
                    <td>{ts.project || "-"}</td>
                    <td>{ts.task || "-"}</td>
                    <td>{ts.activity_type || "-"}</td>
                    <td>{ts.hours.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SubmissionDetails;
