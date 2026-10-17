<script setup lang="ts">
defineProps<{
  title: string
  eyebrow?: string
  description?: string
}>()
</script>

<template>
  <header class="workspace-page-title">
    <p v-if="eyebrow" class="workspace-page-title__eyebrow">{{ eyebrow }}</p>
    <h1 class="workspace-page-title__heading">{{ title }}</h1>
    <p v-if="description" class="workspace-page-title__description">{{ description }}</p>
  </header>
</template>

<style scoped>
.workspace-page-title {
  min-width: 0;
}

.workspace-page-title__eyebrow {
  margin: 0 0 0.25rem;
  color: var(--accent-color, #5965f5);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  line-height: 1.3;
  text-transform: uppercase;
}

.workspace-page-title__heading {
  margin: 0;
  overflow: hidden;
  color: var(--heading-color, #1d2742);
  font-size: clamp(1.1rem, 2vw, 1.4rem);
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-page-title__description {
  margin: 0.4rem 0 0;
  color: var(--muted-color, #64748b);
  font-size: 0.875rem;
  line-height: 1.55;
}
</style>
