// Inspector Modal — Instructor view: confusion matrix, LOPO metrics, differentiation gain
function InspectorModal({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState("overview");

  useEffect(() => {
    fetch(`${API_BASE}/api/inspector`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div className="modal-header">
          <div className="modal-title">🔬 Model Inspector — Instructor View</div>
          <button className="modal-close" onClick={onClose} id="inspector-close-btn">✕</button>
        </div>
        <div className="modal-body">
          {loading ? (
            <div style={{textAlign:'center', color:'var(--text-muted)', padding: 40}}>
              <span className="loading-spinner" />
              <div style={{marginTop:10}}>Loading metrics…</div>
            </div>
          ) : data ? (
            <>
              {/* Model info banner */}
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '10px 14px',
                fontSize: 12,
                color: 'var(--text-secondary)',
              }}>
                <strong style={{color:'var(--text-primary)'}}>Model:</strong> {data.model_info?.type}
                <span style={{marginLeft: 12, opacity: 0.7}}>Classes: {data.model_info?.classes?.join(", ")}</span>
              </div>

              {/* Key metrics */}
              <div>
                <div className="section-title">📊 Overall Metrics</div>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-value">{(data.overall_accuracy * 100).toFixed(1)}%</div>
                    <div className="metric-label">Accuracy</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value">{(data.macro_f1 * 100).toFixed(1)}%</div>
                    <div className="metric-label">Macro F1</div>
                  </div>
                  <div className="metric-card" style={{background:'rgba(79,124,255,0.08)'}}>
                    <div className="metric-value" style={{color:'var(--accent-purple)'}}>8</div>
                    <div className="metric-label">M Classes</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value" style={{color:'var(--accent-green)'}}>4</div>
                    <div className="metric-label">Probes</div>
                  </div>
                </div>
              </div>

              {/* Confusion Matrix */}
              <div>
                <div className="section-title">🔢 Confusion Matrix (Top 5 Classes)</div>
                <div style={{overflowX: 'auto'}}>
                  <table className="confusion-matrix">
                    <thead>
                      <tr>
                        <th>Pred →<br/>Actual ↓</th>
                        {data.confusion_matrix.labels.map(l => <th key={l}>{l}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {data.confusion_matrix.matrix.map((row, i) => (
                        <tr key={i}>
                          <th>{data.confusion_matrix.labels[i]}</th>
                          {row.map((v, j) => (
                            <td key={j} className={i === j ? "diag" : ""}>{v}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* LOPO Metrics */}
              <div>
                <div className="section-title">📈 LOPO Metrics (Leave-One-Problem-Out)</div>
                <div className="metrics-grid">
                  {Object.entries(data.lopo_metrics).map(([m, metrics]) => (
                    <div key={m} className="metric-card">
                      <div className="metric-value" style={{fontSize: 16, color: M_COLORS[m] || 'var(--accent-blue)'}}>
                        {m}
                      </div>
                      <div style={{marginTop: 4, fontSize: 11}}>
                        <div>P: <strong>{(metrics.precision*100).toFixed(0)}%</strong></div>
                        <div>R: <strong>{(metrics.recall*100).toFixed(0)}%</strong></div>
                        <div>F1: <strong style={{color:'var(--accent-blue)'}}>{(metrics.f1*100).toFixed(0)}%</strong></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Differentiation Gain */}
              <div>
                <div className="section-title">⚡ Probe Differentiation Gain</div>
                {Object.entries(data.differentiation_gain).map(([key, after]) => {
                  // key format: M1_vs_M2_pre_probe / post_probe
                  if (!key.endsWith("_post_probe")) return null;
                  const base = key.replace("_post_probe", "");
                  const preKey = base + "_pre_probe";
                  const before = data.differentiation_gain[preKey] || 0;
                  const label = base.replace(/_/g, " ").replace("vs", "vs.");
                  return (
                    <div key={key} className="gain-row">
                      <div className="gain-label">{label}</div>
                      <div className="gain-before">{(before*100).toFixed(0)}%</div>
                      <div className="gain-arrow">→</div>
                      <div className="gain-after">{(after*100).toFixed(0)}%</div>
                      <div style={{fontSize:11, color:'var(--accent-green)', fontWeight:700}}>
                        +{((after - before)*100).toFixed(0)}pp
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <div style={{textAlign:'center', color:'var(--accent-red)', padding: 40}}>
              Failed to load inspector data. Is the backend running?
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
