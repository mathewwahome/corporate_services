import React, { ReactNode } from "react";

interface FadeProps {
  children: ReactNode;
  className?: string;
}

export function Fade({ children, className = "" }: FadeProps) {
  return <div className={`sm-fade-in${className ? ` ${className}` : ""}`}>{children}</div>;
}
