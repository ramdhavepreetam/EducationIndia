import { describe, it, expect, vi } from 'vitest'
import { paymentApi } from './paymentApi'
import apiClient from '@/config/apiClient'

// Mock the apiClient
vi.mock('@/config/apiClient', () => {
  return {
    default: {
      get: vi.fn().mockResolvedValue({ data: { active: true } }),
      post: vi.fn().mockResolvedValue({ data: {} })
    }
  }
})

describe('paymentApi', () => {
  it('getStatus calls /api/payment/status', async () => {
    await paymentApi.getStatus()
    expect(apiClient.get).toHaveBeenCalledWith('/api/payment/status')
  })
})
