import { defineStore } from 'pinia'

import { loginApi, meApi } from '@/services/auth'

const TOKEN_KEY = 't_alpha_admin_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    username: '',
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    async login(username: string, password: string) {
      const response = await loginApi(username, password)
      this.token = response.access_token
      this.username = response.user.username
      localStorage.setItem(TOKEN_KEY, this.token)
    },
    async loadMe() {
      if (!this.token) return
      const user = await meApi()
      this.username = user.username
    },
    logout() {
      this.token = ''
      this.username = ''
      localStorage.removeItem(TOKEN_KEY)
    },
  },
})
