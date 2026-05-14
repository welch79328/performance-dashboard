import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
}

export const workloadApi = {
  team: (params?: { department?: string; start?: string; end?: string }) =>
    api.get('/workload/team', { params }),
  member: (name: string) => api.get(`/workload/member/${name}`),
}

export const efficiencyApi = {
  overview: () => api.get('/efficiency/overview'),
  stalled: () => api.get('/efficiency/stalled'),
  trends: (weeks = 12) => api.get('/efficiency/trends', { params: { weeks } }),
}

export const scheduleApi = {
  gantt: () => api.get('/schedule/gantt'),
  heatmapPerson: () => api.get('/schedule/heatmap/person'),
  heatmapClient: () => api.get('/schedule/heatmap/client'),
  aging: () => api.get('/schedule/aging'),
  calendar: () => api.get('/schedule/calendar'),
}

export const qualityApi = {
  overview: () => api.get('/quality/overview'),
  bugRecurrence: () => api.get('/quality/bug-recurrence'),
}

export const syncApi = {
  trigger: () => api.post('/sync'),
  status: () => api.get('/sync/status'),
}

export const usersApi = {
  list: () => api.get('/users'),
}

export const exportApi = {
  weekly: () => api.get('/export/weekly', { responseType: 'blob' }),
  monthly: () => api.get('/export/monthly', { responseType: 'blob' }),
}

export default api
