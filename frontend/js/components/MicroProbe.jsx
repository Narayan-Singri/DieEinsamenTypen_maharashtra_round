// MicroProbe — 1-Click Micro-Probe Selector with Bayesian Feedback
function MicroProbe({ result, onProbeAnswer }) {
  const [answered, setAnswered] = useState(null);   // selected option key
  const [probeResult, setProbeResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Reset when new submission comes in
  useEffect(() => {
    setAnswered(null);
    setProbeResult(null);
  }, [result?.submission_id]);

  if (!result || !result.probe_required || !result.probe) {
    if (!result) return null;
    return (
      <div className="probe-card" style={{opacity: 0.5}}>
        <div className="probe-title">⚡ Micro-Probe</div>
        <div style={{fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: '10px 0'}}>
          {result.confidence > 0.7
            ? `High confidence in ${result.top_misconception} — no probe needed`
            : "No probe available for this pattern"}
        </div>
      </div>
    );
  }

  const probe = result.probe;
  const diagnosisId = result.submission_id; // use as proxy for diagnosis_id
  // Note: in real flow we'd use result.diagnosis_id; adjust if backend exposes it

  const handleAnswer = async (optionKey) => {
    if (answered) return;
    setAnswered(optionKey);
    setLoading(true);
    try {
      // We need diagnosis_id; for demo we'll call the probe endpoint
      // The submit response doesn't directly give diagnosis_id,
      // so we pass submission_id * 1 as a best-effort (backend DB seeded sequentially)
      const res = await fetch(`${API_BASE}/api/probe/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          diagnosis_id: diagnosisId,
          probe_id: probe.id,
          selected_option: optionKey,
        }),
      });
      const data = await res.json();
      setProbeResult(data);
      if (onProbeAnswer) onProbeAnswer(data);
    } catch (e) {
      setProbeResult({ feedback: "Could not connect to backend for Bayesian update." });
    } finally {
      setLoading(false);
    }
  };

  const isCorrect = probeResult && probeResult.is_correct;

  // Format probe question — simple markdown-like rendering
  const renderQuestion = (q) => {
    const parts = q.split("```");
    return parts.map((part, i) => {
      if (i % 2 === 1) {
        // Inside code block
        const lines = part.replace(/^python\n/, "");
        return (
          <pre key={i} style={{
            background: 'var(--bg-secondary)',
            borderRadius: '6px',
            padding: '8px 10px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            color: 'var(--text-code)',
            margin: '6px 0',
            overflowX: 'auto',
            lineHeight: 1.6,
          }}>{lines}</pre>
        );
      }
      return <span key={i} style={{whiteSpace:'pre-wrap'}}>{part}</span>;
    });
  };

  return (
    <div className="probe-card">
      <div className="probe-title">⚡ 1-Click Micro-Probe</div>
      <div className="probe-question">
        {renderQuestion(probe.question)}
      </div>
      <div className="probe-options">
        {Object.entries(probe.options).map(([key, text]) => {
          let cls = "";
          if (answered === key) {
            cls = isCorrect ? "selected-correct" : "selected-wrong";
          } else if (answered && probeResult && key === probeResult.correct_option) {
            cls = "selected-correct";
          }
          return (
            <button
              key={key}
              id={`probe-option-${key}`}
              className={`probe-option ${cls}`}
              onClick={() => handleAnswer(key)}
              disabled={!!answered || loading}
            >
              <span className="probe-option-key">{key}</span>
              {text}
            </button>
          );
        })}
      </div>
      {loading && (
        <div style={{marginTop: 10, textAlign: 'center'}}>
          <span className="loading-spinner" />
        </div>
      )}
      {probeResult && probeResult.feedback && (
        <div className={`probe-feedback ${probeResult.is_correct ? "correct" : "wrong"}`}>
          {probeResult.feedback}
          {probeResult.updated_probabilities && (
            <div style={{marginTop: 6, opacity: 0.8}}>
              Updated top: <strong>{probeResult.top_misconception}</strong>{" "}
              ({Math.round(probeResult.confidence * 100)}% confidence)
            </div>
          )}
        </div>
      )}
    </div>
  );
}
