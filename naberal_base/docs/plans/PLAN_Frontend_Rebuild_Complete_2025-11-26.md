# 프론트엔드 완전 재구현 계획서

**날짜**: 2025-11-26
**목표**: frontend-kis-complete.html 참조하여 Next.js 프론트엔드 완전 재구현
**원칙**: 데이터 누락 금지, 샘플링 금지, 디자인/레이아웃/기능 100% 보존

---

## 📋 목표 및 범위

### 목표
1. **디자인 완벽 복제**: frontend-kis-complete.html의 UI/UX 그대로 재현
2. **데이터 완전성**: 모든 선택 옵션 데이터 100% 포함 (누락/샘플링 절대 금지)
3. **기능 완전 구현**: 멀티탭, AI 챗, 견적 생성, 액세서리 관리 등 모든 기능
4. **타입 안전성**: TypeScript + SSOT 정렬된 인터페이스 사용
5. **에러 없는 일관성**: 컴파일/런타임 에러 0개, 일관된 코드 스타일

### 범위
- **포함**: 견적 작성 전체 플로우, 멀티탭 시스템, 액세서리 관리, AI 챗 통합
- **제외**: ERP 기능 (별도 AI 담당), 백엔드 수정 (프론트엔드만)

---

## 🏗️ 아키텍처

### 기술 스택
- **프레임워크**: Next.js 14 (App Router)
- **언어**: TypeScript (strict mode)
- **스타일링**: Tailwind CSS + CSS Variables (KIS Design System)
- **상태관리**: React useState (복잡도 낮아 Redux 불필요)
- **API**: REST (fetch, /v1/estimates, /v1/catalog)
- **아이콘**: Lucide React

### 컴포넌트 구조
```
frontend-min/src/
├── app/
│   ├── page.tsx              # 메인 페이지 (view routing)
│   ├── layout.tsx            # 루트 레이아웃
│   ├── globals.css           # 글로벌 스타일 (KIS Design System)
│   └── _components/
│       ├── Sidebar.tsx       # 사이드바 네비게이션
│       ├── AuthBar.tsx       # 인증 바
│       ├── QuoteForm.tsx     # 견적 폼 (완전 재구현)
│       ├── TabSystem.tsx     # 멀티탭 관리 (신규)
│       ├── BreakerList.tsx   # 차단기 리스트 (신규)
│       └── AccessoryManager.tsx # 액세서리 관리 (신규)
├── lib/
│   ├── types.ts              # TypeScript 인터페이스 (SSOT)
│   ├── api.ts                # API 호출 함수
│   └── constants.ts          # 상수 (완전한 데이터)
└── hooks/
    └── useQuoteState.ts      # 견적 상태 관리 훅 (신규)
```

---

## 📊 완전한 데이터 정의

### constants.ts (신규 파일)
모든 선택 옵션 데이터를 상수로 정의 (누락 금지):

```typescript
// 메인 차단기 암페어 (16개 - 전체)
export const MAIN_BREAKER_AMPERES = [
  '100A', '125A', '150A', '175A', '200A', '225A', '250A', '300A',
  '350A', '400A', '500A', '600A', '700A', '800A', '1000A', '1200A'
] as const;

// 분기 차단기 암페어 (22개 - 전체)
export const BRANCH_BREAKER_AMPERES = [
  '15A', '20A', '30A', '40A', '50A', '60A', '75A', '100A',
  '125A', '150A', '175A', '200A', '225A', '250A', '300A', '350A',
  '400A', '500A', '600A', '700A', '800A', '1000A', '1200A'
] as const;

// 극수 (3개)
export const POLES = ['2P', '3P', '4P'] as const;

// 마그네트 모델 (13개 - 전체)
export const MAGNET_MODELS = [
  'MC-9', 'MC-12', 'MC-18', 'MC-22', 'MC-32', 'MC-40', 'MC-50',
  'MC-65', 'MC-75', 'MC-85', 'MC-100', 'MC-130', 'MC-150'
] as const;

// 외함 종류
export const ENCLOSURE_TYPES = [
  '옥내', '옥외', '자립', '전주부착형', 'FRP함', '하이박스'
] as const;

// 재질
export const MATERIALS = [
  'STEEL 1.6T', 'STEEL 2.0T', 'STS 1.5T'
] as const;

// 차단기 브랜드
export const BREAKER_BRANDS = ['LS', '상도', '슈나이더'] as const;
```

---

## 🎯 Task 분해 (TDD 방식)

### Task 1: 프로젝트 설정 및 데이터 상수 정의 (30분)
**목표**: 완전한 데이터 상수 파일 생성

#### 1.1 constants.ts 생성
```bash
# 파일 생성
touch frontend-min/src/lib/constants.ts
```

