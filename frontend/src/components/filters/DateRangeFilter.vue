<script setup lang="ts">
import { useFiltersStore } from '@/stores/filters'

const filters = useFiltersStore()

const presets = [
  { label: '本週', value: 'this-week' },
  { label: '本月', value: 'this-month' },
  { label: '上月', value: 'last-month' },
  { label: '自訂', value: 'custom' },
]
</script>

<template>
  <div class="flex items-center gap-3">
    <el-radio-group v-model="filters.preset" size="small">
      <el-radio-button v-for="p in presets" :key="p.value" :value="p.value">
        {{ p.label }}
      </el-radio-button>
    </el-radio-group>
    <template v-if="filters.preset === 'custom'">
      <el-date-picker v-model="filters.customStart" type="date" placeholder="起始日" size="small" value-format="YYYY-MM-DD" />
      <span class="text-gray-400">~</span>
      <el-date-picker v-model="filters.customEnd" type="date" placeholder="結束日" size="small" value-format="YYYY-MM-DD" />
    </template>
  </div>
</template>
