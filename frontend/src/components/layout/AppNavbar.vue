<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const tabs = [
  { label: '總覽', path: '/dashboard' },
  { label: '效率', path: '/dashboard/efficiency' },
  { label: '排程', path: '/dashboard/schedule' },
  { label: '品質', path: '/dashboard/quality' },
]

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-6">
      <h1 class="text-lg font-bold text-gray-800">績效管理平台</h1>
      <el-tabs :model-value="route.path" @tab-change="(p: string) => router.push(p)" class="navbar-tabs">
        <el-tab-pane v-for="tab in tabs" :key="tab.path" :label="tab.label" :name="tab.path" />
      </el-tabs>
    </div>
    <div class="flex items-center gap-4">
      <span class="text-sm text-gray-600">{{ auth.user?.name }}</span>
      <el-button size="small" @click="handleLogout">登出</el-button>
    </div>
  </div>
</template>

<style scoped>
.navbar-tabs :deep(.el-tabs__header) {
  margin: 0;
}
.navbar-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}
</style>
