// Header Component — includes Judge Quick-Switcher and Inspector button
function Header({ presetLearners, onPresetChange, onOpenInspector, currentSession }) {
  return (
    <header className="header">
      <div className="header-logo">
        <div className="header-logo-icon">🎓</div>
        <div>
          <div className="header-logo-text">Re:Learn</div>
          <div className="header-logo-subtitle">Adaptive Misconception Diagnosis</div>
        </div>
      </div>

      <div className="header-controls">
        {/* Judge Quick-Switcher */}
        <div className="judge-switcher" id="judge-quick-switcher">
          <label>🎭 Judge:</label>
          <select
            onChange={e => onPresetChange(e.target.value)}
            defaultValue=""
            title="Switch to a preset learner profile for demo"
          >
            <option value="">— Live Session —</option>
            {presetLearners.map(l => (
              <option key={l.session_token} value={l.session_token}>
                {l.name}
              </option>
            ))}
          </select>
        </div>

        <div className="header-badge">v1.0 Demo</div>

        <button
          id="inspector-modal-btn"
          className="inspector-btn"
          onClick={onOpenInspector}
          title="Open Model Inspector"
        >
          🔬 Inspector
        </button>
      </div>
    </header>
  );
}

// Problem Bar
function ProblemBar({ problems, selectedId, onSelect, problem }) {
  return (
    <>
      <div className="problem-bar">
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Problem
        </span>
        <select
          id="problem-select"
          className="problem-select"
          value={selectedId || ""}
          onChange={e => onSelect(Number(e.target.value))}
        >
          {problems.map(p => (
            <option key={p.id} value={p.id}>
              #{p.id} — {p.title}
              {p.misconception_tags ? ` [${p.misconception_tags.join(", ")}]` : ""}
            </option>
          ))}
        </select>
      </div>
      {problem && (
        <div className="problem-description">
          <h3>
            <span style={{color: 'var(--accent-blue)'}}>📋</span>
            {problem.title}
          </h3>
          <p style={{whiteSpace: 'pre-wrap'}}>{problem.description}</p>
        </div>
      )}
    </>
  );
}

// Editor Toolbar
function EditorToolbar({ onSubmit, isSubmitting, diagnosisResult }) {
  const passed = diagnosisResult?.passed ?? null;
  const total = diagnosisResult?.total ?? null;

  let badgeClass = "";
  let badgeText = "";
  if (passed !== null) {
    if (passed === total) { badgeClass = "pass"; badgeText = `✅ ${passed}/${total}`; }
    else if (passed === 0) { badgeClass = "fail"; badgeText = `❌ ${passed}/${total}`; }
    else { badgeClass = "partial"; badgeText = `⚡ ${passed}/${total}`; }
  }

  return (
    <div className="editor-toolbar">
      <button
        id="submit-btn"
        className="btn btn-primary"
        onClick={onSubmit}
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <><span className="loading-spinner" /> Analysing…</>
        ) : (
          <>▶ Run &amp; Diagnose</>
        )}
      </button>
      <div className="test-status">
        {badgeText && (
          <span className={`test-badge ${badgeClass}`}>{badgeText}</span>
        )}
        <span>Tests</span>
      </div>
    </div>
  );
}

// Console Panel
function ConsolePanel({ lines }) {
  const ref = React.useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);

  return (
    <div className="console-panel">
      <div className="console-header">
        <span className="console-dot" />
        Console Output
      </div>
      <div className="console-content" ref={ref}>
        {lines.length === 0 ? (
          <span style={{color: 'var(--text-muted)'}}>Submit code to see output…</span>
        ) : (
          lines.map(l => (
            <div key={l.id} className={`console-line ${l.type}`}>{l.text}</div>
          ))
        )}
      </div>
    </div>
  );
}
