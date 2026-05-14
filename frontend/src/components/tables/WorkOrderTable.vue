<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  orders: Array<{
    id: string
    name: string
    client: string
    type: string
    pm: string
    developer: string
    tester: string
    assign_date: string | null
    test_assign_date: string | null
    close_date: string | null
    status: string
    total_days: number | null
  }>
}>()

const statusFilter = ref('')
const clientFilter = ref('')
const typeFilter = ref('')

function mondayLink(id: string) {
  return `https://jgbgroup.monday.com/boards/7960591450/pulses/${id}`
}

function statusType(status: string) {
  if (status === '已結案') return 'success'
  if (status === '測試中') return '' as const
  if (status === '開發中') return 'warning'
  return 'info'
}
</script>

<template>
  <el-card shadow="hover">
    <template #header>
      <div class="flex items-center justify-between flex-wrap gap-2">
        <span class="font-semibold">工單明細</span>
        <div class="flex gap-2">
          <el-select v-model="statusFilter" placeholder="狀態" clearable size="small" style="width: 100px">
            <el-option label="已結案" value="已結案" />
            <el-option label="開發中" value="開發中" />
            <el-option label="測試中" value="測試中" />
            <el-option label="未指派" value="未指派" />
          </el-select>
          <el-input v-model="clientFilter" placeholder="客戶" clearable size="small" style="width: 100px" />
          <el-input v-model="typeFilter" placeholder="類型" clearable size="small" style="width: 100px" />
        </div>
      </div>
    </template>
    <el-table
      :data="orders.filter(o =>
        (!statusFilter || o.status === statusFilter) &&
        (!clientFilter || o.client.includes(clientFilter)) &&
        (!typeFilter || o.type.includes(typeFilter))
      )"
      stripe size="small" max-height="500"
      :default-sort="{ prop: 'assign_date', order: 'descending' }"
    >
      <el-table-column prop="name" label="工單名稱" min-width="200">
        <template #default="{ row }">
          <a :href="mondayLink(row.id)" target="_blank" class="text-blue-600 hover:underline">
            {{ row.name }}
          </a>
        </template>
      </el-table-column>
      <el-table-column prop="client" label="客戶" width="90" sortable />
      <el-table-column prop="type" label="類型" width="80" sortable />
      <el-table-column prop="status" label="狀態" width="80">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assign_date" label="指派日期" width="110" sortable />
      <el-table-column prop="close_date" label="結案日期" width="110" sortable />
      <el-table-column prop="total_days" label="天數" width="70" sortable>
        <template #default="{ row }">
          {{ row.total_days ?? '-' }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
