<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, CanvasRenderer])

const props = defineProps<{
  trends: Array<{
    week_start: string
    task_count: number
    bug_count: number
    change_count: number
  }>
  changeDensityTrend: number[]
}>()

const option = computed(() => {
  const weeks = props.trends.map((t) => t.week_start)

  return {
    tooltip: {
      trigger: 'axis' as const,
      formatter: (params: any) => {
        const week = params[0]?.axisValue || ''
        let html = `<b>${week}</b><br/>`
        for (const p of params) {
          html += `${p.marker} ${p.seriesName}: <b>${p.value}${p.seriesName.includes('%') ? '' : ''}</b><br/>`
        }
        return html
      },
    },
    legend: { top: 0 },
    grid: { left: 50, right: 50, top: 40, bottom: 30 },
    xAxis: {
      type: 'category' as const,
      data: weeks,
      axisLabel: { fontSize: 10 },
    },
    yAxis: [
      { type: 'value' as const, name: '工單數', position: 'left' as const },
      { type: 'value' as const, name: '異動佔比%', position: 'right' as const, max: 100 },
    ],
    series: [
      {
        name: 'Bug 數量',
        type: 'bar' as const,
        color: '#FF6B6B',
        data: props.trends.map((t) => t.bug_count),
        barMaxWidth: 20,
      },
      {
        name: '異動數量',
        type: 'bar' as const,
        color: '#FFD93D',
        data: props.trends.map((t) => t.change_count),
        barMaxWidth: 20,
      },
      {
        name: '總工單數',
        type: 'line' as const,
        color: '#4472C4',
        data: props.trends.map((t) => t.task_count),
        smooth: true,
      },
      {
        name: '異動佔比%',
        type: 'line' as const,
        yAxisIndex: 1,
        color: '#ED7D31',
        data: props.changeDensityTrend,
        smooth: true,
        lineStyle: { type: 'dashed' as const },
        markLine: {
          silent: true,
          data: [
            {
              yAxis: 20,
              label: { formatter: '警戒線 20%', position: 'end' as const, fontSize: 10 },
              lineStyle: { color: '#FF6B6B', type: 'dotted' as const },
            },
          ],
        },
      },
    ],
  }
})
</script>

<template>
  <el-card shadow="hover">
    <template #header>
      <div>
        <span class="font-semibold">品質趨勢（近 12 週）</span>
        <p class="text-xs text-gray-400 mt-1">
          長條 = 每週 Bug / 異動數量，藍線 = 總工單數，橘虛線 = 異動佔比（右軸），紅虛線 = 20% 警戒線
        </p>
      </div>
    </template>
    <v-chart :option="option" style="height: 350px" autoresize />
  </el-card>
</template>
