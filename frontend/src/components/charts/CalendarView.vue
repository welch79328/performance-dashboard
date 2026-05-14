<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { CalendarComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([HeatmapChart, CalendarComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps<{
  campaigns: Array<{
    name: string
    publish_date: string | null
    group_name: string
    completion_status: string
  }>
}>()

const option = computed(() => {
  const dateCounts: Record<string, number> = {}
  const dateNames: Record<string, string[]> = {}
  for (const c of props.campaigns) {
    if (!c.publish_date) continue
    dateCounts[c.publish_date] = (dateCounts[c.publish_date] || 0) + 1
    if (!dateNames[c.publish_date]) dateNames[c.publish_date] = []
    dateNames[c.publish_date]!.push(c.name.slice(0, 30))
  }

  const dates = Object.keys(dateCounts).sort()
  if (!dates.length) return {}

  const firstMonth = dates[0]!.slice(0, 7)
  const lastMonth = dates[dates.length - 1]!.slice(0, 7)

  return {
    tooltip: {
      formatter: (params: any) => {
        const d = params.data[0]
        const names = dateNames[d] || []
        return `<b>${d}</b> (${params.data[1]} 篇)<br/>${names.join('<br/>')}`
      },
    },
    visualMap: {
      min: 0, max: Math.max(...Object.values(dateCounts), 1),
      calculable: true, orient: 'vertical' as const,
      right: 0, top: 'middle' as const,
      itemHeight: 100,
      inRange: { color: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'] },
    },
    calendar: {
      range: [firstMonth, lastMonth],
      cellSize: ['auto', 20],
      left: 40, right: 80, top: 20,
      itemStyle: { borderWidth: 2, borderColor: '#fff' },
    },
    series: [{
      type: 'heatmap' as const,
      coordinateSystem: 'calendar' as const,
      data: Object.entries(dateCounts).map(([d, c]) => [d, c]),
    }],
  }
})
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">行銷發佈日曆</span></template>
    <v-chart v-if="campaigns.length" :option="option" style="height: 240px" autoresize />
    <div v-else class="text-center py-4 text-gray-400">無行銷資料</div>
  </el-card>
</template>
