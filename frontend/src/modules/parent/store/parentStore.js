import { create } from 'zustand'
import { parentApi } from '../api/parentApi'

export const useParentStore = create((set, get) => ({

  // ── State ─────────────────────────────────────────
  children: [],     // list[ChildProfileSchema]
  selectedChildId: null,   // UUID string
  childDetail: null,   // ChildDetailSchema
  isLoading: false,  // initial dashboard load
  isLoadingDetail: false,  // switching between children
  isSaving: false,  // link/unlink/nickname operations
  error: null,
  saveError: null,

  // ── Actions ───────────────────────────────────────

  loadDashboard: async () => {
    set({ isLoading: true, error: null })
    try {
      const data = await parentApi.getDashboard()
      set({
        children: data.children,
        selectedChildId: data.children[0]?.id ?? null,
        childDetail: data.selected_child_detail,
        isLoading: false
      })
    } catch (err) {
      set({
        error: err.response?.data?.detail ?? err.message,
        isLoading: false
      })
    }
  },

  selectChild: async (studentId) => {
    // No-op if already selected
    if (get().selectedChildId === studentId) return

    set({ selectedChildId: studentId, isLoadingDetail: true, error: null })
    try {
      const detail = await parentApi.getChildDetail(studentId)
      set({ childDetail: detail, isLoadingDetail: false })
    } catch (err) {
      set({
        error: err.response?.data?.detail ?? err.message,
        isLoadingDetail: false
      })
    }
  },

  createChild: async (formData) => {
    set({ isSaving: true, saveError: null })
    try {
      const child = await parentApi.createChild(formData)
      set(state => ({
        children: [...state.children, child],
        selectedChildId: child.id,
        isSaving: false
      }))
      await get().selectChild(child.id)
      return { success: true, child }
    } catch (err) {
      const message = err.response?.data?.detail ?? err.message
      set({ saveError: message, isSaving: false })
      return { success: false, error: message }
    }
  },

  updateChild: async (childId, formData) => {
    set({ isSaving: true, saveError: null })
    try {
      const updated = await parentApi.updateChild(childId, formData)
      set(state => ({
        children: state.children.map(c =>
          c.id === childId ? updated : c
        ),
        childDetail: state.childDetail && state.selectedChildId === childId
          ? {
            ...state.childDetail,
            profile: updated
          }
          : state.childDetail,
        isSaving: false
      }))
      return { success: true }
    } catch (err) {
      const message = err.response?.data?.detail ?? err.message
      set({ saveError: message, isSaving: false })
      return { success: false, error: message }
    }
  },

  deleteChild: async (childId) => {
    set({ isSaving: true, saveError: null })
    try {
      await parentApi.deleteChild(childId)

      const remainingChildren = get().children.filter(
        c => c.id !== childId
      )
      const nextSelectedId = remainingChildren[0]?.id ?? null

      set({
        children: remainingChildren,
        selectedChildId: nextSelectedId,
        childDetail: null,
        isSaving: false
      })

      if (nextSelectedId) {
        await get().selectChild(nextSelectedId)
      }

      return { success: true }
    } catch (err) {
      const message = err.response?.data?.detail ?? err.message
      set({ saveError: message, isSaving: false })
      return { success: false, error: message }
    }
  },

  clearError: () => set({ error: null, saveError: null }),

  reset: () => set({
    children: [],
    selectedChildId: null,
    childDetail: null,
    isLoading: false,
    isLoadingDetail: false,
    isSaving: false,
    error: null,
    saveError: null
  })
}))
