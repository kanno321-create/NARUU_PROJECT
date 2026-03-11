'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

// Theme types including Claude theme
export type ThemeType =
  | 'claude'      // Claude.ai warm beige (Default)
  | 'claude-dark' // Claude.ai dark mode
  | 'light'       // Default light
  | 'dark'        // Professional dark
  | 'midnight'    // Elegant blue-black (Cool)
  | 'ocean'       // Deep blue (Cool)
  | 'forest'      // Nature green (Cool)
  | 'pink'        // Sweet & lovely (Cute)
  | 'lavender'    // Soft & dreamy (Cute)
  | 'peach'       // Warm & cozy (Cute)
  | 'sakura';     // Cherry blossom (Cute)

export interface ThemeInfo {
  id: ThemeType;
  name: string;
  nameKo: string;
  description: string;
  category: 'basic' | 'cool' | 'cute' | 'claude';
  preview: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

export const THEMES: ThemeInfo[] = [
  {
    id: 'claude',
    name: 'Claude',
    nameKo: '클로드',
    description: 'Claude.ai 스타일 웜 베이지',
    category: 'claude',
    preview: { primary: '#F5EDE6', secondary: '#FFFFFF', accent: '#D97756' }
  },
  {
    id: 'claude-dark',
    name: 'Claude Dark',
    nameKo: '클로드 다크',
    description: 'Claude.ai 다크 모드',
    category: 'claude',
    preview: { primary: '#2D2A26', secondary: '#3D3929', accent: '#D97756' }
  },
  {
    id: 'light',
    name: 'Light',
    nameKo: '라이트',
    description: '기본 밝은 테마',
    category: 'basic',
    preview: { primary: '#ffffff', secondary: '#f3f2f1', accent: '#10a37f' }
  },
  {
    id: 'dark',
    name: 'Dark',
    nameKo: '다크',
    description: '눈이 편한 다크 모드',
    category: 'basic',
    preview: { primary: '#1e1e1e', secondary: '#2d2d2d', accent: '#10a37f' }
  },
  {
    id: 'midnight',
    name: 'Midnight',
    nameKo: '미드나잇',
    description: '우아한 블루-블랙',
    category: 'cool',
    preview: { primary: '#0f172a', secondary: '#1e293b', accent: '#6366f1' }
  },
  {
    id: 'ocean',
    name: 'Ocean',
    nameKo: '오션',
    description: '깊고 시원한 바다',
    category: 'cool',
    preview: { primary: '#082f49', secondary: '#0c4a6e', accent: '#0ea5e9' }
  },
  {
    id: 'forest',
    name: 'Forest',
    nameKo: '포레스트',
    description: '자연의 푸른 숲',
    category: 'cool',
    preview: { primary: '#052e16', secondary: '#14532d', accent: '#22c55e' }
  },
  {
    id: 'pink',
    name: 'Pink',
    nameKo: '핑크',
    description: '달콤한 핑크빛',
    category: 'cute',
    preview: { primary: '#fdf2f8', secondary: '#fce7f3', accent: '#ec4899' }
  },
  {
    id: 'lavender',
    name: 'Lavender',
    nameKo: '라벤더',
    description: '부드러운 보라빛',
    category: 'cute',
    preview: { primary: '#faf5ff', secondary: '#f3e8ff', accent: '#a855f7' }
  },
  {
    id: 'peach',
    name: 'Peach',
    nameKo: '피치',
    description: '따뜻한 복숭아빛',
    category: 'cute',
    preview: { primary: '#fff7ed', secondary: '#ffedd5', accent: '#f97316' }
  },
  {
    id: 'sakura',
    name: 'Sakura',
    nameKo: '벚꽃',
    description: '봄날의 벚꽃',
    category: 'cute',
    preview: { primary: '#fff1f7', secondary: '#fce7f3', accent: '#f9a8d4' }
  }
];

interface ThemeContextType {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  themeInfo: ThemeInfo;
  themes: ThemeInfo[];
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'kis-theme';
const DEFAULT_THEME: ThemeType = 'claude'; // Claude theme as default

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<ThemeType>(DEFAULT_THEME);
  const [mounted, setMounted] = useState(false);

  // Load theme from localStorage on mount
  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem(STORAGE_KEY) as ThemeType;
    if (savedTheme && THEMES.find(t => t.id === savedTheme)) {
      setThemeState(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      // Set default Claude theme if no saved theme
      document.documentElement.setAttribute('data-theme', DEFAULT_THEME);
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    if (mounted) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem(STORAGE_KEY, theme);
    }
  }, [theme, mounted]);

  const setTheme = (newTheme: ThemeType) => {
    setThemeState(newTheme);
  };

  const themeInfo = THEMES.find(t => t.id === theme) || THEMES[0];
  const isDark = ['dark', 'midnight', 'ocean', 'forest', 'claude-dark'].includes(theme);

  // Prevent hydration mismatch - but still provide context
  if (!mounted) {
    return (
      <ThemeContext.Provider value={{ theme: DEFAULT_THEME, setTheme: () => {}, themeInfo: THEMES[0], themes: THEMES, isDark: false }}>
        <div style={{ visibility: 'hidden' }}>
          {children}
        </div>
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themeInfo, themes: THEMES, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Helper hook to get theme category
export function useThemeCategory() {
  const { themeInfo } = useTheme();
  return themeInfo.category;
}
