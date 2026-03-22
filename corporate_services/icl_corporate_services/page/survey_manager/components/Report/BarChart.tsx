import React, { useEffect, useState } from "react";

export interface BarChartItem {
  label: string;
  count: number;
}

interface BarChartProps {
  items: BarChartItem[];
  total: number;
  colorVar?: string;
}

const BAR_COLORS = [
  "var(--primary, #5e64ff)",
  "#36b37e",
  "#ff8b00",
  "#0065ff",
  "#ff5630",
  "#6554c0",
  "#00b8d9",
];

export function BarChart({ items, total, colorVar }: BarChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      setTimeout(() => setMounted(true), 40);
    });
    return () => cancelAnimationFrame(raf);
  }, []);

  if (items.length === 0) {
    return <div className="text-muted small">No data yet.</div>;
  }

  const maxCount = Math.max(...items.map((i) => i.count), 1);

  return (
    <div className="d-flex flex-column gap-3 mt-2">
      {items.map((item, i) => {
        const pct = total > 0 ? Math.round((item.count / total) * 100) : 0;
        const relPct = Math.round((item.count / maxCount) * 100);
        const color = colorVar ?? BAR_COLORS[i % BAR_COLORS.length];

        return (
          <div key={item.label}>
            {/* Label row */}
            <div
              className="d-flex justify-content-between align-items-baseline mb-1"
              style={{ fontSize: 12 }}
            >
              <span
                style={{
                  maxWidth: "60%",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  fontWeight: 500,
                }}
                title={item.label}
              >
                {item.label}
              </span>
              <span style={{ flexShrink: 0 }}>
                <span className="fw-semibold">{item.count}</span>
                <span className="text-muted ms-1" style={{ fontSize: 11 }}>
                  ({pct}%)
                </span>
              </span>
            </div>

            {/* Track — relative to highest bar for visual impact */}
            <div
              style={{
                background: "var(--border-color, #eaecef)",
                borderRadius: 6,
                height: 14,
                overflow: "hidden",
              }}
            >
              <div
                className="sm-bar-fill"
                style={{
                  width: mounted ? `${relPct}%` : "0%",
                  height: "100%",
                  background: color,
                  borderRadius: 6,
                  minWidth: item.count > 0 ? 6 : 0,
                }}
              />
            </div>
          </div>
        );
      })}

      {/* Legend note when relative scale is used */}
      {items.length > 1 && (
        <div className="text-muted" style={{ fontSize: 10, marginTop: -4 }}>
          Bar length is relative to the highest response. Percentages show share of respondents.
        </div>
      )}
    </div>
  );
}
