import React, { useState, useMemo } from "react";
import { SurveyCard } from "./SurveyCard";
import { Spinner } from "../ui/Spinner";
import { SurveyRow } from "../types";
import { NEW_SURVEY_KEY } from "../hooks/useSurveys";

interface SurveyListPanelProps {
  surveys: SurveyRow[];
  selectedName: string | null;
  isNew: boolean;
  loading: boolean;
  error: string | null;
  onSelect: (name: string) => void;
  onNew: () => void;
}

export function SurveyListPanel({
  surveys,
  selectedName,
  isNew,
  loading,
  error,
  onSelect,
  onNew,
}: SurveyListPanelProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return surveys;
    return surveys.filter(
      (s) =>
        s.title?.toLowerCase().includes(q) ||
        String(s.year ?? "").includes(q)
    );
  }, [surveys, search]);

  return (
    <div
      className="d-flex flex-column flex-shrink-0"
      style={{
        width: 290,
        borderRight: "1px solid var(--border-color, #e2e6ea)",
        height: "100%",
        background: "var(--bg-color, #fff)",
      }}
    >
      {/* Header */}
      <div
        className="d-flex align-items-center justify-content-between px-3 py-3"
        style={{ borderBottom: "1px solid var(--border-color, #e2e6ea)" }}
      >
        <span className="fw-bold" style={{ fontSize: 14 }}>
          Surveys
        </span>
        <button
          className="btn btn-sm btn-primary"
          type="button"
          onClick={onNew}
          disabled={isNew}
          style={{ fontSize: 12 }}
        >
          + New
        </button>
      </div>

      {/* Search */}
      <div
        className="px-3 py-2"
        style={{ borderBottom: "1px solid var(--border-color, #e2e6ea)" }}
      >
        <div className="sm-search-wrap">
          <span className="sm-search-icon">🔍</span>
          <input
            className="form-control form-control-sm"
            type="search"
            placeholder="Search surveys…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ fontSize: 12 }}
          />
        </div>
      </div>

      {/* Card list */}
      <div className="flex-grow-1 overflow-auto p-2">
        {loading ? (
          <div className="d-flex justify-content-center align-items-center mt-4 gap-2 text-muted">
            <Spinner />
            <small>Loading…</small>
          </div>
        ) : error ? (
          <div className="text-danger small p-2">{error}</div>
        ) : (
          <>
            {isNew && (
              <SurveyCard
                survey={{
                  name: NEW_SURVEY_KEY,
                  title: "",
                  year: new Date().getFullYear(),
                  is_published: 0,
                  total_submissions: 0,
                }}
                isActive={selectedName === NEW_SURVEY_KEY}
                isNew
                onClick={() => onSelect(NEW_SURVEY_KEY)}
              />
            )}

            {filtered.map((s) => (
              <SurveyCard
                key={s.name}
                survey={s}
                isActive={selectedName === s.name}
                onClick={() => s.name && onSelect(s.name)}
              />
            ))}

            {!isNew && filtered.length === 0 && (
              <div className="text-muted text-center small mt-4 px-2">
                {search
                  ? "No surveys match your search."
                  : "No surveys yet. Click + New to create one."}
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer count */}
      {!loading && !error && surveys.length > 0 && (
        <div
          className="px-3 py-2 text-muted"
          style={{
            borderTop: "1px solid var(--border-color, #e2e6ea)",
            fontSize: 11,
          }}
        >
          {filtered.length} of {surveys.length} survey{surveys.length !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
