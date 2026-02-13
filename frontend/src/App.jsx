import { useState, useEffect } from 'react'

const API_BASE = '/api'

export default function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <h1>热点文章收集</h1>
      {error && <p style={{ color: 'crimson' }}>连接后端失败: {error}</p>}
      {health && (
        <p style={{ color: 'green' }}>
          后端状态: {health.status} ({health.service})
        </p>
      )}
    </div>
  )
}
