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
    return (
      <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
        No data yet.
      </div>
    );
  }

  const maxCount = Math.max(...items.map((i) => i.count), 1);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8 }}>
      {items.map((item, i) => {
        const pct = total > 0 ? Math.round((item.count / total) * 100) : 0;
        const relPct = Math.round((item.count / maxCount) * 100);
        const color = colorVar ?? BAR_COLORS[i % BAR_COLORS.length];

        return (
          <div key={item.label}>
            {/* Label row */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                fontSize: 12,
                marginBottom: 4,
              }}
            >
              <span
                style={{
                  maxWidth: "60%",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  fontWeight: 500,
                  color: "var(--text-color)",
                }}
                title={item.label}
              >
                {item.label}
              </span>
              <span style={{ flexShrink: 0 }}>
                <span style={{ fontWeight: 600, color: "var(--text-color)" }}>
                  {item.count}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--text-muted)",
                    marginLeft: 4,
                  }}
                >
                  ({pct}%)
                </span>
              </span>
            </div>

            {/* Bar track */}
            <div
              style={{
                background: "var(--border-color, #eaecef)",
                borderRadius: 4,
                height: 12,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: mounted ? `${relPct}%` : "0%",
                  height: "100%",
                  background: color,
                  borderRadius: 4,
                  minWidth: item.count > 0 ? 6 : 0,
                  transition: "width 0.4s ease",
                }}
              />
            </div>
          </div>
        );
      })}

      {/* Scale note */}
      {items.length > 1 && (
        <div
          style={{
            fontSize: 10,
            color: "var(--text-muted)",
            marginTop: -2,
          }}
        >
          Bar length is relative to the highest response. Percentages show share of respondents.
        </div>
      )}
    </div>
  );
}