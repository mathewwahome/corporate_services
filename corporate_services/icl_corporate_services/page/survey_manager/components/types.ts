export type QuestionType = "MULTI_SELECT" | "RATING" | "SINGLE_SELECT" | "TEXT";

export type SurveyQuestionRow = {
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

export type SurveySectionRow = {
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

export type SurveyDoc = {
  doctype: "Survey";
  name?: string;
  __islocal?: 1;
  title: string;
  description?: string;
  year: number;
  is_published?: 0 | 1;
  departments?: string;
  total_submissions?: number;
  owner?: string;
  creation?: string;
  modified?: string;
  sections: SurveySectionRow[];
};

export type SurveyRow = {
  name?: string;
  title?: string;
  year?: number;
  is_published?: 0 | 1;
  departments?: string;
  total_submissions?: number;
  modified?: string;
};

export type AnalyticsQuestion = {
  name: string;
  section: string;
  question_text: string;
  question_type: QuestionType;
  response_count: number;
  aggregation: Record<string, number>;
  text_responses: string[];
};

export type Analytics = {
  total_responses: number;
  questions: AnalyticsQuestion[];
};

export type ToastMessage = {
  id: string;
  message: string;
  type: "success" | "error" | "info";
};
