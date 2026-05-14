<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.value.email, form.value.password)
    router.push('/dashboard')
  } catch {
    error.value = '帳號或密碼錯誤'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-100">
    <el-card class="w-96">
      <template #header>
        <h2 class="text-xl font-bold text-center">績效管理平台</h2>
      </template>
      <el-form @submit.prevent="handleLogin" label-position="top">
        <el-form-item label="Email">
          <el-input v-model="form.email" type="email" placeholder="請輸入 Email" />
        </el-form-item>
        <el-form-item label="密碼">
          <el-input v-model="form.password" type="password" placeholder="請輸入密碼" show-password />
        </el-form-item>
        <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb-4" />
        <el-button type="primary" :loading="loading" @click="handleLogin" class="w-full">
          登入
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>
