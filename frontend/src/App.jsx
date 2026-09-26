import { useState } from 'react'
import './index.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

/**
 * Extract a human-readable error message from a FastAPI/Pydantic error response.
 * Pydantic 422 responses return { detail: [{msg, loc, ...}, ...] } (array),
 * while custom HTTPExceptions return { detail: "string" }.
 */
function extractErrorDetail(errData, fallback = 'Something went wrong.') {
  if (!errData || !errData.detail) return fallback
  if (typeof errData.detail === 'string') return errData.detail
  if (Array.isArray(errData.detail)) {
    return errData.detail
      .map((e) => e.msg || JSON.stringify(e))
      .join('; ')
  }
  return fallback
}

function App() {
  const [file, setFile] = useState(null)
  const [pastedText, setPastedText] = useState('')
  const [results, setResults] = useState(null)
  const [documentText, setDocumentText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
      setError('')
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError('')
    }
  }

  const loadSample = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/sample`)
      const data = await res.json()
      setPastedText(data.text)
      setFile(null)
      // Auto-analyze the sample
      await analyzeText(data.text)
    } catch (err) {
      setError('Could not load sample agreement. Make sure the backend is running.')
      setLoading(false)
    }
  }

  const analyzeText = async (text) => {
    setLoading(true)
    setError('')
    const formData = new FormData()
    formData.append('text', text)
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(extractErrorDetail(errData, 'Analysis failed'))
      }
      const data = await res.json()
      setResults(data)
      setDocumentText(data.document_text)
      setChatMessages([])
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (file) {
      setLoading(true)
      setError('')
      const formData = new FormData()
      formData.append('file', file)
      try {
        const res = await fetch(`${API_BASE}/analyze`, {
          method: 'POST',
          body: formData,
        })
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(extractErrorDetail(errData, 'Analysis failed'))
        }
        const data = await res.json()
        setResults(data)
        setDocumentText(data.document_text)
        setChatMessages([])
      } catch (err) {
        setError(err.message || 'Something went wrong. Please try again.')
      } finally {
        setLoading(false)
      }
    } else if (pastedText.trim()) {
      await analyzeText(pastedText.trim())
    } else {
      setError('Please upload a PDF or paste the agreement text.')
    }
  }

  const handleAsk = async () => {
    if (!chatInput.trim() || !documentText) return
    const question = chatInput.trim()
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', content: question }])
    setChatLoading(true)

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_text: documentText, question }),
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(extractErrorDetail(errData, 'Failed to get answer'))
      }
      const data = await res.json()
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        source_quote: data.source_quote,
      }])
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}`,
      }])
    } finally {
      setChatLoading(false)
    }
  }

  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  const downloadLawyerQuestions = () => {
    if (!results?.lawyer_questions) return
    const lines = [
      'QUESTIONS TO ASK A LAWYER',
      '=' .repeat(40),
      'Generated by ClauseCheck',
      'This is general information, not legal advice.',
      '',
      ...results.lawyer_questions.map((q, i) => `[ ] ${i + 1}. ${q}`),
      '',
      '---',
      'Bring this list and your rental agreement to a qualified lawyer.',
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'lawyer-questions-clausecheck.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  const resetAll = () => {
    setFile(null)
    setPastedText('')
    setResults(null)
    setDocumentText('')
    setError('')
    setChatMessages([])
    setChatInput('')
  }

  const severityOrder = { High: 0, Medium: 1, Low: 2 }
  const sortedFlags = results?.red_flags
    ? [...results.red_flags].sort((a, b) => (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3))
    : []

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header__logo">
          <div className="header__icon">CC</div>
          <h1 className="header__title">ClauseCheck</h1>
        </div>
        <p className="header__subtitle">
          Understand your rental agreement before you sign. Built for tenants in India.
        </p>
      </header>

      {/* Notices */}
      <div className="notice-bar">
        <div className="notice notice--disclaimer">
          <strong>Disclaimer:</strong> This tool gives general information, not legal advice. Talk to a qualified lawyer before signing.
        </div>
        <div className="notice notice--privacy">
          <strong>Privacy:</strong> Your document is not stored. All processing happens in memory and nothing is saved.
        </div>
      </div>

      {/* Error */}
      {error && <div className="error-message" id="error-message" role="alert">{error}</div>}

      {/* Upload Section */}
      {!results && !loading && (
        <section className="upload-section">
          <div
            className={`upload-zone ${dragActive ? 'upload-zone--active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input').click()}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.getElementById('file-input').click() } }}
            role="button"
            tabIndex="0"
            aria-label="Upload rental agreement PDF"
            id="upload-zone"
          >
            <label htmlFor="file-input" className="sr-only">Upload rental agreement PDF</label>
            <input
              type="file"
              id="file-input"
              accept=".pdf"
              onChange={handleFileInput}
              style={{ display: 'none' }}
            />
            <span className="upload-zone__icon" aria-hidden="true">&#8593;</span>
            <p className="upload-zone__text">
              Drop your rental agreement PDF here, or click to browse
            </p>
            <p className="upload-zone__hint">PDF files up to 5 MB</p>
          </div>

          {file && (
            <div className="file-info">
              <span className="file-info__name">{file.name}</span>
              <button
                className="file-info__remove"
                onClick={(e) => { e.stopPropagation(); setFile(null) }}
                aria-label="Remove file"
              >
                x
              </button>
            </div>
          )}

          <div className="upload-divider">or paste text</div>

          <label htmlFor="text-input" className="sr-only">Paste rental agreement text</label>
          <textarea
            className="text-input-area"
            placeholder="Paste the full text of your rental agreement here..."
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            id="text-input"
          />

          <div className="upload-actions">
            <button
              className="btn btn--primary"
              onClick={handleAnalyze}
              disabled={!file && !pastedText.trim()}
              id="analyze-btn"
            >
              Analyze Agreement
            </button>
            <button
              className="btn btn--secondary"
              onClick={loadSample}
              id="sample-btn"
            >
              Try a sample rental agreement
            </button>
          </div>
        </section>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading">
          <div className="loading__spinner"></div>
          <p className="loading__text">Analyzing your agreement...</p>
          <p className="loading__subtext">This usually takes 15-30 seconds</p>
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div className="results">
          {/* Section 1: Summary */}
          <section className="section" id="summary-section">
            <div className="section__header">
              <span className="section__number">1</span>
              <h2 className="section__title">Plain English Summary</h2>
            </div>
            <ul className="summary-list">
              {results.summary.map((item, i) => (
                <li key={i} className="summary-item">{item}</li>
              ))}
            </ul>
          </section>

          {/* Section 2: Red Flags */}
          <section className="section" id="red-flags-section">
            <div className="section__header">
              <span className="section__number">2</span>
              <h2 className="section__title">Red Flags</h2>
            </div>
            <p className="flags-count">
              {sortedFlags.length} issue{sortedFlags.length !== 1 ? 's' : ''} found
              {sortedFlags.filter(f => f.severity === 'High').length > 0 &&
                ` \u2014 ${sortedFlags.filter(f => f.severity === 'High').length} high severity`}
            </p>
            {sortedFlags.map((flag, i) => (
              <div
                key={i}
                className={`flag-card flag-card--${flag.severity.toLowerCase()}`}
                id={`flag-${i}`}
              >
                <div className="flag-header">
                  <span className={`flag-severity flag-severity--${flag.severity.toLowerCase()}`}>
                    {flag.severity}
                  </span>
                </div>
                <blockquote className="flag-quote">
                  &ldquo;{flag.clause_quote}&rdquo;
                </blockquote>
                <p className="flag-risk">{flag.risk}</p>
                <div className="flag-suggestion">
                  <strong>Suggestion:</strong> {flag.suggestion}
                </div>
              </div>
            ))}
          </section>

          {/* Section 3: Ask a Question */}
          <section className="section" id="ask-section">
            <div className="section__header">
              <span className="section__number">3</span>
              <h2 className="section__title">Ask About This Document</h2>
            </div>
            <div className="chat-section">
              {chatMessages.length > 0 && (
                <div className="chat-messages" id="chat-messages">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`chat-message chat-message--${msg.role}`}>
                      <p>{msg.content}</p>
                      {msg.source_quote && (
                        <div className="chat-source-quote">
                          Source: &ldquo;{msg.source_quote}&rdquo;
                        </div>
                      )}
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="chat-message chat-message--assistant">
                      <p style={{ color: 'var(--color-text-muted)' }}>Thinking...</p>
                    </div>
                  )}
                </div>
              )}
              <div className="chat-input-area">
                <label htmlFor="chat-input" className="sr-only">Ask a question about your agreement</label>
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask a question about your agreement..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={handleChatKeyDown}
                  disabled={chatLoading}
                  id="chat-input"
                />
                <button
                  className="btn btn--primary"
                  onClick={handleAsk}
                  disabled={!chatInput.trim() || chatLoading}
                  id="ask-btn"
                >
                  Ask
                </button>
              </div>
            </div>
          </section>

          {/* Section 4: Lawyer Questions */}
          <section className="section" id="lawyer-section">
            <div className="section__header">
              <span className="section__number">4</span>
              <h2 className="section__title">Questions to Ask a Lawyer</h2>
            </div>
            <ul className="lawyer-questions-list">
              {results.lawyer_questions.map((q, i) => (
                <li key={i} className="lawyer-question-item">
                  <span className="lawyer-question-item__check"></span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
            <button
              className="btn btn--secondary"
              onClick={downloadLawyerQuestions}
              id="download-btn"
            >
              Download as text file
            </button>
          </section>

          {/* Reset */}
          <div className="new-analysis">
            <button className="btn btn--ghost" onClick={resetAll} id="reset-btn">
              Analyze another agreement
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        <p>ClauseCheck gives general information, not legal advice.</p>
      </footer>
    </div>
  )
}

export default App
