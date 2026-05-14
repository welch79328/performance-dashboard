<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { scheduleApi } from '@/api'

import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import GanttChart from '@/components/charts/GanttChart.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import AgingTable from '@/components/tables/AgingTable.vue'
import CalendarView from '@/components/charts/CalendarView.vue'

const loading = ref(false)
const ganttItems = ref<any[]>([])
const personHeatmap = ref<any[]>([])
const clientHeatmap = ref<any[]>([])
const agingOrders = ref<any[]>([])
const campaigns = ref<any[]>([])

const activeTab = ref('pm_rd')
const heatmapDimension = ref<'person' | 'client'>('person')
const ganttFilter = ref<'recent' | 'open' | 'all'>('open')

async function fetchData() {
  loading.value = true
  try {
    const [ganttRes, personRes, clientRes, agingRes, calRes] = await Promise.all([
      scheduleApi.gantt(),
      scheduleApi.heatmapPerson(),
      scheduleApi.heatmapClient(),
      scheduleApi.aging(),
      scheduleApi.calendar(),
    ])
    ganttItems.value = ganttRes.data
    personHeatmap.value = personRes.data
    clientHeatmap.value = clientRes.data
    agingOrders.value = agingRes.data
    campaigns.value = calRes.data
  } catch (e) {
    console.error('Failed to fetch schedule data', e)
  } finally {
    loading.value = false
  }
}

const filteredGantt = computed(() => {
  if (ganttFilter.value === 'open') {
    return ganttItems.value.filter((i) => !i.end_date)
  }
  if (ganttFilter.value === 'recent') {
    const cutoff = new Date()
    cutoff.setDate(cutoff.getDate() - 30)
    const cutoffStr = cutoff.toISOString().slice(0, 10)
    return ganttItems.value.filter((i) => i.start_date >= cutoffStr)
  }
  return ganttItems.value
})

const agingSummary = computed(() => {
  const red = agingOrders.value.filter((o) => o.severity === 'red').length
  const yellow = agingOrders.value.filter((o) => o.severity === 'yellow').length
  const green = agingOrders.value.filter((o) => o.severity === 'green').length
  return { red, yellow, green, total: agingOrders.value.length }
})

// Marketing stats
const marketingSummary = computed(() => {
  const total = campaigns.value.length
  const completed = campaigns.value.filter((c) => c.completion_status === 'Completed').length
  const scheduled = campaigns.value.filter((c) => c.completion_status === 'Scheduled').length
  return { total, completed, scheduled }
})

const sortedCampaigns = computed(() => {
  return [...campaigns.value]
    .filter((c) => c.publish_date)
    .sort((a, b) => (b.publish_date || '').localeCompare(a.publish_date || ''))
})

onMounted(fetchData)
</script>

<template>
  <DashboardLayout>
    <div class="space-y-6">
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-bold">專案排程</h2>
        <el-radio-group v-model="activeTab" size="default">
          <el-radio-button value="pm_rd">PM + RD</el-radio-button>
          <el-radio-button value="marketing">行銷</el-radio-button>
        </el-radio-group>
      </div>

      <!-- ==================== PM+RD Tab ==================== -->
      <template v-if="activeTab === 'pm_rd'">
        <!-- Aging summary cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <el-card shadow="hover">
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-600">{{ agingSummary.total }}</div>
              <div class="text-sm text-gray-500">未結案工單</div>
            </div>
          </el-card>
          <el-card shadow="hover">
            <div class="text-center">
              <div class="text-2xl font-bold text-red-600">{{ agingSummary.red }}</div>
              <div class="text-sm text-gray-500">超時（>7天）</div>
            </div>
          </el-card>
          <el-card shadow="hover">
            <div class="text-center">
              <div class="text-2xl font-bold text-yellow-600">{{ agingSummary.yellow }}</div>
              <div class="text-sm text-gray-500">注意（4-7天）</div>
            </div>
          </el-card>
          <el-card shadow="hover">
            <div class="text-center">
              <div class="text-2xl font-bold text-green-600">{{ agingSummary.green }}</div>
              <div class="text-sm text-gray-500">正常（≤3天）</div>
            </div>
          </el-card>
        </div>

        <!-- Gantt chart -->
        <div>
          <div class="flex items-center gap-4 mb-2">
            <span class="text-sm text-gray-600 font-medium">工單時間軸</span>
            <el-radio-group v-model="ganttFilter" size="small">
              <el-radio-button value="open">未結案</el-radio-button>
              <el-radio-button value="recent">近 30 天</el-radio-button>
              <el-radio-button value="all">全部</el-radio-button>
            </el-radio-group>
            <span class="text-xs text-gray-400">共 {{ filteredGantt.length }} 筆</span>
          </div>
          <GanttChart v-if="filteredGantt.length" :items="filteredGantt" />
          <el-empty v-else description="無符合條件的工單" />
        </div>

        <!-- Heatmap -->
        <div>
          <div class="flex items-center gap-4 mb-2">
            <span class="text-sm text-gray-600 font-medium">排程密度</span>
            <el-radio-group v-model="heatmapDimension" size="small">
              <el-radio-button value="person">人員 × 週</el-radio-button>
              <el-radio-button value="client">客戶 × 週</el-radio-button>
            </el-radio-group>
          </div>
          <HeatmapChart
            v-if="heatmapDimension === 'person' && personHeatmap.length"
            :cells="personHeatmap"
            title="人員每週工單量（顏色越深越忙）"
          />
          <HeatmapChart
            v-if="heatmapDimension === 'client' && clientHeatmap.length"
            :cells="clientHeatmap"
            title="客戶每週工單量（顏色越深需求越多）"
          />
        </div>

        <!-- Aging table -->
        <AgingTable :orders="agingOrders" />
      </template>

      <!-- ==================== Marketing Tab ==================== -->
      <template v-if="activeTab === 'marketing'">
        <!-- Summary cards -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <el-card shadow="hover">
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-600">{{ marketingSummary.total }}</div>
              <div class="text-sm text-gray-500">內容總數</div>
            </div>
          </el-card>
          <el-card shadow="hover">
            <div class="text-center">
              <div class="text-2xl font-bold text-green-600">{{ marketingSummary.completed }}</div>
              <div class="text-sm text-gray-500">已完成</div>
            </div>
          </el-card>
          <el-card shadow="hover">
            <div class="text-center">
              <div class="text-2xl font-bold text-orange-600">{{ marketingSummary.scheduled }}</div>
              <div class="text-sm text-gray-500">排程中</div>
            </div>
          </el-card>
        </div>

        <!-- Calendar heatmap -->
        <CalendarView :campaigns="campaigns" />

        <!-- Content schedule table -->
        <el-card shadow="hover">
          <template #header><span class="font-semibold">內容排程明細</span></template>
          <el-table :data="sortedCampaigns" stripe size="small" max-height="500">
            <el-table-column prop="publish_date" label="發佈日期" width="110" sortable />
            <el-table-column prop="name" label="內容名稱" min-width="200" />
            <el-table-column prop="group_name" label="平台" width="160" />
            <el-table-column prop="content_type" label="類型" width="120" />
            <el-table-column prop="owner" label="負責人" width="80" />
            <el-table-column prop="completion_status" label="狀態" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="row.completion_status === 'Completed' ? 'success' : row.completion_status === 'Scheduled' ? 'warning' : 'info'"
                  size="small"
                >
                  {{ row.completion_status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>
    </div>
  </DashboardLayout>
</template>
