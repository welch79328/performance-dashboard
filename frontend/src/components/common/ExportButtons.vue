<script setup lang="ts">
import { ref } from 'vue'
import { exportApi } from '@/api'

const exporting = ref(false)

async function download(type: 'weekly' | 'monthly') {
  exporting.value = true
  try {
    const { data } = type === 'weekly' ? await exportApi.weekly() : await exportApi.monthly()
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${type}_report.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="flex gap-2">
    <el-button size="small" :loading="exporting" @click="download('weekly')">匯出週報</el-button>
    <el-button size="small" :loading="exporting" @click="download('monthly')">匯出月報</el-button>
  </div>
</template>
