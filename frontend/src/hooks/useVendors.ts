import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'
import type { Vendor, VendorCreate, VendorUpdate } from '@/types/vendor'

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export function useVendors() {
  return useQuery({
    queryKey: ['vendors'],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<Vendor>>(API_ROUTES.vendors)
      return res.items
    },
  })
}

export function useVendor(id: string) {
  return useQuery({
    queryKey: ['vendor', id],
    queryFn: () => api.get<Vendor>(API_ROUTES.vendor(id)),
    enabled: !!id,
  })
}

export function useCreateVendor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: VendorCreate) => api.post<Vendor>(API_ROUTES.vendors, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
    },
  })
}

export function useUpdateVendor(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: VendorUpdate) => api.patch<Vendor>(API_ROUTES.vendor(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
      queryClient.invalidateQueries({ queryKey: ['vendor', id] })
    },
  })
}

export function useDeleteVendor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(API_ROUTES.vendor(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
    },
  })
}

export function useRescanVendor(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.post(API_ROUTES.vendorRescan(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor', id] })
      queryClient.invalidateQueries({ queryKey: ['vendor-score', id] })
    },
  })
}
