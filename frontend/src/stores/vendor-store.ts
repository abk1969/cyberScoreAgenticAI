import { create } from "zustand";
import type { Grade } from "@/types/scoring";
import type { VendorTier } from "@/types/vendor";

interface VendorStoreState {
  selectedVendorId: string | null;
  filters: {
    tier: VendorTier | null;
    grade: Grade | null;
    industry: string | null;
    search: string;
  };
  setSelectedVendor: (id: string | null) => void;
  setFilter: (key: string, value: unknown) => void;
  resetFilters: () => void;
}

const initialFilters = {
  tier: null,
  grade: null,
  industry: null,
  search: "",
};

export const useVendorStore = create<VendorStoreState>((set) => ({
  selectedVendorId: null,
  filters: { ...initialFilters },
  setSelectedVendor: (id) => set({ selectedVendorId: id }),
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    })),
  resetFilters: () => set({ filters: { ...initialFilters } }),
}));
