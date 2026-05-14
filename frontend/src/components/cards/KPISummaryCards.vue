<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: Record<string, any> | null
}>()

const isMarketing = computed(() => props.data?.department === 'marketing')
</script>

<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4" v-if="data">
    <el-card shadow="hover">
      <div class="text-center">
        <div class="text-2xl font-bold text-blue-600">{{ data.total_tasks }}</div>
        <div class="text-sm text-gray-500 mt-1">{{ isMarketing ? '內容總數' : '總工單量' }}</div>
      </div>
    </el-card>
    <el-card shadow="hover">
      <div class="text-center">
        <div class="text-2xl font-bold text-green-600">{{ data.close_rate }}%</div>
        <div class="text-sm text-gray-500 mt-1">{{ isMarketing ? '完成率' : '結案率' }}</div>
      </div>
    </el-card>
    <el-card shadow="hover" v-if="!isMarketing">
      <div class="text-center">
        <div class="text-2xl font-bold text-orange-600">{{ data.avg_processing_days }}</div>
        <div class="text-sm text-gray-500 mt-1">平均結案天數</div>
      </div>
    </el-card>
    <el-card shadow="hover" v-if="isMarketing">
      <div class="text-center">
        <div class="text-2xl font-bold text-orange-600">{{ data.completed_tasks }}</div>
        <div class="text-sm text-gray-500 mt-1">已完成</div>
      </div>
    </el-card>
    <el-card shadow="hover">
      <div class="text-center">
        <div class="text-2xl font-bold text-red-500">{{ data.in_progress_tasks }}</div>
        <div class="text-sm text-gray-500 mt-1">{{ isMarketing ? '排程中' : '未結案量' }}</div>
      </div>
    </el-card>
  </div>
</template>
