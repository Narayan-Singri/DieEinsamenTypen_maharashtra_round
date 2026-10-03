// Visualizer — Interactive Memory-Box Trace Timeline
// Reads memory_boxes from submit response, renders step-by-step variable state

function Visualizer({ memoryBoxes, traceFrames }) {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const intervalRef = React.useRef(null);
  const prevVarsRef = React.useRef({});

  const frames = memoryBoxes && memoryBoxes.length > 0 ? memoryBoxes : [];
  const total = frames.length;

  useEffect(() => {
    setStep(0);
    prevVarsRef.current = {};
    setPlaying(false);
  }, [memoryBoxes]);

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setStep(s => {
          if (s >= total - 1) {
            setPlaying(false);
            clearInterval(intervalRef.current);
            return s;
          }
          return s + 1;
        });
      }, 600);
    }
    return () => clearInterval(intervalRef.current);
  }, [playing, total]);

  if (!frames.length) {
    return (
      <div className="visualizer-section">
        <div className="section-title">🧠 Memory-Box Trace</div>
        <div className="viz-empty">Submit code to see variable trace…</div>
      </div>
    );
  }

  const currentFrame = frames[step];
  const currentVars = currentFrame?.vars || {};

  // Detect changed vars vs previous step
  const prevVars = step > 0 ? (frames[step - 1]?.vars || {}) : {};

  return (
    <div className="visualizer-section">
      <div className="section-title">🧠 Memory-Box Trace</div>

      {/* Playback controls */}
      <div className="viz-playback">
        <button className="viz-btn" onClick={() => setStep(0)} title="First" disabled={step === 0}>⏮</button>
        <button className="viz-btn" onClick={() => setStep(s => Math.max(0, s-1))} title="Prev" disabled={step === 0}>◀</button>
        <button
          className={`viz-btn ${playing ? "play-active" : ""}`}
          onClick={() => setPlaying(p => !p)}
          title={playing ? "Pause" : "Play"}
          id="viz-play-btn"
        >
          {playing ? "⏸" : "▶"}
        </button>
        <button className="viz-btn" onClick={() => setStep(s => Math.min(total-1, s+1))} title="Next" disabled={step >= total - 1}>▶</button>
        <button className="viz-btn" onClick={() => setStep(total - 1)} title="Last" disabled={step >= total - 1}>⏭</button>
        <input
          type="range"
          className="viz-slider"
          min={0}
          max={total - 1}
          value={step}
          onChange={e => { setPlaying(false); setStep(Number(e.target.value)); }}
          id="viz-scrub-slider"
        />
        <span className="viz-counter">{step + 1}/{total}</span>
      </div>

      {/* Current source line */}
      <div className="viz-source-line">
        <span className="line-num">L{currentFrame?.line}</span>
        <span style={{color: currentFrame?.event === 'return' ? 'var(--accent-green)' : 'var(--text-code)'}}>
          {currentFrame?.event === 'return' ? '→ return ' : ''}
          {currentFrame?.source_line || "…"}
        </span>
        <span style={{marginLeft:'auto', fontSize: 10, color:'var(--text-muted)', textTransform:'uppercase'}}>
          {currentFrame?.event}
        </span>
      </div>

      {/* Memory boxes */}
      <div className="memory-boxes">
        {Object.entries(currentVars).length === 0 ? (
          <div style={{color: 'var(--text-muted)', fontSize: 12}}>No variables at this step</div>
        ) : (
          Object.entries(currentVars).map(([name, value]) => {
            const prevVal = prevVars[name];
            const changed = JSON.stringify(prevVal) !== JSON.stringify(value) && step > 0;
            const displayVal = Array.isArray(value)
              ? `[${value.join(", ")}]`
              : value === null ? "None"
              : String(value);
            const prevDisplay = Array.isArray(prevVal)
              ? `[${prevVal.join(", ")}]`
              : prevVal === null ? "None"
              : prevVal !== undefined ? String(prevVal) : null;

            return (
              <div key={name} className={`memory-box ${changed ? "changed" : ""}`}>
                <div className="memory-box-name">{name}</div>
                {changed && prevDisplay !== null && (
                  <div className="memory-box-arrow">{prevDisplay} →</div>
                )}
                <div className="memory-box-value">{displayVal}</div>
              </div>
            );
          })
        )}
      </div>

      {/* Step description */}
      {currentFrame?.event === 'return' && (
        <div style={{
          marginTop: 8,
          padding: '6px 10px',
          background: 'rgba(34,197,94,0.08)',
          border: '1px solid rgba(34,197,94,0.3)',
          borderRadius: 6,
          fontSize: 12,
          color: 'var(--accent-green)',
        }}>
          ✅ Function returned: <strong style={{fontFamily:'JetBrains Mono', monospace: true}}>
            {JSON.stringify(currentVars)}
          </strong>
        </div>
      )}
    </div>
  );
}
