const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || ''

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

/* ================================================================
   OPENBOT FEATURES — COWORKERS, COMPUTERS, TAKE THE WHEEL, AUDIT
   ================================================================ */

export interface VirtualScreenState {
  current_url: string
  page_title: string
  viewport_width: number
  viewport_height: number
  is_secure: boolean
  status_code: number
  dom_summary: string
  last_snapshot_at: string
}

export interface VirtualTerminalLine {
  type: 'command' | 'stdout' | 'stderr' | 'info'
  text: string
  timestamp: string
}

export interface CoworkerRoutine {
  id: string
  name: string
  description: string
  cron_schedule: string
  last_run?: string
  last_status: string
  command_to_run: string
  coworker_id?: string
  coworker_name?: string
}

export type CoworkerControlState = 'IDLE' | 'BOT_ACTIVE' | 'HELP_REQUESTED' | 'HUMAN_CONTROLLED'

export interface CoworkerProfile {
  id: string
  name: string
  role: string
  speciality: string
  avatar_color: string
  description: string
  tools: string[]
  control_state: CoworkerControlState
  help_reason?: string
  workspace_path: string
  screen: VirtualScreenState
  terminal_buffer: VirtualTerminalLine[]
  routines: CoworkerRoutine[]
}

export interface AuditEntry {
  id: string
  timestamp: string
  coworker_id: string
  coworker_name: string
  actor_id: string
  initiator_kind: 'person' | 'routine' | 'responsibility' | 'handoff' | 'deployment'
  initiator_id?: string
  tool_name: string
  intent: string
  target?: string
  decision: 'ALLOWED' | 'DENIED' | 'REQUIRE_TAKEOVER'
  rule_id: string
  reason: string
  status: string
  duration_ms: number
  details?: Record<string, any>
}

export interface AuditQueryResult {
  total: number
  items: AuditEntry[]
  limit: number
  offset: number
}

export async function getCoworkers(token?: string | null): Promise<{ coworkers: CoworkerProfile[] }> {
  return fetchApi('/coworkers', undefined, token)
}

export async function getCoworker(coworkerId: string, token?: string | null): Promise<{ coworker: CoworkerProfile }> {
  return fetchApi(`/coworkers/${coworkerId}`, undefined, token)
}

export async function takeTheWheel(
  coworkerId: string,
  operatorId: string = 'human_operator',
  token?: string | null
): Promise<{ status: string; coworker: CoworkerProfile }> {
  return fetchApi(`/coworkers/${coworkerId}/take-wheel`, {
    method: 'POST',
    body: JSON.stringify({ operator_id: operatorId }),
  }, token)
}

export async function releaseTheWheel(
  coworkerId: string,
  operatorId: string = 'human_operator',
  token?: string | null
): Promise<{ status: string; coworker: CoworkerProfile }> {
  return fetchApi(`/coworkers/${coworkerId}/release-wheel`, {
    method: 'POST',
    body: JSON.stringify({ operator_id: operatorId }),
  }, token)
}

export async function requestHelp(
  coworkerId: string,
  reason: string,
  token?: string | null
): Promise<{ status: string; coworker: CoworkerProfile }> {
  return fetchApi(`/coworkers/${coworkerId}/request-help`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  }, token)
}

export async function executeOnComputer(
  coworkerId: string,
  params: {
    tool_name: string
    intent: string
    command?: string
    url?: string
    file_path?: string
    initiator_kind?: string
    actor_id?: string
  },
  token?: string | null
): Promise<any> {
  return fetchApi(`/coworkers/${coworkerId}/execute`, {
    method: 'POST',
    body: JSON.stringify(params),
  }, token)
}

export async function getAuditTrail(
  params?: {
    nobody_watching?: boolean
    decision?: string
    coworker_id?: string
    search?: string
    limit?: number
    offset?: number
  },
  token?: string | null
): Promise<AuditQueryResult> {
  const q = new URLSearchParams()
  if (params?.nobody_watching !== undefined) q.set('nobody_watching', String(params.nobody_watching))
  if (params?.decision) q.set('decision', params.decision)
  if (params?.coworker_id) q.set('coworker_id', params.coworker_id)
  if (params?.search) q.set('search', params.search)
  if (params?.limit) q.set('limit', String(params.limit))
  if (params?.offset) q.set('offset', String(params.offset))
  const qs = q.toString() ? `?${q.toString()}` : ''
  return fetchApi(`/audit${qs}`, undefined, token)
}

export async function getRoutines(token?: string | null): Promise<{ routines: CoworkerRoutine[] }> {
  return fetchApi('/routines', undefined, token)
}

export async function runRoutine(routineId: string, token?: string | null): Promise<any> {
  return fetchApi(`/routines/${routineId}/run`, {
    method: 'POST',
  }, token)
}

// =============================================================================
// FACTURATION & ABONNEMENTS STRIPE
// =============================================================================

export interface BillingPlanLimits {
  max_daily_runs: number
  parallel_agents: number
  cloud_llm_access: boolean
}

export interface BillingPlan {
  id: string
  name: string
  badge: string
  price_monthly_cents: number
  price_yearly_cents: number
  currency: string
  description: string
  popular: boolean
  features: string[]
  limits: BillingPlanLimits
}

export interface BillingConfig {
  publishable_key: string
  stripe_configured: boolean
  plans: Record<string, BillingPlan>
  currency: string
}

export interface PaymentOrderInfo {
  id: number
  amount_cents: number
  currency: string
  status: string
  tier: string
  billing_reason?: string
  created_at?: string
}

export interface BillingStatus {
  tier: string
  tier_name: string
  status: string
  current_period_end: string | null
  cancel_at_period_end: boolean
  has_stripe_customer: boolean
  stripe_customer_id: string | null
  orders: PaymentOrderInfo[]
  plan_limits: BillingPlanLimits
}

export async function getBillingConfig(): Promise<BillingConfig> {
  return fetchApi('/billing/config')
}

export async function getBillingStatus(token?: string | null): Promise<BillingStatus> {
  return fetchApi('/billing/status', undefined, token)
}

export async function createCheckoutSession(
  tier: string,
  interval: 'month' | 'year' = 'month',
  token?: string | null
): Promise<{ checkout_url: string; session_id: string; simulated: boolean }> {
  return fetchApi(
    '/billing/checkout',
    {
      method: 'POST',
      body: JSON.stringify({ tier, interval }),
    },
    token
  )
}

export async function createPortalSession(
  returnUrl?: string,
  token?: string | null
): Promise<{ portal_url: string; simulated: boolean }> {
  return fetchApi(
    '/billing/portal',
    {
      method: 'POST',
      body: JSON.stringify({ return_url: returnUrl }),
    },
    token
  )
}


