export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agent?: string
  model?: string
  score?: number
  duration?: string
  file?: string
}

export interface ConversationSession {
  id: string
  title: string
  subtitle: string
  messages: Message[]
}

export interface ScheduledTask {
  id: string
  name: string
  schedule: string
  status: 'active' | 'paused'
}

export interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}
