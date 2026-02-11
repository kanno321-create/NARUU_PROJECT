import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  sidebarCollapsed: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: (() => {
    try {
      const stored = localStorage.getItem('naruu_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  })(),
  isAuthenticated: !!localStorage.getItem('naruu_token'),
  sidebarCollapsed: false,

  login: (user, token) => {
    localStorage.setItem('naruu_token', token);
    localStorage.setItem('naruu_user', JSON.stringify(user));
    set({ user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('naruu_token');
    localStorage.removeItem('naruu_user');
    set({ user: null, isAuthenticated: false });
  },

  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}));
