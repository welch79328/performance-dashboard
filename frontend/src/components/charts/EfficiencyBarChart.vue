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
    count: number
    avg_total_days: number
    avg_dev_days: number
    avg_test_days: number
    close_rate: number
  }>
}>()

const option = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  legend: { data: ['平均結案天數', '開發耗時', '測試耗時'], top: 0 },
  grid: { left: 50, right: 20, top: 40, bottom: 30 },
  xAxis: {
    type: 'category' as const,
    data: props.byType.map((t) => `${t.type_name} (${t.count})`),
  },
  yAxis: { type: 'value' as const, name: '天數' },
  series: [
    { name: '平均結案天數', type: 'bar' as const, color: '#4472C4', data: props.byType.map((t) => t.avg_total_days) },
    { name: '開發耗時', type: 'bar' as const, color: '#ED7D31', data: props.byType.map((t) => t.avg_dev_days) },
    { name: '測試耗時', type: 'bar' as const, color: '#70AD47', data: props.byType.map((t) => t.avg_test_days) },
  ],
}))
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">各類型平均處理耗時</span></template>
    <v-chart :option="option" style="height: 300px" autoresize />
  </el-card>
</template>