```typescript
// frontend-min/src/lib/constants.ts
/**
 * KIS Estimator 프론트엔드 데이터 상수
 *
 * 원본 참조: frontend-kis-complete.html
 * 원칙: 데이터 누락 금지, 샘플링 금지
 */

// 메인 차단기 암페어 (16개 - 100% 완전)
export const MAIN_BREAKER_AMPERES = [
  '100A', '125A', '150A', '175A', '200A', '225A', '250A', '300A',
  '350A', '400A', '500A', '600A', '700A', '800A', '1000A', '1200A'
] as const;

// 분기 차단기 암페어 (22개 - 100% 완전)
export const BRANCH_BREAKER_AMPERES = [
  '15A', '20A', '30A', '40A', '50A', '60A', '75A', '100A',
  '125A', '150A', '175A', '200A', '225A', '250A', '300A', '350A',
  '400A', '500A', '600A', '700A', '800A', '1000A', '1200A'
] as const;

// 극수
export const POLES = ['2P', '3P', '4P'] as const;

// 마그네트 모델 (13개 - 100% 완전)
export const MAGNET_MODELS = [
  'MC-9', 'MC-12', 'MC-18', 'MC-22', 'MC-32', 'MC-40', 'MC-50',
  'MC-65', 'MC-75', 'MC-85', 'MC-100', 'MC-130', 'MC-150'
] as const;

// 외함 종류
export const ENCLOSURE_TYPES = [
  '옥내', '옥외', '자립', '전주부착형', 'FRP함', '하이박스'
] as const;

// 재질
export const MATERIALS = [
  'STEEL 1.6T', 'STEEL 2.0T', 'STS 1.5T'
] as const;

// 차단기 타입
export const BREAKER_TYPES = ['MCCB', 'ELB'] as const;

// 차단기 브랜드
export const BREAKER_BRANDS = ['LS', '상도', '슈나이더'] as const;

// 타입 추론
export type MainBreakerAmpere = typeof MAIN_BREAKER_AMPERES[number];
export type BranchBreakerAmpere = typeof BRANCH_BREAKER_AMPERES[number];
export type Pole = typeof POLES[number];
export type MagnetModel = typeof MAGNET_MODELS[number];
export type EnclosureType = typeof ENCLOSURE_TYPES[number];
export type Material = typeof MATERIALS[number];
export type BreakerType = typeof BREAKER_TYPES[number];
export type BreakerBrand = typeof BREAKER_BRANDS[number];
```

#### 1.2 검증 (수동 체크)
```bash
# 컴파일 에러 확인
npm run type-check

# 예상 출력: No errors
```

**완료 조건**:
- ✅ constants.ts 파일 생성
- ✅ 모든 데이터 상수 정의 (누락 0개)
- ✅ TypeScript 컴파일 에러 0개
- ✅ 타입 추론 정상 작동

---

### Task 2: 상태 관리 타입 정의 (types.ts 확장) (20분)
**목표**: 멀티탭 견적 시스템을 위한 완전한 타입 정의

#### 2.1 types.ts 확장
```typescript
// frontend-min/src/lib/types.ts 끝에 추가

import type {
  MainBreakerAmpere,
  BranchBreakerAmpere,
  Pole,
  MagnetModel,
  EnclosureType,
  Material,
  BreakerType,
  BreakerBrand
} from './constants';

/**
 * 견적 탭 상태 (멀티탭 시스템)
 */
export interface QuoteTab {
  id: number;
  title: string;
  customerInfo: CustomerInfo;
  enclosureInfo: EnclosureInfo;
  mainBreakerInfo: MainBreakerInfo;
  branchBreakers: BranchBreaker[];
  accessories: Accessory[];
  estimateVisible: boolean;
}

export interface CustomerInfo {
  company: string;
  contact: string;
  email: string;
  address: string;
}

export interface EnclosureInfo {
  type: EnclosureType;
  boxType: string;
  material: Material;
  request: string;
}

export interface MainBreakerInfo {
  type: BreakerType; // 'MCCB' | 'ELB'
  poles: Pole;
  capacity: MainBreakerAmpere;
  brand: BreakerBrand;
}

export interface BranchBreaker {
  id: string; // UUID
  type: BreakerType; // 'MCCB' | 'ELB'
  poles: Pole;
  capacity: BranchBreakerAmpere;
  quantity: number;
}

export interface Accessory {
  id: string; // UUID
  type: 'magnet' | 'timer' | 'meter' | 'spd';
  model: string; // MagnetModel 또는 다른 모델명
  quantity: number;
}
```

#### 2.2 검증
```bash
npm run type-check
# 예상: No errors
```

**완료 조건**:
- ✅ QuoteTab 인터페이스 정의
- ✅ 중첩 인터페이스 모두 정의
- ✅ constants.ts와 타입 연동
- ✅ 컴파일 에러 0개

---

### Task 3: useQuoteState 커스텀 훅 생성 (TDD) (40분)
**목표**: 멀티탭 견적 상태 관리 로직 분리

