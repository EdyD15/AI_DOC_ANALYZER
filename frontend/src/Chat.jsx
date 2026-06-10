import { useState, useRef, useEffect } from 'react'
import { FileQuestion, ArrowUp, Paperclip, X } from 'lucide-react'
import styles from './Chat.module.css'

const MAX_INPUT = 5000
const CHAR_WARN_THRESHOLD = 4000

function renderText(text) {
  if (!text) return null

  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)

  const nodes = []
  let keyIdx = 0

  for (const part of parts) {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      nodes.push(<strong key={keyIdx++}>{part.slice(2, -2)}</strong>)
    } else if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      nodes.push(<code key={keyIdx++}>{part.slice(1, -1)}</code>)
    } else {
      const lines = part.split('\n')
      lines.forEach((line, i) => {
        nodes.push(line)
        if (i < lines.length - 1) {
          nodes.push(<br key={keyIdx++} />)
        }
      })
    }
  }

  return nodes
}

export default function Chat({ messages, onSend, loading, activeDocs }) {
  const [input, setInput] = useState('')
  const [attachedImage, setAttachedImage] = useState(null) // { file, url }
  const textareaRef = useRef(null)
  const messagesEndRef = useRef(null)
  const imgInputRef = useRef(null)

  const charCount = input.length
  const isEmpty = input.trim().length === 0 && !attachedImage
  const canSend = !isEmpty && !loading && charCount <= MAX_INPUT

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Revoke object URL on unmount to avoid memory leaks
  useEffect(() => {
    return () => {
      if (attachedImage) URL.revokeObjectURL(attachedImage.url)
    }
  }, [attachedImage])

  function handleInputChange(e) {
    setInput(e.target.value)
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = ta.scrollHeight + 'px'
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) submit()
    }
  }

  function handleImagePick(e) {
    const file = e.target.files[0]
    if (!file) return
    if (attachedImage) URL.revokeObjectURL(attachedImage.url)
    setAttachedImage({ file, url: URL.createObjectURL(file) })
    e.target.value = ''
  }

  function removeImage() {
    if (attachedImage) URL.revokeObjectURL(attachedImage.url)
    setAttachedImage(null)
  }

  function submit() {
    if (!canSend) return
    onSend(input.trim(), attachedImage?.file || null)
    setInput('')
    setAttachedImage(null)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const hasMessages = messages.length > 0

  return (
    <main className={styles.chat}>
      {/* Messages area */}
      {hasMessages ? (
        <div className={styles.messages}>
          {messages.map((msg, i) => {
            const isUser = msg.role === 'user'
            const isLast = i === messages.length - 1
            const isStreaming = isLast && msg.role === 'assistant' && loading

            return (
              <div key={i} className={styles.msgWrapper}>
                {isUser ? (
                  <div className={styles.userMsg}>
                    {msg.imageUrl && (
                      <img src={msg.imageUrl} className={styles.msgImage} alt="attached" />
                    )}
                    {renderText(msg.content)}
                  </div>
                ) : (
                  <div>
                    <div className={styles.aiLabel}>DocuMind AI</div>
                    <div className={styles.aiMsg}>
                      {renderText(msg.content)}
                      {isStreaming && <span className={styles.cursor} aria-hidden="true" />}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
          <div ref={messagesEndRef} />
        </div>
      ) : (
        <div className={styles.emptyState}>
          <FileQuestion size={28} color="var(--text-3)" />
          <p className={styles.emptyTitle}>What would you like to know?</p>
          <p className={styles.emptySubtitle}>
            Upload a document and ask anything about it.
          </p>
          {activeDocs.length > 0 && (
            <p className={styles.activeFilter}>
              Searching in: {activeDocs.join(', ')}
            </p>
          )}
        </div>
      )}

      {/* Input bar */}
      <div className={styles.inputArea}>
        {hasMessages && activeDocs.length > 0 && (
          <p className={styles.activeFilter} style={{ marginBottom: 8 }}>
            Searching in: {activeDocs.join(', ')}
          </p>
        )}
        {charCount > CHAR_WARN_THRESHOLD && (
          <p className={styles.charCount}>
            {charCount.toLocaleString()} / {MAX_INPUT.toLocaleString()}
          </p>
        )}

        {/* Image preview */}
        {attachedImage && (
          <div className={styles.imagePreview}>
            <img src={attachedImage.url} className={styles.imagePreviewThumb} alt="preview" />
            <button className={styles.imageRemoveBtn} onClick={removeImage} aria-label="Remove image">
              <X size={10} />
            </button>
          </div>
        )}

        <div className={styles.inputPill}>
          {/* Hidden image file input */}
          <input
            ref={imgInputRef}
            type="file"
            accept=".png,.jpg,.jpeg,.webp,.gif"
            style={{ display: 'none' }}
            onChange={handleImagePick}
          />

          {/* Attach button */}
          <button
            className={styles.attachBtn}
            onClick={() => imgInputRef.current?.click()}
            disabled={loading}
            aria-label="Attach image"
          >
            <Paperclip size={15} />
          </button>

          <textarea
            ref={textareaRef}
            className={styles.textarea}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your documents…"
            rows={1}
            maxLength={MAX_INPUT}
            aria-label="Message input"
            disabled={loading}
          />
          <button
            className={styles.sendBtn}
            onClick={submit}
            disabled={!canSend}
            aria-label="Send message"
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
    </main>
  )
}
