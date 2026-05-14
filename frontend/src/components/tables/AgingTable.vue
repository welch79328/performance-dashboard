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

function severityTag(severity: string) {
  if (severity === 'red') return { type: 'danger' as const, label: '超時' }
  if (severity === 'yellow') return { type: 'warning' as const, label: '注意' }
  return { type: 'success' as const, label: '正常' }
}
</script>

<template>
  <el-card shadow="hover">
    <template #header><span class="font-semibold">未結案工單老化表</span></template>
    <el-table :data="orders" stripe size="small" max-height="500">
      <el-table-column label="嚴重度" width="80">
        <template #default="{ row }">
          <el-tag :type="severityTag(row.severity).type" size="small">
            {{ severityTag(row.severity).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="工單名稱" min-width="200">
        <template #default="{ row }">
          <a :href="mondayLink(row.id)" target="_blank" class="text-blue-600 hover:underline">
            {{ row.name }}
          </a>
        </template>
      </el-table-column>
      <el-table-column prop="client" label="客戶" width="100" />
      <el-table-column prop="developer" label="開發者" width="100" />
      <el-table-column prop="days_open" label="已開天數" width="100" sortable />
      <el-table-column prop="assign_date" label="指派日期" width="120" />
    </el-table>
    <div v-if="!orders.length" class="text-center py-4 text-gray-400">所有工單均已結案</div>
  </el-card>
</template>
