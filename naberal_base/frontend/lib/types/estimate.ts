/**
 * Estimate Types
 * FIX-4 Pipeline request/response models
 */

export interface PanelInput {
  name: string;
  mainBreaker: BreakerInput;
  branchBreakers: BreakerInput[];
  accessories?: AccessoryInput[];
  enclosurePreference?: {
    type?: string;
    material?: string;
  };
}

export interface BreakerInput {
  category: 'MCCB' | 'ELB';
  poles: 2 | 3 | 4;
  ampere: number;
  quantity?: number;
  economy?: 'standard' | 'economy';
  brand?: 'SANGDO' | 'LS' | 'HANGUK';
}

export interface AccessoryInput {
  type: string;
  model?: string;
  quantity: number;
  specification?: string;
}

export interface EnclosureInput {
  type?: string;
  material?: string;
  width?: number;
  height?: number;
  depth?: number;
}

export interface EstimateRequest {
  panels: PanelInput[];
  customer?: {
    name?: string;
    projectName?: string;
  };
  options?: {
    skipValidation?: boolean;
    generatePdf?: boolean;
    includeCover?: boolean;
  };
}

export interface ValidationCheck {
  checkId: string;
  name: string;
  status: 'PASS' | 'FAIL' | 'WARN';
  message?: string;
  details?: Record<string, unknown>;
}

export interface PipelineStageResult {
  stage: 'enclosure' | 'breaker' | 'critic' | 'format' | 'cover' | 'lint';
  status: 'SUCCESS' | 'FAILED' | 'SKIPPED';
  duration?: number;
  data?: Record<string, unknown>;
  validations?: ValidationCheck[];
}

export interface PipelineResult {
  stages: PipelineStageResult[];
  overallStatus: 'SUCCESS' | 'PARTIAL' | 'FAILED';
  totalDuration: number;
  evidencePath?: string;
}

export interface EvidenceInfo {
  hash: string;
  timestamp: string;
  path: string;
  files?: {
    input?: string;
    output?: string;
    metrics?: string;
    validation?: string;
    visual?: string;
  };
}

export interface PanelEstimate {
  panelId: string;
  panelName: string;
  enclosure: {
    sku: string;
    type: string;
    material: string;
    size: { width: number; height: number; depth: number };
    price: number;
    fitScore?: number;
  };
  mainBreaker: {
    model: string;
    specification: string;
    price: number;
    quantity: number;
  };
  branchBreakers: Array<{
    model: string;
    specification: string;
    price: number;
    quantity: number;
    placement?: {
      row: number;
      column: number;
      side: 'left' | 'right';
    };
  }>;
  accessories: Array<{
    type: string;
    model: string;
    specification?: string;
    price: number;
    quantity: number;
  }>;
  materials: Array<{
    name: string;
    specification?: string;
    unit: string;
    quantity: number;
    price: number;
  }>;
  subtotal: number;
  total: number;
  validation?: {
    phaseBalance?: number;
    clearanceViolations?: number;
    thermalViolations?: number;
  };
}

export interface EstimateResponse {
  estimateId: string;
  panels: PanelEstimate[];
  customer?: {
    name?: string;
    projectName?: string;
  };
  summary: {
    totalPanels: number;
    totalBreakers: number;
    totalAccessories: number;
    subtotal: number;
    total: number;
    totalWithVat: number;
  };
  pipeline: PipelineResult;
  evidence: EvidenceInfo;
  createdAt: string;
  expiresAt?: string;
}

export interface ValidateEstimateRequest {
  panels: PanelInput[];
  checks?: string[];
}

export interface ValidateEstimateResponse {
  valid: boolean;
  checks: ValidationCheck[];
  errors?: Array<{
    field: string;
    message: string;
    code: string;
  }>;
  warnings?: Array<{
    field: string;
    message: string;
  }>;
}

export interface EstimateListItem {
  estimateId: string;
  createdAt: string;
  customerName?: string;
  projectName?: string;
  panelCount: number;
  totalAmount: number;
  status: 'draft' | 'validated' | 'approved' | 'expired';
}
