import React from "react";
import { SurveyRow } from "../types";

interface SurveyCardProps {
  survey: SurveyRow;
  isActive: boolean;
  isNew?: boolean;
  onClick: () => void;
}

export function SurveyCard({ survey, isActive, isNew, onClick }: SurveyCardProps) {
  const isPublished = !!survey.is_published;

  const cardClass = [
    "sm-card card mb-2",
    isActive ? "sm-card-active" : "",
    !isNew && isPublished ? "sm-card-published" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={cardClass}
      onClick={onClick}
      style={{
        borderRadius: 8,
        border: "1px solid var(--border-color, #e2e6ea)",
        paddingLeft: 3,
      }}
    >
      <div className="card-body py-2 px-3">
        <div className="d-flex align-items-center justify-content-between gap-2">
          {/* Left: title + meta */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              className="fw-semibold text-truncate"
              style={{ fontSize: 13, lineHeight: 1.4 }}
              title={survey.title}
            >
              {isNew ? (
                <em className="text-muted">(New Survey)</em>
              ) : (
                survey.title || <span className="text-muted">Untitled</span>
              )}
            </div>

            <div
              className="d-flex align-items-center gap-2 mt-1"
              style={{ fontSize: 11 }}
            >
              {isNew ? (
                <span className="text-warning fw-semibold">Unsaved</span>
              ) : (
                <>
                  {/* Status dot */}
                  <span
                    className="sm-status-dot"
                    style={{
                      background: isPublished ? "#28a745" : "#adb5bd",
                    }}
                    title={isPublished ? "Published" : "Draft"}
                  />
                  <span className="text-muted">
                    {survey.year}
                    {survey.departments
                      ? ` · ${survey.departments}`
                      : ""}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Right: response count */}
          {!isNew && (
            <div
              className="text-muted text-end flex-shrink-0"
              style={{ fontSize: 11 }}
            >
              <div className="fw-semibold" style={{ fontSize: 13 }}>
                {survey.total_submissions ?? 0}
              </div>
              <div>resp.</div>
            </div>
          )}

          {isNew && (
            <span
              className="badge bg-warning text-dark flex-shrink-0"
              style={{ fontSize: 10 }}
            >
              New
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
