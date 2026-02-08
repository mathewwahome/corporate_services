import React, { useEffect, useState } from "react";

function EmployeeTimesheets({ employee, onBack }) {
    const [timesheets, setTimesheets] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        frappe.call({
            method: "corporate_services.icl_corporate_services.page.timesheet_workflow.timesheet_workflow.get_employee_timesheets",
            args: { employee_name: employee.name },
            callback: (r) => {
                setTimesheets(r.message || []);
                setLoading(false);
            },
            error: (err) => {
                console.error("Error fetching timesheets:", err);
                setLoading(false);
            }
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
            <button className="btn btn-secondary mb-4" onClick={onBack}>
                ← Back to Employees
            </button>

            <h2 className="mb-3">{employee.employee_name || employee.name}</h2>
            <p><strong>Department:</strong> {employee.department || "-"}</p>
            <p><strong>Designation:</strong> {employee.designation || "-"}</p>

            <h3 className="mt-4 mb-3">Timesheets</h3>
            <div className="table-responsive">
                <table className="table table-striped table-bordered">
                    <thead className="table-dark">
                        <tr>
                            <th>#</th>
                            <th>Project</th>
                            <th>Task</th>
                            <th>Hours</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {timesheets.map((ts, index) => (
                            <tr key={index}>
                                <td>{index + 1}</td>
                                <td>{ts.project || "-"}</td>
                                <td>{ts.task || "-"}</td>
                                <td>{ts.hours || 0}</td>
                                <td>{ts.start_date || "-"}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default EmployeeTimesheets;
