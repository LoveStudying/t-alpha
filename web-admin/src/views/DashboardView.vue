<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">工作台</h1>
        <p class="page-subtitle">查看服务状态、监控规模和最近数据记录。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>

    <RiskDisclaimer />

    <div class="metrics">
      <MetricTile label="监控标的" :value="overview?.watchlist_count ?? '-'" hint="watchlist 总数" />
      <MetricTile label="已启用" :value="overview?.enabled_watchlist_count ?? '-'" hint="当前会参与监控" />
      <MetricTile label="打开 T 仓" :value="overview?.open_position_count ?? '-'" hint="虚拟仓未关闭" />
      <MetricTile label="最近提醒" :value="overview?.recent_alert_count ?? '-'" hint="近 7 天记录" />
    </div>

    <section class="surface section-pad">
      <h3>快速入口</h3>
      <div class="quick-actions">
        <el-button type="primary" @click="$router.push('/market')">查询行情</el-button>
        <el-button @click="$router.push('/strategy/t0')">生成 T0 报告</el-button>
        <el-button @click="$router.push('/watchlist')">维护监控标的</el-button>
        <el-button @click="$router.push('/records')">查看数据记录</el-button>
      </div>
    </section>

    <section class="surface section-pad">
      <h3>运行环境</h3>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="环境">{{ overview?.app_env || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Host">{{ overview?.app_host || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Port">{{ overview?.app_port || '-' }}</el-descriptions-item>
      </el-descriptions>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import MetricTile from '@/components/MetricTile.vue'
import RiskDisclaimer from '@/components/RiskDisclaimer.vue'
import { getOverview, type AdminOverview } from '@/services/admin'

const loading = ref(false)
const overview = ref<AdminOverview>()

async function load() {
  loading.value = true
  try {
    overview.value = await getOverview()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 960px) {
  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
