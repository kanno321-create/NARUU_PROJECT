/**
 * Quote Types
 * Quote management and approval workflow models
 */

export enum QuoteStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
}

export interface QuoteCreateRequest {
  estimateId: string;
  customer: {
    name: string;
    email?: string;
    phone?: string;
    company?: string;
  };
  projectName?: string;
  notes?: string;
  validUntil?: string;
}

export interface QuoteUpdateRequest {
  customer?: {
    name?: string;
    email?: string;
    phone?: string;
    company?: string;
  };
  projectName?: string;
  notes?: string;
  validUntil?: string;
  status?: QuoteStatus;
}

export interface QuoteItem {
  itemId: string;
  type: 'panel' | 'breaker' | 'enclosure' | 'accessory' | 'material';
  name: string;
  specification?: string;
  unit: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  panelId?: string;
}

export interface QuoteResponse {
  quoteId: string;
  quoteNumber: string;
  estimateId: string;
  status: QuoteStatus;
  customer: {
    name: string;
    email?: string;
    phone?: string;
    company?: string;
  };
  projectName?: string;
  items: QuoteItem[];
  summary: {
    subtotal: number;
    discount?: number;
    total: number;
    vat: number;
    totalWithVat: number;
  };
  notes?: string;
  createdAt: string;
  updatedAt: string;
  validUntil?: string;
  approvedAt?: string;
  approvedBy?: string;
  pdfUrl?: string;
  shareUrl?: string;
}

export interface QuoteApproveRequest {
  approvedBy: string;
  notes?: string;
}

export interface QuoteApproveResponse {
  quoteId: string;
  status: QuoteStatus;
  approvedAt: string;
  approvedBy: string;
}

export interface QuotePdfResponse {
  quoteId: string;
  pdfUrl: string;
  expiresAt: string;
}

export interface QuoteShareUrlResponse {
  quoteId: string;
  shareUrl: string;
  expiresAt?: string;
}

export interface QuoteListItem {
  quoteId: string;
  quoteNumber: string;
  status: QuoteStatus;
  customerName: string;
  projectName?: string;
  totalAmount: number;
  createdAt: string;
  validUntil?: string;
}
