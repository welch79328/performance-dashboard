<script setup lang="ts">
defineProps<{
  orders: Array<{
    id: string
    name: string
    client: string
    developer: string
    assign_date: string
    days_open: number
    severity: string
  }>
}>()

function mondayLink(id: string) {
  return `https://jgbgroup.monday.com/boards/7960591450/pulses/${id}`
}

function severityColor(severity: string) {
  if (severity === 'red') return '#FF6B6B'
  if (severity === 'yellow') return '#FFD93D'
  return '#6BCB77'
}
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold text-red-600">卡關工單（>7天未進測試）</span></template>
    <el-table :data="orders" stripe size="small" max-height="400">
      <el-table-column prop="name" label="工單名稱" min-width="200">
        <template #default="{ row }">
          <a :href="mondayLink(row.id)" target="_blank" class="text-blue-600 hover:underline">
            {{ row.name }}
          </a>
        </template>
      </el-table-column>
      <el-table-column prop="client" label="客戶" width="100" />
      <el-table-column prop="developer" label="開發者" width="100" />
      <el-table-column prop="days_open" label="已開天數" width="100" sortable>
        <template #default="{ row }">
          <el-tag :color="severityColor(row.severity)" effect="dark" size="small">
            {{ row.days_open }} 天
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assign_date" label="指派日期" width="120" />
    </el-table>
    <div v-if="!orders.length" class="text-center py-4 text-gray-400">無卡關工單</div>
  </el-card>
</template>
