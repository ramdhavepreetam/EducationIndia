import { useEffect, useRef } from 'react'
import { useAttemptStore } from '../store/attemptStore'

export function useExamTimer() {
    const timeRemaining = useAttemptStore(s => s.timeRemaining)
    const isWarning = timeRemaining !== null && timeRemaining <= 300 // < 5 minutes
    const isUrgent = timeRemaining !== null && timeRemaining <= 60   // < 1 minute

    useEffect(() => {
        const currentStore = useAttemptStore.getState()
        if (currentStore.timeRemaining === null || currentStore.isSubmitting) {
            return
        }

        const interval = setInterval(() => {
            const state = useAttemptStore.getState()
            if (state.isSubmitting) {
                clearInterval(interval)
                return
            }

            const newTime = state.timeRemaining - 1
            if (newTime <= 0) {
                clearInterval(interval)
                state.setTimeRemaining(0)
                state.autoExpire() // Trigger server-side submission
            } else {
                state.setTimeRemaining(newTime)
            }
        }, 1000)

        // Cleanup
        return () => clearInterval(interval)
    }, []) // Empty deps so it sets up once and uses getState() inside

    return { timeRemaining, isWarning, isUrgent }
}
