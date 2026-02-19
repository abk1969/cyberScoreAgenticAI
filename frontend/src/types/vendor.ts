import type { Grade, TrendDirection } from "./scoring";

export type VendorTier = 1 | 2 | 3;

export interface Vendor {
  id: string;
  name: string;
  domain: string;
  tier: VendorTier;
  industry: string;
  score: number;
  grade: Grade;
  trend: TrendDirection;
  lastScanDate: string;
  contractValue: number | null;
  contactEmail: string | null;
  country: string;
  employeeCount: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface VendorCreate {
  name: string;
  domain: string;
  tier: VendorTier;
  industry: string;
  contactEmail?: string;
  country?: string;
}

export interface VendorUpdate {
  name?: string;
  domain?: string;
  tier?: VendorTier;
  industry?: string;
  contactEmail?: string;
  country?: string;
}

export interface VendorFilters {
  tier?: VendorTier;
  grade?: Grade;
  industry?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}
