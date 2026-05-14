<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  byType: Array<{
    type_name: string
    avg_dev_days: number
    avg_test_days: number
  }>
}>()

const option = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  legend: { data: ['開發階段', '測試階段'], top: 0 },
  grid: { left: 50, right: 20, top: 40, bottom: 30 },
  xAxis: {
    type: 'category' as const,
    data: props.byType.map((t) => t.type_name),
  },
  yAxis: { type: 'value' as const, name: '天數' },
  series: [
    { name: '開發階段', type: 'bar' as const, stack: 'stage', color: '#ED7D31', data: props.byType.map((t) => t.avg_dev_days) },
    { name: '測試階段', type: 'bar' as const, stack: 'stage', color: '#70AD47', data: props.byType.map((t) => t.avg_test_days) },
  ],
}))
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">開發 vs 測試階段耗時</span></template>
    <v-chart :option="option" style="height: 300px" autoresize />
  </el-card>
</template>
