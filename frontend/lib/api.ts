const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export interface AgentInfo {
  icon: string
  label: string
  speciality: string
  description: string
  default_model: string
  approach: string
}

export interface ScoringResult {
  task_id: string
  description: string
  agent: string
  model: string
  score: number
  dimensions: {
    complexity: number
    stakes: number
    creativity: number
    speed_need: number
    domain_match: number
  }
  subtasks: ScoringResult[]
}

export interface TaskResult {
  task_id: string
  description: string
  agent: string
  model: string
  score: number
  status: string
  output?: string
  error?: string
  iteration: number
  quality_score: number
}

export interface HealthStatus {
  status: string
  agent: string
  version: string
  openrouter_configured: boolean
  memory_tokens: number
}

async function fetchApi<T>(path: string, options?: RequestInit, token?: string | null): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    credentials: 'include',
    ...options,
    headers,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

export async function getHealth(): Promise<HealthStatus> {
  return fetchApi('/health')
}

export async function getAgents(): Promise<Record<string, AgentInfo>> {
  return fetchApi('/agents')
}

export async function getMemory(): Promise<any> {
  return fetchApi('/memory')
}

export async function scoreTask(description: string, taskType: string = 'QUICK', token?: string | null): Promise<ScoringResult> {
  return fetchApi('/score', {
    method: 'POST',
    body: JSON.stringify({ description, task_type: taskType }),
  }, token)
}

export async function executeTask(description: string, taskType: string = 'QUICK', context?: string, token?: string | null): Promise<TaskResult> {
  return fetchApi('/execute', {
    method: 'POST',
    body: JSON.stringify({ description, task_type: taskType, context }),
  }, token)
}

export async function chat(
  message: string,
  token?: string | null,
  conversationId?: number | null,
): Promise<{ response: string; task: TaskResult; conversation_id?: number }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const body: any = { role: 'user', content: message }
  if (conversationId) body.conversation_id = conversationId

  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    credentials: 'include',
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}


export async function webSearch(query: string, maxResults: number = 5): Promise<any> {
  const body: any = { query }
  if (maxResults !== 5) body.max_results = maxResults
  return fetchApi('/tools/search', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function executeCode(language: string, code: string): Promise<any> {
  return fetchApi('/tools/code', {
    method: 'POST',
    body: JSON.stringify({ language, code }),
  })
}

export async function createFile(path: string, content: string = ''): Promise<any> {
  return fetchApi('/tools/file', {
    method: 'POST',
    body: JSON.stringify({ path, content }),
  })
}

export async function getErrors(): Promise<any> {
  return fetchApi('/errors')
}

export async function logError(payload: {
  tier?: number
  agent?: string
  context?: string
  symptom?: string
  root_cause?: string
  fix?: string
  lesson?: string
  score?: number
}): Promise<any> {
  return fetchApi('/errors', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export interface SkillInfo {
  repo: string
  source_url: string
  skill: string
  path: string
  description: string
  content?: string
}

export async function getSkills(query: string = '', limit: number = 500): Promise<{ total: number; skills: SkillInfo[] }> {
  const queryParam = query ? `?query=${encodeURIComponent(query)}&limit=${limit}` : `?limit=${limit}`
  return fetchApi(`/skills${queryParam}`)
}

export async function getSkillDetails(repo: string, skillName: string, includeReadme: boolean = false): Promise<SkillInfo> {
  return fetchApi(`/skills/${encodeURIComponent(repo)}/${encodeURIComponent(skillName)}?readme=${includeReadme}`)
}