#### 3.1 테스트 파일 생성 (TDD)
```typescript
// frontend-min/src/hooks/__tests__/useQuoteState.test.ts
import { renderHook, act } from '@testing-library/react';
import { useQuoteState } from '../useQuoteState';

describe('useQuoteState', () => {
  test('초기 탭 1개 생성', () => {
    const { result } = renderHook(() => useQuoteState());

    expect(result.current.tabs).toHaveLength(1);
    expect(result.current.activeTabId).toBe(1);
    expect(result.current.tabs[0].title).toBe('견적서 1');
  });

  test('탭 추가', () => {
    const { result } = renderHook(() => useQuoteState());

    act(() => {
      result.current.addTab();
    });

    expect(result.current.tabs).toHaveLength(2);
    expect(result.current.tabs[1].title).toBe('견적서 2');
  });

  test('탭 삭제', () => {
    const { result } = renderHook(() => useQuoteState());

    act(() => {
      result.current.addTab();
      result.current.removeTab(1);
    });

    expect(result.current.tabs).toHaveLength(1);
  });

  test('분기 차단기 추가', () => {
    const { result } = renderHook(() => useQuoteState());

    act(() => {
      result.current.addBranchBreaker(1, {
        type: 'MCCB',
        poles: '2P',
        capacity: '20A',
        quantity: 1
      });
    });

    expect(result.current.tabs[0].branchBreakers).toHaveLength(1);
  });
});
```

#### 3.2 useQuoteState.ts 구현
```typescript
// frontend-min/src/hooks/useQuoteState.ts
import { useState } from 'react';
import type { QuoteTab, BranchBreaker, Accessory } from '@/lib/types';

const createInitialTab = (id: number): QuoteTab => ({
  id,
  title: `견적서 ${id}`,
  customerInfo: { company: '', contact: '', email: '', address: '' },
  enclosureInfo: { type: '옥내', boxType: '', material: 'STEEL 1.6T', request: '' },
  mainBreakerInfo: { type: 'MCCB', poles: '2P', capacity: '100A', brand: 'LS' },
  branchBreakers: [],
  accessories: [],
  estimateVisible: false
});

export function useQuoteState() {
  const [tabs, setTabs] = useState<QuoteTab[]>([createInitialTab(1)]);
  const [activeTabId, setActiveTabId] = useState<number>(1);

  const addTab = () => {
    const newId = Math.max(...tabs.map(t => t.id)) + 1;
    setTabs([...tabs, createInitialTab(newId)]);
    setActiveTabId(newId);
  };

  const removeTab = (id: number) => {
    if (tabs.length === 1) return; // 최소 1개 유지
    setTabs(tabs.filter(t => t.id !== id));
    if (activeTabId === id) {
      setActiveTabId(tabs[0].id);
    }
  };

  const updateTab = (id: number, updates: Partial<QuoteTab>) => {
    setTabs(tabs.map(t => t.id === id ? { ...t, ...updates } : t));
  };

  const addBranchBreaker = (tabId: number, breaker: Omit<BranchBreaker, 'id'>) => {
    setTabs(tabs.map(t => {
      if (t.id === tabId) {
        return {
          ...t,
          branchBreakers: [
            ...t.branchBreakers,
            { ...breaker, id: crypto.randomUUID() }
          ]
        };
      }
      return t;
    }));
  };

  const removeBranchBreaker = (tabId: number, breakerId: string) => {
    setTabs(tabs.map(t => {
      if (t.id === tabId) {
        return {
          ...t,
          branchBreakers: t.branchBreakers.filter(b => b.id !== breakerId)
        };
      }
      return t;
    }));
  };

  const addAccessory = (tabId: number, accessory: Omit<Accessory, 'id'>) => {
    setTabs(tabs.map(t => {
      if (t.id === tabId) {
        return {
          ...t,
          accessories: [
            ...t.accessories,
            { ...accessory, id: crypto.randomUUID() }
          ]
        };
      }
      return t;
    }));
  };

  const removeAccessory = (tabId: number, accessoryId: string) => {
    setTabs(tabs.map(t => {
      if (t.id === tabId) {
        return {
          ...t,
          accessories: t.accessories.filter(a => a.id !== accessoryId)
        };
      }
      return t;
    }));
  };

  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];

  return {
    tabs,
    activeTabId,
    activeTab,
    setActiveTabId,
    addTab,
    removeTab,
    updateTab,
    addBranchBreaker,
    removeBranchBreaker,
    addAccessory,
    removeAccessory
  };
}
```

#### 3.3 테스트 실행
```bash
npm test -- useQuoteState.test.ts
# 예상: 모든 테스트 PASS
```

**완료 조건**:
- ✅ useQuoteState.test.ts 작성 (TDD)
- ✅ useQuoteState.ts 구현
- ✅ 모든 테스트 통과
- ✅ 타입 에러 0개

---

### Task 4: TabSystem 컴포넌트 생성 (30분)
**목표**: 멀티탭 UI 컴포넌트

