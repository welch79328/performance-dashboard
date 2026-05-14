<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usersApi } from '@/api'

const router = useRouter()
const route = useRoute()
const users = ref<{ id: string; name: string; email: string; department: string }[]>([])
const collapsed = ref(false)

onMounted(async () => {
  try {
    const { data } = await usersApi.list()
    users.value = data
  } catch { /* empty */ }
})

const pmRdUsers = computed(() => users.value.filter((u) => u.department === 'pm_rd'))
const marketingUsers = computed(() => users.value.filter((u) => u.department === 'marketing'))

function goToMember(name: string) {
  router.push(`/dashboard/member/${encodeURIComponent(name)}`)
}

function isActive(name: string) {
  return decodeURIComponent(route.params.name as string || '') === name
}
</script>

<template>
  <!-- Collapsed toggle button (always visible) -->
  <div class="relative flex">
    <!-- Sidebar -->
    <transition name="slide">
      <div
        v-show="!collapsed"
        class="w-56 min-w-[14rem] border-r border-gray-200 bg-white/80 backdrop-blur overflow-y-auto"
        style="max-height: calc(100vh - 56px)"
      >
        <div class="p-4 pt-3">
          <!-- Header -->
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">團隊成員</span>
            <button
              @click="collapsed = true"
              class="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
          </div>

          <!-- PM+RD Section -->
          <div class="mb-4">
            <div class="flex items-center gap-2 mb-2 px-2">
              <span class="w-2 h-2 rounded-full bg-blue-500"></span>
              <span class="text-xs font-semibold text-gray-500">PM + RD</span>
              <span class="text-[10px] text-gray-300 ml-auto">{{ pmRdUsers.length }}</span>
            </div>
            <div class="space-y-0.5">
              <div
                v-for="user in pmRdUsers"
                :key="user.id"
                @click="goToMember(user.name)"
                class="group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-150"
                :class="isActive(user.name)
                  ? 'bg-blue-50 text-blue-700 font-medium shadow-sm'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
              >
                <span
                  class="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold text-white shrink-0"
                  :class="isActive(user.name) ? 'bg-blue-500' : 'bg-gray-300 group-hover:bg-blue-400'"
                >
                  {{ user.name.charAt(0) }}
                </span>
                <span class="text-sm truncate">{{ user.name }}</span>
              </div>
            </div>
          </div>

          <!-- Divider -->
          <div class="border-t border-gray-100 my-3"></div>

          <!-- Marketing Section -->
          <div>
            <div class="flex items-center gap-2 mb-2 px-2">
              <span class="w-2 h-2 rounded-full bg-orange-500"></span>
              <span class="text-xs font-semibold text-gray-500">行銷</span>
              <span class="text-[10px] text-gray-300 ml-auto">{{ marketingUsers.length }}</span>
            </div>
            <div class="space-y-0.5">
              <div
                v-for="user in marketingUsers"
                :key="user.id"
                @click="goToMember(user.name)"
                class="group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-150"
                :class="isActive(user.name)
                  ? 'bg-orange-50 text-orange-700 font-medium shadow-sm'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
              >
                <span
                  class="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold text-white shrink-0"
                  :class="isActive(user.name) ? 'bg-orange-500' : 'bg-gray-300 group-hover:bg-orange-400'"
                >
                  {{ user.name.charAt(0) }}
                </span>
                <span class="text-sm truncate">{{ user.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Collapsed expand button -->
    <button
      v-if="collapsed"
      @click="collapsed = false"
      class="w-8 flex flex-col items-center justify-center gap-1 border-r border-gray-200 bg-white hover:bg-gray-50 text-gray-400 hover:text-gray-600 transition cursor-pointer"
      style="min-height: calc(100vh - 56px)"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
      <span class="text-[10px] writing-vertical" style="writing-mode: vertical-rl">成員</span>
    </button>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  width: 0;
  min-width: 0;
  opacity: 0;
}
</style>
