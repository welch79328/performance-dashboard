<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  trends: Array<{ week_start: string; task_count: number; close_rate: number }>
  title?: string
}>()

const option = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category' as const,
    data: props.trends.map((t) => t.week_start),
  },
  yAxis: [
    { type: 'value' as const, name: '工單數' },
    { type: 'value' as const, name: '結案率%', max: 100 },
  ],
  series: [
    {
      name: '工單數', type: 'line' as const, data: props.trends.map((t) => t.task_count),
      smooth: true, color: '#4472C4',
    },
    {
      name: '結案率', type: 'line' as const, yAxisIndex: 1,
      data: props.trends.map((t) => t.close_rate),
      smooth: true, color: '#70AD47',
    },
  ],
}))
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">{{ title || '週趨勢' }}</span></template>
    <v-chart :option="option" style="height: 300px" autoresize />
  </el-card>
</template>
