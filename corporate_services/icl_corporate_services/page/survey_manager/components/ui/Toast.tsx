import React, { useState, useEffect } from "react";
import { ToastMessage } from "../types";

const COLOR: Record<ToastMessage["type"], string> = {
  success: "bg-success",
  error: "bg-danger",
  info: "bg-primary",
};

const ICON: Record<ToastMessage["type"], string> = {
  success: "✓",
  error: "✕",
  info: "ℹ",
};

interface ToastItemProps {
  toast: ToastMessage;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const [removing, setRemoving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setRemoving(true);
      setTimeout(() => onRemove(toast.id), 260);
    }, 3200);
    return () => clearTimeout(timer);
  }, [toast.id, onRemove]);

  const dismiss = () => {
    setRemoving(true);
    setTimeout(() => onRemove(toast.id), 260);
  };

  return (
    <div
      className={`sm-toast d-flex align-items-center gap-2 px-3 py-2 text-white ${COLOR[toast.type]}${removing ? " sm-toast-out" : ""}`}
    >
      <span style={{ fontSize: 14, fontWeight: 700 }}>{ICON[toast.type]}</span>
      <span className="flex-grow-1 small">{toast.message}</span>
      <button
        type="button"
        className="btn-close btn-close-white ms-1"
        style={{ fontSize: 10 }}
        onClick={dismiss}
        aria-label="Close"
      />
    </div>
  );
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="sm-toast-container">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onRemove={onRemove} />
      ))}
    </div>
  );
}
