import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ErrorBoundary from './ErrorBoundary'
import { MemoryRouter } from 'react-router-dom'

// Create a component that explicitly throws an error
const BuggyComponent = () => {
    throw new Error('Test boundary error')
}

describe('ErrorBoundary', () => {
    it('catches errors and displays a fallback UI', () => {
        // Suppress console.error in tests for the intentional error
        vi.spyOn(console, 'error').mockImplementation(() => {})

        render(
            <MemoryRouter>
                <ErrorBoundary>
                    <BuggyComponent />
                </ErrorBoundary>
            </MemoryRouter>
        )

        expect(screen.getByText('Something went wrong.')).toBeInTheDocument()
        expect(screen.queryByText('Test boundary error')).not.toBeInTheDocument()
        
        console.error.mockRestore()
    })

    it('renders children normally when no error occurs', () => {
        render(
            <ErrorBoundary>
                <div>All good here</div>
            </ErrorBoundary>
        )

        expect(screen.getByText('All good here')).toBeInTheDocument()
    })
})
