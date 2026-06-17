<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">T0 策略</h1>
        <p class="page-subtitle">生成低吸型 T0 报告，检查准入后再开启监控。</p>
      </div>
    </div>

    <RiskDisclaimer />

    <section class="surface section-pad">
      <div class="toolbar">
        <el-input v-model="code" style="max-width: 260px" placeholder="601318.SH" />
        <el-button type="primary" :loading="loading" @click="build">生成报告</el-button>
        <el-button v-if="report?.eligibility?.eligible" :loading="monitoring" @click="enableMonitor">开启监控</el-button>
      </div>
    </section>

    <section v-if="report" class="surface section-pad">
      <div class="report-title">
        <h3>{{ report.code }} · {{ report.strategy_name }}</h3>
        <StatusBadge :value="report.eligibility?.level || 'invalid'" />
      </div>
      <div class="metrics">
        <MetricTile label="3 年交易数" :value="report.full_metrics?.trade_count ?? '-'" />
        <MetricTile label="3 年成功率" :value="percent(report.full_metrics?.success_rate)" />
        <MetricTile label="验证成功率" :value="percent(report.validation_metrics?.success_rate)" />
        <MetricTile label="近期交易数" :value="report.recent_metrics?.trade_count ?? '-'" />
      </div>
      <el-alert
        v-if="report.eligibility?.reasons?.length"
        style="margin-top: 14px"
        type="warning"
        :closable="false"
        :title="report.eligibility.reasons.join('；')"
      />
      <el-table :data="report.recent_trades" border style="margin-top: 16px">
        <el-table-column prop="buy_time" label="买入时间" min-width="160" />
        <el-table-column prop="sell_time" label="卖出时间" min-width="160" />
        <el-table-column prop="buy_price" label="买入价" min-width="100" />
        <el-table-column prop="sell_price" label="卖出价" min-width="100" />
        <el-table-column prop="net_return" label="净收益率" min-width="120">
          <template #default="{ row }">{{ percent(row.net_return) }}</template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

import MetricTile from '@/components/MetricTile.vue'
import RiskDisclaimer from '@/components/RiskDisclaimer.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { buildT0Report, toggleT0Monitor, type T0BuildResponse } from '@/services/strategy'

const code = ref('601318.SH')
const loading = ref(false)
const monitoring = ref(false)
const report = ref<T0BuildResponse>()

function percent(value: unknown) {
  return typeof value === 'number' ? `${(value * 100).toFixed(2)}%` : '-'
}

async function build() {
  loading.value = true
  try {
    report.value = await buildT0Report(code.value)
  } finally {
    loading.value = false
  }
}

async function enableMonitor() {
  monitoring.value = true
  try {
    await toggleT0Monitor(code.value, true)
    ElMessage.success('已开启监控')
  } finally {
    monitoring.value = false
  }
}
</script>

<style scoped>
.report-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.report-title h3 {
  margin: 0;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}
</style>
