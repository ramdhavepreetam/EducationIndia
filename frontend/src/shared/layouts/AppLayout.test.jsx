import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import AppLayout from './AppLayout'

// Mock the auth store and payment store
vi.mock('@/modules/auth', () => ({
    useAuthStore: vi.fn((selector) => {
        const state = {
            user: { full_name: 'Test User', role: 'student' },
            logout: vi.fn(),
        }
        return selector(state)
    })
}))

vi.mock('@/modules/payment', () => ({
    usePaymentStore: vi.fn(() => ({ loadStatus: vi.fn() })),
    SubscriptionStatus: () => <div data-testid="sub-status">Sub Status</div>
}))

vi.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key, def) => def || key,
    }),
}))

describe('AppLayout mobile sidebar', () => {
    it('toggles mobile sidebar when hamburger is clicked', () => {
        render(
            <MemoryRouter>
                <AppLayout />
            </MemoryRouter>
        )

        // It should have a hamburger button for mobile
        const hamburgerBtn = screen.getByLabelText(/open menu/i)
        expect(hamburgerBtn).toBeInTheDocument()

        // Clicking the hamburger button should open the sidebar
        fireEvent.click(hamburgerBtn)
        
        // We expect the overlay to appear
        const overlay = screen.getByTestId('mobile-overlay')
        expect(overlay).toBeInTheDocument()

        // Clicking overlay should close the sidebar
        fireEvent.click(overlay)
        
        // Overlay should disappear (or get hidden class depending on impl)
        // So we can check if overlay is not visible or doesn't exist
        // Best practice is either removing from DOM or adding a hidden class
    })
})
