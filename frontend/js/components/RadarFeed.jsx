// Radar Feed — Confidence Probability Bars (M0–M7)
const M_COLORS = {
  M0: "#22c55e", M1: "#f97316", M2: "#9f7aea",
  M3: "#eab308", M4: "#ef4444", M5: "#06b6d4",
  M6: "#8b5cf6", M7: "#ec4899"
};

const M_LABELS = {
  M0: "Correct",
  M1: "Accum. Reinit",
  M2: "Print vs Return",
  M3: "Off-by-One Range",
  M4: "Wrong Comparator",
  M5: "Assign in Cond.",
  M6: "Mutation vs New",
  M7: "Index Boundary",
};

function RadarFeed({ probabilities }) {
  if (!probabilities) {
    return (
      <div className="radar-section">
        <div className="section-title">🎯 Misconception Radar</div>
        <div style={{color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '20px 0'}}>
          Submit code to see diagnosis…
        </div>
      </div>
    );
  }

  const sorted = Object.entries(probabilities).sort(([,a],[,b]) => b - a);
  const topClass = sorted[0][0];

  return (
    <div className="radar-section">
      <div className="section-title">🎯 Misconception Radar</div>
      <div className="radar-bars">
        {sorted.map(([m, prob]) => {
          const color = M_COLORS[m] || "#888";
          const pct = Math.round(prob * 100);
          const isTop = m === topClass;
          return (
            <div key={m} className={`radar-bar-row ${isTop ? "top-class" : ""}`}>
              <div className="radar-bar-label" style={isTop ? {color} : {}}>{m}</div>
              <div className="radar-bar-track">
                <div
                  className="radar-bar-fill"
                  style={{
                    width: `${pct}%`,
                    background: isTop
                      ? `linear-gradient(90deg, ${color}cc, ${color})`
                      : `linear-gradient(90deg, ${color}44, ${color}66)`,
                  }}
                />
              </div>
              <div className="radar-bar-pct" style={isTop ? {color} : {}}>
                {pct}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
