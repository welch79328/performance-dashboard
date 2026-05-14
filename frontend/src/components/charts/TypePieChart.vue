<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{ distribution: Record<string, number>; title: string }>()

const itemCount = computed(() => Object.keys(props.distribution).length)
const isCrowded = computed(() => itemCount.value > 5)

const option = computed(() => {
  const data = Object.entries(props.distribution)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  if (isCrowded.value) {
    // Many items: legend on right, smaller pie, no labels on pie
    return {
      tooltip: {
        trigger: 'item' as const,
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical' as const,
        right: 10,
        top: 'middle' as const,
        textStyle: { fontSize: 11 },
        formatter: (name: string) => {
          const item = data.find((d) => d.name === name)
          return item ? `${name.slice(0, 12)} (${item.value})` : name
        },
      },
      series: [{
        type: 'pie' as const,
        radius: ['35%', '65%'],
        center: ['35%', '50%'],
        data,
        label: { show: false },
        emphasis: { itemStyle: { shadowBlur: 10 } },
      }],
    }
  }

  // Few items: normal layout with labels
  return {
    tooltip: {
      trigger: 'item' as const,
      formatter: '{b}: {c} ({d}%)',
    },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie' as const,
      radius: ['40%', '70%'],
      data,
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        fontSize: 11,
      },
      emphasis: { itemStyle: { shadowBlur: 10 } },
    }],
  }
})
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">{{ title }}</span></template>
    <v-chart :option="option" :style="{ height: isCrowded ? '320px' : '280px' }" autoresize />
  </el-card>
</template>
