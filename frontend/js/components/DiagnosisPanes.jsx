// DiagnosisPane — Main right-pane tab: radar + badge + probe + intervention
function DiagnosisPane({ result }) {
  const [probeData, setProbeData] = useState(null);

  useEffect(() => {
    setProbeData(null);
  }, [result?.submission_id]);

  if (!result) {
    return (
      <div style={{color: 'var(--text-muted)', textAlign: 'center', paddingTop: 40}}>
        <div style={{fontSize: 32, marginBottom: 12}}>🎯</div>
        <div style={{fontSize: 13, fontWeight: 600, marginBottom: 6}}>Awaiting Submission</div>
        <div style={{fontSize: 12, lineHeight: 1.6}}>
          Write your code in the editor and click<br/>
          <strong>▶ Run &amp; Diagnose</strong> to start.
        </div>
      </div>
    );
  }

  const { probabilities, top_misconception, confidence, intervention } = result;
  const effectiveIntervention = (probeData && probeData.intervention) || intervention;
  const effectiveTop = (probeData && probeData.top_misconception) || top_misconception;
  const effectiveConf = (probeData && probeData.confidence) || confidence;
  const effectiveProbs = (probeData && probeData.updated_probabilities) || probabilities;
  const color = M_COLORS[effectiveTop] || "#888";

  return (
    <>
      {/* Diagnosis badge */}
      <div
        className="diagnosis-badge"
        style={{
          borderColor: `${color}44`,
          background: `${color}11`,
          color,
        }}
      >
        <div className="diagnosis-badge-icon">{effectiveIntervention?.badge?.split(" ")[0]}</div>
        <div className="diagnosis-badge-label">{effectiveTop}: {M_LABELS[effectiveTop]}</div>
        <div className="diagnosis-badge-sub">{effectiveIntervention?.badge?.replace(/^[^\s]+\s/, "")}</div>
        <div className="diagnosis-badge-confidence">
          <ConfidenceRing value={effectiveConf} color={color} />
          <div style={{fontSize: 12}}>
            <div style={{fontWeight: 700}}>{Math.round(effectiveConf * 100)}% confident</div>
            <div style={{color: 'var(--text-muted)', fontSize: 11}}>
              {effectiveConf < 0.45 ? "Probe required" : "High confidence"}
            </div>
          </div>
        </div>
      </div>

      {/* Radar */}
      <RadarFeed probabilities={effectiveProbs} />

      {/* Micro-Probe */}
      <MicroProbe
        result={result}
        onProbeAnswer={data => setProbeData(data)}
      />

      {/* Intervention Card */}
      {effectiveIntervention && (
        <div
          className="intervention-card"
          style={{
            borderColor: `${color}44`,
            background: `${color}08`,
            color,
          }}
        >
          <div style={{fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 8}}>
            💡 Intervention
          </div>
          <div style={{fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6}}>
            {effectiveIntervention.message}
          </div>
          {effectiveIntervention.hint && (
            <div className="intervention-hint" style={{borderLeftColor: color}}>
              <strong>Hint:</strong> {effectiveIntervention.hint}
            </div>
          )}
        </div>
      )}
    </>
  );
}

// Confidence ring (SVG donut)
function ConfidenceRing({ value, color }) {
  const r = 14;
  const circ = 2 * Math.PI * r;
  const dash = circ * value;
  return (
    <div className="confidence-ring">
      <svg width="36" height="36" viewBox="0 0 36 36">
        <circle cx="18" cy="18" r={r} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="3"/>
        <circle
          cx="18" cy="18" r={r}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{transition: 'stroke-dasharray 0.5s ease'}}
        />
        <text
          x="18" y="18"
          textAnchor="middle"
          dominantBaseline="central"
          style={{
            fill: color,
            fontSize: 9,
            fontWeight: 700,
            fontFamily: 'JetBrains Mono, monospace',
            transform: 'rotate(90deg)',
            transformOrigin: '18px 18px',
          }}
        >
          {Math.round(value * 100)}
        </text>
      </svg>
    </div>
  );
}

