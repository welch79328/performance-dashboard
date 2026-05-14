<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { efficiencyApi } from '@/api'

import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import EfficiencyBarChart from '@/components/charts/EfficiencyBarChart.vue'
import StageStackChart from '@/components/charts/StageStackChart.vue'
import TrendLineChart from '@/components/charts/TrendLineChart.vue'
import StalledTable from '@/components/tables/StalledTable.vue'

const loading = ref(false)
const efficiency = ref<any>(null)
const byType = ref<any[]>([])
const stalled = ref<any[]>([])
const trends = ref<any[]>([])

async function fetchData() {
  loading.value = true
  try {
    const [overviewRes, stalledRes, trendsRes] = await Promise.all([
      efficiencyApi.overview(),
      efficiencyApi.stalled(),
      efficiencyApi.trends(12),
    ])
    efficiency.value = overviewRes.data.efficiency
    byType.value = overviewRes.data.by_type
    stalled.value = stalledRes.data
    trends.value = trendsRes.data
  } catch (e) {
    console.error('Failed to fetch efficiency data', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <DashboardLayout>
    <div class="space-y-6">
      <h2 class="text-xl font-bold">流程效率分析</h2>

      <!-- KPI summary -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4" v-if="efficiency">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">{{ efficiency.avg_total_days }}</div>
            <div class="text-xs text-gray-500">平均結案天數</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-600">{{ efficiency.avg_dev_days }}</div>
            <div class="text-xs text-gray-500">開發耗時</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600">{{ efficiency.avg_test_days }}</div>
            <div class="text-xs text-gray-500">測試耗時</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600">{{ efficiency.close_rate }}%</div>
            <div class="text-xs text-gray-500">結案率</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-red-500">{{ efficiency.stalled_rate }}%</div>
            <div class="text-xs text-gray-500">卡關率</div>
          </div>
        </el-card>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <EfficiencyBarChart v-if="byType.length" :byType="byType" />
        <StageStackChart v-if="byType.length" :byType="byType" />
      </div>

      <!-- Trend -->
      <TrendLineChart v-if="trends.length" :trends="trends" title="結案率週趨勢" />

      <!-- Stalled orders -->
      <StalledTable :orders="stalled" />
    </div>
  </DashboardLayout>
</template>
