export interface ApiResponse<T> {
  data: T;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: Record<string, string[]>;
}

export interface AlertItem {
  id: string;
  vendorId: string;
  vendorName: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  type: "score_drop" | "new_finding" | "threshold_breach" | "scan_complete" | "vendor_added";
  isRead: boolean;
  isResolved: boolean;
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}
