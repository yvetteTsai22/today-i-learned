"use client"

import * as React from "react"
import { PenLine, Search, Sparkles } from "lucide-react"
import { fetchActivity, type ActivityItem, type ActivityEventType } from "@/lib/api"

const EVENT_ICONS: Record<ActivityEventType, React.ComponentType<{ className?: string }>> = {
  note: PenLine,
  search: Search,
  digest: Sparkles,
}

function relativeTime(timestamp: string): string {
  const diffMs = Date.now() - new Date(timestamp).getTime()
  const mins = Math.floor(diffMs / 60_000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return days === 1 ? "yesterday" : `${days}d ago`
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const Icon = EVENT_ICONS[item.type]
  return (
    <div className="flex gap-3 items-start py-3 first:pt-0 last:pb-0">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2">
          <p className="text-sm font-medium text-foreground truncate">{item.label}</p>
          <span className="text-xs text-muted-foreground whitespace-nowrap shrink-0">
            {relativeTime(item.timestamp)}
          </span>
        </div>
        {item.preview && (
          <p className="text-xs text-muted-foreground truncate mt-0.5">{item.preview}</p>
        )}
      </div>
    </div>
  )
}

function ActivitySkeleton() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex gap-3 items-start py-3 first:pt-0 animate-pulse">
          <div className="mt-0.5 h-7 w-7 rounded-md bg-muted shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3.5 w-2/3 rounded bg-muted" />
            <div className="h-3 w-1/3 rounded bg-muted" />
          </div>
        </div>
      ))}
    </>
  )
}

export function ActivityFeed() {
  const [items, setItems] = React.useState<ActivityItem[] | null>(null)
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    fetchActivity(20)
      .then((data) => setItems(data.items))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="rounded-xl border bg-card p-6">
      {loading ? (
        <div className="divide-y divide-border">
          <ActivitySkeleton />
        </div>
      ) : !items || items.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No activity yet — capture your first note
        </p>
      ) : (
        <div className="divide-y divide-border">
          {items.map((item, i) => (
            <ActivityRow key={i} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
