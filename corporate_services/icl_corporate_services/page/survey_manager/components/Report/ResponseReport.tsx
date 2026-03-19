import React from "react";
import { Analytics } from "../types";
import { QuestionReportCard } from "./QuestionReportCard";
import { Spinner } from "../ui/Spinner";
import { Fade } from "../ui/Fade";

interface ResponseReportProps {
  analytics: Analytics | null;
  loading: boolean;
  onLoad: () => void;
  totalSubmissions: number;
}

export function ResponseReport({
  analytics,
  loading,
  onLoad,
  totalSubmissions,
}: ResponseReportProps) {
  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center gap-2 py-5 text-muted">
        <Spinner />
        <span>Loading report…</span>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-5">
        <div style={{ fontSize: 44, lineHeight: 1, marginBottom: 12 }}>📊</div>
        <div className="fw-semibold mb-1" style={{ fontSize: 16 }}>
          Response Report
        </div>
        <div className="text-muted small mb-4" style={{ maxWidth: 340, margin: "0 auto 20px" }}>
          View per-question grouped results across all{" "}
          <strong>{totalSubmissions}</strong> submission
          {totalSubmissions !== 1 ? "s" : ""}.
        </div>
        <button
          className="btn btn-primary btn-sm px-4"
          type="button"
          onClick={onLoad}
        >
          Load Report
        </button>
      </div>
    );
  }

  // Derived stats
  const avgRate =
    analytics.questions.length > 0
      ? Math.round(
          analytics.questions.reduce((sum, q) => {
            const r =
              analytics.total_responses > 0
                ? (q.response_count / analytics.total_responses) * 100
                : 0;
            return sum + r;
          }, 0) / analytics.questions.length
        )
      : 0;

  const openEndedCount = analytics.questions.filter(
    (q) => q.question_type === "TEXT"
  ).length;

  const stats = [
    {
      icon: "📬",
      num: analytics.total_responses,
      label: "Total Responses",
      color: "var(--primary, #5e64ff)",
    },
    {
      icon: "❓",
      num: analytics.questions.length,
      label: "Questions",
      color: "#0d6efd",
    },
    {
      icon: "✍️",
      num: openEndedCount,
      label: "Open-ended",
      color: "#6610f2",
    },
    {
      icon: "✅",
      num: `${avgRate}%`,
      label: "Avg. Response Rate",
      color: avgRate >= 75 ? "#28a745" : avgRate >= 50 ? "#fd7e14" : "#dc3545",
    },
  ];

  return (
    <Fade>
      {/* ── Summary strip ─────────────────────────────────────────────────── */}
      <div
        className="d-flex mb-4 rounded overflow-hidden"
        style={{
          border: "1px solid var(--border-color, #e2e6ea)",
          background: "var(--subtle-fg, #f8f9fa)",
        }}
      >
        {stats.map((s, i) => (
          <React.Fragment key={s.label}>
            {i > 0 && <div className="sm-vr" />}
            <div className="sm-stat-card">
              <span className="sm-stat-icon">{s.icon}</span>
              <div
                className="sm-stat-num"
                style={{ color: s.color }}
              >
                {s.num}
              </div>
              <div className="sm-stat-label">{s.label}</div>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* ── Refresh + section heading ───────────────────────────────────── */}
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h6 className="fw-bold mb-0" style={{ fontSize: 14 }}>
          Per-question Results
        </h6>
        <button
          className="btn btn-sm btn-outline-secondary"
          type="button"
          onClick={onLoad}
          style={{ fontSize: 12 }}
          title="Refresh report data"
        >
          ↻ Refresh
        </button>
      </div>

      {/* ── Per-question cards ─────────────────────────────────────────────── */}
      {analytics.questions.length === 0 ? (
        <div className="text-muted text-center py-4">No questions found.</div>
      ) : (
        analytics.questions.map((q, i) => (
          <QuestionReportCard
            key={q.name}
            question={q}
            totalResponses={analytics.total_responses}
            questionNumber={i + 1}
          />
        ))
      )}
    </Fade>
  );
}
