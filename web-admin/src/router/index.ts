import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import AdminLayout from '@/layouts/AdminLayout.vue'
import DashboardView from '@/views/DashboardView.vue'
import LoginView from '@/views/LoginView.vue'
import MarketQueryView from '@/views/MarketQueryView.vue'
import RecordsView from '@/views/RecordsView.vue'
import RoadmapView from '@/views/RoadmapView.vue'
import SystemView from '@/views/SystemView.vue'
import T0StrategyView from '@/views/T0StrategyView.vue'
import WatchlistView from '@/views/WatchlistView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    {
      path: '/',
      component: AdminLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: DashboardView },
        { path: 'market', name: 'market', component: MarketQueryView },
        { path: 'strategy/t0', name: 'strategy-t0', component: T0StrategyView },
        { path: 'watchlist', name: 'watchlist', component: WatchlistView },
        { path: 'records', name: 'records', component: RecordsView },
        { path: 'system', name: 'system', component: SystemView },
        { path: 'roadmap', name: 'roadmap', component: RoadmapView },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
  if (!to.matched.some((record) => record.meta.requiresAuth)) {
    return true
  }
  if (!auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
