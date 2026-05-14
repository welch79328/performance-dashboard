<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { workloadApi, efficiencyApi } from '@/api'

import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import TrendLineChart from '@/components/charts/TrendLineChart.vue'
import TypePieChart from '@/components/charts/TypePieChart.vue'
import DistributionBarChart from '@/components/charts/DistributionBarChart.vue'
import WorkOrderTable from '@/components/tables/WorkOrderTable.vue'

const route = useRoute()
const loading = ref(false)
const department = ref('')
const workload = ref<any>(null)
const orders = ref<any[]>([])
const trends = ref<any[]>([])

const memberName = () => decodeURIComponent(route.params.name as string)
const isMarketing = computed(() => department.value === 'marketing')

async function fetchData() {
  loading.value = true
  try {
    const [memberRes, trendsRes] = await Promise.all([
      workloadApi.member(memberName()),
      efficiencyApi.trends(12),
    ])
    department.value = memberRes.data.department || 'pm_rd'
    workload.value = memberRes.data.workload
    orders.value = memberRes.data.orders
    trends.value = trendsRes.data
  } catch (e) {
    console.error('Failed to fetch member data', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
watch(() => route.params.name, fetchData)

function typeDistribution() {
  const dist: Record<string, number> = {}
  for (const o of orders.value) {
    const key = isMarketing.value ? (o.content_type || '未指定') : (o.type || '未指定')
    dist[key] = (dist[key] || 0) + 1
  }
  return dist
}

function platformDistribution() {
  const dist: Record<string, number> = {}
  for (const o of orders.value) {
    const key = o.group_name || '未指定'
    dist[key] = (dist[key] || 0) + 1
  }
  return dist
}
</script>

<template>
  <DashboardLayout>
    <div class="space-y-6">
      <h2 class="text-xl font-bold">
        {{ memberName() }} 的績效
        <el-tag size="small" class="ml-2" :type="isMarketing ? 'warning' : 'primary'">
          {{ isMarketing ? '行銷' : 'PM+RD' }}
        </el-tag>
      </h2>

      <!-- PM+RD KPI cards -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4" v-if="workload && !isMarketing">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">{{ workload.unique_count }}</div>
            <div class="text-xs text-gray-500">實際工單數</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-purple-600">{{ workload.pm_count }}</div>
            <div class="text-xs text-gray-500">PM 參與</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-600">{{ workload.dev_count }}</div>
            <div class="text-xs text-gray-500">開發參與</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600">{{ workload.test_count }}</div>
            <div class="text-xs text-gray-500">測試參與</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-red-500">{{ workload.in_progress_count }}</div>
            <div class="text-xs text-gray-500">在手量</div>
          </div>
        </el-card>
      </div>

      <!-- Marketing KPI cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4" v-if="workload && isMarketing">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">{{ workload.content_count }}</div>
            <div class="text-xs text-gray-500">內容產出量</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600">{{ workload.posts_per_week }}</div>
            <div class="text-xs text-gray-500">篇/週</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-600">{{ workload.cross_platform_count }}</div>
            <div class="text-xs text-gray-500">跨平台發佈</div>
          </div>
        </el-card>
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-2xl font-bold text-purple-600">{{ workload.scheduled_count }}</div>
            <div class="text-xs text-gray-500">排程前瞻</div>
          </div>
        </el-card>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- PM+RD: type pie -->
        <TypePieChart
          v-if="!isMarketing && orders.length"
          :distribution="typeDistribution()"
          title="工單類型分布"
        />
        <!-- Marketing: content type pie -->
        <TypePieChart
          v-if="isMarketing && orders.length"
          :distribution="typeDistribution()"
          title="內容類型分布"
        />
        <!-- Marketing: platform bar -->
        <DistributionBarChart
          v-if="isMarketing && orders.length"
          :distribution="platformDistribution()"
          title="平台分布"
          :topN="10"
          color="#4472C4"
        />
        <!-- Trend (PM+RD only, marketing doesn't have weekly trend by person yet) -->
        <TrendLineChart
          v-if="!isMarketing && trends.length"
          :trends="trends"
          title="近 12 週趨勢"
        />
      </div>

      <!-- Work order detail table (PM+RD) -->
      <WorkOrderTable v-if="!isMarketing && orders.length" :orders="orders" />

      <!-- Campaign detail table (Marketing) -->
      <el-card shadow="hover" v-if="isMarketing && orders.length">
        <template #header><span class="font-semibold">內容明細</span></template>
        <el-table :data="orders" stripe size="small" max-height="500"
                  :default-sort="{ prop: 'publish_date', order: 'descending' }">
          <el-table-column prop="name" label="名稱" min-width="200" />
          <el-table-column prop="content_type" label="類型" width="120" />
          <el-table-column prop="group_name" label="平台" width="160" />
          <el-table-column prop="publish_date" label="發佈日期" width="120" sortable />
          <el-table-column prop="completion_status" label="狀態" width="100">
            <template #default="{ row }">
              <el-tag :type="row.completion_status === 'Completed' ? 'success' : 'warning'" size="small">
                {{ row.completion_status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="material_completeness" label="素材完備" width="100">
            <template #default="{ row }">
              {{ row.material_completeness }}%
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Empty state -->
      <el-empty v-if="!loading && !orders.length" description="無績效資料" />

      <div v-if="loading" class="flex justify-center py-10">
        <span class="text-gray-400">載入中...</span>
      </div>
    </div>
  </DashboardLayout>
</template>
