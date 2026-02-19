'use client'

import { useEffect, useRef } from 'react'
import type { SankeyData } from '@/types/chart'

interface ConcentrationSankeyProps {
  data: SankeyData
  width?: number
  height?: number
  className?: string
}

const LINK_COLORS = [
  '#2E75B6', '#1B3A5C', '#27AE60', '#F39C12', '#E67E22',
  '#C0392B', '#2ECC71', '#3498DB', '#9B59B6', '#1ABC9C',
]

export function ConcentrationSankey({
  data,
  width = 800,
  height = 400,
  className,
}: ConcentrationSankeyProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || data.nodes.length === 0) return

    async function render() {
      const d3 = await import('d3')
      const { sankey, sankeyLinkHorizontal } = await import('d3-sankey')

      const svg = d3.select(svgRef.current)
      svg.selectAll('*').remove()

      const margin = { top: 10, right: 10, bottom: 10, left: 10 }
      const innerWidth = width - margin.left - margin.right
      const innerHeight = height - margin.top - margin.bottom

      const g = svg
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`)

      const nodeMap = new Map(data.nodes.map((n, i) => [n.id, i]))

      const sankeyGen = sankey()
        .nodeId((d: { index?: number }) => d.index ?? 0)
        .nodeWidth(16)
        .nodePadding(12)
        .extent([[0, 0], [innerWidth, innerHeight]])

      const sankeyData = sankeyGen({
        nodes: data.nodes.map((n) => ({ ...n })),
        links: data.links.map((l) => ({
          source: nodeMap.get(l.source) ?? 0,
          target: nodeMap.get(l.target) ?? 0,
          value: l.value,
        })),
      })

      g.append('g')
        .selectAll('rect')
        .data(sankeyData.nodes)
        .join('rect')
        .attr('x', (d: { x0?: number }) => d.x0 ?? 0)
        .attr('y', (d: { y0?: number }) => d.y0 ?? 0)
        .attr('height', (d: { y1?: number; y0?: number }) => (d.y1 ?? 0) - (d.y0 ?? 0))
        .attr('width', (d: { x1?: number; x0?: number }) => (d.x1 ?? 0) - (d.x0 ?? 0))
        .attr('fill', '#1B3A5C')
        .attr('opacity', 0.8)

      g.append('g')
        .selectAll('text')
        .data(sankeyData.nodes)
        .join('text')
        .attr('x', (d: { x0?: number; x1?: number }) => {
          const x0 = d.x0 ?? 0
          const x1 = d.x1 ?? 0
          return x0 < innerWidth / 2 ? x1 + 6 : x0 - 6
        })
        .attr('y', (d: { y0?: number; y1?: number }) => ((d.y0 ?? 0) + (d.y1 ?? 0)) / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', (d: { x0?: number }) => (d.x0 ?? 0) < innerWidth / 2 ? 'start' : 'end')
        .attr('font-size', '11px')
        .attr('fill', '#2C3E50')
        .text((d: { name?: string }) => d.name ?? '')

      g.append('g')
        .attr('fill', 'none')
        .selectAll('path')
        .data(sankeyData.links)
        .join('path')
        .attr('d', sankeyLinkHorizontal())
        .attr('stroke', (_: unknown, i: number) => LINK_COLORS[i % LINK_COLORS.length])
        .attr('stroke-width', (d: { width?: number }) => Math.max(1, d.width ?? 1))
        .attr('stroke-opacity', 0.4)
    }

    render()
  }, [data, width, height])

  return (
    <div className={className}>
      <svg ref={svgRef} width={width} height={height} className="w-full" />
    </div>
  )
}
