const BASE = ''  // Vite proxy handles /api → localhost:8000

// Documents
export async function listDocuments() {
  const r = await fetch(`${BASE}/api/documents`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()  // { filename: "Vectorized", ... }
}

export async function uploadDocument(file) {
  const fd = new FormData()
  fd.append('file', file)
  const r = await fetch(`${BASE}/api/documents/upload`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function clearDocuments() {
  const r = await fetch(`${BASE}/api/documents`, { method: 'DELETE' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

// Sessions
export async function listSessions() {
  const r = await fetch(`${BASE}/api/sessions`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()  // { "Chat 1": [...messages], ... }
}

export async function saveSession(name, messages) {
  const r = await fetch(`${BASE}/api/sessions/${encodeURIComponent(name)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function deleteSession(name) {
  const r = await fetch(`${BASE}/api/sessions/${encodeURIComponent(name)}`, { method: 'DELETE' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// Chat streaming — returns an async generator of text chunks
export async function* streamChat(question, selectedDocuments = [], imageFile = null, chatHistory = []) {
  const body = { question, selected_documents: selectedDocuments, chat_history: chatHistory }
  if (imageFile) {
    body.image_base64 = await fileToBase64(imageFile)
    body.image_mime = imageFile.type
  }
  const r = await fetch(`${BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())

  const reader = r.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const payload = line.slice(6).trim()
      if (payload === '[DONE]') return
      try {
        const parsed = JSON.parse(payload)
        if (parsed.error) throw new Error(parsed.error)
        if (parsed.chunk) yield parsed.chunk
      } catch (e) {
        if (e.message && !e.message.startsWith('Unexpected')) throw e
      }
    }
  }
}

// Export
export async function exportChat(messages, format) {
  // format: 'docx' or 'pdf'
  const r = await fetch(`${BASE}/api/export/${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  if (!r.ok) throw new Error(await r.text())
  const blob = await r.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `DocuMind_export.${format}`
  a.click()
  URL.revokeObjectURL(url)
}
