"use client"

import * as React from "react"
import { fetchGraph, type GraphResponse } from "@/lib/api"

// Local types for force-graph node/link objects
interface ForceNode {
  id: string
  label: string
  content: string
  color: string
}

interface ForceLink {
  source: string
  target: string
  type: string
}

// Color mapping for different node types
const NODE_COLORS: Record<string, string> = {
  DocumentChunk: "#0d9488",  // teal-600
  Entity: "#6366f1",         // indigo-500
  EntityType: "#8b5cf6",     // violet-500
  default: "#94a3b8",        // slate-400
}

export function KnowledgeGraph() {
  const containerRef = React.useRef<HTMLDivElement>(null)
  const [graphData, setGraphData] = React.useState<GraphResponse | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- react-force-graph-2d has no exported component type
  const [ForceGraph, setForceGraph] = React.useState<React.ComponentType<Record<string, any>> | null>(null)

  // Dynamically import react-force-graph-2d (it uses canvas/window)
  React.useEffect(() => {
    import("react-force-graph-2d").then((mod) => {
      setForceGraph(() => mod.default)
    })
  }, [])

  // Fetch graph data
  React.useEffect(() => {
    fetchGraph()
      .then(setGraphData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="rounded-xl border bg-card p-8 text-center min-h-[300px] flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading knowledge graph...</p>
      </div>
    )
  }

  if (error || !graphData || graphData.nodes.length === 0) {
    return (
      <div className="rounded-xl border bg-card p-8 text-center min-h-[300px] flex items-center justify-center">
        <p className="text-sm text-muted-foreground">
          {error ?? "No graph data yet. Add some notes to see your knowledge graph."}
        </p>
      </div>
    )
  }

  if (!ForceGraph) {
    return (
      <div className="rounded-xl border bg-card p-8 text-center min-h-[300px] flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading graph renderer...</p>
      </div>
    )
  }

  // Transform to force-graph format
  const data = {
    nodes: graphData.nodes.map((n) => ({
      id: n.id,
      label: n.label,
      content: n.content,
      color: NODE_COLORS[n.label] ?? NODE_COLORS.default,
    })),
    links: graphData.edges.map((e) => ({
      source: e.source,
      target: e.target,
      type: e.type,
    })),
  }

  return (
    <div ref={containerRef} className="rounded-xl border bg-card overflow-hidden min-h-[300px]">
      <ForceGraph
        graphData={data}
        width={containerRef.current?.clientWidth ?? 800}
        height={350}
        nodeLabel={(node: ForceNode) => `${node.label}: ${node.content}`}
        nodeColor={(node: ForceNode) => node.color}
        nodeRelSize={5}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkLabel={(link: ForceLink) => link.type}
        linkColor={() => "rgba(148, 163, 184, 0.3)"}
        backgroundColor="transparent"
        cooldownTicks={100}
        onNodeClick={(node: ForceNode) => {
          // Future: navigate to note detail
          console.log("Clicked node:", node)
        }}
      />
    </div>
  )
}
