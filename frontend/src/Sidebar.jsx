import { useEffect, useRef, useState } from 'react'
import { FileText, MoreVertical, Pencil, Share2, Trash2, Loader, ChevronLeft, ChevronRight, ChevronDown, LogOut, KeyRound } from 'lucide-react'
import ChangePasswordModal from './ChangePasswordModal'
import styles from './Sidebar.module.css'

export default function Sidebar({
  sessions,
  currentSession,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onRenameSession,
  onShareSession,
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
  username,
  onLogout,
}) {
  const fileInputRef = useRef(null)
  const sessionNames = Object.keys(sessions)
  const [filterOpen, setFilterOpen] = useState(false)
  const [menuOpenFor, setMenuOpenFor] = useState(null)
  const [renamingSession, setRenamingSession] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const menuRef = useRef(null)
  const userMenuRef = useRef(null)

  useEffect(() => {
    if (!menuOpenFor) return
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpenFor(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [menuOpenFor])

  useEffect(() => {
    if (!userMenuOpen) return
    function handleClickOutside(e) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [userMenuOpen])

  function commitRename() {
    const newName = renameValue.trim()
    if (newName && newName !== renamingSession) {
      onRenameSession(renamingSession, newName)
    }
    setRenamingSession(null)
  }

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
            {sessionNames.map(name => {
              const isRenaming = renamingSession === name
              return (
                <div
                  key={name}
                  className={`${styles.sessionItem} ${name === currentSession ? styles.sessionItemActive : ''}`}
                  onClick={() => !isRenaming && onSelectSession(name)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && !isRenaming && onSelectSession(name)}
                  aria-current={name === currentSession ? 'true' : undefined}
                >
                  {isRenaming ? (
                    <input
                      className={styles.renameInput}
                      value={renameValue}
                      autoFocus
                      onClick={e => e.stopPropagation()}
                      onChange={e => setRenameValue(e.target.value)}
                      onBlur={commitRename}
                      onKeyDown={e => {
                        if (e.key === 'Enter') { e.preventDefault(); commitRename() }
                        if (e.key === 'Escape') { e.preventDefault(); setRenamingSession(null) }
                      }}
                    />
                  ) : (
                    <span className={styles.sessionName} title={name}>{name}</span>
                  )}

                  <div className={styles.sessionMenuWrap} ref={menuOpenFor === name ? menuRef : null}>
                    <button
                      className={styles.sessionMenuBtn}
                      aria-label={`More actions for ${name}`}
                      aria-haspopup="true"
                      aria-expanded={menuOpenFor === name}
                      onClick={e => {
                        e.stopPropagation()
                        setMenuOpenFor(o => (o === name ? null : name))
                      }}
                    >
                      <MoreVertical size={13} />
                    </button>

                    {menuOpenFor === name && (
                      <div className={styles.sessionMenu} role="menu">
                        <button
                          className={styles.sessionMenuItem}
                          role="menuitem"
                          onClick={e => {
                            e.stopPropagation()
                            setRenamingSession(name)
                            setRenameValue(name)
                            setMenuOpenFor(null)
                          }}
                        >
                          <Pencil size={13} />
                          Rename
                        </button>
                        <button
                          className={styles.sessionMenuItem}
                          role="menuitem"
                          onClick={e => {
                            e.stopPropagation()
                            onShareSession(name)
                            setMenuOpenFor(null)
                          }}
                        >
                          <Share2 size={13} />
                          Share
                        </button>
                        {sessionNames.length > 1 && (
                          <button
                            className={`${styles.sessionMenuItem} ${styles.sessionMenuItemDanger}`}
                            role="menuitem"
                            onClick={e => {
                              e.stopPropagation()
                              onDeleteSession(name)
                              setMenuOpenFor(null)
                            }}
                          >
                            <Trash2 size={13} />
                            Delete
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
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

          {/* User footer */}
          <div className={styles.userFooter} ref={userMenuRef}>
            <button
              className={styles.userTrigger}
              onClick={() => setUserMenuOpen(o => !o)}
              aria-haspopup="true"
              aria-expanded={userMenuOpen}
            >
              <span className={styles.username} title={username}>{username}</span>
              <ChevronDown
                size={13}
                className={`${styles.chevron} ${userMenuOpen ? styles.chevronOpen : ''}`}
              />
            </button>

            {userMenuOpen && (
              <div className={styles.userMenu} role="menu">
                <button
                  className={styles.userMenuItem}
                  role="menuitem"
                  onClick={() => {
                    setUserMenuOpen(false)
                    setShowPasswordModal(true)
                  }}
                >
                  <KeyRound size={13} />
                  Change Password
                </button>
                <button
                  className={`${styles.userMenuItem} ${styles.userMenuItemDanger}`}
                  role="menuitem"
                  onClick={onLogout}
                >
                  <LogOut size={13} />
                  Log out
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </aside>
  )
}
