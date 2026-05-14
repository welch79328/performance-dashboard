<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = withDefaults(defineProps<{
  distribution: Record<string, number>
  title: string
  topN?: number
  color?: string
}>(), {
  topN: 10,
  color: '#4472C4',
})

const chartData = computed(() => {
  const sorted = Object.entries(props.distribution)
    .sort((a, b) => b[1] - a[1])
    .slice(0, props.topN)
    .reverse() // ECharts horizontal bar renders bottom-up
  return {
    names: sorted.map(([n]) => n),
    values: sorted.map(([, v]) => v),
  }
})

const option = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  grid: { left: 100, right: 30, top: 10, bottom: 20 },
  xAxis: { type: 'value' as const },
  yAxis: {
    type: 'category' as const,
    data: chartData.value.names,
    axisLabel: { fontSize: 12 },
  },
  series: [{
    type: 'bar' as const,
    data: chartData.value.values,
    itemStyle: { color: props.color },
    barMaxWidth: 20,
    label: { show: true, position: 'right' as const, fontSize: 11 },
  }],
}))
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">{{ title }}（Top {{ topN }}）</span></template>
    <v-chart :option="option" style="height: 300px" autoresize />
  </el-card>
</template>
