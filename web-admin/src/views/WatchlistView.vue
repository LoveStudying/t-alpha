<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">监控维护</h1>
        <p class="page-subtitle">维护 watchlist，控制 T0 监控启停。</p>
      </div>
      <el-button type="primary" @click="openCreate">新增标的</el-button>
    </div>

    <section class="surface">
      <DataTableToolbar title="监控标的" subtitle="启用前请先生成并检查 eligible 报告">
        <el-button :loading="loading" @click="load">刷新</el-button>
      </DataTableToolbar>
      <el-table :data="rows" border>
        <el-table-column prop="code" label="代码" min-width="130" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="strategy_name" label="策略" min-width="190" />
        <el-table-column prop="enabled" label="状态" min-width="100">
          <template #default="{ row }"><StatusBadge :value="row.enabled" /></template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="180" />
        <el-table-column prop="updated_at" label="更新时间" min-width="170" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button text @click="edit(row)">编辑</el-button>
            <el-button text @click="toggle(row)">{{ row.enabled ? '停用' : '启用' }}</el-button>
            <el-button text type="primary" @click="build(row)">生成报告</el-button>
            <el-button text type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="editing?.id ? '编辑标的' : '新增标的'" width="520px">
      <el-form :model="form" label-position="top">
        <el-form-item label="代码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="策略"><el-input v-model="form.strategy_name" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" type="textarea" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import DataTableToolbar from '@/components/DataTableToolbar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { createWatchlist, deleteWatchlist, listWatchlist, updateWatchlist, type WatchlistRow } from '@/services/admin'
import { buildT0Report, toggleT0Monitor } from '@/services/strategy'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const rows = ref<WatchlistRow[]>([])
const editing = ref<WatchlistRow | null>(null)
const form = reactive<Partial<WatchlistRow>>({
  code: '',
  name: '',
  enabled: true,
  strategy_name: 'mean_reversion_t0_v1',
  note: '',
})

async function load() {
  loading.value = true
  try {
    rows.value = (await listWatchlist()).items
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, { code: '', name: '', enabled: true, strategy_name: 'mean_reversion_t0_v1', note: '' })
  dialogVisible.value = true
}

function edit(row: WatchlistRow) {
  editing.value = row
  Object.assign(form, row)
  dialogVisible.value = true
}

async function save() {
  saving.value = true
  try {
    if (editing.value?.id) await updateWatchlist(editing.value.id, form)
    else await createWatchlist(form)
    dialogVisible.value = false
    await load()
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}

async function toggle(row: WatchlistRow) {
  await toggleT0Monitor(row.code, !row.enabled)
  await updateWatchlist(row.id, { enabled: !row.enabled })
  await load()
}

async function build(row: WatchlistRow) {
  await buildT0Report(row.code)
  ElMessage.success('报告已生成')
}

async function remove(row: WatchlistRow) {
  await ElMessageBox.confirm(`确认删除 ${row.code}？`, '删除监控标的', { type: 'warning' })
  await deleteWatchlist(row.id)
  await load()
}

onMounted(load)
</script>
