import React, { useEffect, useState } from "react";
import { AnalyticsQuestion } from "../types";
import { BarChart, BarChartItem } from "./BarChart";
import { TextResponseList } from "./TextResponseList";

const TYPE_LABELS: Record<string, string> = {
  TEXT: "Free Text",
  SINGLE_SELECT: "Single Select",
  MULTI_SELECT: "Multi Select",
  RATING: "Rating",
};

const TYPE_BADGE_COLOR: Record<string, string> = {
  TEXT: "#6c757d",
  SINGLE_SELECT: "#0d6efd",
  MULTI_SELECT: "#6610f2",
  RATING: "#fd7e14",
};

interface QuestionReportCardProps {
  question: AnalyticsQuestion;
  totalResponses: number;
  questionNumber: number;
}

export function QuestionReportCard({
  question,
  totalResponses,
  questionNumber,
}: QuestionReportCardProps) {
  const [expanded, setExpanded] = useState(true);
  const [rateMounted, setRateMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setRateMounted(true), 80);
    return () => clearTimeout(t);
  }, []);

  const hasAggregation =
    (question.question_type === "SINGLE_SELECT" ||
      question.question_type === "MULTI_SELECT" ||
      question.question_type === "RATING") &&
    Object.keys(question.aggregation).length > 0;

  const barItems: BarChartItem[] = hasAggregation
    ? Object.entries(question.aggregation)
        .map(([label, count]) => ({ label, count }))
        .sort((a, b) => b.count - a.count)
    : [];

  const skipCount = totalResponses - question.response_count;
  const responseRate =
    totalResponses > 0
      ? Math.round((question.response_count / totalResponses) * 100)
      : 0;

  const badgeColor = TYPE_BADGE_COLOR[question.question_type] ?? "#6c757d";

  return (
    <div
      className="card border mb-3"
      style={{ borderRadius: 8, overflow: "hidden" }}
    >
      {/* ── Card header ─────────────────────────────────────────────────── */}
      <div
        className="card-header px-3 py-2"
        style={{
          background: "var(--subtle-fg, #f8f9fa)",
          cursor: "pointer",
        }}
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="d-flex align-items-start gap-3">
          {/* Question number */}
          <span
            className="fw-bold flex-shrink-0"
            style={{
              fontSize: 13,
              color: "var(--primary, #5e64ff)",
              minWidth: 28,
              paddingTop: 1,
            }}
          >
            Q{questionNumber}
          </span>

          {/* Question text + type badge + section */}
          <div className="flex-grow-1" style={{ minWidth: 0 }}>
            <div
              className="fw-semibold"
              style={{ fontSize: 13, lineHeight: 1.45 }}
            >
              {question.question_text}
            </div>
            <div className="d-flex align-items-center gap-2 mt-1 flex-wrap">
              <span
                className="badge"
                style={{ background: badgeColor, color: "#fff", fontSize: 10 }}
              >
                {TYPE_LABELS[question.question_type] ?? question.question_type}
              </span>
              <span className="text-muted" style={{ fontSize: 11 }}>
                {question.section}
              </span>
            </div>
          </div>

          {/* Response stats + mini rate bar */}
          <div
            className="text-end flex-shrink-0"
            style={{ minWidth: 90 }}
          >
            <div style={{ fontSize: 13 }}>
              <span className="fw-semibold">{question.response_count}</span>
              <span className="text-muted fw-normal" style={{ fontSize: 11 }}>
                /{totalResponses}
              </span>
            </div>
            <div className="text-muted" style={{ fontSize: 10, whiteSpace: "nowrap" }}>
              {responseRate}% answered
              {skipCount > 0 && ` · ${skipCount} skipped`}
            </div>
            {/* Mini progress bar */}
            <div className="sm-rate-track" style={{ minWidth: 80 }}>
              <div
                className="sm-rate-fill"
                style={{
                  width: rateMounted ? `${responseRate}%` : "0%",
                  background:
                    responseRate >= 80
                      ? "#28a745"
                      : responseRate >= 50
                      ? "var(--primary, #5e64ff)"
                      : "#fd7e14",
                }}
              />
            </div>
          </div>

          {/* Caret */}
          <span
            className={`sm-caret flex-shrink-0${expanded ? " open" : ""}`}
            style={{ marginTop: 3 }}
          >
            ▶
          </span>
        </div>
      </div>

      {/* ── Card body — smooth collapse ──────────────────────────────────── */}
      <div className={`sm-section-body ${expanded ? "open" : "closed"}`}>
        <div className="card-body p-3">
          {hasAggregation && (
            <BarChart items={barItems} total={question.response_count} />
          )}

          {question.question_type === "TEXT" && (
            <TextResponseList responses={question.text_responses} />
          )}

          {!hasAggregation && question.question_type !== "TEXT" && (
            <div className="text-muted small">No responses recorded.</div>
          )}
        </div>
      </div>
    </div>
  );
}
