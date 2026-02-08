import React, { useEffect, useState } from "react";

function TimesheetSubmissions({ employee = null, onBack }) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('TimesheetSubmissions - Employee prop:', employee);
    
    const method = employee
      ? "corporate_services.icl_corporate_services.page.timesheet_workflow.timesheet_workflow.get_timesheet_submissions_by_employee"
      : "corporate_services.icl_corporate_services.page.timesheet_workflow.timesheet_workflow.get_all_timesheet_submissions";

    const args = employee ? { employee_name: employee.employee_name } : {};
    
    console.log('Making API call with method:', method, 'and args:', args);

    frappe.call({
      method: method,
      args: args,
      callback: (r) => {
        console.log('API response:', r.message);
        setSubmissions(r.message || []);
        setLoading(false);
      },
    });
  }, [employee]);

  useEffect(() => {
    if (submissions.length > 0) {
      renderCharts();
    }
  }, [submissions]);

  const renderCharts = () => {
    if (typeof window.Chart === "undefined") {
      console.error("Chart.js is not loaded");
      return;
    }

    const Chart = window.Chart;

    const chartIds = [
      "hoursChart",
      "statusChart",
      "trendChart",
      "employeeChart",
    ];
    chartIds.forEach((id) => {
      const existingChart = Chart.getChart(id);
      if (existingChart) {
        existingChart.destroy();
      }
    });

    const hoursCtx = document.getElementById("hoursChart");
    if (hoursCtx) {
      const monthlyData = {};
      submissions.forEach((ts) => {
        const month = ts.month_year || "Unknown";
        if (!monthlyData[month]) {
          monthlyData[month] = 0;
        }
        monthlyData[month] += parseFloat(ts.total_working_hours || 0);
      });

      new Chart(hoursCtx, {
        type: "bar",
        data: {
          labels: Object.keys(monthlyData),
          datasets: [
            {
              label: "Total Hours",
              data: Object.values(monthlyData),
              backgroundColor: "rgba(54, 162, 235, 0.6)",
              borderColor: "rgba(54, 162, 235, 1)",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: "Total Hours by Month",
              font: { size: 16 },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: "Hours",
              },
            },
          },
        },
      });
    }

    const statusCtx = document.getElementById("statusChart");
    if (statusCtx) {
      const statusData = {};
      submissions.forEach((ts) => {
        const status = ts.status || "Unknown";
        statusData[status] = (statusData[status] || 0) + 1;
      });

      const colors = {
        Open: "rgba(255, 206, 86, 0.6)",
        Approved: "rgba(75, 192, 192, 0.6)",
        Rejected: "rgba(255, 99, 132, 0.6)",
        Cancelled: "rgba(201, 203, 207, 0.6)",
      };

      new Chart(statusCtx, {
        type: "doughnut",
        data: {
          labels: Object.keys(statusData),
          datasets: [
            {
              data: Object.values(statusData),
              backgroundColor: Object.keys(statusData).map(
                (status) => colors[status] || "rgba(153, 102, 255, 0.6)",
              ),
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: "Submission Status Distribution",
              font: { size: 16 },
            },
            legend: {
              position: "bottom",
            },
          },
        },
      });
    }

    const trendCtx = document.getElementById("trendChart");
    if (trendCtx) {
      const sortedSubmissions = [...submissions].sort(
        (a, b) => new Date(a.creation) - new Date(b.creation),
      );

      const trendData = {};
      sortedSubmissions.forEach((ts) => {
        const month = ts.month_year || "Unknown";
        if (!trendData[month]) {
          trendData[month] = 0;
        }
        trendData[month]++;
      });

      new Chart(trendCtx, {
        type: "line",
        data: {
          labels: Object.keys(trendData),
          datasets: [
            {
              label: "Number of Submissions",
              data: Object.values(trendData),
              borderColor: "rgba(75, 192, 192, 1)",
              backgroundColor: "rgba(75, 192, 192, 0.2)",
              tension: 0.4,
              fill: true,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: "Submission Trend Over Time",
              font: { size: 16 },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                stepSize: 1,
              },
              title: {
                display: true,
                text: "Submissions",
              },
            },
          },
        },
      });
    }

    if (!employee) {
      const employeeCtx = document.getElementById("employeeChart");
      if (employeeCtx) {
        const employeeData = {};
        submissions.forEach((ts) => {
          const empName = ts.employee_name || ts.employee || "Unknown";
          if (!employeeData[empName]) {
            employeeData[empName] = 0;
          }
          employeeData[empName] += parseFloat(ts.total_working_hours || 0);
        });

        const sortedEmployees = Object.entries(employeeData)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 10);

        new Chart(employeeCtx, {
          type: "bar",
          data: {
            labels: sortedEmployees.map((e) => e[0]),
            datasets: [
              {
                label: "Total Hours",
                data: sortedEmployees.map((e) => e[1]),
                backgroundColor: "rgba(153, 102, 255, 0.6)",
                borderColor: "rgba(153, 102, 255, 1)",
                borderWidth: 1,
              },
            ],
          },
          options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: "Top 10 Employees by Total Hours",
                font: { size: 16 },
              },
            },
            scales: {
              x: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: "Hours",
                },
              },
            },
          },
        });
      }
    }
  };

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
      {employee && (
        <button className="btn btn-secondary mb-3" onClick={onBack}>
          ← Back to Employees
        </button>
      )}
      <h1 className="mb-4 text-center">
        {employee
          ? `${employee.employee_name}'s Timesheet Submissions`
          : "All Timesheet Submissions"}
      </h1>

      <div className="row mb-4">
        <div className="col-md-3">
          <div className="card">
            <div className="card-body text-center">
              <div className="text-muted small">Total Submissions</div>
              <div className="h3 mt-2 mb-0">{submissions.length}</div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card">
            <div className="card-body text-center">
              <div className="text-muted small">Total Hours</div>
              <div className="h3 mt-2 mb-0">
                {submissions
                  .reduce(
                    (sum, ts) => sum + parseFloat(ts.total_working_hours || 0),
                    0,
                  )
                  .toFixed(1)}
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card">
            <div className="card-body text-center">
              <div className="text-muted small">Approved</div>
              <div className="h3 mt-2 mb-0">
                {submissions.filter((ts) => ts.status === "Approved").length}
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card">
            <div className="card-body text-center">
              <div className="text-muted small">Pending</div>
              <div className="h3 mt-2 mb-0">
                {submissions.filter((ts) => ts.status === "Open").length}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row g-4 mb-5">
        <div className="col-lg-6">
          <div className="card">
            <div className="card-body" style={{ height: "350px" }}>
              <canvas id="hoursChart"></canvas>
            </div>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card">
            <div className="card-body" style={{ height: "350px" }}>
              <canvas id="statusChart"></canvas>
            </div>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card">
            <div className="card-body" style={{ height: "350px" }}>
              <canvas id="trendChart"></canvas>
            </div>
          </div>
        </div>

        {!employee && (
          <div className="col-lg-6">
            <div className="card">
              <div className="card-body" style={{ height: "350px" }}>
                <canvas id="employeeChart"></canvas>
              </div>
            </div>
          </div>
        )}
      </div>

      <h3 className="mb-3">Submission Details</h3>
      <div className="table-responsive">
        <table className="table table-striped table-bordered">
          <thead className="table-dark">
            <tr>
              <th>#</th>
              <th>Employee</th>
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
                <td>{ts.employee_name || ts.employee}</td>
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
    </div>
  );
}

export default TimesheetSubmissions;