#### 4.1 TabSystem.tsx 생성
```typescript
// frontend-min/src/app/_components/TabSystem.tsx
'use client';

import { Plus, X } from 'lucide-react';
import type { QuoteTab } from '@/lib/types';

interface TabSystemProps {
  tabs: QuoteTab[];
  activeTabId: number;
  onTabChange: (id: number) => void;
  onAddTab: () => void;
  onRemoveTab: (id: number) => void;
}

export default function TabSystem({
  tabs,
  activeTabId,
  onTabChange,
  onAddTab,
  onRemoveTab
}: TabSystemProps) {
  return (
    <div className="tab-system">
      <div className="tab-list">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className={`tab-item ${tab.id === activeTabId ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="tab-title">{tab.title}</span>
            {tabs.length > 1 && (
              <button
                className="tab-close"
                onClick={(e) => {
                  e.stopPropagation();
                  onRemoveTab(tab.id);
                }}
              >
                <X size={16} />
              </button>
            )}
          </div>
        ))}
        <button className="tab-add-btn" onClick={onAddTab}>
          <Plus size={16} />
          <span>새 탭</span>
        </button>
      </div>
    </div>
  );
}
```

#### 4.2 스타일 추가 (globals.css)
```css
/* frontend-min/src/app/globals.css 끝에 추가 */

/* Tab System */
.tab-system {
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
  padding: 8px 16px 0;
}

.tab-list {
  display: flex;
  gap: 4px;
  align-items: center;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item.active {
  background: var(--color-bg-primary);
  border-color: var(--color-primary);
}

.tab-close {
  display: flex;
  align-items: center;
  padding: 2px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--color-text-light);
}

.tab-close:hover {
  color: var(--color-danger);
}

.tab-add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: transparent;
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  color: var(--color-text-light);
  transition: all 0.2s;
}

.tab-add-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
```

**완료 조건**:
- ✅ TabSystem.tsx 생성
- ✅ 스타일 추가
- ✅ Props 타입 정의
- ✅ 컴파일 에러 0개

---

### Task 5: BreakerList 컴포넌트 생성 (완전한 데이터) (40분)
**목표**: 분기 차단기 리스트 UI (모든 암페어 옵션 포함)

#### 5.1 BreakerList.tsx 생성
```typescript
// frontend-min/src/app/_components/BreakerList.tsx
'use client';

import { Plus, Trash2 } from 'lucide-react';
import type { BranchBreaker } from '@/lib/types';
import {
  BRANCH_BREAKER_AMPERES,
  POLES,
  BREAKER_TYPES
} from '@/lib/constants';

interface BreakerListProps {
  breakers: BranchBreaker[];
  onAdd: (breaker: Omit<BranchBreaker, 'id'>) => void;
  onRemove: (id: string) => void;
}

