// Re:Learn — Main App Shell
// Dual-pane IDE with Monaco Editor, Diagnosis Feed, Visualizer

const { useState, useEffect, useRef, useCallback } = React;

const API_BASE = "http://127.0.0.1:8000";

// ─────────────────────────────────────────────
// Utility: fetch wrapper
// ─────────────────────────────────────────────
async function api(path, body = null) {
  const opts = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : { method: "GET" };
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Network error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ─────────────────────────────────────────────
// Main App
// ─────────────────────────────────────────────
function App() {
  const [problems, setProblems] = useState([]);
  const [selectedProblemId, setSelectedProblemId] = useState(null);
  const [selectedProblem, setSelectedProblem] = useState(null);
  const [code, setCode] = useState("def solution(nums):\n    # your code here\n    pass\n");
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionToken, setSessionToken] = useState(() => localStorage.getItem("relearn_session") || null);
  const [activeTab, setActiveTab] = useState("diagnosis"); // diagnosis | visualizer | reassess
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [consoleLines, setConsoleLines] = useState([]);
  const [presetLearners, setPresetLearners] = useState([]);

  // Load problems on mount
  useEffect(() => {
    api("/api/inspector/problems")
      .then(data => {
        setProblems(data);
        if (data.length > 0) {
          setSelectedProblemId(data[0].id);
          setSelectedProblem(data[0]);
        }
      })
      .catch(err => addConsole(`error`, `Failed to load problems: ${err.message}`));

    api("/api/inspector/learners")
      .then(setPresetLearners)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedProblemId) {
      const p = problems.find(x => x.id === selectedProblemId);
      if (p) {
        setSelectedProblem(p);
        setDiagnosisResult(null);
      }
    }
  }, [selectedProblemId, problems]);

  const addConsole = useCallback((type, text) => {
    setConsoleLines(prev => [...prev.slice(-50), { type, text, id: Date.now() + Math.random() }]);
  }, []);

  const handleSubmit = async () => {
    if (!selectedProblemId) return;
    setIsSubmitting(true);
    setConsoleLines([]);
    addConsole("info", `Submitting to problem #${selectedProblemId}…`);

    try {
      const result = await api("/api/submit", {
        code,
        problem_id: selectedProblemId,
        session_token: sessionToken,
      });

      // Store session token
      if (!sessionToken) {
        // We'd need the token from response; store submission_id as proxy
        const tok = `session-${result.submission_id}-${Date.now()}`;
        setSessionToken(tok);
        localStorage.setItem("relearn_session", tok);
      }

      setDiagnosisResult(result);

      // Console output
      addConsole("info", `Tests: ${result.passed}/${result.total} passed`);
      result.test_results.forEach((tr, i) => {
        const status = tr.ok ? "pass" : "fail";
        addConsole(status, `  [${i + 1}] input=${JSON.stringify(tr.input)} → got ${JSON.stringify(tr.actual)} (expected ${JSON.stringify(tr.expected)})`);
      });
      if (result.error) addConsole("error", `Error: ${result.error}`);
      if (result.passed === result.total) {
        addConsole("pass", "✅ All tests passed!");
      }
      setActiveTab("diagnosis");
    } catch (err) {
      addConsole("error", `❌ ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePresetChange = (token) => {
    if (!token) return;
    setSessionToken(token);
    localStorage.setItem("relearn_session", token);
    addConsole("info", `Switched to preset learner: ${token}`);
  };

  return (
    <div id="root">
      <Header
        presetLearners={presetLearners}
        onPresetChange={handlePresetChange}
        onOpenInspector={() => setInspectorOpen(true)}
        currentSession={sessionToken}
      />
      <div className="workspace">
        {/* Left Pane */}
        <div className="pane-editor">
          <ProblemBar
            problems={problems}
            selectedId={selectedProblemId}
            onSelect={id => setSelectedProblemId(id)}
            problem={selectedProblem}
          />
          <EditorPane
            code={code}
            onChange={setCode}
          />
          <EditorToolbar
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
            diagnosisResult={diagnosisResult}
          />
          <ConsolePanel lines={consoleLines} />
        </div>

        {/* Right Pane */}
        <div className="pane-diagnosis">
          <div className="pane-tabs">
            {["diagnosis", "visualizer", "reassess"].map(tab => (
              <div
                key={tab}
                className={`pane-tab ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === "diagnosis" ? "🎯 Diagnosis" :
                 tab === "visualizer" ? "🧠 Trace" : "🔁 Reassess"}
              </div>
            ))}
          </div>
          <div className="pane-content">
            {activeTab === "diagnosis" && (
              <DiagnosisPane result={diagnosisResult} />
            )}
            {activeTab === "visualizer" && (
              <VisualizerPane result={diagnosisResult} />
            )}
            {activeTab === "reassess" && (
              <ReassessPane
                result={diagnosisResult}
                problems={problems}
                sessionToken={sessionToken}
              />
            )}
          </div>
        </div>
      </div>

      {inspectorOpen && (
        <InspectorModal onClose={() => setInspectorOpen(false)} />
      )}
    </div>
  );
}
