import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api'

function useArticles(filters, refreshTrigger) {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [trigger, setTrigger] = useState(0)
  const refetch = useCallback(() => setTrigger((t) => t + 1), [])
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
  }, [filters.source_id, filters.tag_id, filters.date_from, filters.date_to, filters.limit, filters.offset, trigger, refreshTrigger])
  return { list, loading, error, refetch }
}

function useSources() {
  const [sources, setSources] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const fetchSources = useCallback(() => {
    setLoading(true)
    fetch(`${API_BASE}/sources`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
      .then((data) => {
        setSources(data)
        setError(null)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])
  useEffect(() => {
    fetchSources()
  }, [fetchSources])
  return { sources, error, loading, refetch: fetchSources }
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

  const { sources, error: sourcesError, refetch: refetchSources } = useSources()
  const { tags, error: tagsError } = useTags()
  const [sourceForm, setSourceForm] = useState(null) // null = 隐藏, { id, name, type_or_kind, url_or_config } = 编辑, {} = 新建
  const [sourceSubmitError, setSourceSubmitError] = useState(null)
  const [collectRunning, setCollectRunning] = useState(false)
  const [collectResult, setCollectResult] = useState(null)
  const [collectingSourceId, setCollectingSourceId] = useState(null)
  const [sourceCollectResult, setSourceCollectResult] = useState({})
  const { list, loading, error, refetch: refetchArticles } = useArticles({
    ...filters,
    source_id: filters.source_id || undefined,
    tag_id: filters.tag_id || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
  })

  const setFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }))
  }, [])

  const openAddSource = () => {
    setSourceForm({ name: '', type_or_kind: 'manual', url_or_config: '' })
    setSourceSubmitError(null)
  }
  const openEditSource = (s) => {
    setSourceForm({
      id: s.id,
      name: s.name,
      type_or_kind: s.type_or_kind || '',
      url_or_config: s.url_or_config || '',
    })
    setSourceSubmitError(null)
  }
  const closeSourceForm = () => {
    setSourceForm(null)
    setSourceSubmitError(null)
  }
  const saveSource = async () => {
    if (!sourceForm) return
    setSourceSubmitError(null)
    const body = {
      name: sourceForm.name.trim(),
      type_or_kind: sourceForm.type_or_kind || null,
      url_or_config: sourceForm.url_or_config?.trim() || null,
    }
    if (!body.name) {
      setSourceSubmitError('请填写来源名称')
      return
    }
    try {
      if (sourceForm.id != null) {
        const r = await fetch(`${API_BASE}/sources/${sourceForm.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        if (!r.ok) {
          const text = await r.text()
          let msg = text
          try {
            const j = JSON.parse(text)
            if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
          } catch (_) {}
          throw new Error(msg || r.statusText)
        }
      } else {
        const r = await fetch(`${API_BASE}/sources`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        if (!r.ok) {
          const text = await r.text()
          let msg = text
          try {
            const j = JSON.parse(text)
            if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
          } catch (_) {}
          throw new Error(msg || r.statusText)
        }
      }
      refetchSources()
      closeSourceForm()
    } catch (e) {
      setSourceSubmitError(e.message || '保存失败')
    }
  }
  const deleteSource = async (id) => {
    if (!window.confirm('确定删除该来源？')) return
    try {
      const r = await fetch(`${API_BASE}/sources/${id}`, { method: 'DELETE' })
      if (!r.ok) throw new Error(r.statusText)
      refetchSources()
    } catch (e) {
      setSourceSubmitError(e.message || '删除失败')
    }
  }

  const runCollect = async () => {
    setCollectRunning(true)
    setCollectResult(null)
    try {
      const r = await fetch(`${API_BASE}/collect/run`, { method: 'POST' })
      const data = await r.json().catch(() => ({}))
      setCollectResult(data)
      refetchArticles()
    } catch (e) {
      setCollectResult({ errors: [e.message || '请求失败'] })
    } finally {
      setCollectRunning(false)
    }
  }

  const canCollectSource = (s) => {
    const kind = (s.type_or_kind || '').toLowerCase()
    const hasUrl = (s.url_or_config || '').trim().length > 0
    return (kind === 'rss' || kind === 'api') && hasUrl
  }

  const runCollectSource = async (sourceId) => {
    setCollectingSourceId(sourceId)
    setSourceCollectResult((prev) => ({ ...prev, [sourceId]: null }))
    try {
      const r = await fetch(`${API_BASE}/collect/run/${sourceId}`, { method: 'POST' })
      const data = await r.json().catch(() => ({}))
      setSourceCollectResult((prev) => ({ ...prev, [sourceId]: data }))
      refetchArticles()
    } catch (e) {
      setSourceCollectResult((prev) => ({ ...prev, [sourceId]: { ok: false, error: e.message || '请求失败' } }))
    } finally {
      setCollectingSourceId(null)
    }
  }

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
          <button
            type="button"
            onClick={runCollect}
            disabled={collectRunning}
            style={{ marginLeft: '0.5rem', padding: '0.4rem 0.75rem' }}
          >
            {collectRunning ? '采集中…' : '立即采集'}
          </button>
        </div>
        {collectResult && (
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', color: 'var(--muted)' }}>
            上次采集: 成功 {collectResult.sources_ok ?? 0} 个来源，失败 {collectResult.sources_fail ?? 0} 个，新增文章 {collectResult.articles_added ?? 0} 篇
            {collectResult.errors?.length > 0 && (
              <span style={{ color: 'crimson', marginLeft: '0.5rem' }}> 错误: {collectResult.errors.join('; ')}</span>
            )}
          </p>
        )}
        {(sourcesError || tagsError) && (
          <p style={{ color: 'crimson', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            {sourcesError || tagsError}
          </p>
        )}
      </section>

      <section style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.1rem', marginBottom: '0.75rem' }}>来源配置</h2>
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
          管理热点文章来源，添加后可在此处编辑、删除；筛选中的「来源」下拉会同步更新。
        </p>
        <button
          type="button"
          onClick={openAddSource}
          style={{ marginBottom: '0.75rem', padding: '0.4rem 0.75rem' }}
        >
          添加来源
        </button>
        {sourceForm && (
          <div className="source-form" style={{ marginBottom: '1rem', padding: '1rem', background: '#fff', borderRadius: 6, border: '1px solid #eee' }}>
            <h3 style={{ fontSize: '1rem', marginTop: 0, marginBottom: '0.75rem' }}>
              {sourceForm.id != null ? '编辑来源' : '新建来源'}
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: 400 }}>
              <label>
                名称 <span style={{ color: 'crimson' }}>*</span>
                <input
                  type="text"
                  value={sourceForm.name}
                  onChange={(e) => setSourceForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="如：某 RSS"
                  style={{ display: 'block', width: '100%', marginTop: 2, padding: '0.35rem 0.5rem' }}
                />
              </label>
              <label>
                类型
                <select
                  value={sourceForm.type_or_kind || ''}
                  onChange={(e) => setSourceForm((f) => ({ ...f, type_or_kind: e.target.value }))}
                  style={{ display: 'block', width: '100%', marginTop: 2, padding: '0.35rem 0.5rem' }}
                >
                  <option value="">—</option>
                  <option value="manual">manual</option>
                  <option value="rss">rss</option>
                  <option value="api">api</option>
                </select>
              </label>
              <label>
                URL 或配置
                <input
                  type="text"
                  value={sourceForm.url_or_config || ''}
                  onChange={(e) => setSourceForm((f) => ({ ...f, url_or_config: e.target.value }))}
                  placeholder="可选"
                  style={{ display: 'block', width: '100%', marginTop: 2, padding: '0.35rem 0.5rem' }}
                />
              </label>
              {sourceSubmitError && (
                <p style={{ color: 'crimson', fontSize: '0.9rem', margin: 0 }}>{sourceSubmitError}</p>
              )}
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button type="button" onClick={saveSource} style={{ padding: '0.4rem 0.75rem' }}>
                  保存
                </button>
                <button type="button" onClick={closeSourceForm} style={{ padding: '0.4rem 0.75rem' }}>
                  取消
                </button>
              </div>
            </div>
          </div>
        )}
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {sources.map((s) => (
            <li
              key={s.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.5rem 0',
                borderBottom: '1px solid #eee',
              }}
            >
              <span style={{ fontWeight: 500, minWidth: 120 }}>{s.name}</span>
              <span style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>{s.type_or_kind || '—'}</span>
              <span style={{ color: 'var(--muted)', fontSize: '0.85rem', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={s.url_or_config || ''}>
                {s.url_or_config || '—'}
              </span>
              {canCollectSource(s) && (
                <button
                  type="button"
                  onClick={() => runCollectSource(s.id)}
                  disabled={collectingSourceId === s.id}
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem' }}
                >
                  {collectingSourceId === s.id ? '采集中…' : '采集'}
                </button>
              )}
              <button type="button" onClick={() => openEditSource(s)} style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem' }}>
                编辑
              </button>
              <button type="button" onClick={() => deleteSource(s.id)} style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem' }}>
                删除
              </button>
              {sourceCollectResult[s.id] != null && (
                <span style={{ fontSize: '0.85rem', color: sourceCollectResult[s.id].ok ? 'var(--muted)' : 'crimson' }}>
                  {sourceCollectResult[s.id].ok
                    ? `已采集，新增 ${sourceCollectResult[s.id].articles_added ?? 0} 篇`
                    : `失败: ${sourceCollectResult[s.id].error || '未知错误'}`}
                </span>
              )}
            </li>
          ))}
        </ul>
        {sources.length === 0 && !sourcesError && (
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>暂无来源，点击「添加来源」创建。</p>
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
                <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                  {a.url ? (
                    <a
                      href={a.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="article-title-link"
                    >
                      {a.title}
                    </a>
                  ) : (
                    a.title
                  )}
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                  {a.source_name && <span>来源: {a.source_name}</span>}
                  <span style={{ marginLeft: '0.75rem' }}>
                    {(a.tags && a.tags.length > 0)
                      ? (a.tags.slice(0, 3)).map((t) => t.name).join('、')
                      : '—'}
                  </span>
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
