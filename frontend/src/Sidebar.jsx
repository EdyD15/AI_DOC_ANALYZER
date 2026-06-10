import { useRef, useState } from 'react'
import { FileText, Trash2, Loader, ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react'
import styles from './Sidebar.module.css'

export default function Sidebar({
  sessions,
  currentSession,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  documents,
  activeDocs,
  onSetActiveDocs,
  onUpload,
  onClearDocs,
  onClearChat,
  messages,
  onExport,
  uploading,
  uploadError,
  sidebarOpen,
  onToggleSidebar,
}) {
  const fileInputRef = useRef(null)
  const sessionNames = Object.keys(sessions)
  const [filterOpen, setFilterOpen] = useState(false)

  function handleFileChange(e) {
    const file = e.target.files[0]
    if (file) {
      onUpload(file)
      e.target.value = ''
    }
  }

  function toggleDoc(name) {
    if (activeDocs.includes(name)) {
      onSetActiveDocs(activeDocs.filter(d => d !== name))
    } else {
      onSetActiveDocs([...activeDocs, name])
    }
  }

  return (
    <aside className={`${styles.sidebar} ${!sidebarOpen ? styles.sidebarCollapsed : ''}`}>
      {/* Brand */}
      <div className={`${styles.brand} ${!sidebarOpen ? styles.brandCollapsed : ''}`}>
        {sidebarOpen && (
          <>
            <FileText size={16} color="var(--accent)" />
            <span className={styles.brandName}>DocuMind</span>
          </>
        )}
        <button
          className={styles.collapseBtn}
          style={sidebarOpen ? { marginLeft: 'auto' } : {}}
          onClick={onToggleSidebar}
          aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          {sidebarOpen ? <ChevronLeft size={15} /> : <ChevronRight size={15} />}
        </button>
      </div>

      {sidebarOpen && (
        <div className={styles.sidebarBody}>
          {/* New Chat */}
          <div className={styles.section}>
            <button className={styles.newChatBtn} onClick={onNewChat}>
              New Chat
            </button>
          </div>

          {/* Session list */}
          <nav className={styles.sessionList} aria-label="Chat sessions">
            {sessionNames.map(name => (
              <div
                key={name}
                className={`${styles.sessionItem} ${name === currentSession ? styles.sessionItemActive : ''}`}
                onClick={() => onSelectSession(name)}
                role="button"
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && onSelectSession(name)}
                aria-current={name === currentSession ? 'true' : undefined}
              >
                <span className={styles.sessionName} title={name}>{name}</span>
                {sessionNames.length > 1 && (
                  <button
                    className={styles.deleteBtn}
                    aria-label={`Delete ${name}`}
                    onClick={e => {
                      e.stopPropagation()
                      onDeleteSession(name)
                    }}
                  >
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            ))}
          </nav>

          <hr className={styles.divider} />

          {/* Knowledge base */}
          <div className={styles.section}>
            <div className={styles.kbHeader}>
              <span className={styles.caption} style={{ marginBottom: 0 }}>Knowledge base</span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.webp"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <button
                className={styles.uploadBtnSmall}
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                aria-label="Upload document"
              >
                {uploading ? <Loader size={12} className={styles.spinning} /> : '+ Upload'}
              </button>
            </div>
            {uploadError && <p className={styles.error} style={{ marginTop: 4 }}>{uploadError}</p>}

            {documents.length === 0 ? (
              <p className={styles.caption} style={{ marginTop: 6, marginBottom: 0 }}>
                No documents yet. Upload a PDF, DOCX, TXT, or image.
              </p>
            ) : (
              <>
                {/* Filter toggle */}
                <button
                  className={styles.filterToggle}
                  onClick={() => setFilterOpen(o => !o)}
                  aria-expanded={filterOpen}
                >
                  <span className={styles.filterLabel}>
                    Filter
                    <span className={styles.countBadge}>{documents.length}</span>
                  </span>
                  {activeDocs.length > 0 && (
                    <span className={styles.activeBadge}>{activeDocs.length} active</span>
                  )}
                  <ChevronDown
                    size={13}
                    className={`${styles.chevron} ${filterOpen ? styles.chevronOpen : ''}`}
                  />
                </button>

                {/* Sliding document list */}
                <div className={`${styles.docPanel} ${filterOpen ? styles.docPanelOpen : ''}`}>
                  <p className={styles.caption} style={{ marginTop: 8, marginBottom: 4 }}>
                    Leave empty to search all.
                  </p>
                  <ul style={{ listStyle: 'none' }}>
                    {documents.map(doc => {
                      const isActive = activeDocs.includes(doc)
                      return (
                        <li
                          key={doc}
                          className={styles.docItem}
                          onClick={() => toggleDoc(doc)}
                          role="checkbox"
                          aria-checked={isActive}
                          tabIndex={filterOpen ? 0 : -1}
                          onKeyDown={e => e.key === 'Enter' && toggleDoc(doc)}
                        >
                          <span className={`${styles.dot} ${isActive ? styles.dotActive : ''}`} />
                          <span className={styles.docName} title={doc}>{doc}</span>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              </>
            )}
          </div>

          <hr className={styles.divider} />

          {/* Actions */}
          <div className={styles.section}>
            {messages.length > 0 && (
              <>
                <div className={styles.actionRow}>
                  <button className={styles.actionBtn} onClick={() => onExport('docx')}>
                    Export .docx
                  </button>
                  <button className={styles.actionBtn} onClick={() => onExport('pdf')}>
                    Export .pdf
                  </button>
                </div>
                <button className={styles.clearBtn} onClick={onClearChat}>
                  Clear chat
                </button>
              </>
            )}
            {documents.length > 0 && (
              <button
                className={styles.clearBtn}
                style={messages.length > 0 ? { marginTop: 4 } : {}}
                onClick={onClearDocs}
              >
                Clear docs
              </button>
            )}
          </div>
        </div>
      )}
    </aside>
  )
}
