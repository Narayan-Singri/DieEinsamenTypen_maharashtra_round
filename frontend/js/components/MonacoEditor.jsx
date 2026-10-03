// Monaco Editor Pane
function EditorPane({ code, onChange }) {
  const containerRef = React.useRef(null);
  const editorRef = React.useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    if (editorRef.current) return; // Already initialized

    // Wait for Monaco to be ready
    if (!window.monaco) {
      const interval = setInterval(() => {
        if (window.monaco) {
          clearInterval(interval);
          initEditor();
        }
      }, 100);
      return () => clearInterval(interval);
    }
    initEditor();

    function initEditor() {
      editorRef.current = monaco.editor.create(containerRef.current, {
        value: code,
        language: "python",
        theme: "relearn-dark",
        fontSize: 13,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontLigatures: true,
        lineHeight: 22,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        wordWrap: "on",
        automaticLayout: true,
        padding: { top: 12, bottom: 12 },
        renderLineHighlight: "gutter",
        cursorBlinking: "smooth",
        cursorSmoothCaretAnimation: "on",
        smoothScrolling: true,
        bracketPairColorization: { enabled: true },
        guides: { bracketPairs: true },
        suggest: { showKeywords: true },
        tabSize: 4,
        insertSpaces: true,
      });

      editorRef.current.onDidChangeModelContent(() => {
        onChange(editorRef.current.getValue());
      });
    }

    return () => {
      if (editorRef.current) {
        editorRef.current.dispose();
        editorRef.current = null;
      }
    };
  }, []);

  // Sync external code changes (e.g. problem switching)
  useEffect(() => {
    if (editorRef.current) {
      const current = editorRef.current.getValue();
      if (current !== code) {
        editorRef.current.setValue(code);
      }
    }
  }, [code]);

  return <div className="editor-container" ref={containerRef} id="monaco-editor" />;
}
