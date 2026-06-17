<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-copy">
        <span class="eyebrow">T-ALPHA ADMIN</span>
        <h1>本地量化研究维护台</h1>
        <p>把行情查询、T0 报告、监控标的和提醒记录收束到一个清爽的日常工作台。</p>
      </div>
      <el-form class="login-form" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" size="large" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" autocomplete="current-password" show-password type="password" size="large" />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" native-type="submit" @click="submit">登录</el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin' })

async function submit() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    await router.push((route.query.redirect as string) || '/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 32px;
}

.login-panel {
  display: grid;
  width: min(920px, 100%);
  grid-template-columns: 1.1fr 0.9fr;
  gap: 36px;
  padding: 38px;
  border: 1px solid var(--ta-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--ta-shadow);
}

.eyebrow {
  color: var(--ta-primary);
  font-size: 12px;
  font-weight: 800;
}

h1 {
  margin: 18px 0 14px;
  font-size: 42px;
  letter-spacing: 0;
}

p {
  max-width: 460px;
  color: var(--ta-muted);
  line-height: 1.8;
}

.login-form {
  align-self: center;
}

.login-form .el-button {
  width: 100%;
}

@media (max-width: 780px) {
  .login-panel {
    grid-template-columns: 1fr;
  }
}
</style>
