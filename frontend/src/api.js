// In dev, BASE is empty and Vite proxies /api → localhost:8000.
// In production builds, set VITE_API_URL to the backend's full URL
// (e.g. https://aidocanalyzer-production.up.railway.app) so the
// frontend can call it directly when served from a different origin.
const BASE = import.meta.env.VITE_API_URL || ''

const TOKEN_KEY = 'documind_token'
const USERNAME_KEY = 'documind_username'

// Thrown when a request fails authentication (missing/expired/invalid token).
export class AuthError extends Error {}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getUsername() {
  return localStorage.getItem(USERNAME_KEY)
}

function setAuth(token, username) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USERNAME_KEY, username)
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

// Shared fetch wrapper: attaches the bearer token and turns 401s into AuthError.
async function request(path, options = {}) {
  const token = getToken()
  const headers = { ...(options.headers || {}) }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const r = await fetch(`${BASE}${path}`, { ...options, headers })
  if (r.status === 401) {
    clearAuth()
    throw new AuthError('Unauthorized')
  }
  if (!r.ok) {
    const text = await r.text()
    try {
      const data = JSON.parse(text)
      throw new Error(data.detail || text)
    } catch (e) {
      if (e instanceof SyntaxError) throw new Error(text)
      throw e
    }
  }
  return r
}

// Auth
export async function register(username, password) {
  const r = await fetch(`${BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || 'Registration failed')
  setAuth(data.access_token, data.username)
  return data
}

export async function login(username, password) {
  const r = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || 'Login failed')
  setAuth(data.access_token, data.username)
  return data
}

export function logout() {
  clearAuth()
}

export async function getMe() {
  const r = await request('/api/auth/me')
  return r.json()
}

export async function changePassword(currentPassword, newPassword) {
  const r = await request('/api/auth/change-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
  return r.json()
}

// Documents
export async function listDocuments() {
  const r = await request('/api/documents')
  return r.json()  // { filename: "Vectorized", ... }
}

export async function uploadDocument(file) {
  const fd = new FormData()
  fd.append('file', file)
  const r = await request('/api/documents/upload', { method: 'POST', body: fd })
  return r.json()
}

export async function clearDocuments() {
  const r = await request('/api/documents', { method: 'DELETE' })
  return r.json()
}

// Sessions
export async function listSessions() {
  const r = await request('/api/sessions')
  return r.json()  // { "Chat 1": [...messages], ... }
}

export async function saveSession(name, messages) {
  const r = await request(`/api/sessions/${encodeURIComponent(name)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  return r.json()
}

export async function deleteSession(name) {
  const r = await request(`/api/sessions/${encodeURIComponent(name)}`, { method: 'DELETE' })
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

  const token = getToken()
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const r = await fetch(`${BASE}/api/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  if (r.status === 401) {
    clearAuth()
    throw new AuthError('Unauthorized')
  }
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
export async function exportChat(messages, format, filename) {
  // format: 'docx' or 'pdf'
  const r = await request(`/api/export/${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  const blob = await r.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || `DocuMind_export.${format}`
  a.click()
  URL.revokeObjectURL(url)
}
