import type { BreakerInput, EnclosureInput, AccessoryInput } from "@/lib/api";

/* ──────────────────────────────────────────────
   위저드 전체 상태
   ────────────────────────────────────────────── */
export interface WizardState {
  step: 1 | 2 | 3;

  /* Step 1: 용도/외함 */
  panelUsage: PanelUsage | null;
  installLocation: InstallLocation | null;
  enclosureMaterial: EnclosureInput["material"] | null;

  /* Step 2: 차단기 구성 */
  breakerBrand: BreakerBrand | null;
  breakerGrade: BreakerGrade | null;
  mainBreaker: BreakerInput;
  branchBreakers: BreakerInput[];
  accessories: AccessoryInput[];

  /* Step 3: 결과 */
  customerName: string;
  projectName: string;
  contactPhone: string;
}

/* ──────────────────────────────────────────────
   Step 1 선택지
   ────────────────────────────────────────────── */
export type PanelUsage =
  | "주택용"
  | "상가용"
  | "공장용"
  | "전기차충전"
  | "태양광"
  | "기타";

export type InstallLocation =
  | "옥내노출"
  | "옥외노출"
  | "옥내자립"
  | "옥외자립"
  | "매입함";

export type BreakerBrand = "상도" | "LS";
export type BreakerGrade = "표준형" | "경제형";

/* ──────────────────────────────────────────────
   기본값
   ────────────────────────────────────────────── */
export const DEFAULT_MAIN_BREAKER: BreakerInput = {
  breaker_type: "MCCB",
  ampere: 50,
  poles: 4,
  quantity: 1,
};

export const DEFAULT_BRANCH_BREAKER: BreakerInput = {
  breaker_type: "ELB",
  ampere: 30,
  poles: 2,
  quantity: 1,
};

export const INITIAL_WIZARD_STATE: WizardState = {
  step: 1,
  panelUsage: null,
  installLocation: null,
  enclosureMaterial: null,
  breakerBrand: null,
  breakerGrade: null,
  mainBreaker: { ...DEFAULT_MAIN_BREAKER },
  branchBreakers: [{ ...DEFAULT_BRANCH_BREAKER }],
  accessories: [],
  customerName: "",
  projectName: "",
  contactPhone: "",
};

/* ──────────────────────────────────────────────
   선택 옵션 데이터
   ────────────────────────────────────────────── */
export const AMPERE_OPTIONS = [15, 20, 30, 50, 60, 75, 100, 125, 150, 200, 225, 250, 300, 400];

export const ACCESSORY_TYPES: { value: AccessoryInput["type"]; label: string }[] = [
  { value: "magnet", label: "마그네트" },
  { value: "timer", label: "타이머" },
  { value: "meter", label: "계량기" },
  { value: "spd", label: "SPD (서지보호)" },
  { value: "switch", label: "스위치" },
];
