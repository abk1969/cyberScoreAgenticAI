'use client'

import { useEffect, useRef } from 'react'
import type { SupplyChainGraphData, SupplyChainNode, SupplyChainLink } from '@/types/chart'

interface SupplyChainGraphProps {
  data: SupplyChainGraphData
  width?: number
  height?: number
  className?: string
}

const TIER_COLORS: Record<number, string> = {
  0: '#1B3A5C',
  1: '#2E75B6',
  2: '#F39C12',
  3: '#E67E22',
}

const TYPE_RADIUS: Record<string, number> = {
  vendor: 12,
  provider: 8,
  subcontractor: 6,
}

export function SupplyChainGraph({
  data,
  width = 800,
  height = 600,
  className,
}: SupplyChainGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || data.nodes.length === 0) return

    let d3Module: typeof import('d3') | null = null

    async function render() {
      d3Module = await import('d3')
      const d3 = d3Module
      const svg = d3.select(svgRef.current)
      svg.selectAll('*').remove()

      const g = svg.append('g')

      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => {
          g.attr('transform', event.transform)
        })

      svg.call(zoom)

      interface SimNode extends SupplyChainNode, d3.SimulationNodeDatum {}
      interface SimLink extends d3.SimulationLinkDatum<SimNode> {
        type: string
      }

      const nodes: SimNode[] = data.nodes.map((d) => ({ ...d }))
      const links: SimLink[] = data.links.map((d) => ({
        source: d.source,
        target: d.target,
        type: d.type,
      }))

      const simulation = d3
        .forceSimulation(nodes)
        .force('link', d3.forceLink<SimNode, SimLink>(links).id((d) => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(20))

      const link = g
        .append('g')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', '#94A3B8')
        .attr('stroke-width', (d) => (d.type === 'direct' ? 2 : 1))
        .attr('stroke-dasharray', (d) => (d.type === 'indirect' ? '4,4' : 'none'))

      const node = g
        .append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .call(
          d3.drag<SVGGElement, SimNode>()
            .on('start', (event, d) => {
              if (!event.active) simulation.alphaTarget(0.3).restart()
              d.fx = d.x
              d.fy = d.y
            })
            .on('drag', (event, d) => {
              d.fx = event.x
              d.fy = event.y
            })
            .on('end', (event, d) => {
              if (!event.active) simulation.alphaTarget(0)
              d.fx = null
              d.fy = null
            }),
        )

      node
        .append('circle')
        .attr('r', (d) => TYPE_RADIUS[d.type] ?? 8)
        .attr('fill', (d) => TIER_COLORS[d.tier] ?? '#94A3B8')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)

      node
        .append('text')
        .attr('dy', (d) => -(TYPE_RADIUS[d.type] ?? 8) - 4)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#2C3E50')
        .text((d) => d.name)

      simulation.on('tick', () => {
        link
          .attr('x1', (d) => (d.source as SimNode).x ?? 0)
          .attr('y1', (d) => (d.source as SimNode).y ?? 0)
          .attr('x2', (d) => (d.target as SimNode).x ?? 0)
          .attr('y2', (d) => (d.target as SimNode).y ?? 0)

        node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
      })

      return () => {
        simulation.stop()
      }
    }

    const cleanup = render()
    return () => {
      cleanup.then((fn) => fn?.())
    }
  }, [data, width, height])

  return (
    <div className={className}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="w-full"
        style={{ minHeight: height }}
      />
    </div>
  )
}
