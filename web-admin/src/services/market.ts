import { http } from './http'

export interface DateRange {
  start_date?: string
  end_date?: string
}

export interface PriceRow {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
}

export interface PriceResponse {
  code: string
  asset_type: string
  period: string
  adjust: string
  requested_dates: DateRange
  normalized_dates: DateRange
  rows: PriceRow[]
  disclaimer: string
}

export interface FundNavResponse {
  code: string
  requested_dates: DateRange
  normalized_dates: DateRange
  rows: Record<string, unknown>[]
  disclaimer: string
}

export interface MarketQuery {
  assetType: 'stock' | 'etf' | 'fund' | 'nav'
  code: string
  start_date?: string
  end_date?: string
  period?: string
  adjust?: string
}

export async function queryMarket(payload: MarketQuery): Promise<PriceResponse | FundNavResponse> {
  const params = {
    code: payload.code,
    start_date: payload.start_date,
    end_date: payload.end_date,
    period: payload.period,
    adjust: payload.adjust,
  }
  const pathMap = {
    stock: '/api/v1/market/stock/prices',
    etf: '/api/v1/market/etf/prices',
    fund: '/api/v1/market/fund/prices',
    nav: '/api/v1/market/fund/nav',
  }
  const response = await http.get<PriceResponse | FundNavResponse>(pathMap[payload.assetType], { params })
  return response.data
}
