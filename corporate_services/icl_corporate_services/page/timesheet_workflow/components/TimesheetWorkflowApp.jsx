import React, { useEffect, useState } from "react";
import TimesheetSubmissions from "./TimesheetSubmissions";
import SubmissionDetails from "./SubmissionDetails";

function TimesheetWorkflowApp() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showAllSubmissions, setShowAllSubmissions] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState(null);

  useEffect(() => {
    frappe.call({
      method:
        "corporate_services.icl_corporate_services.page.timesheet_workflow.timesheet_workflow.get_all_employees",
      callback: (r) => {
        setEmployees(r.message || []);
        setLoading(false);
      },
    });
  }, []);

  useEffect(() => {
    let isHandling = false;

    const handleRouteChange = () => {
      if (isHandling) {
        console.log("Already handling route change, skipping...");
        return;
      }

      isHandling = true;
      const route = frappe.get_route();
      console.log("Route changed:", route);

      if (route.length > 1 && route[0] === "timesheet_workflow") {
        if (route[1] === "all-submissions") {
          console.log("Setting all submissions view");
          setShowAllSubmissions(true);
          setSelectedEmployee(null);
          setSelectedSubmission(null);
        } else if (route[1] === "employee" && route[2]) {
          const employeeId = decodeURIComponent(route[2]);
          
          // Check if it's a submission detail route
          if (route[3] === "submission" && route[4]) {
            const submissionId = decodeURIComponent(route[4]);
            const emp = employees.find(
              (e) => e.name === employeeId || e.employee_name === employeeId
            );
            if (emp) {
              setSelectedEmployee(emp);
              setSelectedSubmission({ name: submissionId });
              setShowAllSubmissions(false);
            }
          } else {
            // Regular employee view
            const emp = employees.find(
              (e) => e.name === employeeId || e.employee_name === employeeId
            );
            if (emp) {
              console.log("Found employee:", emp);
              setSelectedEmployee(emp);
              setSelectedSubmission(null);
              setShowAllSubmissions(false);
            } else {
              console.log("Employee not found, available employees:", employees);
            }
          }
        } else {
          setShowAllSubmissions(false);
          setSelectedEmployee(null);
          setSelectedSubmission(null);
        }
      } else if (route[0] === "timesheet_workflow" && route.length === 1) {
        console.log("Setting default view");
        setShowAllSubmissions(false);
        setSelectedEmployee(null);
        setSelectedSubmission(null);
      }

      setTimeout(() => {
        isHandling = false;
      }, 100);
    };

    if (!loading && employees.length > 0) {
      handleRouteChange();
    }

    frappe.router.on("change", handleRouteChange);

    return () => {
      frappe.router.off("change", handleRouteChange);
    };
  }, [employees, loading]);

  const navigateToAllSubmissions = () => {
    frappe.set_route("timesheet_workflow", "all-submissions");
  };

  const navigateToEmployeeSubmissions = (employee) => {
    console.log("Navigating to employee:", employee);
    frappe.set_route("timesheet_workflow", "employee", employee.name);
  };

  const navigateToSubmissionDetails = (employee, submission) => {
    frappe.set_route("timesheet_workflow", "employee", employee.name, "submission", submission.name);
  };

  const navigateToHome = () => {
    frappe.set_route("timesheet_workflow");
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

  // Show submission details
  if (selectedSubmission && selectedEmployee) {
    return (
      <SubmissionDetails
        submission={selectedSubmission}
        employee={selectedEmployee}
        onBack={() => navigateToEmployeeSubmissions(selectedEmployee)}
      />
    );
  }

  // Show all submissions
  if (showAllSubmissions) {
    return (
      <TimesheetSubmissions
        onBack={navigateToHome}
        onEmployeeClick={(employeeName) => {
          const emp = employees.find(
            (e) => e.employee_name === employeeName || e.name === employeeName
          );
          if (emp) {
            navigateToEmployeeSubmissions(emp);
          }
        }}
        onSubmissionClick={(submission) => {
          const emp = employees.find(
            (e) => e.name === submission.employee || e.employee_name === submission.employee_name
          );
          if (emp) {
            navigateToSubmissionDetails(emp, submission);
          }
        }}
      />
    );
  }

  // Show employee submissions
  if (selectedEmployee) {
    return (
      <TimesheetSubmissions
        employee={selectedEmployee}
        onBack={navigateToHome}
        onSubmissionClick={(submission) => {
          navigateToSubmissionDetails(selectedEmployee, submission);
        }}
      />
    );
  }

  // Show employee list (home)
  return (
    <div className="container py-5">
      <div className="mb-3 text-end">
        <button className="btn btn-primary" onClick={navigateToAllSubmissions}>
          View All Timesheet Submissions
        </button>
      </div>
      <div className="table-responsive">
        <table className="table table-striped table-bordered">
          <thead className="table-dark">
            <tr>
              <th>#</th>
              <th>Employee Name</th>
              <th>Department</th>
              <th>Designation</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((emp, index) => (
              <tr key={emp.name}>
                <td>{index + 1}</td>
                <td>{emp.employee_name || emp.name}</td>
                <td>{emp.department || "-"}</td>
                <td>{emp.designation || "-"}</td>
                <td>
                  <button
                    className="btn btn-sm btn-primary me-2"
                    onClick={() => navigateToEmployeeSubmissions(emp)}
                  >
                    View Timesheet Submissions
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TimesheetWorkflowApp;