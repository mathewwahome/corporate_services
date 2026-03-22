import React from "react";

interface SpinnerProps {
  size?: "sm" | "md";
}

export function Spinner({ size = "sm" }: SpinnerProps) {
  const cls = size === "sm" ? "spinner-border spinner-border-sm" : "spinner-border";
  return <span className={cls} role="status" aria-hidden="true" />;
}
