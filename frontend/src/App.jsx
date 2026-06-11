import { useState, useEffect, useRef } from 'react'
import Sidebar from './Sidebar'
import Chat from './Chat'
import {
  listSessions,
  listDocuments,
  saveSession,
  deleteSession,
  uploadDocument,
  clearDocuments,
  streamChat,
  exportChat,
} from './api.js'
import styles from './App.module.css'

const MAX_INPUT = 5000

function stripForStorage(msg) {
  return { role: msg.role, content: msg.content }
}

export default function App() {
  const [sessions, setSessions] = useState({})
  const [currentSession, setCurrentSession] = useState('Chat 1')
  const [sessionCounter, setSessionCounter] = useState(1)
  const [documents, setDocuments] = useState([])
  const [activeDocs, setActiveDocs] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  // Sidebar starts as an overlay drawer (closed) on mobile, persistent (open) on desktop
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 768)

  const accumulatorRef = useRef('')

  // On mount: load sessions and documents from API
  useEffect(() => {
    async function init() {
      let [sessionData, docData] = [null, null]

      try {
        sessionData = await listSessions()
      } catch {
        sessionData = {}
      }

      try {
        docData = await listDocuments()
      } catch {
        docData = {}
      }

      const docNames = Object.keys(docData || {})
      setDocuments(docNames)

      const sessionNames = Object.keys(sessionData || {})

      if (sessionNames.length === 0) {
        // Create a default session
        const defaultName = 'Chat 1'
        try {
          await saveSession(defaultName, [])
        } catch {
          // best effort
        }
        setSessions({ [defaultName]: [] })
        setCurrentSession(defaultName)
        setSessionCounter(1)
      } else {
        setSessions(sessionData)
        setCurrentSession(sessionNames[sessionNames.length - 1])

        // Derive the highest Chat N counter
        let highest = 0
        for (const name of sessionNames) {
          const match = name.match(/^Chat (\d+)$/)
          if (match) {
            const n = parseInt(match[1], 10)
            if (n > highest) highest = n
          }
        }
        setSessionCounter(highest || sessionNames.length)
      }
    }

    init()
  }, [])

  // Session management
  async function handleNewChat() {
    const next = sessionCounter + 1
    const name = `Chat ${next}`
    try {
      await saveSession(name, [])
    } catch {
      // best effort
    }
    setSessions(prev => ({ ...prev, [name]: [] }))
    setSessionCounter(next)
    setCurrentSession(name)
    setActiveDocs([])
    if (window.innerWidth < 768) setSidebarOpen(false)
  }

  function handleSelectSession(name) {
    setCurrentSession(name)
    if (window.innerWidth < 768) setSidebarOpen(false)
  }

  async function handleDeleteSession(name) {
    try {
      await deleteSession(name)
    } catch {
      // best effort
    }

    setSessions(prev => {
      const updated = { ...prev }
      delete updated[name]
      return updated
    })

    setSessions(prev => {
      const remaining = Object.keys(prev)
      if (remaining.length === 0) {
        // Will be handled by the effect below
        return prev
      }
      setCurrentSession(remaining[remaining.length - 1])
      return prev
    })

    // If we just deleted the last session, create a fresh one
    setSessions(prev => {
      const remaining = Object.keys(prev)
      if (remaining.length === 0) {
        const defaultName = 'Chat 1'
        saveSession(defaultName, []).catch(() => {})
        setSessionCounter(1)
        setCurrentSession(defaultName)
        return { [defaultName]: [] }
      }
      return prev
    })
  }

  // Document management
  async function handleUpload(file) {
    setUploading(true)
    setUploadError(null)
    try {
      await uploadDocument(file)
      const docData = await listDocuments()
      setDocuments(Object.keys(docData || {}))
    } catch (err) {
      setUploadError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function handleClearDocs() {
    try {
      await clearDocuments()
    } catch {
      // best effort
    }
    setDocuments([])
    setActiveDocs([])
  }

  async function handleClearChat() {
    setSessions(prev => ({ ...prev, [currentSession]: [] }))
    try {
      await saveSession(currentSession, [])
    } catch {
      // best effort
    }
  }

  // Chat
  async function handleSend(text, imageFile = null) {
    if (text.length > MAX_INPUT) return

    const chatHistory = (sessions[currentSession] || []).map(stripForStorage)

    const imageUrl = imageFile ? URL.createObjectURL(imageFile) : undefined
    const userMessage = { role: 'user', content: text, ...(imageUrl ? { imageUrl } : {}) }

    // Append user message immediately (imageUrl for in-session display only)
    setSessions(prev => ({
      ...prev,
      [currentSession]: [...(prev[currentSession] || []), userMessage],
    }))

    // Persist user message (strip imageUrl — not serializable long-term)
    const messagesWithUser = [
      ...(sessions[currentSession] || []).map(stripForStorage),
      { role: 'user', content: text },
    ]
    try {
      await saveSession(currentSession, messagesWithUser)
    } catch {
      // best effort
    }

    // Add a placeholder AI message for streaming
    const aiPlaceholder = { role: 'assistant', content: '' }
    setSessions(prev => ({
      ...prev,
      [currentSession]: [...(prev[currentSession] || []), aiPlaceholder],
    }))

    accumulatorRef.current = ''
    setLoading(true)

    try {
      for await (const chunk of streamChat(text, activeDocs, imageFile, chatHistory)) {
        accumulatorRef.current += chunk
        const accumulated = accumulatorRef.current
        setSessions(prev => {
          const msgs = [...(prev[currentSession] || [])]
          if (msgs.length > 0) {
            msgs[msgs.length - 1] = { role: 'assistant', content: accumulated }
          }
          return { ...prev, [currentSession]: msgs }
        })
      }

      // Persist final session after streaming is complete
      setSessions(prev => {
        const finalMessages = (prev[currentSession] || []).map(stripForStorage)
        saveSession(currentSession, finalMessages).catch(() => {})
        return prev
      })
    } catch {
      // Rollback: remove user message and AI placeholder
      setSessions(prev => {
        const msgs = prev[currentSession] || []
        const rolledBack = msgs.slice(0, msgs.length - 2)
        saveSession(currentSession, rolledBack.map(stripForStorage)).catch(() => {})
        return { ...prev, [currentSession]: rolledBack }
      })
    } finally {
      setLoading(false)
      accumulatorRef.current = ''
    }
  }

  // Export
  function handleExport(format) {
    const currentMessages = sessions[currentSession] || []
    exportChat(currentMessages, format).catch(() => {})
  }

  const currentMessages = sessions[currentSession] || []

  return (
    <div className={styles.shell}>
      <Sidebar
        sessions={sessions}
        currentSession={currentSession}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        documents={documents}
        activeDocs={activeDocs}
        onSetActiveDocs={setActiveDocs}
        onUpload={handleUpload}
        onClearDocs={handleClearDocs}
        onClearChat={handleClearChat}
        messages={currentMessages}
        onExport={handleExport}
        uploading={uploading}
        uploadError={uploadError}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(o => !o)}
      />
      {sidebarOpen && (
        <div className={styles.backdrop} onClick={() => setSidebarOpen(false)} />
      )}
      <Chat
        messages={currentMessages}
        onSend={handleSend}
        loading={loading}
        activeDocs={activeDocs}
        onToggleSidebar={() => setSidebarOpen(o => !o)}
      />
    </div>
  )
}
