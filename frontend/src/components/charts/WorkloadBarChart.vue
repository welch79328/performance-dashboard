<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  workloads: Array<Record<string, any>>
  department?: string
}>()

const isMarketing = computed(() => props.department === 'marketing')

const option = computed(() => {
  if (isMarketing.value) {
    // Marketing: show content_count per person
    return {
      tooltip: { trigger: 'axis' as const },
      legend: { data: ['內容產出量', '排程前瞻'], top: 0 },
      grid: { left: 50, right: 20, top: 40, bottom: 40 },
      xAxis: {
        type: 'category' as const,
        data: props.workloads.map((w) => w.user_name),
        axisLabel: { rotate: 30, fontSize: 11 },
      },
      yAxis: { type: 'value' as const },
      series: [
        {
          name: '內容產出量', type: 'bar' as const, color: '#4472C4',
          data: props.workloads.map((w) => w.content_count || 0),
          label: { show: true, position: 'top' as const, fontSize: 11 },
        },
        {
          name: '排程前瞻', type: 'bar' as const, color: '#70AD47',
          data: props.workloads.map((w) => w.scheduled_count || 0),
        },
      ],
    }
  }

  // PM+RD: stacked bar by role
  return {
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['PM', '開發', '測試'], top: 0 },
    grid: { left: 50, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category' as const,
      data: props.workloads.map((w) => w.user_name),
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: { type: 'value' as const },
    series: [
      { name: 'PM', type: 'bar' as const, stack: 'total', color: '#4472C4', data: props.workloads.map((w) => w.pm_count || 0) },
      { name: '開發', type: 'bar' as const, stack: 'total', color: '#ED7D31', data: props.workloads.map((w) => w.dev_count || 0) },
      { name: '測試', type: 'bar' as const, stack: 'total', color: '#70AD47', data: props.workloads.map((w) => w.test_count || 0) },
    ],
  }
})
</script>

<template>
  <el-card shadow="hover">
    <template #header>
      <span class="font-semibold">
        {{ isMarketing ? '成員內容產出量' : '成員工作量（角色拆分）' }}
      </span>
    </template>
    <v-chart :option="option" style="height: 350px" autoresize />
  </el-card>
</template>
