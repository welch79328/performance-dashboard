import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
    },
    {
      path: '/dashboard/efficiency',
      name: 'efficiency',
      component: () => import('../views/EfficiencyView.vue'),
    },
    {
      path: '/dashboard/schedule',
      name: 'schedule',
      component: () => import('../views/ScheduleView.vue'),
    },
    {
      path: '/dashboard/quality',
      name: 'quality',
      component: () => import('../views/QualityView.vue'),
    },
    {
      path: '/dashboard/member/:name',
      name: 'member',
      component: () => import('../views/MemberView.vue'),
    },
  ],
})

// Navigation guard
router.beforeEach((to) => {
  if (to.name !== 'login' && !localStorage.getItem('token')) {
    return { name: 'login' }
  }
})

export default router