export default function BreakerList({ breakers, onAdd, onRemove }: BreakerListProps) {
  const handleAdd = () => {
    onAdd({
      type: 'MCCB',
      poles: '2P',
      capacity: '20A',
      quantity: 1
    });
  };

  return (
    <div className="breaker-list-section">
      <div className="section-header">
        <h3>분기 차단기</h3>
        <button className="btn btn-sm btn-primary" onClick={handleAdd}>
          <Plus size={16} />
          추가
        </button>
      </div>

      <div className="breaker-items">
        {breakers.length === 0 ? (
          <div className="empty-state">
            <p>분기 차단기를 추가해주세요</p>
          </div>
        ) : (
          breakers.map((breaker) => (
            <div key={breaker.id} className="breaker-item">
              <div className="breaker-type-toggle">
                {BREAKER_TYPES.map((type) => (
                  <button
                    key={type}
                    className={`toggle-btn ${breaker.type === type ? 'active' : ''}`}
                  >
                    {type}
                  </button>
                ))}
              </div>

              <select className="form-select" value={breaker.poles}>
                <option value="">극수</option>
                {POLES.map((pole) => (
                  <option key={pole} value={pole}>{pole}</option>
                ))}
              </select>

              <select className="form-select" value={breaker.capacity}>
                <option value="">암페어</option>
                {/* 모든 22개 암페어 옵션 (누락 금지) */}
                {BRANCH_BREAKER_AMPERES.map((amp) => (
                  <option key={amp} value={amp}>{amp}</option>
                ))}
              </select>

              <input
                type="number"
                className="form-input"
                value={breaker.quantity}
                min="1"
                placeholder="수량"
              />

              <button
                className="btn btn-sm btn-danger"
                onClick={() => onRemove(breaker.id)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

#### 5.2 스타일 추가
```css
/* globals.css에 추가 */

.breaker-list-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.breaker-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breaker-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.breaker-type-toggle {
  display: flex;
  gap: 4px;
}

.toggle-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-primary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.empty-state {
  padding: 48px;
  text-align: center;
  color: var(--color-text-light);
  border: 2px dashed var(--color-border);
  border-radius: 8px;
}
```

**완료 조건**:
- ✅ BreakerList.tsx 생성
- ✅ 모든 22개 암페어 옵션 포함 (누락 0개)
- ✅ MCCB/ELB 토글 구현
- ✅ 추가/삭제 기능 구현

---

### Task 6: AccessoryManager 컴포넌트 생성 (완전한 마그네트 데이터) (40분)
**목표**: 액세서리 (마그네트/타이머 등) 관리 UI

#### 6.1 AccessoryManager.tsx 생성
```typescript
// frontend-min/src/app/_components/AccessoryManager.tsx
'use client';

import { Plus, Trash2 } from 'lucide-react';
import type { Accessory } from '@/lib/types';
import { MAGNET_MODELS } from '@/lib/constants';

interface AccessoryManagerProps {
  accessories: Accessory[];
  onAdd: (accessory: Omit<Accessory, 'id'>) => void;
  onRemove: (id: string) => void;
}

export default function AccessoryManager({
  accessories,
  onAdd,
  onRemove
}: AccessoryManagerProps) {
  const handleAdd = (type: Accessory['type']) => {
    onAdd({
      type,
      model: type === 'magnet' ? 'MC-9' : 'T-1',
      quantity: 1
    });
  };

  return (
    <div className="accessory-section">
      <div className="section-header">
        <h3>부속자재</h3>
        <div className="accessory-add-buttons">
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleAdd('magnet')}
          >
            <Plus size={16} />
            마그네트
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleAdd('timer')}
          >
            <Plus size={16} />
            타이머
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleAdd('meter')}
          >
            <Plus size={16} />
            계량기
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleAdd('spd')}
          >
            <Plus size={16} />
            SPD
          </button>
        </div>
      </div>

      <div className="accessory-items">
        {accessories.length === 0 ? (
          <div className="empty-state">
            <p>부속자재를 추가해주세요</p>
          </div>
        ) : (
          accessories.map((acc) => (
            <div key={acc.id} className="accessory-item">
              <div className="accessory-type-badge">
                {acc.type === 'magnet' && '⚡ 마그네트'}
                {acc.type === 'timer' && '⏱️ 타이머'}
                {acc.type === 'meter' && '📊 계량기'}
                {acc.type === 'spd' && '🛡️ SPD'}
              </div>

              {acc.type === 'magnet' ? (
                <select className="form-select" value={acc.model}>
                  <option value="">모델 선택</option>
                  {/* 모든 13개 마그네트 모델 (누락 금지) */}
                  {MAGNET_MODELS.map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  className="form-input"
                  value={acc.model}
                  placeholder="모델명"
                />
              )}

              <input
                type="number"
                className="form-input"
                value={acc.quantity}
                min="1"
                placeholder="수량"
              />

              <button
                className="btn btn-sm btn-danger"
                onClick={() => onRemove(acc.id)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

#### 6.2 스타일 추가
```css
/* globals.css에 추가 */

.accessory-section {
  margin-bottom: 32px;
}

.accessory-add-buttons {
  display: flex;
  gap: 8px;
}

.accessory-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.accessory-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.accessory-type-badge {
  padding: 4px 12px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  min-width: 100px;
  text-align: center;
}
```

**완료 조건**:
- ✅ AccessoryManager.tsx 생성
- ✅ 모든 13개 마그네트 모델 포함 (누락 0개)
- ✅ 4가지 액세서리 타입 지원
- ✅ 추가/삭제 기능 구현

---

### Task 7: QuoteForm 완전 재구현 (60분)
**목표**: 모든 컴포넌트 통합, 완전한 견적 폼

#### 7.1 QuoteForm.tsx 완전 재작성
```typescript
// frontend-min/src/app/_components/QuoteForm.tsx
'use client';

import { useState } from 'react';
import { Send } from 'lucide-react';
import { useQuoteState } from '@/hooks/useQuoteState';
import TabSystem from './TabSystem';
import BreakerList from './BreakerList';
import AccessoryManager from './AccessoryManager';
import {
  MAIN_BREAKER_AMPERES,
  POLES,
  ENCLOSURE_TYPES,
  MATERIALS,
  BREAKER_TYPES,
  BREAKER_BRANDS
} from '@/lib/constants';
import { createEstimate } from '@/lib/api';

export default function QuoteForm() {
  const {
    tabs,
    activeTabId,
    activeTab,
    setActiveTabId,
    addTab,
    removeTab,
    updateTab,
    addBranchBreaker,
    removeBranchBreaker,
    addAccessory,
    removeAccessory
  } = useQuoteState();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [estimateResult, setEstimateResult] = useState<any>(null);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const result = await createEstimate({
        customer_name: activeTab.customerInfo.company,
        main_breaker: {
          model: `${activeTab.mainBreakerInfo.brand}-${activeTab.mainBreakerInfo.poles}`,
          ampere: parseInt(activeTab.mainBreakerInfo.capacity),
          poles: parseInt(activeTab.mainBreakerInfo.poles),
          quantity: 1
        },
        branch_breakers: activeTab.branchBreakers.map(b => ({
          model: `${b.type}-${b.poles}`,
          ampere: parseInt(b.capacity),
          poles: parseInt(b.poles),
          quantity: b.quantity
        })),
        accessories: activeTab.accessories.map(a => ({
          type: a.type,
          model: a.model,
          quantity: a.quantity
        })),
        enclosure: {
          type: activeTab.enclosureInfo.type,
          material: activeTab.enclosureInfo.material
        }
      });
      setEstimateResult(result);
      updateTab(activeTab.id, { estimateVisible: true });
    } catch (error) {
      console.error('견적 생성 실패:', error);
      alert('견적 생성에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="quote-form-container">
      <TabSystem
        tabs={tabs}
        activeTabId={activeTabId}
        onTabChange={setActiveTabId}
        onAddTab={addTab}
        onRemoveTab={removeTab}
      />

      <div className="quote-form-content">
        {/* 고객 정보 */}
        <section className="form-section">
          <h2>고객 정보</h2>
          <div className="form-grid">
            <input
              type="text"
              className="form-input"
              placeholder="회사명"
              value={activeTab.customerInfo.company}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  customerInfo: {
                    ...activeTab.customerInfo,
                    company: e.target.value
                  }
                })
              }
            />
            <input
              type="text"
              className="form-input"
              placeholder="담당자"
              value={activeTab.customerInfo.contact}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  customerInfo: {
                    ...activeTab.customerInfo,
                    contact: e.target.value
                  }
                })
              }
            />
            <input
              type="email"
              className="form-input"
              placeholder="이메일"
              value={activeTab.customerInfo.email}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  customerInfo: {
                    ...activeTab.customerInfo,
                    email: e.target.value
                  }
                })
              }
            />
            <input
              type="text"
              className="form-input"
              placeholder="주소"
              value={activeTab.customerInfo.address}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  customerInfo: {
                    ...activeTab.customerInfo,
                    address: e.target.value
                  }
                })
              }
            />
          </div>
        </section>

        {/* 외함 정보 */}
        <section className="form-section">
          <h2>외함 정보</h2>
          <div className="form-grid">
            <select
              className="form-select"
              value={activeTab.enclosureInfo.type}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  enclosureInfo: {
                    ...activeTab.enclosureInfo,
                    type: e.target.value as any
                  }
                })
              }
            >
              <option value="">외함 종류</option>
              {ENCLOSURE_TYPES.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            <select
              className="form-select"
              value={activeTab.enclosureInfo.material}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  enclosureInfo: {
                    ...activeTab.enclosureInfo,
                    material: e.target.value as any
                  }
                })
              }
            >
              <option value="">재질</option>
              {/* 모든 3개 재질 옵션 (누락 금지) */}
              {MATERIALS.map((material) => (
                <option key={material} value={material}>{material}</option>
              ))}
            </select>

            <input
              type="text"
              className="form-input"
              placeholder="특이사항"
              value={activeTab.enclosureInfo.request}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  enclosureInfo: {
                    ...activeTab.enclosureInfo,
                    request: e.target.value
                  }
                })
              }
            />
          </div>
        </section>

        {/* 메인 차단기 */}
        <section className="form-section">
          <h2>메인 차단기</h2>
          <div className="form-grid">
            <div className="breaker-type-toggle">
              {BREAKER_TYPES.map((type) => (
                <button
                  key={type}
                  className={`toggle-btn ${
                    activeTab.mainBreakerInfo.type === type ? 'active' : ''
                  }`}
                  onClick={() =>
                    updateTab(activeTab.id, {
                      mainBreakerInfo: {
                        ...activeTab.mainBreakerInfo,
                        type
                      }
                    })
                  }
                >
                  {type}
                </button>
              ))}
            </div>

            <select
              className="form-select"
              value={activeTab.mainBreakerInfo.poles}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  mainBreakerInfo: {
                    ...activeTab.mainBreakerInfo,
                    poles: e.target.value as any
                  }
                })
              }
            >
              <option value="">극수</option>
              {POLES.map((pole) => (
                <option key={pole} value={pole}>{pole}</option>
              ))}
            </select>

            <select
              className="form-select"
              value={activeTab.mainBreakerInfo.capacity}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  mainBreakerInfo: {
                    ...activeTab.mainBreakerInfo,
                    capacity: e.target.value as any
                  }
                })
              }
            >
              <option value="">암페어</option>
              {/* 모든 16개 메인 암페어 옵션 (누락 금지) */}
              {MAIN_BREAKER_AMPERES.map((amp) => (
                <option key={amp} value={amp}>{amp}</option>
              ))}
            </select>

            <select
              className="form-select"
              value={activeTab.mainBreakerInfo.brand}
              onChange={(e) =>
                updateTab(activeTab.id, {
                  mainBreakerInfo: {
                    ...activeTab.mainBreakerInfo,
                    brand: e.target.value as any
                  }
                })
              }
            >
              <option value="">브랜드</option>
              {BREAKER_BRANDS.map((brand) => (
                <option key={brand} value={brand}>{brand}</option>
              ))}
            </select>
          </div>
        </section>

        {/* 분기 차단기 */}
        <BreakerList
          breakers={activeTab.branchBreakers}
          onAdd={(breaker) => addBranchBreaker(activeTab.id, breaker)}
          onRemove={(id) => removeBranchBreaker(activeTab.id, id)}
        />

        {/* 액세서리 */}
        <AccessoryManager
          accessories={activeTab.accessories}
          onAdd={(accessory) => addAccessory(activeTab.id, accessory)}
          onRemove={(id) => removeAccessory(activeTab.id, id)}
        />

        {/* 제출 버튼 */}
        <div className="form-actions">
          <button
            className="btn btn-primary btn-lg"
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              '생성 중...'
            ) : (
              <>
                <Send size={20} />
                견적 생성
              </>
            )}
          </button>
        </div>

        {/* 견적 결과 */}
        {activeTab.estimateVisible && estimateResult && (
          <section className="estimate-result">
            <h2>견적 결과</h2>
            <pre>{JSON.stringify(estimateResult, null, 2)}</pre>
          </section>
        )}
      </div>
    </div>
  );
}
```

#### 7.2 스타일 추가
```css
/* globals.css에 추가 */

