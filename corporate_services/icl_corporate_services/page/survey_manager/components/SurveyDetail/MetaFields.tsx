import React from "react";
import { SurveyDoc } from "../types";

interface MetaFieldsProps {
  doc: SurveyDoc;
  publicUrl: string;
  linkCopied: boolean;
  onUpdate: (updater: (d: SurveyDoc) => SurveyDoc) => void;
  onCopyLink: () => void;
}

export function MetaFields({
  doc,
  publicUrl,
  linkCopied,
  onUpdate,
  onCopyLink,
}: MetaFieldsProps) {
  return (
    <div className="row g-3">
      {/* Title */}
      <div className="col-md-8">
        <label className="form-label fw-semibold" style={{ fontSize: 13 }}>
          Title <span className="text-danger">*</span>
        </label>
        <input
          className="form-control"
          placeholder="e.g. Annual Staff Satisfaction Survey 2025"
          value={doc.title}
          onChange={(e) => onUpdate((d) => ({ ...d, title: e.target.value }))}
        />
      </div>

      {/* Year */}
      <div className="col-md-4">
        <label className="form-label fw-semibold" style={{ fontSize: 13 }}>
          Year <span className="text-danger">*</span>
        </label>
        <input
          className="form-control"
          type="number"
          min={2000}
          max={2100}
          value={doc.year}
          onChange={(e) => onUpdate((d) => ({ ...d, year: Number(e.target.value) }))}
        />
      </div>

      {/* Description */}
      <div className="col-12">
        <label className="form-label fw-semibold" style={{ fontSize: 13 }}>
          Description
        </label>
        <textarea
          className="form-control"
          rows={2}
          placeholder="Brief description of the survey purpose"
          value={doc.description ?? ""}
          onChange={(e) => onUpdate((d) => ({ ...d, description: e.target.value }))}
          style={{ resize: "vertical" }}
        />
      </div>

      {/* Departments */}
      <div className="col-12">
        <label className="form-label fw-semibold" style={{ fontSize: 13 }}>
          Departments
        </label>
        <input
          className="form-control"
          placeholder="e.g. Accounts, DISAH (leave blank for all)"
          value={doc.departments ?? ""}
          onChange={(e) => onUpdate((d) => ({ ...d, departments: e.target.value }))}
        />
      </div>

      {/* Public link - only shown for saved surveys */}
      {!doc.__islocal && publicUrl && (
        <div className="col-12">
          <label className="form-label fw-semibold" style={{ fontSize: 13 }}>
            Public Link
          </label>
          <div className="input-group">
            <input
              className="form-control form-control-sm"
              readOnly
              value={publicUrl}
              style={{ fontFamily: "monospace", fontSize: 12 }}
            />
            <button
              className={`btn btn-sm ${linkCopied ? "btn-success" : "btn-outline-secondary"}`}
              type="button"
              onClick={onCopyLink}
              style={{ whiteSpace: "nowrap", transition: "all 0.2s ease" }}
            >
              {linkCopied ? "✓ Copied" : "Copy Link"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
