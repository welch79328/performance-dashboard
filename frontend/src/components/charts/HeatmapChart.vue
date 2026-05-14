<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([HeatmapChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps<{
  cells: Array<{ label: string; week: string; count: number }>
  title: string
}>()

const option = computed(() => {
  const labels = [...new Set(props.cells.map((c) => c.label))]
  const weeks = [...new Set(props.cells.map((c) => c.week))].sort()
  const maxCount = Math.max(...props.cells.map((c) => c.count), 1)

  const data = props.cells.map((c) => [
    weeks.indexOf(c.week),
    labels.indexOf(c.label),
    c.count,
  ])

  return {
    tooltip: {
      formatter: (params: any) => {
        const [wIdx, lIdx, count] = params.data
        return `${labels[lIdx]} / ${weeks[wIdx]}: ${count} 筆`
      },
    },
    grid: { left: 120, right: 80, top: 10, bottom: 40 },
    xAxis: { type: 'category' as const, data: weeks, axisLabel: { fontSize: 10, rotate: 45 } },
    yAxis: { type: 'category' as const, data: labels },
    visualMap: {
      min: 0, max: maxCount, calculable: true, orient: 'vertical' as const,
      right: 0, top: 'middle' as const,
      itemHeight: 120,
      inRange: { color: ['#f0f9ff', '#3b82f6', '#1e3a5f'] },
    },
    series: [{
      type: 'heatmap' as const,
      data,
      label: { show: true, fontSize: 10 },
    }],
  }
})
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">{{ title }}</span></template>
    <v-chart :option="option" style="height: 350px" autoresize />
  </el-card>
</template>
