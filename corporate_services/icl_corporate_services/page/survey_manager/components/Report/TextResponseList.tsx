import React, { useState } from "react";

const PAGE_SIZE = 20;

interface TextResponseListProps {
  responses: string[];
}

export function TextResponseList({ responses }: TextResponseListProps) {
  const [page, setPage] = useState(0);

  const total = responses.length;
  const pages = Math.ceil(total / PAGE_SIZE);
  const slice = responses.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  if (total === 0) {
    return <div className="text-muted small">No text responses yet.</div>;
  }

  return (
    <div>
      <div
        className="border rounded overflow-hidden"
        style={{ background: "var(--bg-color, #fff)" }}
      >
        {slice.map((r, i) => (
          <div
            key={i}
            className="px-3 py-2"
            style={{
              fontSize: 13,
              borderBottom:
                i < slice.length - 1
                  ? "1px solid var(--border-color, #e9ecef)"
                  : "none",
              lineHeight: 1.5,
            }}
          >
            {r ? (
              <span>{r}</span>
            ) : (
              <em className="text-muted" style={{ fontSize: 12 }}>
                — (blank)
              </em>
            )}
          </div>
        ))}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div
          className="d-flex align-items-center justify-content-between mt-2"
          style={{ fontSize: 12 }}
        >
          <button
            className="btn btn-sm btn-outline-secondary"
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Prev
          </button>
          <span className="text-muted">
            {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
          </span>
          <button
            className="btn btn-sm btn-outline-secondary"
            type="button"
            disabled={page >= pages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      )}

      {pages <= 1 && total > 0 && (
        <div className="text-muted mt-1" style={{ fontSize: 11 }}>
          {total} response{total !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
