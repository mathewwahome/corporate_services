import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

type SurveyRow = {
  name: string;
  title: string;
  year: number;
  is_published: number;
  departments?: string;
  total_submissions?: number;
  modified: string;
};

declare global {
  interface Window {
    frappe: any;
    initSurveyManager?: (page?: any) => void;
  }
}

function SurveyManagerApp() {
  const [surveys, setSurveys] = useState<SurveyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SurveyRow | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    const frappeCall = window.frappe.call as <T,>(opts: any) => PromiseLike<T>;
    Promise.resolve(
      frappeCall<{ message: SurveyRow[] }>({
        method: "corporate_services.api.survey.get_surveys",
      }),
    )
      .then((r: any) => {
        const data = r?.message || [];
        setSurveys(data);
        if (!selected && data.length > 0) {
          setSelected(data[0]);
        } else if (selected) {
          const match = data.find((s: SurveyRow) => s.name === selected.name);
          setSelected(match || data[0] || null);
        }
      })
      .catch((e: any) => {
        setError(e?.message || "Failed to load surveys");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const togglePublish = async (row: SurveyRow) => {
    await window.frappe.call({
      method: "corporate_services.api.survey.set_survey_published",
      args: { survey: row.name, is_published: row.is_published ? 0 : 1 },
    });
    load();
  };

  const publicUrl = (row: SurveyRow | null) => {
    if (!row) return "";
    const base = window.location.origin || "";
    return `${base}/survey-public?survey=${encodeURIComponent(row.name)}`;
  };

  const openERPForm = (row?: SurveyRow) => {
    if (!row) {
      window.frappe.set_route("Form", "Survey");
    } else {
      window.frappe.set_route("Form", "Survey", row.name);
    }
  };

  const openResponsesList = (row: SurveyRow | null) => {
    if (!row) return;
    window.frappe.set_route("List", "Survey Response", { survey: row.name });
  };

  return (
    <div style={{ padding: "16px" }}>
      <h2>Survey Manager</h2>
      {error && <div className="text-danger" style={{ marginBottom: 8 }}>{error}</div>}
      <div style={{ display: "flex", gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ marginBottom: 8, display: "flex", justifyContent: "space-between" }}>
            <strong>Surveys</strong>
            <button className="btn btn-sm btn-primary" onClick={() => openERPForm()}>
              New Survey
            </button>
          </div>
          {loading ? (
            <div>Loading…</div>
          ) : (
            <table className="table table-bordered">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Year</th>
                  <th>Published</th>
                  <th>Submissions</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {surveys.map((row) => (
                  <tr
                    key={row.name}
                    onClick={() => setSelected(row)}
                    style={{ cursor: "pointer", background: selected?.name === row.name ? "#f5f5f5" : undefined }}
                  >
                    <td>{row.title}</td>
                    <td>{row.year}</td>
                    <td>{row.is_published ? "Yes" : "No"}</td>
                    <td>{row.total_submissions ?? 0}</td>
                    <td>
                      <button
                        className="btn btn-xs btn-default"
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          togglePublish(row);
                        }}
                      >
                        {row.is_published ? "Hide" : "Publish"}
                      </button>
                    </td>
                  </tr>
                ))}
                {surveys.length === 0 && (
                  <tr>
                    <td colSpan={5}>No surveys yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ flex: 1 }}>
          <strong>Details</strong>
          {!selected ? (
            <div style={{ marginTop: 8 }}>Select a survey to see details.</div>
          ) : (
            <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
              <div>
                <div><strong>Title:</strong> {selected.title}</div>
                <div><strong>Year:</strong> {selected.year}</div>
                <div><strong>Published:</strong> {selected.is_published ? "Yes" : "No"}</div>
                <div><strong>Departments:</strong> {selected.departments || "—"}</div>
              </div>
              <div>
                <div><strong>Public link:</strong></div>
                <input
                  type="text"
                  className="form-control"
                  readOnly
                  value={publicUrl(selected)}
                />
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-sm btn-default" onClick={() => openERPForm(selected)}>
                  Edit Survey
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => openResponsesList(selected)}>
                  View Responses
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function mount() {
  const el = document.getElementById("survey-manager-root");
  if (!el) return;
  const root = createRoot(el);
  root.render(<SurveyManagerApp />);
}

function ensureRootEl(page?: any) {
  const existing = document.getElementById("survey-manager-root");
  if (existing) return existing;

  const parent: HTMLElement | null =
    page?.body instanceof HTMLElement
      ? page.body
      : typeof page?.body?.get === "function"
        ? page.body.get(0)
        : null;

  if (!parent) return null;
  const div = document.createElement("div");
  div.id = "survey-manager-root";
  parent.appendChild(div);
  return div;
}

window.initSurveyManager = (page?: any) => {
  ensureRootEl(page);
  mount();
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => mount());
} else {
  mount();
}

