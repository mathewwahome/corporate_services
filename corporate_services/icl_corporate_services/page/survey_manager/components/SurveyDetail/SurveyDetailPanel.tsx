import React, { useState, useEffect } from "react";
import { SurveyDoc, SurveyRow, SurveyQuestionRow, Analytics } from "../types";
import { Spinner } from "../ui/Spinner";
import { Fade } from "../ui/Fade";
import { Badge } from "../ui/Badge";
import { MetaFields } from "./MetaFields";
import { SectionEditor } from "./SectionEditor";
import { ResponseReport } from "../Report/ResponseReport";

type TabId = "edit" | "report";

interface SurveyDetailPanelProps {
  selectedRow: SurveyRow | null;
  doc: SurveyDoc | null;
  docLoading: boolean;
  docError: string | null;
  dirty: boolean;
  isNew: boolean;
  analytics: Analytics | null;
  analyticsLoading: boolean;
  publicUrl: string;
  linkCopied: boolean;
  onUpdateDoc: (updater: (d: SurveyDoc) => SurveyDoc) => void;
  onSave: () => void;
  onCancelNew: () => void;
  onTogglePublish: () => void;
  onLoadAnalytics: () => void;
  onAddSection: () => void;
  onRemoveSection: (idx: number) => void;
  onAddQuestion: (sectionIdx: number) => void;
  onRemoveQuestion: (sectionIdx: number, qIdx: number) => void;
  onCopyLink: () => void;
}

