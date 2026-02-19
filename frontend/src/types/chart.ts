export interface SupplyChainNode {
  id: string
  name: string
  type: 'vendor' | 'provider' | 'subcontractor'
  tier: number
  score?: number
  grade?: string
}

export interface SupplyChainLink {
  source: string
  target: string
  type: 'direct' | 'indirect'
}

export interface SupplyChainGraphData {
  nodes: SupplyChainNode[]
  links: SupplyChainLink[]
}

export interface SankeyNode {
  id: string
  name: string
}

export interface SankeyLink {
  source: string
  target: string
  value: number
}

export interface SankeyData {
  nodes: SankeyNode[]
  links: SankeyLink[]
}

export interface GaugeZone {
  min: number
  max: number
  color: string
}

export interface RadarDataPoint {
  domain: string
  label: string
  score: number
}
