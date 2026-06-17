<template>
  <el-drawer v-model="visible" :title="title" size="560px">
    <pre class="json-view">{{ formatted }}</pre>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const visible = defineModel<boolean>({ required: true })
const props = defineProps<{
  title: string
  data: unknown
}>()

const formatted = computed(() => JSON.stringify(props.data, null, 2))
</script>

<style scoped>
.json-view {
  min-height: 100%;
  padding: 14px;
  overflow: auto;
  border: 1px solid var(--ta-border);
  border-radius: 8px;
  background: #0f1720;
  color: #d8f3ee;
  font-size: 12px;
  line-height: 1.6;
}
</style>
