"use client";

import Component from "@/components/ui/ai-diff";

export default function DemoOne() {
  return (
    <main className="min-h-screen w-full bg-background text-foreground flex flex-col items-center justify-center p-10">
      <div className="w-full max-w-xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">AI Code Diff Review Component</h1>
          <p className="text-sm text-muted-foreground">Interactive code modification reviewer with Accept / Reject actions</p>
        </div>

        <Component
          lines={[
            { content: "const shouldReduceMotion = useReducedMotion();", kind: "context", number: 12 },
            { content: "", kind: "context", number: 13 },
            { content: '  transition={{ ease: "easeInOut", duration: 0.6 }}', kind: "removed", number: 14 },
            { content: "  transition={", kind: "added", number: 14 },
            { content: "    shouldReduceMotion", kind: "added", number: 15 },
            { content: "      ? { duration: 0 }", kind: "added", number: 16 },
            { content: '      : { type: "spring", duration: 0.25, bounce: 0.1 }', kind: "added", number: 17 },
            { content: "  }", kind: "added", number: 18 },
            { content: "", kind: "context", number: 19 },
          ]}
          title="components/card.tsx"
          onAccept={() => console.log("Diff Accepted")}
          onReject={() => console.log("Diff Rejected")}
        />
      </div>
    </main>
  );
}
