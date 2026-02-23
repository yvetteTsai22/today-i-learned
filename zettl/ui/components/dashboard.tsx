"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import {
  PenLine,
  Search,
  Sparkles,
  FileText,
  GitFork,
  Tag,
  TrendingUp,
} from "lucide-react"
import { fetchStats, type StatsResponse } from "@/lib/api"

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string
  icon: React.ComponentType<{ className?: string }>
}) {
  return (
    <div className="rounded-xl border bg-card p-6">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <p className="mt-2 text-3xl font-bold text-foreground">{value}</p>
    </div>
  )
}

function QuickActionCard({
  label,
  description,
  icon: Icon,
  onClick,
}: {
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-start gap-4 rounded-xl border bg-card p-6 text-left transition-colors hover:bg-accent cursor-pointer"
    >
      <div className="rounded-lg bg-primary/10 p-2.5">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <div>
        <p className="font-semibold text-foreground">{label}</p>
        <p className="text-sm text-muted-foreground mt-1">{description}</p>
      </div>
    </button>
  )
}

export function Dashboard() {
  const router = useRouter()
  const [stats, setStats] = React.useState<StatsResponse | null>(null)
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-8">
      {/* Stats Row */}
      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          Overview
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Notes" value={loading ? "…" : String(stats?.notes ?? 0)} icon={FileText} />
          <StatCard label="Topics" value={loading ? "…" : String(stats?.topics ?? 0)} icon={Tag} />
          <StatCard label="Connections" value={loading ? "…" : String(stats?.connections ?? 0)} icon={GitFork} />
          <StatCard label="This Week" value={loading ? "…" : String(stats?.this_week ?? 0)} icon={TrendingUp} />
        </div>
      </section>

      {/* Quick Actions */}
      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          Quick Actions
        </h2>
        <div className="grid sm:grid-cols-3 gap-4">
          <QuickActionCard
            label="Capture"
            description="Add a new note to your knowledge graph"
            icon={PenLine}
            onClick={() => router.push("/capture")}
          />
          <QuickActionCard
            label="Search"
            description="Find connections across your notes"
            icon={Search}
            onClick={() => router.push("/search")}
          />
          <QuickActionCard
            label="Digest"
            description="Generate your weekly content digest"
            icon={Sparkles}
            onClick={() => router.push("/digest")}
          />
        </div>
      </section>

      {/* Activity Feed placeholder */}
      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          Recent Activity
        </h2>
        <div className="rounded-xl border bg-card p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Activity feed will appear here once the /activity endpoint is implemented.
          </p>
        </div>
      </section>

      {/* Graph placeholder */}
      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          Knowledge Graph
        </h2>
        <div className="rounded-xl border bg-card p-8 text-center min-h-[300px] flex items-center justify-center">
          <p className="text-sm text-muted-foreground">
            Interactive knowledge graph will appear here once the /graph endpoint is implemented.
          </p>
        </div>
      </section>
    </div>
  )
}
