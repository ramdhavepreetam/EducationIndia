/**
 * User module API — FastAPI calls for profile management.
 *
 * ADR-010: All API calls go through apiClient (JWT auto-attached).
 * ADR-003: X-Language header auto-set by apiClient interceptor.
 */
import apiClient from '@/config/apiClient'

export const userApi = {
  getMe: () =>
    apiClient.get('/api/users/me').then(r => r.data),

  updateMe: (data) =>
    apiClient.put('/api/users/me', data).then(r => r.data),

  uploadAvatar: (file) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post('/api/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data)
  },

  changePassword: (data) =>
    apiClient.post('/api/users/me/change-password', data).then(r => r.data),
}
