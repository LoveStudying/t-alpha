<template>
  <div class="admin-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">T</div>
        <div>
          <strong>t-alpha</strong>
          <span>研究维护台</span>
        </div>
      </div>
      <nav>
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="main">
      <header class="topbar">
        <div>
          <span class="eyebrow">LOCAL ADMIN</span>
          <strong>本地管理后台</strong>
        </div>
        <div class="topbar-actions">
          <el-tag type="success" effect="light">本地使用</el-tag>
          <span class="user">{{ auth.username || 'admin' }}</span>
          <el-button :icon="SwitchButton" text @click="logout">退出</el-button>
        </div>
      </header>
      <section class="content">
        <RouterView />
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import {
  Collection,
  DataAnalysis,
  HomeFilled,
  Monitor,
  Operation,
  Setting,
  SwitchButton,
  TrendCharts,
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const navItems = [
  { path: '/', label: '工作台', icon: HomeFilled },
  { path: '/market', label: '行情查询', icon: TrendCharts },
  { path: '/strategy/t0', label: 'T0 策略', icon: DataAnalysis },
  { path: '/watchlist', label: '监控维护', icon: Operation },
  { path: '/records', label: '数据记录', icon: Collection },
  { path: '/system', label: '系统', icon: Setting },
  { path: '/roadmap', label: '远期规划', icon: Monitor },
]

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.admin-shell {
  display: grid;
  grid-template-columns: 248px 1fr;
  min-height: 100vh;
}

.sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 22px;
  height: 100vh;
  padding: 22px 16px;
  border-right: 1px solid rgba(201, 219, 216, 0.8);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(18px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 8px;
}

.brand-mark {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--ta-primary), var(--ta-accent));
  color: #fff;
  font-weight: 800;
}

.brand strong,
.brand span {
  display: block;
}

.brand span {
  margin-top: 2px;
  color: var(--ta-muted);
  font-size: 12px;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 42px;
  padding: 0 12px;
  border-radius: 8px;
  color: #425456;
  font-size: 14px;
  transition: background 0.18s ease, color 0.18s ease;
}

.nav-item.router-link-exact-active,
.nav-item:hover {
  background: rgba(26, 143, 138, 0.1);
  color: var(--ta-primary-dark);
}

.main {
  min-width: 0;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 68px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(213, 226, 224, 0.8);
  background: rgba(246, 250, 249, 0.82);
  backdrop-filter: blur(18px);
}

.eyebrow {
  display: block;
  margin-bottom: 2px;
  color: var(--ta-primary);
  font-size: 11px;
  font-weight: 700;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user {
  color: var(--ta-muted);
  font-size: 14px;
}

.content {
  padding: 28px;
}

@media (max-width: 900px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: relative;
    height: auto;
  }

  nav {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
