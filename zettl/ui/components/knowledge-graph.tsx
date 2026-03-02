"use client"

import * as React from "react"
import { fetchGraph, type GraphResponse } from "@/lib/api"

// Local types for force-graph node/link objects
interface ForceNode {
  id: string
  label: string
  content: string
  color: string
  // Populated by d3-force at runtime
  x?: number
  y?: number
  __connections?: number
}

interface ForceLink {
  source: string | ForceNode
  target: string | ForceNode
  type: string
}

// Color mapping for different node types
const NODE_COLORS: Record<string, string> = {
  DocumentChunk: "#0d9488",  // teal-600
  Entity: "#6366f1",         // indigo-500
  EntityType: "#8b5cf6",     // violet-500
  default: "#94a3b8",        // slate-400
}

/** Convert hex color to rgba string */
function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export function KnowledgeGraph() {
  const containerRef = React.useRef<HTMLDivElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- react-force-graph-2d ref type is not exported
  const graphRef = React.useRef<any>(null)
  const [graphData, setGraphData] = React.useState<GraphResponse | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [dimensions, setDimensions] = React.useState<{ width: number; height: number }>({ width: 0, height: 0 })
  const [hoveredNode, setHoveredNode] = React.useState<ForceNode | null>(null)
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

  // Tune d3-force simulation for Obsidian-like feel
  React.useEffect(() => {
    const fg = graphRef.current
    if (!fg) return
    fg.d3Force("charge")?.strength(-120)       // Stronger repulsion for spacing
    fg.d3Force("link")?.distance(60)            // Longer rest length
    fg.d3Force("center")?.strength(0.05)        // Gentle centering
  })

  // Pre-compute connection counts for node sizing
  const neighborMap = React.useMemo(() => {
    if (!graphData) return { neighbors: new Set<string>(), connectionCounts: new Map<string, number>() }
    const connectionCounts = new Map<string, number>()
    const neighbors = new Set<string>()
    for (const edge of graphData.edges) {
      connectionCounts.set(edge.source, (connectionCounts.get(edge.source) ?? 0) + 1)
      connectionCounts.set(edge.target, (connectionCounts.get(edge.target) ?? 0) + 1)
    }
    return { neighbors, connectionCounts }
  }, [graphData])

  // Build adjacency set for hover highlight
  const adjacencySet = React.useMemo(() => {
    if (!graphData) return new Set<string>()
    const set = new Set<string>()
    for (const edge of graphData.edges) {
      set.add(`${edge.source}-${edge.target}`)
      set.add(`${edge.target}-${edge.source}`)
    }
    return set
  }, [graphData])

  const isNeighbor = React.useCallback(
    (a: string, b: string) => adjacencySet.has(`${a}-${b}`),
    [adjacencySet],
  )

  const ready = !loading && !error && graphData && graphData.nodes.length > 0 && ForceGraph && dimensions.width > 0

  // Transform to force-graph format with connection counts
  const data = React.useMemo(() => {
    if (!ready) return null
    return {
      nodes: graphData.nodes.map((n) => ({
        id: n.id,
        label: n.label,
        content: n.content,
        color: NODE_COLORS[n.label] ?? NODE_COLORS.default,
        __connections: neighborMap.connectionCounts.get(n.id) ?? 0,
      })),
      links: graphData.edges.map((e) => ({
        source: e.source,
        target: e.target,
        type: e.type,
      })),
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, graphData])

  // Custom node renderer: sized by connections, with hover glow
  const paintNode = React.useCallback(
    (node: ForceNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const connections = node.__connections ?? 0
      const baseRadius = 3 + Math.sqrt(connections) * 2
      const x = node.x ?? 0
      const y = node.y ?? 0

      // Determine opacity based on hover state
      const isHovered = hoveredNode?.id === node.id
      const isConnected = hoveredNode ? isNeighbor(hoveredNode.id, node.id) : false
      const dimmed = hoveredNode && !isHovered && !isConnected
      const alpha = dimmed ? 0.1 : 1

      // Glow ring on hover
      if (isHovered) {
        ctx.beginPath()
        ctx.arc(x, y, baseRadius + 3, 0, 2 * Math.PI)
        ctx.fillStyle = hexToRgba(node.color, 0.25)
        ctx.fill()
      }

      // Node circle
      ctx.beginPath()
      ctx.arc(x, y, baseRadius, 0, 2 * Math.PI)
      ctx.fillStyle = hexToRgba(node.color, alpha)
      ctx.fill()

      // Label (only when zoomed in enough or hovered/connected)
      const showLabel = globalScale > 1.2 || isHovered || isConnected
      if (showLabel && !dimmed) {
        const fontSize = Math.max(10 / globalScale, 2)
        ctx.font = `${fontSize}px sans-serif`
        ctx.textAlign = "center"
        ctx.textBaseline = "top"
        ctx.fillStyle = hexToRgba(node.color, Math.min(alpha, 0.9))
        const labelText = node.content?.length > 24 ? node.content.slice(0, 24) + "..." : (node.content || node.label)
        ctx.fillText(labelText, x, y + baseRadius + 2)
      }
    },
    [hoveredNode, isNeighbor],
  )

  // Custom link renderer for hover dimming
  const linkColor = React.useCallback(
    (link: ForceLink) => {
      if (!hoveredNode) return "rgba(148, 163, 184, 0.3)"
      const sourceId = typeof link.source === "string" ? link.source : link.source.id
      const targetId = typeof link.target === "string" ? link.target : link.target.id
      const connected = sourceId === hoveredNode.id || targetId === hoveredNode.id
      return connected ? "rgba(148, 163, 184, 0.6)" : "rgba(148, 163, 184, 0.04)"
    },
    [hoveredNode],
  )

  // Node area for pointer detection (matches painted size)
  const nodePointerArea = React.useCallback(
    (node: ForceNode) => {
      const connections = node.__connections ?? 0
      return 3 + Math.sqrt(connections) * 2 + 2  // slightly larger than visual for easy hovering
    },
    [],
  )

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
      {ready && data && (
        <ForceGraph
          ref={graphRef}
          graphData={data}
          width={dimensions.width}
          height={dimensions.height}
          // Simulation tuning — Obsidian-like continuous settling
          d3AlphaDecay={0.015}
          d3VelocityDecay={0.3}
          cooldownTicks={Infinity}
          cooldownTime={0}
          warmupTicks={50}
          // Custom node rendering (sized by connections + hover glow)
          nodeCanvasObject={paintNode}
          nodePointerAreaPaint={(node: ForceNode, color: string, ctx: CanvasRenderingContext2D) => {
            const r = nodePointerArea(node)
            ctx.beginPath()
            ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, 2 * Math.PI)
            ctx.fillStyle = color
            ctx.fill()
          }}
          // Links
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkColor={linkColor}
          linkWidth={(link: ForceLink) => {
            if (!hoveredNode) return 1
            const sourceId = typeof link.source === "string" ? link.source : link.source.id
            const targetId = typeof link.target === "string" ? link.target : link.target.id
            return sourceId === hoveredNode.id || targetId === hoveredNode.id ? 2 : 0.5
          }}
          // Interactions
          onNodeHover={(node: ForceNode | null) => setHoveredNode(node)}
          onNodeClick={(node: ForceNode) => {
            // Future: navigate to note detail
            console.log("Clicked node:", node)
          }}
          // Appearance
          backgroundColor="transparent"
          enablePointerInteraction={true}
        />
      )}
    </div>
  )
}
