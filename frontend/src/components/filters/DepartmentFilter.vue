<script setup lang="ts">
import { useFiltersStore } from '@/stores/filters'

const filters = useFiltersStore()

const options = [
  { label: 'PM + RD', value: 'pm_rd' },
  { label: '行銷', value: 'marketing' },
]
</script>

<template>
  <el-radio-group v-model="filters.department" size="small">
    <el-radio-button v-for="opt in options" :key="opt.value" :value="opt.value">
      {{ opt.label }}
    </el-radio-button>
  </el-radio-group>
</template>
