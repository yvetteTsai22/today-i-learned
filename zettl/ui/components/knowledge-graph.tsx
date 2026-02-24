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
  const [dimensions, setDimensions] = React.useState<{ width: number; height: number }>({ width: 0, height: 0 })
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- react-force-graph-2d has no exported component type
  const [ForceGraph, setForceGraph] = React.useState<React.ComponentType<Record<string, any>> | null>(null)

  // Track container dimensions via ResizeObserver
  React.useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

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

  const ready = !loading && !error && graphData && graphData.nodes.length > 0 && ForceGraph && dimensions.width > 0

  // Transform to force-graph format
  const data = ready
    ? {
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
    : null

  const placeholder = loading
    ? "Loading knowledge graph..."
    : error
      ? error
      : !graphData || graphData.nodes.length === 0
        ? "No graph data yet. Add some notes to see your knowledge graph."
        : !ForceGraph
          ? "Loading graph renderer..."
          : null

  return (
    <div ref={containerRef} className="rounded-xl border bg-card overflow-hidden h-[350px]">
      {placeholder && (
        <div className="flex items-center justify-center h-full">
          <p className="text-sm text-muted-foreground">{placeholder}</p>
        </div>
      )}
      {ready && data && <ForceGraph
        graphData={data}
        width={dimensions.width}
        height={dimensions.height}
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
      />}
    </div>
  )
}
