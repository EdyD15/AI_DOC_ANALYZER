import { useState } from 'react'
import Login from './Login'
import Register from './Register'

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login')

  return mode === 'login' ? (
    <Login onSuccess={onAuthenticated} onSwitchToRegister={() => setMode('register')} />
  ) : (
    <Register onSuccess={onAuthenticated} onSwitchToLogin={() => setMode('login')} />
  )
}
