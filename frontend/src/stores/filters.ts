import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type Department = 'all' | 'pm_rd' | 'marketing'
export type Preset = 'this-week' | 'this-month' | 'last-month' | 'custom'

export const useFiltersStore = defineStore('filters', () => {
  const department = ref<Department>(
    (localStorage.getItem('filter_department') as Department) || 'pm_rd',
  )
  const preset = ref<Preset>(
    (localStorage.getItem('filter_preset') as Preset) || 'this-month',
  )
  const customStart = ref(localStorage.getItem('filter_start') || '')
  const customEnd = ref(localStorage.getItem('filter_end') || '')

  watch(department, (v) => localStorage.setItem('filter_department', v))
  watch(preset, (v) => localStorage.setItem('filter_preset', v))
  watch(customStart, (v) => localStorage.setItem('filter_start', v))
  watch(customEnd, (v) => localStorage.setItem('filter_end', v))

  function getQueryParams() {
    const params: Record<string, string> = { department: department.value }
    if (preset.value === 'custom' && customStart.value && customEnd.value) {
      params.start = customStart.value
      params.end = customEnd.value
    }
    return params
  }

  return { department, preset, customStart, customEnd, getQueryParams }
})
