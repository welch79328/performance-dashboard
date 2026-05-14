<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  items: Array<{
    id: string
    name: string
    client: string
    developer: string
    start_date: string
    end_date: string | null
    status: string
  }>
}>()

const today = new Date().toISOString().slice(0, 10)

const statusColors: Record<string, string> = {
  '已結案': '#6BCB77',
  '測試中': '#4472C4',
  '開發中': '#ED7D31',
  '未指派': '#CCCCCC',
}

// Calculate date range for the chart
const dateRange = computed(() => {
  if (!props.items.length) return { min: today, max: today, totalDays: 1 }
  const starts = props.items.map((i) => i.start_date)
  const ends = props.items.map((i) => i.end_date || today)
  const min = starts.sort()[0]!
  const max = ends.sort().reverse()[0]!
  const totalDays = Math.max((new Date(max).getTime() - new Date(min).getTime()) / 86400000, 1)
  return { min, max, totalDays }
})

function barStyle(item: typeof props.items[0]) {
  const start = new Date(item.start_date).getTime()
  const end = new Date(item.end_date || today).getTime()
  const rangeStart = new Date(dateRange.value.min).getTime()
  const totalMs = dateRange.value.totalDays * 86400000

  const left = ((start - rangeStart) / totalMs) * 100
  const width = Math.max(((end - start) / totalMs) * 100, 0.5)

  return {
    left: `${left}%`,
    width: `${width}%`,
    backgroundColor: statusColors[item.status] || '#999',
  }
}

function daysLabel(item: typeof props.items[0]) {
  const start = new Date(item.start_date)
  const end = new Date(item.end_date || today)
  return Math.round((end.getTime() - start.getTime()) / 86400000)
}

function mondayLink(id: string) {
  return `https://jgbgroup.monday.com/boards/7960591450/pulses/${id}`
}
</script>

<template>
  <el-card shadow="hover">
    <template #header>
      <div class="flex items-center gap-4">
        <span class="font-semibold">工單時間軸</span>
        <div class="flex gap-3 text-xs">
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded inline-block" style="background:#ED7D31"></span>開發中</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded inline-block" style="background:#4472C4"></span>測試中</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded inline-block" style="background:#6BCB77"></span>已結案</span>
        </div>
      </div>
    </template>

    <!-- Date axis -->
    <div class="flex justify-between text-xs text-gray-400 mb-2 px-2" style="margin-left: 200px">
      <span>{{ dateRange.min }}</span>
      <span>{{ today }}</span>
      <span>{{ dateRange.max }}</span>
    </div>

    <!-- Gantt rows -->
    <div class="space-y-1 max-h-[500px] overflow-y-auto">
      <div v-for="item in items" :key="item.id" class="flex items-center gap-2 hover:bg-gray-50 rounded px-1 py-0.5">
        <!-- Label -->
        <div class="w-[200px] min-w-[200px] text-xs truncate">
          <a :href="mondayLink(item.id)" target="_blank" class="text-blue-600 hover:underline" :title="item.name">
            {{ item.name.slice(0, 28) }}
          </a>
          <span class="text-gray-400 ml-1">{{ item.developer }}</span>
        </div>
        <!-- Bar -->
        <div class="flex-1 relative h-5 bg-gray-100 rounded">
          <el-tooltip :content="`${item.name}\n客戶: ${item.client}\n開發: ${item.developer}\n${item.start_date} ~ ${item.end_date || '進行中'}\n${daysLabel(item)} 天`" placement="top">
            <div
              class="absolute h-full rounded text-[10px] text-white flex items-center justify-center overflow-hidden"
              :style="barStyle(item)"
            >
              {{ daysLabel(item) > 2 ? `${daysLabel(item)}天` : '' }}
            </div>
          </el-tooltip>
        </div>
      </div>
    </div>

    <div v-if="!items.length" class="text-center py-8 text-gray-400">無工單資料</div>
  </el-card>
</template>
