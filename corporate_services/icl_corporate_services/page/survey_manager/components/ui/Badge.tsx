import React from "react";

interface BadgeProps {
  published: boolean;
}

export function Badge({ published }: BadgeProps) {
  return published ? (
    <span className="badge bg-success" style={{ fontSize: 11 }}>
      Published
    </span>
  ) : (
    <span className="badge bg-secondary" style={{ fontSize: 11 }}>
      Draft
    </span>
  );
}