export function SurveyDetailPanel({
  selectedRow,
  doc,
  docLoading,
  docError,
  dirty,
  isNew,
  analytics,
  analyticsLoading,
  publicUrl,
  linkCopied,
  onUpdateDoc,
  onSave,
  onCancelNew,
  onTogglePublish,
  onLoadAnalytics,
  onAddSection,
  onRemoveSection,
  onAddQuestion,
  onRemoveQuestion,
  onCopyLink,
}: SurveyDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("edit");

  // Reset to edit tab and auto-load analytics when switching surveys
  useEffect(() => {
    setActiveTab("edit");
  }, [selectedRow?.name]);

  // Auto-trigger analytics load when switching to the report tab
  useEffect(() => {
    if (activeTab === "report" && !analytics && !analyticsLoading) {
      onLoadAnalytics();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const hasSubmissions = (selectedRow?.total_submissions ?? 0) > 0;

  // ── Empty state ──────────────────────────────────────────────────────────
  if (!doc && !docLoading) {
    return (
      <div className="flex-grow-1 d-flex flex-column align-items-center justify-content-center text-muted">
        <div style={{ fontSize: 48, lineHeight: 1, marginBottom: 12 }}>📋</div>
        <div className="fw-semibold">Select a survey</div>
        <div className="small mt-1">
          Choose a survey from the list, or create a new one.
        </div>
      </div>
    );
  }

  // ── Initial load spinner ─────────────────────────────────────────────────
  if (docLoading && !doc) {
    return (
      <div className="flex-grow-1 d-flex align-items-center justify-content-center gap-2 text-muted">
        <Spinner />
        <span>Loading survey…</span>
      </div>
    );
  }

  return (
    <div className="flex-grow-1 d-flex flex-column overflow-hidden">
      {/* ── Page header ────────────────────────────────────────────────────── */}
      <div
        className="px-4 pt-3 pb-0"
        style={{ borderBottom: "1px solid var(--border-color, #e2e6ea)" }}
      >
        <div className="d-flex align-items-start justify-content-between mb-2 gap-3">
          {/* Title + meta */}
          <div style={{ minWidth: 0 }}>
            <h5
              className="mb-1 fw-bold text-truncate"
              style={{ fontSize: 18 }}
            >
              {isNew
                ? "New Survey"
                : doc?.title || selectedRow?.title || "Untitled Survey"}
            </h5>
            {!isNew && selectedRow && (
              <div
                className="d-flex align-items-center gap-2 flex-wrap"
                style={{ fontSize: 12 }}
              >
                <Badge published={!!selectedRow.is_published} />
                <span className="text-muted">
                  {selectedRow.total_submissions ?? 0} response
                  {(selectedRow.total_submissions ?? 0) !== 1 ? "s" : ""}
                </span>
                {selectedRow.modified && (
                  <span className="text-muted">
                    · Last modified{" "}
                    {new Date(selectedRow.modified).toLocaleDateString()}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Toolbar */}
          <div
            className="d-flex align-items-center gap-2 flex-wrap flex-shrink-0"
          >
            {dirty && (
              <span
                className="badge bg-warning text-dark sm-unsaved-badge"
                style={{ fontSize: 11 }}
              >
                ● Unsaved changes
              </span>
            )}

            {/* Publish toggle (existing surveys only) */}
            {!isNew && (
              <button
                className={`btn btn-sm ${
                  selectedRow?.is_published
                    ? "btn-outline-secondary"
                    : "btn-success"
                }`}
                type="button"
                onClick={onTogglePublish}
                disabled={!selectedRow?.name || docLoading}
                style={{ transition: "all 0.2s ease" }}
              >
                {selectedRow?.is_published ? "Unpublish" : "Publish"}
              </button>
            )}

            {/* Cancel (new surveys only) */}
            {isNew && (
              <button
                className="btn btn-sm btn-outline-secondary"
                type="button"
                onClick={onCancelNew}
              >
                Cancel
              </button>
            )}

            {/* Save */}
            <button
              className="btn btn-sm btn-primary"
              type="button"
              onClick={onSave}
              disabled={!dirty || docLoading}
            >
              {docLoading ? (
                <>
                  <Spinner size="sm" />
                  <span className="ms-1">Saving…</span>
                </>
              ) : (
                "Save"
              )}
            </button>
          </div>
        </div>

        {/* ── Tab navigation ──────────────────────────────────────────────── */}
        <ul className="nav" style={{ gap: 4, marginBottom: -1 }}>
          <li className="nav-item">
            <button
              type="button"
              className={`sm-nav-tab nav-link px-3 py-2${activeTab === "edit" ? " active" : ""}`}
              style={{ fontSize: 13 }}
              onClick={() => setActiveTab("edit")}
            >
              Edit
            </button>
          </li>
          <li className="nav-item">
            <button
              type="button"
              className={`sm-nav-tab nav-link px-3 py-2${activeTab === "report" ? " active" : ""}${
                !hasSubmissions || isNew ? " disabled text-muted" : ""
              }`}
              style={{ fontSize: 13 }}
              onClick={() => {
                if (hasSubmissions && !isNew) setActiveTab("report");
              }}
              title={
                isNew
                  ? "Save the survey first"
                  : !hasSubmissions
                  ? "No responses yet"
                  : undefined
              }
            >
              Report
              {hasSubmissions && !isNew && (
                <span
                  className="badge bg-primary ms-1"
                  style={{ fontSize: 10, verticalAlign: "middle" }}
                >
                  {selectedRow?.total_submissions}
                </span>
              )}
            </button>
          </li>
        </ul>
      </div>

      {/* ── Tab content ─────────────────────────────────────────────────────── */}
      <div className="flex-grow-1 overflow-auto px-4 py-4">
        {/* Error banner */}
        {docError && (
          <div className="alert alert-danger mb-3 py-2 small">
            <strong>Error:</strong> {docError}
          </div>
        )}

        {/* Edit tab */}
        {activeTab === "edit" && doc && (
          <Fade key={`edit-${selectedRow?.name ?? "new"}`}>
            <MetaFields
              doc={doc}
              publicUrl={publicUrl}
              linkCopied={linkCopied}
              onUpdate={onUpdateDoc}
              onCopyLink={onCopyLink}
            />

            {/* Sections header */}
            <div className="d-flex align-items-center justify-content-between mt-4 mb-3">
              <h6 className="fw-bold mb-0" style={{ fontSize: 14 }}>
                Sections & Questions
              </h6>
              <button
                className="btn btn-sm btn-outline-primary"
                type="button"
                onClick={onAddSection}
                style={{ fontSize: 12 }}
              >
                + Add Section
              </button>
            </div>

            {/* Sections list */}
            {doc.sections.length === 0 ? (
              <div
                className="text-center py-5 rounded"
                style={{
                  border: "2px dashed var(--border-color, #dee2e6)",
                  color: "var(--text-muted)",
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8 }}>📝</div>
                <div className="fw-semibold mb-1">No sections yet</div>
                <div className="small text-muted mb-3">
                  Surveys are organised into sections, each containing questions.
                </div>
                <button
                  className="btn btn-sm btn-primary"
                  type="button"
                  onClick={onAddSection}
                >
                  + Add First Section
                </button>
              </div>
            ) : (
              doc.sections.map((section, si) => (
                <SectionEditor
                  key={
                    section.name ||
                    section.__temporary_name ||
                    `section-${si}`
                  }
                  section={section}
                  sectionIdx={si}
                  onUpdateSection={(updater) =>
                    onUpdateDoc((d) => ({
                      ...d,
                      sections: d.sections.map((s, i) =>
                        i === si ? updater(s) : s
                      ),
                    }))
                  }
                  onRemove={() => onRemoveSection(si)}
                  onAddQuestion={() => onAddQuestion(si)}
                  onRemoveQuestion={(qi) => onRemoveQuestion(si, qi)}
                  onUpdateQuestion={(
                    qi: number,
                    updater: (q: SurveyQuestionRow) => SurveyQuestionRow
                  ) =>
                    onUpdateDoc((d) => ({
                      ...d,
                      sections: d.sections.map((s, i) => {
                        if (i !== si) return s;
                        return {
                          ...s,
                          questions: s.questions.map((q, j) =>
                            j === qi ? updater(q) : q
                          ),
                        };
                      }),
                    }))
                  }
                />
              ))
            )}
          </Fade>
        )}

        {/* Report tab */}
        {activeTab === "report" && (
          <Fade key={`report-${selectedRow?.name}`}>
            <ResponseReport
              analytics={analytics}
              loading={analyticsLoading}
              onLoad={onLoadAnalytics}
              totalSubmissions={selectedRow?.total_submissions ?? 0}
            />
          </Fade>
        )}
      </div>
    </div>
  );
}
