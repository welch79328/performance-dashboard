<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { syncApi } from '@/api'

const lastSync = ref<string | null>(null)
const syncing = ref(false)

onMounted(async () => {
  try {
    const { data } = await syncApi.status()
    lastSync.value = data.last_sync_time
  } catch { /* ignore */ }
})

async function triggerSync() {
  syncing.value = true
  try {
    const { data } = await syncApi.trigger()
    lastSync.value = data.last_sync_time
  } finally {
    syncing.value = false
  }
}

const emit = defineEmits<{ synced: [] }>()

async function handleSync() {
  await triggerSync()
  emit('synced')
}
</script>

<template>
  <div class="flex items-center gap-3 text-sm text-gray-500">
    <span v-if="lastSync">最後同步：{{ new Date(lastSync).toLocaleString('zh-TW') }}</span>
    <span v-else>尚未同步</span>
    <el-button size="small" :loading="syncing" @click="handleSync">立即同步</el-button>
  </div>
</template>
