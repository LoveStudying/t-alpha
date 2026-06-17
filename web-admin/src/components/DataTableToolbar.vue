<template>
  <div class="data-toolbar">
    <div>
      <h3>{{ title }}</h3>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    <div class="actions">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<style scoped>
.data-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--ta-border);
}

h3 {
  margin: 0;
  font-size: 16px;
}

p {
  margin: 4px 0 0;
  color: var(--ta-muted);
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 10px;
}
</style>
