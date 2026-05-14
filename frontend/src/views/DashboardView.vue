<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useFiltersStore } from '@/stores/filters'
import { workloadApi, efficiencyApi } from '@/api'

import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import DepartmentFilter from '@/components/filters/DepartmentFilter.vue'
import DateRangeFilter from '@/components/filters/DateRangeFilter.vue'
import KPISummaryCards from '@/components/cards/KPISummaryCards.vue'
import WorkloadBarChart from '@/components/charts/WorkloadBarChart.vue'
import TypePieChart from '@/components/charts/TypePieChart.vue'
import DistributionBarChart from '@/components/charts/DistributionBarChart.vue'
import TrendLineChart from '@/components/charts/TrendLineChart.vue'
import SyncStatusBar from '@/components/common/SyncStatusBar.vue'
import ExportButtons from '@/components/common/ExportButtons.vue'

const filters = useFiltersStore()
const loading = ref(false)
const teamData = ref<any>(null)
const trends = ref<any[]>([])

// Convert preset to actual date range
function getDateParams() {
  const params: Record<string, string> = { department: filters.department }
  const today = new Date()

  if (filters.preset === 'this-week') {
    const monday = new Date(today)
    monday.setDate(today.getDate() - today.getDay() + 1)
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    params.start = monday.toISOString().slice(0, 10)
    params.end = sunday.toISOString().slice(0, 10)
  } else if (filters.preset === 'this-month') {
    params.start = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`
    params.end = today.toISOString().slice(0, 10)
  } else if (filters.preset === 'last-month') {
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
    const lastDay = new Date(today.getFullYear(), today.getMonth(), 0)
    params.start = lastMonth.toISOString().slice(0, 10)
    params.end = lastDay.toISOString().slice(0, 10)
  } else if (filters.preset === 'custom' && filters.customStart && filters.customEnd) {
    params.start = filters.customStart
    params.end = filters.customEnd
  }
  return params
}

async function fetchData() {
  loading.value = true
  try {
    const params = getDateParams()
    const [teamRes, trendsRes] = await Promise.all([
      workloadApi.team(params),
      efficiencyApi.trends(12),
    ])
    teamData.value = teamRes.data
    trends.value = trendsRes.data
  } catch (e) {
    console.error('Failed to fetch dashboard data', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
watch(() => [filters.department, filters.preset, filters.customStart, filters.customEnd], fetchData)
</script>

<template>
  <DashboardLayout>
    <div class="space-y-6">
      <!-- Filters bar -->
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <DepartmentFilter />
          <DateRangeFilter />
        </div>
        <div class="flex items-center gap-4">
          <ExportButtons />
          <SyncStatusBar @synced="fetchData" />
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <KPISummaryCards :data="teamData" />

      <!-- Charts row 1 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <WorkloadBarChart
          v-if="teamData?.member_workloads?.length"
          :workloads="teamData.member_workloads"
          :department="teamData?.department"
        />
        <TypePieChart
          v-if="teamData?.type_distribution && Object.keys(teamData.type_distribution).length"
          :distribution="teamData.type_distribution"
          title="工單類型分布"
        />
      </div>

      <!-- Charts row 2 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DistributionBarChart
          v-if="teamData?.client_distribution && Object.keys(teamData.client_distribution).length"
          :distribution="teamData.client_distribution"
          title="客戶分布"
          :topN="10"
          color="#ED7D31"
        />
        <TrendLineChart
          v-if="trends.length"
          :trends="trends"
          title="週工單量趨勢"
        />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-10">
        <span class="text-gray-400">載入中...</span>
      </div>
    </div>
  </DashboardLayout>
</template>
