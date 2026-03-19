import React from "react";

function NotFound({ onBackToHome }) {
  return (
    <div className="container">
      <div className="row justify-content-center align-items-center vh-100">
        <div className="col-md-6 text-center">
          <i className="fa fa-exclamation-triangle text-warning" style={{ fontSize: "5rem" }}></i>
          <h1 className="mt-4">404 - Page Not Found</h1>
          <p className="text-muted mb-4">
            The page you're looking for doesn't exist or the employee was not found.
          </p>
          <button className="btn btn-primary btn-lg" onClick={onBackToHome}>
            <i className="fa fa-home"></i> Go to Home
          </button>
        </div>
      </div>
    </div>
  );
}

export default NotFound;