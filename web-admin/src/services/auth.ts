import { http } from './http'

export interface AdminUser {
  username: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: AdminUser
}

export async function loginApi(username: string, password: string): Promise<LoginResponse> {
  const response = await http.post<LoginResponse>('/api/v1/auth/login', { username, password })
  return response.data
}

export async function meApi(): Promise<AdminUser> {
  const response = await http.get<AdminUser>('/api/v1/auth/me')
  return response.data
}
