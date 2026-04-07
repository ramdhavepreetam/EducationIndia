import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { UpgradePrompt } from './UpgradePrompt'
import { usePaymentStore } from '@/modules/payment/store/paymentStore'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key, defaultValue) => defaultValue
  })
}))

// Mock the store
vi.mock('@/modules/payment/store/paymentStore', () => ({
  usePaymentStore: vi.fn()
}))

describe('UpgradePrompt', () => {
  const mockLoadPlan = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
    usePaymentStore.mockImplementation((selector) => {
      // Return mocked state based on the selector
      return selector({
        plan: { price_inr: 499 },
        loadPlan: mockLoadPlan
      })
    })
  })

  it('renders correctly and loads plan from payment store', () => {
    render(
      <MemoryRouter>
        <UpgradePrompt reason="upgrade_required_exam" />
      </MemoryRouter>
    )

    // Check if the title is rendered
    expect(screen.getByText('Full Access Required')).toBeInTheDocument()
    
    // Check if the price is rendered based on the store's mock plan
    expect(screen.getByRole('button')).toHaveTextContent('Unlock Full Access — ₹499')
    
    // It should have either loaded the plan, or read the existing one
    // We expect usePaymentStore to have been called.
    expect(usePaymentStore).toHaveBeenCalled()
  })
  
  it('calls loadPlan if plan is null', () => {
    usePaymentStore.mockImplementation((selector) => {
      return selector({
        plan: null,
        loadPlan: mockLoadPlan
      })
    })
    
    render(
      <MemoryRouter>
        <UpgradePrompt reason="upgrade_required_exam" />
      </MemoryRouter>
    )
    
    expect(mockLoadPlan).toHaveBeenCalled()
  })
})
