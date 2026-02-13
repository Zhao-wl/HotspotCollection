import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api'

function useArticles(filters) {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.source_id) params.set('source_id', filters.source_id)
    if (filters.tag_id) params.set('tag_id', filters.tag_id)
    if (filters.date_from) params.set('date_from', filters.date_from)
    if (filters.date_to) params.set('date_to', filters.date_to)
    params.set('limit', String(filters.limit ?? 20))
    params.set('offset', String(filters.offset ?? 0))
    fetch(`${API_BASE}/articles?${params}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
      .then(setList)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [filters.source_id, filters.tag_id, filters.date_from, filters.date_to, filters.limit, filters.offset])
  return { list, loading, error }
}

function useSources() {
  const [sources, setSources] = useState([])
  const [error, setError] = useState(null)
  useEffect(() => {
    fetch(`${API_BASE}/sources`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
      .then(setSources)
      .catch((e) => setError(e.message))
  }, [])
  return { sources, error }
}

function useTags() {
  const [tags, setTags] = useState([])
  const [error, setError] = useState(null)
  useEffect(() => {
    fetch(`${API_BASE}/tags`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
      .then(setTags)
      .catch((e) => setError(e.message))
  }, [])
  return { tags, error }
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

export default function App() {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState(null)
  const [filters, setFilters] = useState({
    source_id: '',
    tag_id: '',
    date_from: '',
    date_to: '',
    limit: 20,
    offset: 0,
  })

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setHealthError(e.message))
  }, [])

  const { sources, error: sourcesError } = useSources()
  const { tags, error: tagsError } = useTags()
  const { list, loading, error } = useArticles({
    ...filters,
    source_id: filters.source_id || undefined,
    tag_id: filters.tag_id || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
  })

  const setFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }))
  }, [])

  return (
    <div style={{ padding: '2rem', maxWidth: 900, margin: '0 auto' }}>
      <h1>热点文章收集</h1>
      {healthError && <p style={{ color: 'crimson' }}>连接后端失败: {healthError}</p>}
      {health && (
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          后端状态: {health.status} ({health.service})
        </p>
      )}

      <section style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.1rem', marginBottom: '0.75rem' }}>筛选</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
          <label>
            来源
            <select
              value={filters.source_id}
              onChange={(e) => setFilter('source_id', e.target.value)}
              style={{ marginLeft: '0.5rem', padding: '0.35rem 0.5rem' }}
            >
              <option value="">全部</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            标签
            <select
              value={filters.tag_id}
              onChange={(e) => setFilter('tag_id', e.target.value)}
              style={{ marginLeft: '0.5rem', padding: '0.35rem 0.5rem' }}
            >
              <option value="">全部</option>
              {tags.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            日期起
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilter('date_from', e.target.value)}
              style={{ marginLeft: '0.5rem', padding: '0.35rem 0.5rem' }}
            />
          </label>
          <label>
            日期止
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilter('date_to', e.target.value)}
              style={{ marginLeft: '0.5rem', padding: '0.35rem 0.5rem' }}
            />
          </label>
        </div>
        {(sourcesError || tagsError) && (
          <p style={{ color: 'crimson', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            {sourcesError || tagsError}
          </p>
        )}
      </section>

      <section>
        <h2 style={{ fontSize: '1.1rem', marginBottom: '0.75rem' }}>文章列表</h2>
        {error && <p style={{ color: 'crimson' }}>加载失败: {error}</p>}
        {loading && <p style={{ color: 'var(--muted)' }}>加载中…</p>}
        {!loading && !error && list.length === 0 && (
          <p style={{ color: 'var(--muted)' }}>暂无文章</p>
        )}
        {!loading && !error && list.length > 0 && (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {list.map((a) => (
              <li
                key={a.id}
                style={{
                  padding: '0.75rem 0',
                  borderBottom: '1px solid #eee',
                }}
              >
                <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>{a.title}</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                  {a.source_name && <span>来源: {a.source_name}</span>}
                  {a.tags?.length > 0 && (
                    <span style={{ marginLeft: '0.75rem' }}>
                      标签: {a.tags.map((t) => t.name).join(', ')}
                    </span>
                  )}
                  <span style={{ marginLeft: '0.75rem' }}>{formatDate(a.published_at)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
