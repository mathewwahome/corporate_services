import React, { useState } from "react";
import { SurveySectionRow, SurveyQuestionRow } from "../types";
import { QuestionEditor } from "./QuestionEditor";

interface SectionEditorProps {
  section: SurveySectionRow;
  sectionIdx: number;
  onUpdateSection: (updater: (s: SurveySectionRow) => SurveySectionRow) => void;
  onRemove: () => void;
  onAddQuestion: () => void;
  onRemoveQuestion: (qIdx: number) => void;
  onUpdateQuestion: (
    qIdx: number,
    updater: (q: SurveyQuestionRow) => SurveyQuestionRow
  ) => void;
}

export function SectionEditor({
  section,
  sectionIdx,
  onUpdateSection,
  onRemove,
  onAddQuestion,
  onRemoveQuestion,
  onUpdateQuestion,
}: SectionEditorProps) {
  const [open, setOpen] = useState(true);

  return (
    <div
      className="card border mb-3"
      style={{ borderRadius: 8, overflow: "hidden" }}
    >
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div
        className="card-header d-flex align-items-center gap-2 py-2 px-3"
        style={{
          background: "var(--subtle-fg, #f8f9fa)",
          borderBottom: "1px solid var(--border-color, #e2e6ea)",
          minHeight: 44,
        }}
      >
        {/* Animated caret */}
        <button
          className="btn btn-sm btn-link p-0 text-decoration-none d-flex align-items-center justify-content-center"
          type="button"
          onClick={() => setOpen((o) => !o)}
          style={{ width: 20, height: 20, flexShrink: 0 }}
          aria-expanded={open}
          aria-label={open ? "Collapse section" : "Expand section"}
        >
          <span className={`sm-caret${open ? " open" : ""}`}>▶</span>
        </button>

        {/* Section number badge */}
        <span
          className="badge bg-secondary flex-shrink-0"
          style={{ fontSize: 10 }}
        >
          S{sectionIdx + 1}
        </span>

        {/* Section title */}
        <input
          className="form-control form-control-sm flex-grow-1"
          style={{ maxWidth: 340, fontSize: 13 }}
          placeholder="Section title"
          value={section.title}
          onClick={(e) => e.stopPropagation()}
          onChange={(e) =>
            onUpdateSection((s) => ({ ...s, title: e.target.value }))
          }
        />

        {/* Order number */}
        <div
          className="d-flex align-items-center gap-1 flex-shrink-0"
          title="Section order"
        >
          <span className="text-muted" style={{ fontSize: 11 }}>
            #
          </span>
          <input
            className="form-control form-control-sm"
            style={{ width: 52, fontSize: 12, textAlign: "center" }}
            type="number"
            min={1}
            value={section.order}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) =>
              onUpdateSection((s) => ({ ...s, order: Number(e.target.value) }))
            }
          />
        </div>

        {/* Collapsed question count hint */}
        {!open && section.questions.length > 0 && (
          <span className="text-muted ms-1" style={{ fontSize: 11, flexShrink: 0 }}>
            {section.questions.length}Q
          </span>
        )}

        {/* Action buttons */}
        <div className="d-flex gap-2 ms-auto flex-shrink-0">
          <button
            className="btn btn-sm btn-outline-primary"
            type="button"
            onClick={onAddQuestion}
            style={{ fontSize: 12 }}
          >
            + Question
          </button>
          <button
            className="btn btn-sm btn-outline-danger"
            type="button"
            onClick={onRemove}
            style={{ fontSize: 12 }}
            title="Remove section"
          >
            Remove
          </button>
        </div>
      </div>

      {/* ── Questions body — smooth CSS collapse ────────────────────────── */}
      <div className={`sm-section-body ${open ? "open" : "closed"}`}>
        <div className="card-body p-3">
          {section.questions.length === 0 ? (
            <div
              className="text-center text-muted py-3 rounded"
              style={{
                fontSize: 13,
                border: "1px dashed var(--border-color, #dee2e6)",
              }}
            >
              No questions yet.{" "}
              <button
                className="btn btn-link btn-sm p-0"
                type="button"
                onClick={onAddQuestion}
              >
                Add the first question
              </button>
            </div>
          ) : (
            section.questions.map((q, qi) => (
              <QuestionEditor
                key={q.name || q.__temporary_name || `q-${sectionIdx}-${qi}`}
                question={q}
                qIdx={qi}
                onUpdate={(updater) => onUpdateQuestion(qi, updater)}
                onRemove={() => onRemoveQuestion(qi)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
