import { create } from 'zustand'
import type { Grade, Severity } from '@/types/scoring'
import type { VendorTier } from '@/types/vendor'

interface FilterState {
  vendorFilters: {
    tier: VendorTier | null
    grade: Grade | null
    industry: string | null
    search: string
  }
  alertFilters: {
    severity: Severity | null
    isRead: boolean | null
    search: string
  }
  setVendorFilter: (key: string, value: unknown) => void
  setAlertFilter: (key: string, value: unknown) => void
  resetVendorFilters: () => void
  resetAlertFilters: () => void
}

const initialVendorFilters = {
  tier: null,
  grade: null,
  industry: null,
  search: '',
}

const initialAlertFilters = {
  severity: null,
  isRead: null,
  search: '',
}

export const useFilterStore = create<FilterState>((set) => ({
  vendorFilters: { ...initialVendorFilters },
  alertFilters: { ...initialAlertFilters },
  setVendorFilter: (key, value) =>
    set((state) => ({
      vendorFilters: { ...state.vendorFilters, [key]: value },
    })),
  setAlertFilter: (key, value) =>
    set((state) => ({
      alertFilters: { ...state.alertFilters, [key]: value },
    })),
  resetVendorFilters: () => set({ vendorFilters: { ...initialVendorFilters } }),
  resetAlertFilters: () => set({ alertFilters: { ...initialAlertFilters } }),
}))
