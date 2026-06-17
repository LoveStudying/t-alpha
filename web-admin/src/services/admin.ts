import { http } from './http'

export interface PagedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface AdminOverview {
  app_env: string
  app_host: string
  app_port: number
  watchlist_count: number
  enabled_watchlist_count: number
  report_count: number
  open_position_count: number
  recent_alert_count: number
}

export interface WatchlistRow {
  id: number
  code: string
  name: string
  enabled: boolean
  strategy_name: string
  note: string
  created_at: string
  updated_at: string
}

export interface SettingsSummary {
  app_env: string
  app_host: string
  app_port: number
  log_level: string
  ad_username: string
  ad_host: string
  ad_port: number
  db_host: string
  db_port: number
  db_name: string
  smtp_host: string
  smtp_port: number
  smtp_configured: boolean
  alert_to_configured: boolean
  admin_username: string
  admin_configured: boolean
  t0_params: Record<string, unknown>
}

export type RecordRow = Record<string, any>

export async function getOverview(): Promise<AdminOverview> {
  const response = await http.get<AdminOverview>('/api/v1/admin/overview')
  return response.data
}

export async function getSettingsSummary(): Promise<SettingsSummary> {
  const response = await http.get<SettingsSummary>('/api/v1/admin/settings/summary')
  return response.data
}

export async function listWatchlist(): Promise<PagedResponse<WatchlistRow>> {
  const response = await http.get<PagedResponse<WatchlistRow>>('/api/v1/admin/watchlist')
  return response.data
}

export async function createWatchlist(payload: Partial<WatchlistRow>): Promise<WatchlistRow> {
  const response = await http.post<WatchlistRow>('/api/v1/admin/watchlist', payload)
  return response.data
}

export async function updateWatchlist(id: number, payload: Partial<WatchlistRow>): Promise<WatchlistRow> {
  const response = await http.patch<WatchlistRow>(`/api/v1/admin/watchlist/${id}`, payload)
  return response.data
}

export async function deleteWatchlist(id: number): Promise<{ deleted: boolean; id: number }> {
  const response = await http.delete<{ deleted: boolean; id: number }>(`/api/v1/admin/watchlist/${id}`)
  return response.data
}

export async function listReports(): Promise<PagedResponse<RecordRow>> {
  const response = await http.get<PagedResponse<RecordRow>>('/api/v1/admin/t0/reports')
  return response.data
}

export async function listPositions(): Promise<PagedResponse<RecordRow>> {
  const response = await http.get<PagedResponse<RecordRow>>('/api/v1/admin/t0/positions')
  return response.data
}

export async function listAlerts(): Promise<PagedResponse<RecordRow>> {
  const response = await http.get<PagedResponse<RecordRow>>('/api/v1/admin/alerts')
  return response.data
}
