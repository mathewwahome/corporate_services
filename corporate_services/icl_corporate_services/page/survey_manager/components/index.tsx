import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

type QuestionType = "MULTI_SELECT" | "RATING" | "SINGLE_SELECT" | "TEXT";

type SurveyQuestionRow = {
  doctype?: "Survey Question";
  name?: string;
  parent?: string;
  parenttype?: string;
  parentfield?: string;
  idx?: number;
  __islocal?: 1;
  __unsaved?: 1;
  __temporary_name?: string;

  question_text: string;
  question_type: QuestionType;
  options?: string;
  max_selections?: number;
  follow_up_text?: string;
  is_required?: 0 | 1;
  order: number;
};

type SurveySectionRow = {
  doctype?: "Survey Section";
  name?: string;
  parent?: string;
  parenttype?: string;
  parentfield?: string;
  idx?: number;
  __islocal?: 1;
  __unsaved?: 1;
  __temporary_name?: string;

  title: string;
  order: number;
  questions: SurveyQuestionRow[];
};

type SurveyDoc = {
  doctype: "Survey";
  name?: string;
  title: string;
  description?: string;
  year: number;
  is_published?: 0 | 1;
  departments?: string;
  total_submissions?: number;
  modified?: string;
  sections: SurveySectionRow[];
};

type SurveyRow = Pick<
  SurveyDoc,
  "name" | "title" | "year" | "is_published" | "departments" | "total_submissions" | "modified"
>;

declare global {
  interface Window {
    frappe: any;
    initSurveyManager?: (page: any) => void;
  }
}

const uid = () => `tmp_${Math.random().toString(16).slice(2)}${Date.now().toString(16)}`;

function normalizeSurveyDoc(doc: any): SurveyDoc {
  const sections = Array.isArray(doc?.sections) ? doc.sections : [];
  return {
    doctype: "Survey",
    name: doc?.name,
    title: doc?.title || "",
    description: doc?.description || "",
    year: Number(doc?.year || new Date().getFullYear()),
    is_published: doc?.is_published ? 1 : 0,
    departments: doc?.departments || "",
    total_submissions: Number(doc?.total_submissions || 0),
    modified: doc?.modified,
    sections: sections.map((s: any, i: number) => ({
      doctype: "Survey Section",
      name: s?.name,
      parent: s?.parent,
      parenttype: s?.parenttype,
      parentfield: s?.parentfield,
      idx: s?.idx,
      title: s?.title || "",
      order: Number(s?.order ?? i + 1),
      questions: (Array.isArray(s?.questions) ? s.questions : []).map((q: any, qi: number) => ({
        doctype: "Survey Question",
        name: q?.name,
        parent: q?.parent,
        parenttype: q?.parenttype,
        parentfield: q?.parentfield,
        idx: q?.idx,
        question_text: q?.question_text || "",
        question_type: (q?.question_type || "TEXT") as QuestionType,
        options: q?.options || "",
        max_selections: q?.max_selections ? Number(q.max_selections) : undefined,
        follow_up_text: q?.follow_up_text || "",
        is_required: q?.is_required ? 1 : 0,
        order: Number(q?.order ?? qi + 1),
      })),
    })),
  };
}

function validateSurvey(doc: SurveyDoc): string[] {
  const errs: string[] = [];
  if (!doc.title.trim()) errs.push("Title is required.");
  if (!doc.year || Number.isNaN(Number(doc.year))) errs.push("Year is required.");
  if (!doc.sections?.length) errs.push("At least one section is required.");
  doc.sections.forEach((s, si) => {
    if (!s.title.trim()) errs.push(`Section ${si + 1}: title is required.`);
    if (!s.order) errs.push(`Section ${si + 1}: order is required.`);
    if (!s.questions?.length) errs.push(`Section ${si + 1}: add at least one question.`);
    s.questions.forEach((q, qi) => {
      if (!q.question_text.trim()) errs.push(`Section ${si + 1}, Question ${qi + 1}: text is required.`);
      if (!q.order) errs.push(`Section ${si + 1}, Question ${qi + 1}: order is required.`);
      if ((q.question_type === "MULTI_SELECT" || q.question_type === "SINGLE_SELECT") && !q.options?.trim()) {
        errs.push(`Section ${si + 1}, Question ${qi + 1}: options required for ${q.question_type}.`);
      }
    });
  });
  return errs;
}

