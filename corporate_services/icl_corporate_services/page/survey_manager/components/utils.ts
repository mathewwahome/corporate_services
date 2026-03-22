import { SurveyDoc } from "./types";

export const uid = (): string =>
  `tmp_${Math.random().toString(16).slice(2)}${Date.now().toString(16)}`;

export function normalizeSurveyDoc(doc: any): SurveyDoc {
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
    owner: doc?.owner,
    creation: doc?.creation,
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
      questions: (Array.isArray(s?.questions) ? s.questions : []).map(
        (q: any, qi: number) => ({
          doctype: "Survey Question",
          name: q?.name,
          parent: q?.parent,
          parenttype: q?.parenttype,
          parentfield: q?.parentfield,
          idx: q?.idx,
          question_text: q?.question_text || "",
          question_type: (q?.question_type || "TEXT") as any,
          options: q?.options || "",
          max_selections: q?.max_selections ? Number(q.max_selections) : undefined,
          follow_up_text: q?.follow_up_text || "",
          is_required: q?.is_required ? (1 as const) : (0 as const),
          order: Number(q?.order ?? qi + 1),
        })
      ),
    })),
  };
}

export function validateSurvey(doc: SurveyDoc): string[] {
  const errs: string[] = [];
  if (!doc.title.trim()) errs.push("Title is required.");
  if (!doc.year || Number.isNaN(Number(doc.year))) errs.push("Year is required.");
  if (!doc.sections?.length) errs.push("At least one section is required.");
  doc.sections.forEach((s, si) => {
    if (!s.title.trim()) errs.push(`Section ${si + 1}: title is required.`);
    if (!s.questions?.length)
      errs.push(`Section ${si + 1}: add at least one question.`);
    s.questions.forEach((q, qi) => {
      if (!q.question_text.trim())
        errs.push(`Section ${si + 1}, Q${qi + 1}: question text is required.`);
      if (
        (q.question_type === "MULTI_SELECT" ||
          q.question_type === "SINGLE_SELECT") &&
        !q.options?.trim()
      ) {
        errs.push(
          `Section ${si + 1}, Q${qi + 1}: options are required for ${q.question_type}.`
        );
      }
    });
  });
  return errs;
}