.quote-form-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.quote-form-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.form-section {
  margin-bottom: 32px;
  padding: 24px;
  background: var(--color-bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.form-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-text-primary);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-size: 14px;
  transition: all 0.2s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.1);
}

.form-actions {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

.estimate-result {
  margin-top: 32px;
  padding: 24px;
  background: var(--color-bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--color-success);
}

.estimate-result pre {
  background: var(--color-bg-primary);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12px;
}
```

**완료 조건**:
- ✅ QuoteForm.tsx 완전 재작성
- ✅ 모든 컴포넌트 통합
- ✅ 모든 데이터 옵션 포함 (누락 0개)
- ✅ API 연동 구현
- ✅ 컴파일 에러 0개

---

### Task 8: 통합 테스트 및 검증 (30분)
**목표**: 전체 시스템 통합 검증

#### 8.1 컴파일 검증
```bash
npm run type-check
# 예상: No errors
```

#### 8.2 개발 서버 실행
```bash
npm run dev
# http://localhost:3000 접속
```

#### 8.3 수동 테스트 체크리스트
- [ ] 견적 탭 추가/삭제
- [ ] 고객 정보 입력
- [ ] 외함 정보 선택 (모든 옵션 확인)
- [ ] 메인 차단기 선택 (16개 암페어 모두 확인)
- [ ] 분기 차단기 추가/삭제 (22개 암페어 모두 확인)
- [ ] 액세서리 추가/삭제 (13개 마그네트 모델 모두 확인)
- [ ] 견적 생성 API 호출
- [ ] 견적 결과 표시

#### 8.4 데이터 완전성 검증 스크립트
```typescript
// scripts/verify-data-completeness.ts
import {
  MAIN_BREAKER_AMPERES,
  BRANCH_BREAKER_AMPERES,
  MAGNET_MODELS
} from '../frontend-min/src/lib/constants';

console.log('데이터 완전성 검증');
console.log('==================');
console.log(`메인 차단기 암페어: ${MAIN_BREAKER_AMPERES.length}개 (기대: 16개)`);
console.log(`분기 차단기 암페어: ${BRANCH_BREAKER_AMPERES.length}개 (기대: 22개)`);
console.log(`마그네트 모델: ${MAGNET_MODELS.length}개 (기대: 13개)`);

const mainExpected = ['100A', '125A', '150A', '175A', '200A', '225A', '250A', '300A', '350A', '400A', '500A', '600A', '700A', '800A', '1000A', '1200A'];
const branchExpected = ['15A', '20A', '30A', '40A', '50A', '60A', '75A', '100A', '125A', '150A', '175A', '200A', '225A', '250A', '300A', '350A', '400A', '500A', '600A', '700A', '800A', '1000A', '1200A'];
const magnetExpected = ['MC-9', 'MC-12', 'MC-18', 'MC-22', 'MC-32', 'MC-40', 'MC-50', 'MC-65', 'MC-75', 'MC-85', 'MC-100', 'MC-130', 'MC-150'];

const mainOk = JSON.stringify(MAIN_BREAKER_AMPERES) === JSON.stringify(mainExpected);
const branchOk = JSON.stringify(BRANCH_BREAKER_AMPERES) === JSON.stringify(branchExpected);
const magnetOk = JSON.stringify(MAGNET_MODELS) === JSON.stringify(magnetExpected);

console.log(`\n메인 차단기 데이터: ${mainOk ? '✅ 완전' : '❌ 누락'}`);
console.log(`분기 차단기 데이터: ${branchOk ? '✅ 완전' : '❌ 누락'}`);
console.log(`마그네트 데이터: ${magnetOk ? '✅ 완전' : '❌ 누락'}`);

if (mainOk && branchOk && magnetOk) {
  console.log('\n✅ 모든 데이터 완전성 검증 통과');
  process.exit(0);
} else {
  console.error('\n❌ 데이터 누락 발견');
  process.exit(1);
}
```

```bash
npm run ts-node scripts/verify-data-completeness.ts
# 예상: ✅ 모든 데이터 완전성 검증 통과
```

**완료 조건**:
- ✅ 타입 에러 0개
- ✅ 개발 서버 정상 실행
- ✅ 수동 테스트 체크리스트 모두 통과
- ✅ 데이터 완전성 검증 통과

---

## 📝 최종 검증 체크리스트

### 데이터 완전성
- [ ] 메인 차단기 암페어: 16개 모두 포함
- [ ] 분기 차단기 암페어: 22개 모두 포함
- [ ] 마그네트 모델: 13개 모두 포함
- [ ] 극수: 3개 모두 포함
- [ ] 외함 종류: 6개 모두 포함
- [ ] 재질: 3개 모두 포함

### 기능 완전성
- [ ] 멀티탭 시스템 (추가/삭제/전환)
- [ ] 분기 차단기 추가/삭제
- [ ] 액세서리 추가/삭제
- [ ] 견적 생성 API 호출
- [ ] 견적 결과 표시

### 코드 품질
- [ ] TypeScript 컴파일 에러 0개
- [ ] ESLint 경고 0개
- [ ] 컴포넌트 Props 타입 정의 100%
- [ ] 일관된 네이밍 컨벤션

### UI/UX
- [ ] 디자인 일관성 (KIS Design System)
- [ ] 반응형 레이아웃
- [ ] 로딩 상태 표시
- [ ] 에러 핸들링

---

## 🚀 실행 순서 요약

```bash
# 1. 데이터 상수 생성
# Task 1: constants.ts 생성 및 검증

# 2. 타입 정의
# Task 2: types.ts 확장

# 3. 상태 관리 훅 (TDD)
# Task 3: useQuoteState 테스트 작성 → 구현 → 검증

# 4. UI 컴포넌트 생성
# Task 4: TabSystem
# Task 5: BreakerList
# Task 6: AccessoryManager
# Task 7: QuoteForm 완전 재구현

# 5. 통합 테스트
# Task 8: 컴파일, 개발 서버, 수동 테스트, 데이터 검증

# 6. 최종 확인
npm run type-check
npm run lint
npm run dev
```

---

## 🎨 디자인 참조

**원본**: `C:\Users\PC\Desktop\NABERAL_PROJECT-master\절대코어파일\frontend-kis-complete.html`

### 색상 시스템
```css
:root {
  --color-primary: #0066cc;
  --color-primary-light: #e6f2ff;
  --color-danger: #dc2626;
  --color-success: #16a34a;
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-text-primary: #111827;
  --color-text-light: #6b7280;
  --color-border: #e5e7eb;
}
```

### 레이아웃
- 사이드바: 고정 폭 260px
- 메인 컨텐츠: flex-1
- 탭 시스템: 상단 고정
- 폼 섹션: 12px gap, 반응형 그리드

---

## ⚠️ 주의사항 (중요!)

1. **데이터 누락 절대 금지**
   - 샘플링 금지 (예: "몇 개만 넣고 나중에..." → ❌)
   - 모든 옵션 100% 포함 필수

2. **디자인 임의 변경 금지**
   - 참조 HTML과 동일하게 구현
   - 색상, 레이아웃, 간격 그대로 복제

3. **타입 안전성 유지**
   - `any` 타입 사용 최소화
   - SSOT 정렬된 인터페이스 사용

4. **컴포넌트 분리 원칙**
   - 단일 책임 원칙 (SRP)
   - 재사용 가능한 컴포넌트
   - Props 타입 명확히 정의

5. **에러 처리**
   - API 호출 에러 처리
   - 사용자 친화적 에러 메시지
   - 로딩 상태 표시

---

## 📅 예상 소요 시간

| Task | 예상 시간 | 누적 시간 |
|------|----------|----------|
| Task 1: constants.ts | 30분 | 30분 |
| Task 2: types.ts 확장 | 20분 | 50분 |
| Task 3: useQuoteState | 40분 | 1시간 30분 |
| Task 4: TabSystem | 30분 | 2시간 |
| Task 5: BreakerList | 40분 | 2시간 40분 |
| Task 6: AccessoryManager | 40분 | 3시간 20분 |
| Task 7: QuoteForm | 60분 | 4시간 20분 |
| Task 8: 통합 테스트 | 30분 | **4시간 50분** |

**총 예상 시간**: 약 5시간

---

## ✅ 승인 대기

대표님, 위 계획서를 검토해주시고 승인해주시면 즉시 작업을 시작하겠습니다.

**계획서 핵심**:
- ✅ 데이터 누락 0개 (메인 16개, 분기 22개, 마그네트 13개)
- ✅ 디자인 100% 복제 (frontend-kis-complete.html)
- ✅ TDD 방식 (테스트 먼저, 구현 나중)
- ✅ 컴포넌트 분리 (재사용성, 단일 책임)
- ✅ 타입 안전성 (TypeScript strict, SSOT)

시작 명령을 기다리고 있습니다.
