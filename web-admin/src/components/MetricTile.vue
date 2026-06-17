<template>
  <div class="metric-tile">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value mono-number">{{ value }}</div>
    <div v-if="hint" class="metric-hint">{{ hint }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  hint?: string
}>()
</script>

<style scoped>
.metric-tile {
  min-height: 116px;
  padding: 18px;
  border: 1px solid var(--ta-border);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(246, 250, 249, 0.82));
}

.metric-label {
  color: var(--ta-muted);
  font-size: 13px;
}

.metric-value {
  margin-top: 12px;
  color: var(--ta-text);
  font-size: 30px;
  font-weight: 700;
}

.metric-hint {
  margin-top: 8px;
  color: var(--ta-muted);
  font-size: 12px;
}
</style>
