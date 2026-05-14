<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import AppNavbar from './AppNavbar.vue'
import MemberSidebar from './MemberSidebar.vue'

const route = useRoute()

const showSidebar = computed(() => {
  const path = route.path
  return path === '/dashboard' || path.startsWith('/dashboard/member')
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppNavbar />
    <div class="flex flex-1 overflow-hidden">
      <MemberSidebar v-if="showSidebar" />
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
