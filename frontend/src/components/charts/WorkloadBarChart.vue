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

  // PM+RD: unique count bar + role participation stacked
  const names = props.workloads.map((w) => w.user_name)

  return {
    tooltip: {
      trigger: 'axis' as const,
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex ?? 0
        const w = props.workloads[idx]
        if (!w) return ''
        return `<b>${w.user_name}</b><br/>
          實際工單：<b>${w.unique_count ?? 0}</b> 張<br/>
          <hr style="margin:4px 0"/>
          角色參與明細：<br/>
          &nbsp;&nbsp;PM：${w.pm_count ?? 0} 次<br/>
          &nbsp;&nbsp;開發：${w.dev_count ?? 0} 次<br/>
          &nbsp;&nbsp;測試：${w.test_count ?? 0} 次<br/>
          &nbsp;&nbsp;合計：${w.total_count ?? 0} 次`
      },
    },
    legend: { data: ['實際工單數', 'PM', '開發', '測試'], top: 0 },
    grid: { left: 50, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category' as const,
      data: names,
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: { type: 'value' as const },
    series: [
      {
        name: '實際工單數', type: 'bar' as const, color: '#4472C4',
        data: props.workloads.map((w) => w.unique_count ?? w.total_count ?? 0),
        barMaxWidth: 30,
        label: { show: true, position: 'top' as const, fontSize: 11, fontWeight: 'bold' as const },
        z: 10,
      },
      {
        name: 'PM', type: 'bar' as const, stack: 'role', color: 'rgba(148,103,189,0.6)',
        data: props.workloads.map((w) => w.pm_count || 0),
        barMaxWidth: 18,
      },
      {
        name: '開發', type: 'bar' as const, stack: 'role', color: 'rgba(237,125,49,0.6)',
        data: props.workloads.map((w) => w.dev_count || 0),
        barMaxWidth: 18,
      },
      {
        name: '測試', type: 'bar' as const, stack: 'role', color: 'rgba(112,173,71,0.6)',
        data: props.workloads.map((w) => w.test_count || 0),
        barMaxWidth: 18,
      },
    ],
  }
})
</script>

<template>
  <el-card shadow="hover">
    <template #header>
      <div>
        <span class="font-semibold">
          {{ isMarketing ? '成員內容產出量' : '成員工作量' }}
        </span>
        <p v-if="!isMarketing" class="text-xs text-gray-400 mt-1">
          藍色 = 實際工單數（去重），半透明 = 角色參與次數（同一工單可能身兼多角色）
        </p>
      </div>
    </template>
    <v-chart :option="option" style="height: 380px" autoresize />
  </el-card>
</template>
