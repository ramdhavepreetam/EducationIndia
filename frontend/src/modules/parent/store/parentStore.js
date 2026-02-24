import { create } from 'zustand'
import { parentApi } from '../api/parentApi'

export const useParentStore = create((set, get) => ({

  // ── State ─────────────────────────────────────────
  children:         [],     // list[ChildProfileSchema]
  selectedChildId:  null,   // UUID string
  childDetail:      null,   // ChildDetailSchema
  isLoading:        false,  // initial dashboard load
  isLoadingDetail:  false,  // switching between children
  isSaving:         false,  // link/unlink/nickname operations
  error:            null,
  saveError:        null,

  // ── Actions ───────────────────────────────────────

  loadDashboard: async () => {
    set({ isLoading: true, error: null })
    try {
      const data = await parentApi.getDashboard()
      set({
        children:        data.children,
        selectedChildId: data.children[0]?.student_id ?? null,
        childDetail:     data.selected_child_detail,
        isLoading:       false
      })
    } catch (err) {
      set({
        error:     err.response?.data?.detail ?? err.message,
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
        error:           err.response?.data?.detail ?? err.message,
        isLoadingDetail: false
      })
    }
  },

  linkChild: async (studentEmail) => {
    set({ isSaving: true, saveError: null })
    try {
      const child = await parentApi.linkChild(studentEmail)
      // Add to children list, auto-select the new child
      set(state => ({
        children:        [...state.children, child],
        selectedChildId: child.student_id,
        isSaving:        false
      }))
      // Load full detail for newly linked child
      await get().selectChild(child.student_id)
      return { success: true, child }
    } catch (err) {
      const message = err.response?.data?.detail ?? err.message
      set({ saveError: message, isSaving: false })
      return { success: false, error: message }
    }
  },

  updateNickname: async (studentId, nickname) => {
    set({ isSaving: true, saveError: null })
    try {
      const updated = await parentApi.updateNickname(studentId, nickname)
      // Update the child in the children list
      set(state => ({
        children: state.children.map(c =>
          c.student_id === studentId
            ? { ...c, child_nickname: updated.child_nickname }
            : c
        ),
        // Also update inside childDetail if this is the selected child
        childDetail: state.childDetail && state.selectedChildId === studentId
          ? {
              ...state.childDetail,
              profile: { ...state.childDetail.profile, child_nickname: updated.child_nickname }
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

  unlinkChild: async (studentId) => {
    set({ isSaving: true, saveError: null })
    try {
      await parentApi.unlinkChild(studentId)

      const remainingChildren = get().children.filter(
        c => c.student_id !== studentId
      )
      const nextSelectedId = remainingChildren[0]?.student_id ?? null

      set({
        children:        remainingChildren,
        selectedChildId: nextSelectedId,
        childDetail:     null,
        isSaving:        false
      })

      // Load detail for next child if one exists
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
    children:        [],
    selectedChildId: null,
    childDetail:     null,
    isLoading:       false,
    isLoadingDetail: false,
    isSaving:        false,
    error:           null,
    saveError:       null
  })
}))
