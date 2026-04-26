import { useEffect, useRef, useCallback } from 'react'
import { attemptApi } from '../api/attemptApi'
import { useAttemptStore } from '../store/attemptStore'

export function useAutoSave() {
    const setSavingState = useAttemptStore(s => s.setSavingState)
    const currentAttempt = useAttemptStore(s => s.currentAttempt)

    // Keep track of pending saves in case of network drops
    const pendingSaves = useRef(new Map())
    const timeoutRef = useRef(null)
    const isSaving = useRef(false)

    const processQueue = useCallback(async () => {
        if (pendingSaves.current.size === 0 || isSaving.current || !currentAttempt?.attempt_id) {
            return
        }

        isSaving.current = true
        setSavingState(true)

        // Snapshot current queue
        const savesToProcess = new Map(pendingSaves.current)
        pendingSaves.current.clear()

        try {
            // Process sequentially to avoid overlapping DB writes on the backend
            // (Our backend handles ON CONFLICT DO UPDATE, but ordering matters for visit count / last saved at)
            for (const [key, payload] of savesToProcess.entries()) {
                await attemptApi.saveResponse(
                    currentAttempt.attempt_id,
                    payload.questionId,
                    payload.questionNo,
                    payload.selectedOption,
                    payload.selectedOptions,
                    payload.isMarkedReview,
                    payload.timeTakenSeconds
                )
            }
        } catch (err) {
            console.error('Autosave failed. Re-queuing...', err)
            // Re-queue failed items (new items might have been added while we were saving)
            for (const [key, payload] of savesToProcess.entries()) {
                if (!pendingSaves.current.has(key)) {
                    pendingSaves.current.set(key, payload)
                }
            }
        } finally {
            isSaving.current = false
            setSavingState(false)

            // If new items were added while we saved, process again
            if (pendingSaves.current.size > 0) {
                timeoutRef.current = setTimeout(processQueue, 1000)
            }
        }
    }, [currentAttempt, setSavingState])

    const scheduleSave = useCallback((questionNo, questionId, selectedOption, selectedOptions, isMarkedReview, timeTaken = 0) => {
        // Debounce mechanism: overwrite the payload for this question if it already exists in the queue
        pendingSaves.current.set(questionNo, {
            questionNo,
            questionId,
            selectedOption,
            selectedOptions,
            isMarkedReview,
            timeTakenSeconds: timeTaken
        })

        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current)
        }

        // Wait 500ms before sending to allow for rapid clicks
        timeoutRef.current = setTimeout(processQueue, 500)
    }, [processQueue])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current)
            }
            // If there's unfinished saves on unmount, attempt them (best effort fire-and-forget)
            if (pendingSaves.current.size > 0 && currentAttempt?.attempt_id) {
                processQueue()
            }
        }
    }, [processQueue, currentAttempt])

    return { scheduleSave }
}
