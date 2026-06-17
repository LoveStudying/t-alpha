<template>
  <el-tag :type="tagType" effect="light" round>{{ label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  value: string | boolean
}>()

const labelMap: Record<string, string> = {
  true: '启用',
  false: '停用',
  eligible: '可监控',
  observe: '观察',
  invalid: '未通过',
  open: '打开',
  closed: '已关闭',
  buy: '买点',
  sell: '卖点',
  target: '达标',
  timeout: '超时',
}

const normalized = computed(() => String(props.value))
const label = computed(() => labelMap[normalized.value] || normalized.value)
const tagType = computed(() => {
  if (['true', 'eligible', 'closed', 'target'].includes(normalized.value)) return 'success'
  if (['observe', 'open', 'timeout'].includes(normalized.value)) return 'warning'
  if (['false', 'invalid'].includes(normalized.value)) return 'danger'
  return 'info'
})
</script>
