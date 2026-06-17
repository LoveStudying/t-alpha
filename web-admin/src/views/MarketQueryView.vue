<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">行情查询</h1>
        <p class="page-subtitle">用表单封装股票、ETF、基金价格和基金净值接口。</p>
      </div>
    </div>

    <RiskDisclaimer />

    <section class="surface section-pad">
      <el-form :model="form" label-position="top">
        <div class="query-grid">
          <el-form-item label="资产类型">
            <el-select v-model="form.assetType">
              <el-option label="A 股" value="stock" />
              <el-option label="ETF" value="etf" />
              <el-option label="场内基金" value="fund" />
              <el-option label="场外基金净值" value="nav" />
            </el-select>
          </el-form-item>
          <el-form-item label="代码">
            <el-input v-model="form.code" placeholder="601318.SH" />
          </el-form-item>
          <el-form-item label="开始日期">
            <el-input v-model="form.start_date" placeholder="YYYYMMDD" />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-input v-model="form.end_date" placeholder="YYYYMMDD" />
          </el-form-item>
          <el-form-item label="周期">
            <el-select v-model="form.period" :disabled="form.assetType === 'nav'">
              <el-option label="日线" value="day" />
              <el-option label="60 分钟" value="60m" />
            </el-select>
          </el-form-item>
          <el-form-item label="复权">
            <el-select v-model="form.adjust" :disabled="form.assetType === 'nav'">
              <el-option label="不复权" value="none" />
              <el-option label="前复权" value="forward" />
            </el-select>
          </el-form-item>
        </div>
        <el-button type="primary" :loading="loading" @click="submit">查询</el-button>
      </el-form>
    </section>

    <section v-if="result" class="surface section-pad">
      <div class="result-head">
        <h3>{{ result.code }}</h3>
        <el-tag type="info">请求 {{ result.requested_dates?.start_date || '-' }} 至 {{ result.requested_dates?.end_date || '-' }}</el-tag>
        <el-tag type="success">实际 {{ result.normalized_dates?.start_date || '-' }} 至 {{ result.normalized_dates?.end_date || '-' }}</el-tag>
      </div>
      <div ref="chartEl" class="chart" />
      <el-table :data="rows" height="360" border>
        <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" min-width="120" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, reactive, ref } from 'vue'

import RiskDisclaimer from '@/components/RiskDisclaimer.vue'
import { queryMarket, type MarketQuery } from '@/services/market'

const loading = ref(false)
const chartEl = ref<HTMLDivElement>()
const result = ref<any>()
const form = reactive<MarketQuery>({
  assetType: 'stock',
  code: '601318.SH',
  period: 'day',
  adjust: 'forward',
})

const rows = computed(() => result.value?.rows || [])
const columns = computed(() => (rows.value[0] ? Object.keys(rows.value[0]) : []))

async function submit() {
  loading.value = true
  try {
    result.value = await queryMarket(form)
    await nextTick()
    drawChart()
  } finally {
    loading.value = false
  }
}

function drawChart() {
  if (!chartEl.value || !rows.value.length || !('close' in rows.value[0])) return
  const chart = echarts.init(chartEl.value)
  chart.setOption({
    grid: { left: 42, right: 24, top: 30, bottom: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: rows.value.map((row: any) => row.date) },
    yAxis: { type: 'value', scale: true },
    series: [{ type: 'line', smooth: true, data: rows.value.map((row: any) => row.close), name: 'close' }],
  })
}
</script>

<style scoped>
.query-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.result-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.result-head h3 {
  margin: 0 auto 0 0;
}

.chart {
  height: 320px;
  margin-bottom: 16px;
}
</style>
