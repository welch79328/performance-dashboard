<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { qualityApi, efficiencyApi } from '@/api'

import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import QualityTrendChart from '@/components/charts/QualityTrendChart.vue'
import DistributionBarChart from '@/components/charts/DistributionBarChart.vue'

const loading = ref(false)
const qualityData = ref<any>(null)
const bugRecurrence = ref<Record<string, number>>({})
const trends = ref<any[]>([])

async function fetchData() {
  loading.value = true
  try {
    const [qRes, brRes, tRes] = await Promise.all([
      qualityApi.overview(),
      qualityApi.bugRecurrence(),
      efficiencyApi.trends(12),
    ])
    qualityData.value = qRes.data
    bugRecurrence.value = brRes.data
    trends.value = tRes.data
  } catch (e) {
    console.error('Failed to fetch quality data', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)

const bugTotal = computed(() =>
  Object.values(bugRecurrence.value).reduce((a, b) => a + b, 0)
)

const changeDensityLevel = computed(() => {
  const d = qualityData.value?.change_density || 0
  if (d > 30) return { color: 'text-red-600', label: '偏高' }
  if (d > 15) return { color: 'text-orange-600', label: '正常' }
  return { color: 'text-green-600', label: '良好' }
})
</script>

<template>
  <DashboardLayout>
    <div class="space-y-6">
      <h2 class="text-xl font-bold">品質分析</h2>

      <!-- KPI cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4" v-if="qualityData">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold" :class="changeDensityLevel.color">
              {{ qualityData.change_density }}%
            </div>
            <div class="text-sm text-gray-500 mt-1">異動佔比</div>
            <div class="text-xs mt-0.5" :class="changeDensityLevel.color">{{ changeDensityLevel.label }}</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-red-600">{{ bugTotal }}</div>
            <div class="text-sm text-gray-500 mt-1">Bug 總數</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-red-500">{{ Object.keys(bugRecurrence).length }}</div>
            <div class="text-sm text-gray-500 mt-1">受影響客戶數</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">
              {{ trends.length ? trends[trends.length - 1]?.bug_count || 0 : 0 }}
            </div>
            <div class="text-sm text-gray-500 mt-1">本週新增 Bug</div>
          </div>
        </el-card>
      </div>

      <!-- Quality trend chart -->
      <QualityTrendChart
        v-if="trends.length && qualityData?.change_density_trend"
        :trends="trends"
        :changeDensityTrend="qualityData.change_density_trend"
      />

      <!-- Bug recurrence -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DistributionBarChart
          v-if="Object.keys(bugRecurrence).length"
          :distribution="bugRecurrence"
          title="Bug 回流"
          :topN="10"
          color="#FF6B6B"
        />

        <el-card shadow="hover">
          <template #header>
            <div>
              <span class="font-semibold">Bug 回流明細</span>
              <p class="text-xs text-gray-400 mt-1">同一客戶重複出現 Bug 的次數，越多代表該客戶功能品質需關注</p>
            </div>
          </template>
          <el-table
            :data="Object.entries(bugRecurrence).map(([client, count]) => ({ client, count }))"
            stripe size="small" max-height="350"
          >
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="client" label="客戶" />
            <el-table-column prop="count" label="Bug 數" width="100" sortable>
              <template #default="{ row }">
                <el-tag :type="row.count > 10 ? 'danger' : row.count > 5 ? 'warning' : 'info'" size="small">
                  {{ row.count }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>
  </DashboardLayout>
</template>
