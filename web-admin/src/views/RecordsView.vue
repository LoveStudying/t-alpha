<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">数据记录</h1>
        <p class="page-subtitle">查看 T0 报告、虚拟 T 仓和提醒记录。</p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <section class="surface section-pad">
      <el-tabs v-model="active" @tab-change="load">
        <el-tab-pane label="报告记录" name="reports">
          <el-table :data="reports" border>
            <el-table-column prop="code" label="代码" min-width="130" />
            <el-table-column prop="strategy_name" label="策略" min-width="190" />
            <el-table-column prop="eligibility_level" label="准入" min-width="120">
              <template #default="{ row }"><StatusBadge :value="row.eligibility_level" /></template>
            </el-table-column>
            <el-table-column prop="generated_at" label="生成时间" min-width="180" />
            <el-table-column label="详情" width="100">
              <template #default="{ row }"><el-button text @click="show(row)">查看</el-button></template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="虚拟 T 仓" name="positions">
          <el-table :data="positions" border>
            <el-table-column prop="code" label="代码" min-width="130" />
            <el-table-column prop="status" label="状态" min-width="100">
              <template #default="{ row }"><StatusBadge :value="row.status" /></template>
            </el-table-column>
            <el-table-column prop="opened_at" label="打开时间" min-width="180" />
            <el-table-column prop="closed_at" label="关闭时间" min-width="180" />
            <el-table-column label="详情" width="100">
              <template #default="{ row }"><el-button text @click="show(row)">查看</el-button></template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="提醒记录" name="alerts">
          <el-table :data="alerts" border>
            <el-table-column prop="code" label="代码" min-width="130" />
            <el-table-column prop="signal_type" label="类型" min-width="100">
              <template #default="{ row }"><StatusBadge :value="row.signal_type" /></template>
            </el-table-column>
            <el-table-column prop="sent" label="发送" min-width="100">
              <template #default="{ row }"><StatusBadge :value="row.sent" /></template>
            </el-table-column>
            <el-table-column prop="signal_time" label="信号时间" min-width="180" />
            <el-table-column prop="error_message" label="错误" min-width="180" />
            <el-table-column label="详情" width="100">
              <template #default="{ row }"><el-button text @click="show(row)">查看</el-button></template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </section>

    <JsonDrawer v-model="drawerVisible" title="记录详情" :data="selected" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import JsonDrawer from '@/components/JsonDrawer.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { listAlerts, listPositions, listReports, type RecordRow } from '@/services/admin'

const active = ref('reports')
const loading = ref(false)
const reports = ref<RecordRow[]>([])
const positions = ref<RecordRow[]>([])
const alerts = ref<RecordRow[]>([])
const drawerVisible = ref(false)
const selected = ref<RecordRow>()

function show(row: RecordRow) {
  selected.value = row
  drawerVisible.value = true
}

async function load() {
  loading.value = true
  try {
    if (active.value === 'reports') reports.value = (await listReports()).items
    if (active.value === 'positions') positions.value = (await listPositions()).items
    if (active.value === 'alerts') alerts.value = (await listAlerts()).items
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
