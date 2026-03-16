import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

type QuestionType = "MULTI_SELECT" | "RATING" | "SINGLE_SELECT" | "TEXT";

type Question = {
  name: string;
  question_text: string;
  question_type: QuestionType;
  options?: string;
  max_selections?: number;
  follow_up_text?: string;
  is_required?: number;
  order: number;
};

type Section = {
  name: string;
  title: string;
  order: number;
  questions: Question[];
};

type Survey = {
  name: string;
  title: string;
  description?: string;
  year: number;
  departments?: string;
  sections: Section[];
};

declare global {
  interface Window {
    frappe: any;
  }
}

function useQueryParam(key: string): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

function SurveyPublicApp() {
  const surveyName = useQueryParam("survey");
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [department, setDepartment] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [followUps, setFollowUps] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!surveyName) {
      setError("No survey specified.");
      setLoading(false);
      return;
    }
    window.frappe
      .call<{ message: Survey }>({
        method: "corporate_services.api.survey.get_survey_detail",
        args: { survey: surveyName },
      })
      .then((r: any) => {
        setSurvey(r.message);
      })
      .catch((e: any) => {
        setError(e?.message || "Survey not available.");
      })
      .finally(() => setLoading(false));
  }, [surveyName]);

  const handleSubmit = async () => {
    if (!survey) return;
    setSubmitting(true);
    setError(null);
    const payload = Object.entries(answers)
      .filter(([, v]) => v && v.trim() !== "")
      .map(([question, value]) => ({
        question,
        value,
        follow_up: followUps[question] || null,
      }));
    try {
      await window.frappe.call({
        method: "corporate_services.api.survey.submit_survey_response",
        args: {
          survey: survey.name,
          department: department || null,
          answers: payload,
        },
      });
      setSubmitted(true);
    } catch (e: any) {
      setError(e?.message || "Failed to submit response.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div style={{ padding: 16 }}>Loading survey…</div>;
  if (error) return <div style={{ padding: 16 }}>{error}</div>;
  if (!survey) return <div style={{ padding: 16 }}>Survey not available.</div>;

  if (submitted) {
    return (
      <div style={{ padding: 16 }}>
        <h2>Thank you!</h2>
        <p>Your response has been recorded.</p>
      </div>
    );
  }

  const renderQuestionInput = (q: Question) => {
    const val = answers[q.name] || "";
    const follow = followUps[q.name] || "";
    const opts = (q.options || "").split("\n").filter(Boolean);

    const setVal = (v: string) => setAnswers((prev) => ({ ...prev, [q.name]: v }));
    const setFollow = (v: string) => setFollowUps((prev) => ({ ...prev, [q.name]: v }));

    if (q.question_type === "TEXT") {
      return (
        <>
          <textarea
            className="form-control"
            value={val}
            onChange={(e) => setVal(e.target.value)}
          />
          {q.follow_up_text && val && (
            <div style={{ marginTop: 8 }}>
              <small>{q.follow_up_text}</small>
              <textarea
                className="form-control"
                value={follow}
                onChange={(e) => setFollow(e.target.value)}
              />
            </div>
          )}
        </>
      );
    }

    if (q.question_type === "SINGLE_SELECT") {
      return (
        <>
          {opts.map((o) => (
            <div key={o} className="form-check">
              <input
                className="form-check-input"
                type="radio"
                name={q.name}
                id={`${q.name}-${o}`}
                checked={val === o}
                onChange={() => setVal(o)}
              />
              <label className="form-check-label" htmlFor={`${q.name}-${o}`}>
                {o}
              </label>
            </div>
          ))}
          {q.follow_up_text && val && (
            <div style={{ marginTop: 8 }}>
              <small>{q.follow_up_text}</small>
              <textarea
                className="form-control"
                value={follow}
                onChange={(e) => setFollow(e.target.value)}
              />
            </div>
          )}
        </>
      );
    }

    if (q.question_type === "MULTI_SELECT") {
      const selected = val ? val.split("|||") : [];
      const max = q.max_selections ?? Infinity;
      const toggle = (o: string) => {
        if (selected.includes(o)) {
          setVal(selected.filter((v) => v !== o).join("|||"));
        } else if (selected.length < max) {
          setVal([...selected, o].join("|||"));
        }
      };
      return (
        <>
          {opts.map((o) => (
            <div key={o} className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                id={`${q.name}-${o}`}
                checked={selected.includes(o)}
                onChange={() => toggle(o)}
              />
              <label className="form-check-label" htmlFor={`${q.name}-${o}`}>
                {o}
              </label>
            </div>
          ))}
          {q.follow_up_text && selected.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <small>{q.follow_up_text}</small>
              <textarea
                className="form-control"
                value={follow}
                onChange={(e) => setFollow(e.target.value)}
              />
            </div>
          )}
        </>
      );
    }

    if (q.question_type === "RATING") {
      const choices = [1, 2, 3, 4, 5];
      return (
        <>
          <div style={{ display: "flex", gap: 8 }}>
            {choices.map((n) => (
              <button
                key={n}
                type="button"
                className={`btn btn-sm ${val === String(n) ? "btn-primary" : "btn-default"}`}
                onClick={() => setVal(String(n))}
              >
                {n}
              </button>
            ))}
          </div>
          {q.follow_up_text && val && (
            <div style={{ marginTop: 8 }}>
              <small>{q.follow_up_text}</small>
              <textarea
                className="form-control"
                value={follow}
                onChange={(e) => setFollow(e.target.value)}
              />
            </div>
          )}
        </>
      );
    }

    return null;
  };

  return (
    <div style={{ padding: 16, maxWidth: 800, margin: "0 auto" }}>
      <h2>{survey.title}</h2>
      {survey.description && <p>{survey.description}</p>}
      <div style={{ marginBottom: 16 }}>
        <label className="form-label">Department (optional)</label>
        <input
          className="form-control"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
        />
      </div>
      {survey.sections
        .slice()
        .sort((a, b) => a.order - b.order)
        .map((section) => (
          <div key={section.name} style={{ marginBottom: 24 }}>
            <h4>{section.title}</h4>
            {section.questions
              .slice()
              .sort((a, b) => a.order - b.order)
              .map((q) => (
                <div key={q.name} style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 500 }}>
                    {q.question_text}
                    {q.is_required ? " *" : ""}
                  </div>
                  {renderQuestionInput(q)}
                </div>
              ))}
          </div>
        ))}
      {error && <div className="text-danger" style={{ marginBottom: 8 }}>{error}</div>}
      <button
        type="button"
        className="btn btn-primary"
        disabled={submitting}
        onClick={handleSubmit}
      >
        {submitting ? "Submitting…" : "Submit"}
      </button>
    </div>
  );
}

function mount() {
  const el = document.getElementById("survey-public-root");
  if (!el) return;
  const root = createRoot(el);
  root.render(<SurveyPublicApp />);
}

document.addEventListener("DOMContentLoaded", mount);

