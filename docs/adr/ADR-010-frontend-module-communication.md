# ADR-010: Frontend Module Communication

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** All frontend modules

---

## Context

The frontend mirrors the backend vertical slice structure with 7 modules.
Modules need to share state (auth token needed by all API calls, attempt state
needed by timer + palette + question card simultaneously) and communicate events
(exam submitted → navigate to result page). Without a clear communication
contract, frontend modules will import each other's internals, creating the
same dependency tangle the vertical slice architecture is designed to prevent.

---

## Decision

We will use Zustand stores as the communication layer between frontend modules.
Each module owns one store. Cross-module state sharing happens through stores,
never through direct component imports. The Axios API client is a shared
singleton that reads from authStore for the JWT token. Module exports are
controlled through index.js — only pages, stores, and API functions are public.
No WebSockets at launch — evaluate after measuring real usage patterns.

---

## Alternatives Considered

### Option 1: React Context per module
Each module provides its own Context.
- Pro: Built-in React, no extra library
- Con: Context re-renders entire tree on every state change
- Con: During exam (high-frequency autosave), Context causes timer flicker

### Option 2: Redux Toolkit
Centralized global store.
- Pro: Excellent devtools, time-travel debugging
- Con: Boilerplate (actions, reducers, selectors) for every state change
- Con: Tempts developers to put all state in one global store (breaks module isolation)

### Option 3: Zustand stores per module ← CHOSEN
One small Zustand store per module, modules communicate through stores.
- Pro: Minimal boilerplate — set({key: value}) to update
- Pro: Selective re-renders — components subscribe to only what they need
- Pro: During exam: timer subscribes to attemptStore.timeRemaining only
  (no re-render from question answer saves)
- Pro: Stores are importable across modules (the one allowed cross-module import)
- Con: Store proliferation if not disciplined — each module gets ONE store max

---

## Consequences

### Positive
- Timer component never re-renders from response saves (different Zustand slice)
- Auth token available to all API calls without prop drilling
- Module boundaries enforced: components import from index.js only
- Devtools show each store independently

### Negative
- Zustand is an additional dependency (small: 2.9KB)
- Developers must learn "stores are the cross-module interface" convention

### Neutral
- localStorage used ONLY for: JWT token, preferred language, theme preference
  (never for exam responses — those live in DB via autosave)
- No WebSockets at launch — autosave uses HTTP POST per answer (ADR-005)

---

## Module Impact

```
modules/auth/store/authStore.js      → { user, token, isAuthenticated, login(), logout() }
modules/attempt/store/attemptStore.js → { currentAttempt, responses, questionStatus,
                                          timeRemaining, startExam(), resumeExam(),
                                          selectOption(), navigateTo(), submitExam() }
                                        NOTE: autosave is handled by useAutoSave hook,
                                        NOT by a store action. The store is for state only.
modules/attempt/hooks/useAutoSave.js  → Debounced queue (500ms), per-questionNo dedup,
                                        sequentially flushes via attemptApi.saveResponse()
modules/analysis/store/analysisStore.js → { report, isLoading, fetchReport() }
modules/parent/store/parentStore.js  → { children, selectedChild, setSelectedChild() }
config/apiClient.js                  → Axios instance reads authStore.token for Authorization header
```

---

## Implementation Notes

Zustand store example (attempt/store/attemptStore.js):
```javascript
import { create } from 'zustand'
import { attemptApi } from '../api/attemptApi'

export const useAttemptStore = create((set, get) => ({
  currentAttempt: null,
  responses: {},   // { [questionNo]: { selectedOption, isMarkedReview, visitCount, questionId } }
  timeRemaining: null,
  isSaving: false,

  startExam: async (examId) => { ... },
  resumeExam: async (attemptId, examId) => { ... },

  // Local-only optimistic update — does NOT call the API
  selectOption: (questionNo, questionId, selectedOption) => {
    set(state => ({
      responses: {
        ...state.responses,
        [questionNo]: { ...state.responses[questionNo], selectedOption, questionId }
      }
    }))
    // API call is handled by useAutoSave hook (debounced, queued)
  },

  submitExam: async (attemptId) => {
    const result = await attemptApi.submit(attemptId)
    return result
  }
}))
```

Autosave hook (attempt/hooks/useAutoSave.js):
```javascript
// Separate from the store — handles API call with debounce + retry queue
export function useAutoSave() {
  const currentAttempt = useAttemptStore(s => s.currentAttempt)
  // Debounce 500ms, deduplicate by questionNo, flush sequentially:
  const scheduleSave = useCallback((questionNo, questionId, selectedOption, isMarkedReview, timeTaken) => {
    pendingSaves.current.set(questionNo, { questionNo, questionId, selectedOption, isMarkedReview, timeTakenSeconds: timeTaken })
    clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(processQueue, 500)
  }, [processQueue])
  // processQueue: await attemptApi.saveResponse(currentAttempt.attempt_id, ...) for each pending item
  return { scheduleSave }
}
```

Key design choice: `selectOption()` in the store does an optimistic local update ONLY.
The actual HTTP POST is delegated to `useAutoSave.scheduleSave()` which provides
debouncing, deduplication, and retry logic — keeping the store pure state.

API client with auth interceptor (config/apiClient.js):
```javascript
import axios from 'axios'
// Note: import store directly, not useAttemptStore hook (hooks only in components)
import { useAuthStore } from '@/modules/auth'

const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_URL })

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token  // getState() works outside components
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

Module index.js public exports pattern:
```javascript
// modules/attempt/index.js — only these are public
export { ExamPage } from './pages/ExamPage'
export { useAttemptStore } from './store/attemptStore'
export { attemptApi } from './api/attemptApi'
// Internal components like QuestionCard NOT exported
```

---

## Review Trigger

Revisit if live leaderboard or real-time exam monitoring (admin watching
students in-progress) is requested — that's the trigger to evaluate
WebSockets (Socket.io or Supabase Realtime). Revisit if state management
complexity grows beyond what Zustand handles cleanly.
