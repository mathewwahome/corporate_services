import React from "react";
import { SurveyQuestionRow, QuestionType } from "../types";

const QUESTION_TYPES: { value: QuestionType; label: string }[] = [
  { value: "TEXT", label: "Free Text" },
  { value: "SINGLE_SELECT", label: "Single Select" },
  { value: "MULTI_SELECT", label: "Multi Select" },
  { value: "RATING", label: "Rating" },
];

interface QuestionEditorProps {
  question: SurveyQuestionRow;
  qIdx: number;
  onUpdate: (updater: (q: SurveyQuestionRow) => SurveyQuestionRow) => void;
  onRemove: () => void;
}

export function QuestionEditor({ question, qIdx, onUpdate, onRemove }: QuestionEditorProps) {
  const hasOptions =
    question.question_type === "SINGLE_SELECT" ||
    question.question_type === "MULTI_SELECT";

  return (
    <div className="sm-question-card card border mb-2">
      <div className="card-body p-3">
        {/* Top row: number + text + type + required + remove */}
        <div className="d-flex gap-2 align-items-start">
          <span
            className="badge bg-light text-secondary border mt-1 flex-shrink-0"
            style={{ fontSize: 11, minWidth: 26, textAlign: "center" }}
          >
            Q{qIdx + 1}
          </span>

          <div className="flex-grow-1">
            <input
              className="form-control form-control-sm mb-2"
              placeholder="Question text…"
              value={question.question_text}
              onChange={(e) =>
                onUpdate((q) => ({ ...q, question_text: e.target.value }))
              }
            />

            {/* Type + Required + Order on one line */}
            <div className="d-flex gap-2 align-items-center flex-wrap">
              <select
                className="form-select form-select-sm"
                style={{ width: 160, fontSize: 12 }}
                value={question.question_type}
                onChange={(e) =>
                  onUpdate((q) => ({
                    ...q,
                    question_type: e.target.value as QuestionType,
                    options: "",
                  }))
                }
              >
                {QUESTION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>

              <label
                className="d-flex align-items-center gap-1 mb-0"
                style={{ fontSize: 12, cursor: "pointer" }}
              >
                <input
                  type="checkbox"
                  className="form-check-input mt-0"
                  checked={!!question.is_required}
                  onChange={(e) =>
                    onUpdate((q) => ({
                      ...q,
                      is_required: e.target.checked ? 1 : 0,
                    }))
                  }
                />
                Required
              </label>

              <div className="d-flex align-items-center gap-1 ms-auto">
                <span className="text-muted" style={{ fontSize: 11 }}>
                  Order:
                </span>
                <input
                  className="form-control form-control-sm"
                  style={{ width: 60, fontSize: 12 }}
                  type="number"
                  min={1}
                  value={question.order}
                  onChange={(e) =>
                    onUpdate((q) => ({ ...q, order: Number(e.target.value) }))
                  }
                />
              </div>
            </div>
          </div>

          <button
            className="btn btn-sm btn-outline-danger flex-shrink-0"
            type="button"
            onClick={onRemove}
            title="Remove question"
            style={{ fontSize: 12 }}
          >
            ✕
          </button>
        </div>

        {/* Options textarea (shown for SINGLE_SELECT / MULTI_SELECT) */}
        {hasOptions && (
          <div className="mt-2">
            <label className="form-label mb-1" style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Options (one per line)
            </label>
            <textarea
              className="form-control form-control-sm"
              rows={3}
              placeholder={"Option A\nOption B\nOption C"}
              value={question.options ?? ""}
              onChange={(e) =>
                onUpdate((q) => ({ ...q, options: e.target.value }))
              }
              style={{ fontFamily: "monospace", fontSize: 12, resize: "vertical" }}
            />
          </div>
        )}

        {/* Follow-up text */}
        <div className="mt-2">
          <input
            className="form-control form-control-sm"
            placeholder="Follow-up question text (optional)"
            value={question.follow_up_text ?? ""}
            onChange={(e) =>
              onUpdate((q) => ({ ...q, follow_up_text: e.target.value }))
            }
            style={{ fontSize: 12 }}
          />
        </div>
      </div>
    </div>
  );
}
