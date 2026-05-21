const BASE = '/api'

export async function optimize(data) {
  const res = await fetch(`${BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`请求失败: ${res.status}`)
  return res.json()
}

export async function resumeOptimize(threadId, feedback) {
  const res = await fetch(`${BASE}/optimize/resume?thread_id=${encodeURIComponent(threadId)}&feedback=${encodeURIComponent(feedback)}`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(`请求失败: ${res.status}`)
  return res.json()
}

export async function getHistory() {
  const res = await fetch(`${BASE}/history`)
  if (!res.ok) throw new Error(`请求失败: ${res.status}`)
  return res.json()
}
