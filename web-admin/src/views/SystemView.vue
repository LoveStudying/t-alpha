<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">系统</h1>
        <p class="page-subtitle">查看脱敏配置摘要和当前运行环境。</p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <section class="surface section-pad">
      <el-descriptions v-if="summary" :column="2" border>
        <el-descriptions-item label="APP 环境">{{ summary.app_env }}</el-descriptions-item>
        <el-descriptions-item label="API 地址">{{ summary.app_host }}:{{ summary.app_port }}</el-descriptions-item>
        <el-descriptions-item label="AmazingData">{{ summary.ad_host }}:{{ summary.ad_port }}</el-descriptions-item>
        <el-descriptions-item label="数据库">{{ summary.db_host }}:{{ summary.db_port }}/{{ summary.db_name }}</el-descriptions-item>
        <el-descriptions-item label="SMTP">
          <StatusBadge :value="summary.smtp_configured" />
        </el-descriptions-item>
        <el-descriptions-item label="管理账号">
          <StatusBadge :value="summary.admin_configured" />
        </el-descriptions-item>
      </el-descriptions>
    </section>

    <section v-if="summary" class="surface section-pad">
      <h3>T0 参数</h3>
      <el-table :data="paramRows" border>
        <el-table-column prop="key" label="参数" />
        <el-table-column prop="value" label="值" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import StatusBadge from '@/components/StatusBadge.vue'
import { getSettingsSummary, type SettingsSummary } from '@/services/admin'

const loading = ref(false)
const summary = ref<SettingsSummary>()
const paramRows = computed(() =>
  Object.entries(summary.value?.t0_params || {}).map(([key, value]) => ({ key, value })),
)

async function load() {
  loading.value = true
  try {
    summary.value = await getSettingsSummary()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
