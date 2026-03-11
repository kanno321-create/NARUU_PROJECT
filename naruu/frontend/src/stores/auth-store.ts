import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";

interface User {
  id: number;
  email: string;
  name_ko: string;
  name_ja: string | null;
  role: "admin" | "manager" | "staff";
  is_active: boolean;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const data = await api.post<{
            access_token: string;
            refresh_token: string;
          }>("/auth/login", { email, password }, { skipAuth: true });

          set({
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            isLoading: false,
          });

          // Fetch user profile after login
          await get().fetchUser();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
        });
      },

      fetchUser: async () => {
        try {
          const user = await api.get<User>("/auth/me");
          set({ user });
        } catch {
          set({ user: null });
        }
      },
    }),
    {
      name: "naruu-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
