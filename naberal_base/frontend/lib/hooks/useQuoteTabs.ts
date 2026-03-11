/**
 * Quote Tabs Store
 * Zustand store for managing multiple quote tabs with sessionStorage persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { BreakerInput, AccessoryInput, EstimateResponse } from '../types/estimate';

// Customer information interface
export interface CustomerInfo {
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  projectName?: string;
}

// Enclosure information interface
export interface EnclosureInfo {
  type?: string;
  material?: string;
  width?: number;
  height?: number;
  depth?: number;
}

// Breaker item with UI metadata
export interface BreakerItem extends BreakerInput {
  id: string;
  quantity: number;
}

// Accessory item with UI metadata
export interface AccessoryItem extends AccessoryInput {
  id: string;
}

// Tab state interface
export interface Tab {
  id: number;
  title: string;
  customerInfo: CustomerInfo;
  enclosureInfo: EnclosureInfo;
  mainBreaker: BreakerItem | null;
  branchBreakers: BreakerItem[];
  accessories: AccessoryItem[];
  estimateVisible: boolean;
  estimateResult?: EstimateResponse;
  isDirty: boolean; // Track if tab has unsaved changes
}

// Store state interface
interface QuoteTabsState {
  tabs: Tab[];
  activeTabId: number;
  nextId: number;

  // Actions
  addTab: () => void;
  closeTab: (id: number) => boolean;
  setActiveTab: (id: number) => void;
  updateTab: (id: number, data: Partial<Tab>) => void;
  updateCustomerInfo: (id: number, data: Partial<CustomerInfo>) => void;
  updateEnclosureInfo: (id: number, data: Partial<EnclosureInfo>) => void;
  updateMainBreaker: (id: number, breaker: BreakerItem | null) => void;
  addBranchBreaker: (id: number, breaker: BreakerItem) => void;
  removeBranchBreaker: (id: number, breakerId: string) => void;
  updateBranchBreaker: (id: number, breakerId: string, data: Partial<BreakerItem>) => void;
  addAccessory: (id: number, accessory: AccessoryItem) => void;
  removeAccessory: (id: number, accessoryId: string) => void;
  updateAccessory: (id: number, accessoryId: string, data: Partial<AccessoryItem>) => void;
  setEstimateResult: (id: number, result: EstimateResponse) => void;
  showEstimate: (id: number, show: boolean) => void;
  renameTab: (id: number, title: string) => void;
  clearTab: (id: number) => void;
}

// Create default tab
const createDefaultTab = (id: number, nextId: number): Tab => ({
  id,
  title: `견적서 ${nextId}`,
  customerInfo: {
    name: '',
  },
  enclosureInfo: {},
  mainBreaker: null,
  branchBreakers: [],
  accessories: [],
  estimateVisible: false,
  isDirty: false,
});

// Check if tab has any data
const hasTabData = (tab: Tab): boolean => {
  return (
    tab.customerInfo.name !== '' ||
    tab.customerInfo.email !== undefined ||
    tab.customerInfo.phone !== undefined ||
    tab.customerInfo.company !== undefined ||
    tab.customerInfo.projectName !== undefined ||
    tab.mainBreaker !== null ||
    tab.branchBreakers.length > 0 ||
    tab.accessories.length > 0 ||
    tab.estimateResult !== undefined
  );
};

export const useQuoteTabs = create<QuoteTabsState>()(
  persist(
    (set, get) => ({
      tabs: [createDefaultTab(1, 1)],
      activeTabId: 1,
      nextId: 2,

      addTab: () => {
        set((state) => {
          const newTab = createDefaultTab(state.nextId, state.nextId);
          return {
            tabs: [...state.tabs, newTab],
            activeTabId: newTab.id,
            nextId: state.nextId + 1,
          };
        });
      },

      closeTab: (id: number) => {
        const state = get();
        const tab = state.tabs.find((t) => t.id === id);

        // Don't close if it's the last tab
        if (state.tabs.length === 1) {
          return false;
        }

        // Check if tab has data and needs confirmation
        if (tab && hasTabData(tab) && tab.isDirty) {
          const confirmed = window.confirm(
            '이 탭에는 저장되지 않은 변경사항이 있습니다. 정말 닫으시겠습니까?'
          );
          if (!confirmed) {
            return false;
          }
        }

        set((state) => {
          const newTabs = state.tabs.filter((t) => t.id !== id);
          let newActiveId = state.activeTabId;

          // If closing active tab, switch to another tab
          if (id === state.activeTabId) {
            const closingIndex = state.tabs.findIndex((t) => t.id === id);
            // Switch to previous tab if exists, otherwise next tab
            newActiveId = closingIndex > 0
              ? state.tabs[closingIndex - 1].id
              : newTabs[0].id;
          }

          return {
            tabs: newTabs,
            activeTabId: newActiveId,
          };
        });

        return true;
      },

      setActiveTab: (id: number) => {
        set({ activeTabId: id });
      },

      updateTab: (id: number, data: Partial<Tab>) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? { ...tab, ...data, isDirty: true }
              : tab
          ),
        }));
      },

      updateCustomerInfo: (id: number, data: Partial<CustomerInfo>) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  customerInfo: { ...tab.customerInfo, ...data },
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      updateEnclosureInfo: (id: number, data: Partial<EnclosureInfo>) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  enclosureInfo: { ...tab.enclosureInfo, ...data },
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      updateMainBreaker: (id: number, breaker: BreakerItem | null) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? { ...tab, mainBreaker: breaker, isDirty: true }
              : tab
          ),
        }));
      },

      addBranchBreaker: (id: number, breaker: BreakerItem) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  branchBreakers: [...tab.branchBreakers, breaker],
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      removeBranchBreaker: (id: number, breakerId: string) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  branchBreakers: tab.branchBreakers.filter((b) => b.id !== breakerId),
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      updateBranchBreaker: (id: number, breakerId: string, data: Partial<BreakerItem>) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  branchBreakers: tab.branchBreakers.map((b) =>
                    b.id === breakerId ? { ...b, ...data } : b
                  ),
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      addAccessory: (id: number, accessory: AccessoryItem) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  accessories: [...tab.accessories, accessory],
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      removeAccessory: (id: number, accessoryId: string) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  accessories: tab.accessories.filter((a) => a.id !== accessoryId),
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      updateAccessory: (id: number, accessoryId: string, data: Partial<AccessoryItem>) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  accessories: tab.accessories.map((a) =>
                    a.id === accessoryId ? { ...a, ...data } : a
                  ),
                  isDirty: true,
                }
              : tab
          ),
        }));
      },

      setEstimateResult: (id: number, result: EstimateResponse) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? {
                  ...tab,
                  estimateResult: result,
                  estimateVisible: true,
                  isDirty: false, // Mark as saved after estimate
                }
              : tab
          ),
        }));
      },

      showEstimate: (id: number, show: boolean) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? { ...tab, estimateVisible: show }
              : tab
          ),
        }));
      },

      renameTab: (id: number, title: string) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? { ...tab, title }
              : tab
          ),
        }));
      },

      clearTab: (id: number) => {
        set((state) => ({
          tabs: state.tabs.map((tab) =>
            tab.id === id
              ? createDefaultTab(id, id)
              : tab
          ),
        }));
      },
    }),
    {
      name: 'kis-quote-tabs',
      version: 1,
    }
  )
);