// ─────────────────────────────────────────────
// Visualizer Pane wrapper
// ─────────────────────────────────────────────
function VisualizerPane({ result }) {
  return (
    <>
      <Visualizer
        memoryBoxes={result?.memory_boxes || []}
        traceFrames={result?.trace_frames || []}
      />
      {result && (
        <div className="radar-section">
          <div className="section-title">📋 Execution Signature</div>
          <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
            {(result.trace_frames || []).length === 0 ? (
              <span style={{fontSize:12,color:'var(--text-muted)'}}>No trace data</span>
            ) : (
              ["[]","[1]","[1,2]","[1,2,3]","[4,9]"].map((label, i) => (
                <div key={i} style={{
                  background:'var(--bg-secondary)',
                  border:'1px solid var(--border-normal)',
                  borderRadius:'var(--radius-sm)',
                  padding:'5px 8px',
                  fontFamily:'JetBrains Mono,monospace',
                  fontSize:11,
                }}>
                  <span style={{color:'var(--text-muted)'}}>{label}: </span>
                  <span style={{color:'var(--accent-blue)'}}>…</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </>
  );
}

// ─────────────────────────────────────────────
// Reassess Pane
// ─────────────────────────────────────────────
function ReassessPane({ result, problems, sessionToken }) {
  const [transferCode, setTransferCode] = useState("def solution(values):\n    # Transfer problem\n    pass\n");
  const [counterCode, setCounterCode] = useState("def solution(nums):\n    # Counter-probe\n    pass\n");
  const [transferProbId, setTransferProbId] = useState("");
  const [counterProbId, setCounterProbId] = useState("");
  const [verdict, setVerdict] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (problems.length >= 2) {
      setTransferProbId(String(problems[problems.length - 1]?.id || ""));
      setCounterProbId(String(problems[0]?.id || ""));
    }
  }, [problems]);

  const handleReassess = async () => {
    if (!result) return;
    setLoading(true);
    setVerdict(null);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/reassess`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
          learner_id: result.submission_id,
          diagnosis_id: result.submission_id,
          transfer_problem_id: Number(transferProbId),
          counter_probe_problem_id: Number(counterProbId),
          transfer_code: transferCode,
          counter_probe_code: counterCode,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Reassess failed");
      setVerdict(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="reassess-card">
      <div className="section-title">🔁 Dual-Gate Reassessment</div>

      {!result && (
        <div style={{color:'var(--text-muted)',fontSize:12,textAlign:'center',padding:'20px 0'}}>
          Submit code first to enable reassessment.
        </div>
      )}

      {result && (
        <>
          <div style={{marginBottom: 10}}>
            <label style={{fontSize:11,color:'var(--text-muted)',display:'block',marginBottom:4}}>
              Gate 1 — Transfer Problem
            </label>
            <select
              className="problem-select"
              style={{width:'100%',marginBottom:6}}
              value={transferProbId}
              onChange={e => setTransferProbId(e.target.value)}
            >
              {problems.map(p => (
                <option key={p.id} value={p.id}>#{p.id} {p.title}</option>
              ))}
            </select>
            <textarea
              value={transferCode}
              onChange={e => setTransferCode(e.target.value)}
              style={{
                width:'100%', height:80,
                background:'var(--bg-secondary)',
                border:'1px solid var(--border-normal)',
                borderRadius:'var(--radius-sm)',
                color:'var(--text-primary)',
                fontFamily:'JetBrains Mono,monospace',
                fontSize:11,
                padding:'8px',
                resize:'vertical',
                outline:'none',
              }}
            />
          </div>

          <div style={{marginBottom: 12}}>
            <label style={{fontSize:11,color:'var(--text-muted)',display:'block',marginBottom:4}}>
              Gate 2 — Counter-Probe Trap
            </label>
            <select
              className="problem-select"
              style={{width:'100%',marginBottom:6}}
              value={counterProbId}
              onChange={e => setCounterProbId(e.target.value)}
            >
              {problems.map(p => (
                <option key={p.id} value={p.id}>#{p.id} {p.title}</option>
              ))}
            </select>
            <textarea
              value={counterCode}
              onChange={e => setCounterCode(e.target.value)}
              style={{
                width:'100%', height:80,
                background:'var(--bg-secondary)',
                border:'1px solid var(--border-normal)',
                borderRadius:'var(--radius-sm)',
                color:'var(--text-primary)',
                fontFamily:'JetBrains Mono,monospace',
                fontSize:11,
                padding:'8px',
                resize:'vertical',
                outline:'none',
              }}
            />
          </div>

          <button
            id="reassess-btn"
            className="btn btn-primary w-full"
            onClick={handleReassess}
            disabled={loading || !transferProbId || !counterProbId}
            style={{width:'100%', justifyContent:'center'}}
          >
            {loading ? <><span className="loading-spinner"/> Evaluating…</> : "🔁 Run Dual-Gate Check"}
          </button>

          {error && (
            <div style={{marginTop:10,color:'var(--accent-red)',fontSize:12}}>{error}</div>
          )}

          {verdict && (
            <div style={{marginTop:12}}>
              <div className={`verdict-banner ${verdict.verdict.toLowerCase()}`}>
                {verdict.badge}
              </div>
              <div style={{fontSize:12, color:'var(--text-secondary)', lineHeight:1.6}}>
                {verdict.message}
              </div>
              <div style={{marginTop:8, display:'flex', gap:8}}>
                <span style={{fontSize:11,color: verdict.transfer_passed ? 'var(--accent-green)':'var(--accent-red)'}}>
                  Gate 1 {verdict.transfer_passed ? "✅" : "❌"}
                </span>
                <span style={{fontSize:11,color: verdict.counter_probe_passed ? 'var(--accent-green)':'var(--accent-orange)'}}>
                  Gate 2 {verdict.counter_probe_passed ? "✅" : "⚠️"}
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
