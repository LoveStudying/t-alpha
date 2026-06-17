import { http } from './http'

export interface T0BuildResponse {
  code: string
  strategy_name: string
  params: Record<string, unknown>
  full_metrics: Record<string, any>
  train_metrics: Record<string, any>
  validation_metrics: Record<string, any>
  recent_metrics: Record<string, any>
  recent_trades: Record<string, any>[]
  eligibility: Record<string, any>
  generated_at: string
  disclaimer: string
}

export interface T0MonitorResponse {
  code: string
  enabled: boolean
  strategy_name: string
  reason?: string
}

export async function buildT0Report(code: string): Promise<T0BuildResponse> {
  const response = await http.post<T0BuildResponse>('/api/v1/strategy/t0/build', { code })
  return response.data
}

export async function toggleT0Monitor(code: string, enabled: boolean): Promise<T0MonitorResponse> {
  const response = await http.post<T0MonitorResponse>('/api/v1/strategy/t0/monitor', { code, enabled })
  return response.data
}
