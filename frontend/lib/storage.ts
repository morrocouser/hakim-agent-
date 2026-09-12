import { ConversationSession, ScheduledTask } from './types'

export interface AxiomState {
  version: 1
  sessions: ConversationSession[]
  tasks: ScheduledTask[]
  activeSessionId: string | null
}

const STORAGE_KEY = 'axiom_state_v1'

const EMPTY_STATE: AxiomState = { version: 1, sessions: [], tasks: [], activeSessionId: null }

export function isStorageAvailable(): boolean {
  if (typeof window === 'undefined') return false
  try {
    window.localStorage.setItem('__axiom_test__', '1')
    window.localStorage.removeItem('__axiom_test__')
    return true
  } catch {
    return false
  }
}

export function loadState(): AxiomState {
  if (!isStorageAvailable()) return EMPTY_STATE
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return EMPTY_STATE
    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null) return EMPTY_STATE
    const p = parsed as Record<string, unknown>
    if (p.version !== 1) return EMPTY_STATE
    return {
      version: 1,
      sessions: Array.isArray(p.sessions) ? (p.sessions as ConversationSession[]) : [],
      tasks: Array.isArray(p.tasks) ? (p.tasks as ScheduledTask[]) : [],
      activeSessionId: typeof p.activeSessionId === 'string' ? p.activeSessionId : null,
    }
  } catch {
    return EMPTY_STATE
  }
}

export function saveState(state: AxiomState): boolean {
  if (!isStorageAvailable()) return true
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    return true
  } catch {
    return false
  }
}