function SurveyManagerApp({ page }: { page: any }) {
  const frappe = (globalThis as any).frappe;
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [surveys, setSurveys] = useState<SurveyRow[]>([]);

  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);
  const [doc, setDoc] = useState<SurveyDoc | null>(null);
  const [dirty, setDirty] = useState(false);

  const selectedRow = useMemo(
    () => surveys.find((s) => s.name === selectedName) || null,
    [surveys, selectedName],
  );

  const loadList = () => {
    setListLoading(true);
    setListError(null);
    frappe
      .call<{ message: SurveyRow[] }>({ method: "corporate_services.api.survey.get_surveys" })
      .then((r: any) => {
        const data = (r?.message || []) as SurveyRow[];
        setSurveys(data);
        if (!selectedName && data.length) setSelectedName(data[0].name || null);
      })
      .catch((e: any) => setListError(e?.message || "Failed to load surveys."))
      .finally(() => setListLoading(false));
  };

  const loadDoc = async (name: string) => {
    setDocLoading(true);
    setDocError(null);
    setDirty(false);
    try {
      const r = await frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Survey", name },
      });
      setDoc(normalizeSurveyDoc(r?.message));
    } catch (e: any) {
      setDoc(null);
      setDocError(e?.message || "Failed to load survey.");
    } finally {
      setDocLoading(false);
    }
  };

  useEffect(() => {
    loadList();
  }, []);

  useEffect(() => {
    if (selectedName) loadDoc(selectedName);
  }, [selectedName]);

  const ensureDoc = () => {
    if (!doc) throw new Error("No survey selected");
    return doc;
  };

  const updateDoc = (updater: (d: SurveyDoc) => SurveyDoc) => {
    setDoc((prev) => {
      if (!prev) return prev;
      const next = updater(prev);
      return next;
    });
    setDirty(true);
  };

  const addSection = () => {
    updateDoc((d) => {
      const nextOrder = (d.sections?.reduce((m, s) => Math.max(m, s.order || 0), 0) || 0) + 1;
      const section: SurveySectionRow = {
        doctype: "Survey Section",
        __islocal: 1,
        __unsaved: 1,
        __temporary_name: uid(),
        title: "New section",
        order: nextOrder,
        questions: [
          {
            doctype: "Survey Question",
            __islocal: 1,
            __unsaved: 1,
            __temporary_name: uid(),
            question_text: "New question",
            question_type: "TEXT",
            options: "",
            max_selections: undefined,
            follow_up_text: "",
            is_required: 0,
            order: 1,
          },
        ],
      };
      return { ...d, sections: [...(d.sections || []), section] };
    });
  };

  const removeSection = (idx: number) => {
    updateDoc((d) => ({ ...d, sections: d.sections.filter((_, i) => i !== idx) }));
  };

  const addQuestion = (sectionIdx: number) => {
    updateDoc((d) => {
      const sections = d.sections.map((s, i) => {
        if (i !== sectionIdx) return s;
        const nextOrder = (s.questions?.reduce((m, q) => Math.max(m, q.order || 0), 0) || 0) + 1;
        const q: SurveyQuestionRow = {
          doctype: "Survey Question",
          __islocal: 1,
          __unsaved: 1,
          __temporary_name: uid(),
          question_text: "New question",
          question_type: "TEXT",
          options: "",
          max_selections: undefined,
          follow_up_text: "",
          is_required: 0,
          order: nextOrder,
        };
        return { ...s, questions: [...(s.questions || []), q] };
      });
      return { ...d, sections };
    });
  };

  const removeQuestion = (sectionIdx: number, qIdx: number) => {
    updateDoc((d) => {
      const sections = d.sections.map((s, i) => {
        if (i !== sectionIdx) return s;
        return { ...s, questions: s.questions.filter((_, qi) => qi !== qIdx) };
      });
      return { ...d, sections };
    });
  };

  const save = async () => {
    const current = ensureDoc();
    const errs = validateSurvey(current);
    if (errs.length) {
      frappe.msgprint({
        title: "Please fix these issues",
        message: `<ul>${errs.map((e) => `<li>${frappe.utils.escape_html(e)}</li>`).join("")}</ul>`,
        indicator: "red",
      });
      return;
    }
    setDocLoading(true);
    setDocError(null);
    try {
      const r = await frappe.call({
        method: "frappe.client.save",
        args: { doc: current },
      });
      const saved = normalizeSurveyDoc(r?.message);
      setDoc(saved);
      setDirty(false);
      loadList();
      frappe.show_alert({ message: "Saved", indicator: "green" });
    } catch (e: any) {
      setDocError(e?.message || "Save failed.");
    } finally {
      setDocLoading(false);
    }
  };

  const togglePublish = async () => {
    const row = selectedRow;
    if (!row?.name) return;
    await frappe.call({
      method: "corporate_services.api.survey.set_survey_published",
      args: { survey: row.name, is_published: row.is_published ? 0 : 1 },
    });
    loadList();
  };

  const openResponsesList = () => {
    const row = selectedRow;
    if (!row?.name) return;
    frappe.set_route("List", "Survey Response", { survey: row.name });
  };

  const publicUrl = () => {
    if (!selectedRow?.name) return "";
    const base = globalThis.location?.origin || "";
    return `${base}/survey-public?survey=${encodeURIComponent(selectedRow.name)}`;
  };

  return (
    <div style={{ padding: 16, display: "flex", gap: 16 }}>
      <div style={{ width: 380 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Surveys</h3>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => frappe.set_route("Form", "Survey")}
            type="button"
          >
            New
          </button>
        </div>

        {listError && <div className="text-danger" style={{ marginTop: 8 }}>{listError}</div>}
        {listLoading ? (
          <div style={{ marginTop: 12 }}>Loading…</div>
        ) : (
          <div style={{ marginTop: 12, maxHeight: "70vh", overflow: "auto" }}>
            <table className="table table-bordered">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Year</th>
                  <th>Pub</th>
                </tr>
              </thead>
              <tbody>
                {surveys.map((s) => (
                  <tr
                    key={s.name || uid()}
                    onClick={() => s.name && setSelectedName(s.name)}
                    style={{
                      cursor: "pointer",
                      background: selectedName === s.name ? "var(--bg-light-gray)" : undefined,
                    }}
                  >
                    <td>{s.title}</td>
                    <td>{s.year}</td>
                    <td>{s.is_published ? "Yes" : "No"}</td>
                  </tr>
                ))}
                {!surveys.length && (
                  <tr>
                    <td colSpan={3}>No surveys yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div style={{ flex: 1, minWidth: 600 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
          <div>
            <h3 style={{ margin: 0 }}>Workflow</h3>
            {selectedRow?.name && (
              <div style={{ marginTop: 4, opacity: 0.75 }}>
                <small>
                  {selectedRow.is_published ? "Published" : "Unpublished"} · submissions{" "}
                  {selectedRow.total_submissions ?? 0}
                </small>
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button className="btn btn-sm btn-default" onClick={loadList} type="button">
              Refresh
            </button>
            <button
              className="btn btn-sm btn-default"
              onClick={togglePublish}
              type="button"
              disabled={!selectedRow?.name}
            >
              {selectedRow?.is_published ? "Hide" : "Publish"}
            </button>
            <button
              className="btn btn-sm btn-secondary"
              onClick={openResponsesList}
              type="button"
              disabled={!selectedRow?.name}
            >
              Responses
            </button>
            <button className="btn btn-sm btn-primary" onClick={save} type="button" disabled={!dirty || docLoading}>
              Save
            </button>
          </div>
        </div>

        {docError && <div className="text-danger" style={{ marginTop: 8 }}>{docError}</div>}

        <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <label className="control-label" htmlFor="survey_manager_title">
              Title
            </label>
            <input
              id="survey_manager_title"
              className="form-control"
              value={doc?.title || ""}
              onChange={(e) => updateDoc((d) => ({ ...d, title: e.target.value }))}
              disabled={!doc}
            />
          </div>
          <div>
            <label className="control-label" htmlFor="survey_manager_year">
              Year
            </label>
            <input
              id="survey_manager_year"
              className="form-control"
              type="number"
              value={doc?.year ?? ""}
              onChange={(e) => updateDoc((d) => ({ ...d, year: Number(e.target.value) }))}
              disabled={!doc}
            />
          </div>
          <div style={{ gridColumn: "1 / span 2" }}>
            <label className="control-label" htmlFor="survey_manager_description">
              Description
            </label>
            <textarea
              id="survey_manager_description"
              className="form-control"
              value={doc?.description || ""}
              onChange={(e) => updateDoc((d) => ({ ...d, description: e.target.value }))}
              disabled={!doc}
            />
          </div>
          <div style={{ gridColumn: "1 / span 2" }}>
            <label className="control-label" htmlFor="survey_manager_departments">
              Departments
            </label>
            <input
              id="survey_manager_departments"
              className="form-control"
              value={doc?.departments || ""}
              onChange={(e) => updateDoc((d) => ({ ...d, departments: e.target.value }))}
              disabled={!doc}
              placeholder="MultiSelect values (as stored by Frappe)"
            />
          </div>
          <div style={{ gridColumn: "1 / span 2" }}>
            <label className="control-label" htmlFor="survey_manager_public_link">
              Public Link
            </label>
            <input id="survey_manager_public_link" className="form-control" readOnly value={publicUrl()} />
          </div>
        </div>

        <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h4 style={{ margin: 0 }}>Sections & Questions</h4>
          <button className="btn btn-sm btn-default" onClick={addSection} type="button" disabled={!doc}>
            Add section
          </button>
        </div>

        {!doc ? (
          <div style={{ marginTop: 12 }}>Select a survey to edit.</div>
        ) : (
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 12 }}>
            {doc.sections.map((s, si) => (
              <div key={s.name || s.__temporary_name || `${si}`} className="panel panel-default">
                <div className="panel-heading" style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <div style={{ display: "flex", gap: 8, flex: 1 }}>
                    <input
                      className="form-control"
                      style={{ maxWidth: 420 }}
                      value={s.title}
                      onChange={(e) =>
                        updateDoc((d) => ({
                          ...d,
                          sections: d.sections.map((x, i) => (i === si ? { ...x, title: e.target.value } : x)),
                        }))
                      }
                    />
                    <input
                      className="form-control"
                      style={{ width: 120 }}
                      type="number"
                      value={s.order}
                      onChange={(e) =>
                        updateDoc((d) => ({
                          ...d,
                          sections: d.sections.map((x, i) =>
                            i === si ? { ...x, order: Number(e.target.value) } : x,
                          ),
                        }))
                      }
                    />
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="btn btn-xs btn-default" type="button" onClick={() => addQuestion(si)}>
                      Add question
                    </button>
                    <button className="btn btn-xs btn-danger" type="button" onClick={() => removeSection(si)}>
                      Remove
                    </button>
                  </div>
                </div>
                <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {s.questions.map((q, qi) => (
                    <div
                      key={q.name || q.__temporary_name || `${qi}`}
                      style={{ display: "grid", gridTemplateColumns: "1fr 180px 120px 100px 80px", gap: 8 }}
                    >
                      <input
                        className="form-control"
                        value={q.question_text}
                        onChange={(e) =>
                          updateDoc((d) => ({
                            ...d,
                            sections: d.sections.map((sec, i) => {
                              if (i !== si) return sec;
                              return {
                                ...sec,
                                questions: sec.questions.map((qq, j) =>
                                  j === qi ? { ...qq, question_text: e.target.value } : qq,
                                ),
                              };
                            }),
                          }))
                        }
                      />
                      <select
                        className="form-control"
                        value={q.question_type}
                        onChange={(e) =>
                          updateDoc((d) => ({
                            ...d,
                            sections: d.sections.map((sec, i) => {
                              if (i !== si) return sec;
                              return {
                                ...sec,
                                questions: sec.questions.map((qq, j) =>
                                  j === qi ? { ...qq, question_type: e.target.value as QuestionType } : qq,
                                ),
                              };
                            }),
                          }))
                        }
                      >
                        <option value="TEXT">TEXT</option>
                        <option value="SINGLE_SELECT">SINGLE_SELECT</option>
                        <option value="MULTI_SELECT">MULTI_SELECT</option>
                        <option value="RATING">RATING</option>
                      </select>
                      <input
                        className="form-control"
                        type="number"
                        value={q.order}
                        onChange={(e) =>
                          updateDoc((d) => ({
                            ...d,
                            sections: d.sections.map((sec, i) => {
                              if (i !== si) return sec;
                              return {
                                ...sec,
                                questions: sec.questions.map((qq, j) => (j === qi ? { ...qq, order: Number(e.target.value) } : qq)),
                              };
                            }),
                          }))
                        }
                      />
                      <label style={{ display: "flex", gap: 6, alignItems: "center", margin: 0 }}>
                        <input
                          type="checkbox"
                          checked={!!q.is_required}
                          onChange={(e) =>
                            updateDoc((d) => ({
                              ...d,
                              sections: d.sections.map((sec, i) => {
                                if (i !== si) return sec;
                                return {
                                  ...sec,
                                  questions: sec.questions.map((qq, j) =>
                                    j === qi ? { ...qq, is_required: e.target.checked ? 1 : 0 } : qq,
                                  ),
                                };
                              }),
                            }))
                          }
                        />
                        Required
                      </label>
                      <button className="btn btn-xs btn-danger" type="button" onClick={() => removeQuestion(si, qi)}>
                        Remove
                      </button>

                      {(q.question_type === "SINGLE_SELECT" || q.question_type === "MULTI_SELECT") && (
                        <textarea
                          className="form-control"
                          style={{ gridColumn: "1 / span 5" }}
                          placeholder="Options (one per line)"
                          value={q.options || ""}
                          onChange={(e) =>
                            updateDoc((d) => ({
                              ...d,
                              sections: d.sections.map((sec, i) => {
                                if (i !== si) return sec;
                                return {
                                  ...sec,
                                  questions: sec.questions.map((qq, j) => (j === qi ? { ...qq, options: e.target.value } : qq)),
                                };
                              }),
                            }))
                          }
                        />
                      )}
                      <input
                        className="form-control"
                        style={{ gridColumn: "1 / span 5" }}
                        placeholder="Follow-up question text (optional)"
                        value={q.follow_up_text || ""}
                        onChange={(e) =>
                          updateDoc((d) => ({
                            ...d,
                            sections: d.sections.map((sec, i) => {
                              if (i !== si) return sec;
                              return {
                                ...sec,
                                questions: sec.questions.map((qq, j) =>
                                  j === qi ? { ...qq, follow_up_text: e.target.value } : qq,
                                ),
                              };
                            }),
                          }))
                        }
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function mount(page: any) {
  const el = document.getElementById("survey-manager-root");
  if (!el) return;
  createRoot(el).render(<SurveyManagerApp page={page} />);
}

(globalThis as any).initSurveyManager = function initSurveyManager(page: any) {
  mount(page);
};

