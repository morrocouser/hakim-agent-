"use client"

import * as React from "react"
import {
  AiPromptInput,
  type AiModelSelection,
  type AiPromptSendStatus,
} from "@/components/ui/ai-prompt-input"

export default function DemoOne() {
  const [value, setValue] = React.useState("")
  const [status, setStatus] = React.useState<AiPromptSendStatus>("idle")
  const [modelSelection, setModelSelection] = React.useState<AiModelSelection>({
    id: "opus-4.5",
    effort: "high",
    context: "200K",
    fast: true,
    thinking: false,
  })
  const timersRef = React.useRef<number[]>([])

  React.useEffect(() => {
    const timers = timersRef.current
    return () => {
      for (const id of timers) window.clearTimeout(id)
    }
  }, [])

  const handleSubmit = () => {
    setStatus("loading")
    const successTimer = window.setTimeout(() => {
      setStatus("success")
      const idleTimer = window.setTimeout(() => {
        setStatus("idle")
        setValue("")
      }, 900)
      timersRef.current.push(idleTimer)
    }, 1400)
    timersRef.current.push(successTimer)
  }

  return (
    <main className="min-h-screen w-full bg-background text-foreground flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xl flex flex-col items-center justify-center space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Motoko AI Prompt Composer</h1>
          <p className="text-sm text-muted-foreground">Auto-growing textarea, rotating placeholders, model selector & dictation</p>
        </div>
        <AiPromptInput
          value={value}
          onChange={setValue}
          modelSelection={modelSelection}
          onModelSelectionChange={setModelSelection}
          status={status}
          onSubmit={handleSubmit}
        />
      </div>
    </main>
  )
}
