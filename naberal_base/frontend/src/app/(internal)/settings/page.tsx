'use client';

import React, { useState, useEffect } from 'react';
import { useTheme, THEMES, ThemeType, ThemeInfo } from '@/contexts/ThemeContext';
import { useAuth, User } from '@/contexts/AuthContext';
import { fetchAPI } from '@/lib/api';

interface UserProfile {
  id: string;
  name: string;
  email: string;
  company: string;
  role: string;
  phone: string;
  department: string;
  avatar?: string;
  createdAt: string;
}

interface QuoteDefaults {
  breakerBrand: 'sangdo' | 'ls';
  breakerType: 'economy' | 'standard';
  enclosureType: 'indoor' | 'outdoor' | 'standing';
  enclosureMaterial: 'steel16' | 'steel10' | 'sus201';
  marginPercent: number;
  includeVAT: boolean;
}

interface ShortcutSettings {
  newQuote: string;
  saveQuote: string;
  exportPDF: string;
  search: string;
  toggleSidebar: string;
}

interface PrintSettings {
  paperSize: 'A4' | 'A3' | 'Letter';
  orientation: 'portrait' | 'landscape';
  includeLogo: boolean;
  includeTerms: boolean;
  colorMode: 'color' | 'grayscale';
}

interface AutoSaveSettings {
  enabled: boolean;
  intervalMinutes: number;
  showNotification: boolean;
}

interface NotificationSettings {
  quoteExpiry: boolean;
  priceUpdate: boolean;
  systemUpdate: boolean;
  dailyReport: boolean;
  reportTime: string;
}

interface ExportSettings {
  defaultFormat: 'xlsx' | 'pdf' | 'both';
  includeImages: boolean;
  compressFiles: boolean;
  autoOpen: boolean;
}

interface SessionSettings {
  timeoutMinutes: number;
  rememberLogin: boolean;
  showLastLogin: boolean;
}

interface SMTPSettings {
  host: string;
  port: number;
  username: string;
  password: string;
  useTLS: boolean;
  senderName: string;
  senderEmail: string;
}

interface AISettings {
  model: 'claude-sonnet' | 'claude-opus' | 'claude-haiku';
  temperature: number;
  maxTokens: number;
  autoEstimate: boolean;
  priceUpdateInterval: number;
}

export default function SettingsPage() {
  const { theme, setTheme, themes, isDark } = useTheme();
  const { user: authUser, users, createUser, deleteUser, updateUserPassword } = useAuth();

  const [activeTab, setActiveTab] = useState<string>('theme');

  // User Management State (CEO only)
  const [newUserForm, setNewUserForm] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    name: '',
    role: 'staff' as 'ceo' | 'manager' | 'staff'
  });
  const [editPasswordForm, setEditPasswordForm] = useState({
    userId: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(true);

  // User Profile State
  const [profile, setProfile] = useState<UserProfile>({
    id: 'user-001',
    name: '김대표',
    email: 'ceo@koreaindustry.co.kr',
    company: '(주)한국산업',
    role: '대표이사',
    phone: '010-1234-5678',
    department: '경영진',
    createdAt: '2024-01-15T00:00:00Z'
  });

  // Quote Defaults
  const [quoteDefaults, setQuoteDefaults] = useState<QuoteDefaults>({
    breakerBrand: 'sangdo',
    breakerType: 'economy',
    enclosureType: 'indoor',
    enclosureMaterial: 'steel16',
    marginPercent: 15,
    includeVAT: true
  });

  // Shortcuts
  const [shortcuts, setShortcuts] = useState<ShortcutSettings>({
    newQuote: 'Ctrl+N',
    saveQuote: 'Ctrl+S',
    exportPDF: 'Ctrl+P',
    search: 'Ctrl+K',
    toggleSidebar: 'Ctrl+B'
  });

  // Print Settings
  const [printSettings, setPrintSettings] = useState<PrintSettings>({
    paperSize: 'A4',
    orientation: 'portrait',
    includeLogo: true,
    includeTerms: true,
    colorMode: 'color'
  });

  // Auto Save
  const [autoSave, setAutoSave] = useState<AutoSaveSettings>({
    enabled: true,
    intervalMinutes: 5,
    showNotification: true
  });

  // Notifications
  const [notifications, setNotifications] = useState<NotificationSettings>({
    quoteExpiry: true,
    priceUpdate: true,
    systemUpdate: false,
    dailyReport: true,
    reportTime: '09:00'
  });

  // Export Settings
  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    defaultFormat: 'both',
    includeImages: true,
    compressFiles: false,
    autoOpen: true
  });

  // Session Settings
  const [sessionSettings, setSessionSettings] = useState<SessionSettings>({
    timeoutMinutes: 60,
    rememberLogin: true,
    showLastLogin: true
  });

  // SMTP Settings
  const [smtpSettings, setSmtpSettings] = useState<SMTPSettings>({
    host: 'smtp.worksmobile.com',
    port: 587,
    username: '',
    password: '',
    useTLS: true,
    senderName: '(주)한국산업',
    senderEmail: 'noreply@koreaindustry.co.kr'
  });

  // AI Settings
  const [aiSettings, setAiSettings] = useState<AISettings>({
    model: 'claude-sonnet',
    temperature: 0.7,
    maxTokens: 4096,
    autoEstimate: true,
    priceUpdateInterval: 24
  });

  // Password change
  const [passwordForm, setPasswordForm] = useState({
    current: '',
    new: '',
    confirm: ''
  });

  // Load settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('kis-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        if (parsed.quoteDefaults) setQuoteDefaults(parsed.quoteDefaults);
        if (parsed.shortcuts) setShortcuts(parsed.shortcuts);
        if (parsed.printSettings) setPrintSettings(parsed.printSettings);
        if (parsed.autoSave) setAutoSave(parsed.autoSave);
        if (parsed.notifications) setNotifications(parsed.notifications);
        if (parsed.exportSettings) setExportSettings(parsed.exportSettings);
        if (parsed.sessionSettings) setSessionSettings(parsed.sessionSettings);
        if (parsed.aiSettings) setAiSettings(parsed.aiSettings);
      } catch (e) {
        console.error('Failed to load settings:', e);
      }
    }

    // Load saved profile avatar
    const savedAvatar = localStorage.getItem('kis-profile-avatar');
    if (savedAvatar) {
      setProfile(prev => ({ ...prev, avatar: savedAvatar }));
    }
  }, []);

  const handleSaveSettings = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const settings = {
        quoteDefaults,
        shortcuts,
        printSettings,
        autoSave,
        notifications,
        exportSettings,
        sessionSettings,
        aiSettings
      };
      localStorage.setItem('kis-settings', JSON.stringify(settings));

      // Dispatch events so other components can react to settings changes
      window.dispatchEvent(new CustomEvent('kis-settings-updated', {
        detail: settings
      }));

      if (settings.notifications) {
        window.dispatchEvent(new CustomEvent('kis-notification-settings-updated', {
          detail: settings.notifications
        }));
      }


      // 이메일 설정 변경 알림
      window.dispatchEvent(new CustomEvent('kis-email-settings-changed', {
        detail: settings
      }));
      setSuccess('설정이 저장되었습니다.');
    } catch (err) {
      setError('설정 저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (confirm('정말 로그아웃 하시겠습니까?')) {
      setLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 500));
        setIsLoggedIn(false);
        setSuccess('로그아웃되었습니다.');
      } catch (err) {
        setError('로그아웃에 실패했습니다.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setIsLoggedIn(true);
      setSuccess('로그인되었습니다.');
    } catch (err) {
      setError('로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.new.length < 8) {
      setError('비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }
    if (passwordForm.new !== passwordForm.confirm) {
      setError('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    if (!authUser?.id) {
      setError('로그인 정보를 확인할 수 없습니다. 다시 로그인해주세요.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await fetchAPI(`/v1/users/${authUser.id}/password`, {
        method: 'PUT',
        body: JSON.stringify({
          current_password: passwordForm.current,
          new_password: passwordForm.new,
        }),
      });
      setSuccess('비밀번호가 변경되었습니다.');
      setPasswordForm({ current: '', new: '', confirm: '' });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '비밀번호 변경에 실패했습니다.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Group themes by category
  const themesByCategory = {
    basic: themes.filter(t => t.category === 'basic'),
    cool: themes.filter(t => t.category === 'cool'),
    cute: themes.filter(t => t.category === 'cute')
  };

  const baseTabs = [
    { id: 'theme', label: '테마', icon: '🎨' },
    { id: 'account', label: '계정 관리', icon: '👤' },
    { id: 'quote', label: '견적 기본값', icon: '📋' },
    { id: 'shortcuts', label: '단축키', icon: '⌨️' },
    { id: 'print', label: '인쇄/PDF', icon: '🖨️' },
    { id: 'autosave', label: '자동 저장', icon: '💾' },
    { id: 'notifications', label: '알림', icon: '🔔' },
    { id: 'export', label: '내보내기', icon: '📤' },
    { id: 'session', label: '세션', icon: '⏱️' },
    { id: 'email', label: '이메일', icon: '✉️' },
    { id: 'ai', label: 'AI 설정', icon: '🤖' },
    { id: 'security', label: '보안', icon: '🔒' },
    { id: 'about', label: '정보', icon: 'ℹ️' },
  ];

  // CEO 전용 탭 추가
  const tabs = authUser?.role === 'ceo'
    ? [...baseTabs.slice(0, 2), { id: 'users', label: '사용자 관리', icon: '👥' }, ...baseTabs.slice(2)]
    : baseTabs;

  const ThemeCard = ({ themeInfo }: { themeInfo: ThemeInfo }) => (
    <button
      onClick={() => setTheme(themeInfo.id)}
      className={`relative p-4 rounded-xl border-2 transition-all duration-300 hover:scale-105 ${
        theme === themeInfo.id
          ? 'border-blue-500 ring-2 ring-blue-200 shadow-lg'
          : 'border-gray-200 hover:border-gray-300'
      }`}
      style={{ backgroundColor: themeInfo.preview.primary }}
    >
      {/* Preview Colors */}
      <div className="flex gap-1 mb-3">
        <div
          className="w-6 h-6 rounded-full shadow-inner"
          style={{ backgroundColor: themeInfo.preview.primary }}
        />
        <div
          className="w-6 h-6 rounded-full shadow-inner"
          style={{ backgroundColor: themeInfo.preview.secondary }}
        />
        <div
          className="w-6 h-6 rounded-full shadow-inner"
          style={{ backgroundColor: themeInfo.preview.accent }}
        />
      </div>

      {/* Theme Name */}
      <div className="text-left">
        <p className="font-bold" style={{ color: themeInfo.preview.accent }}>
          {themeInfo.nameKo}
        </p>
        <p className="text-xs opacity-70" style={{
          color: themeInfo.category === 'cute' ? '#666' :
                 themeInfo.category === 'cool' ? '#aaa' : '#888'
        }}>
          {themeInfo.description}
        </p>
      </div>

      {/* Selected Check */}
      {theme === themeInfo.id && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
          <span className="text-white text-sm">✓</span>
        </div>
      )}
    </button>
  );

  return (
    <div
      className="min-h-screen p-6 transition-colors duration-300"
      style={{ backgroundColor: 'var(--color-bg)' }}
    >
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div
          className="rounded-lg shadow-sm p-6 mb-6 transition-colors duration-300"
          style={{ backgroundColor: 'var(--color-surface)' }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>
                설정
              </h1>
              <span style={{ color: 'var(--color-text-subtle)' }}>|</span>
              <span style={{ color: 'var(--color-text-subtle)' }}>
                프로그램 전체 설정을 관리합니다
              </span>
            </div>
            <div className="flex items-center gap-3">
              {isLoggedIn ? (
                <button
                  onClick={handleLogout}
                  disabled={loading}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition disabled:opacity-50"
                >
                  로그아웃
                </button>
              ) : (
                <button
                  onClick={handleLogin}
                  disabled={loading}
                  className="px-4 py-2 text-white rounded-lg transition disabled:opacity-50"
                  style={{ backgroundColor: 'var(--color-brand)' }}
                >
                  로그인
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Alert Messages */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6 flex items-center justify-between">
            <span>{success}</span>
            <button onClick={() => setSuccess(null)} className="text-green-500 hover:text-green-700">
              ✕
            </button>
          </div>
        )}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
              ✕
            </button>
          </div>
        )}

        <div className="flex gap-6">
          {/* Sidebar Tabs */}
          <div
            className="w-64 rounded-lg shadow-sm p-4 transition-colors duration-300"
            style={{ backgroundColor: 'var(--color-surface)' }}
          >
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition ${
                    activeTab === tab.id
                      ? 'font-medium'
                      : ''
                  }`}
                  style={{
                    backgroundColor: activeTab === tab.id ? 'var(--color-surface-secondary)' : 'transparent',
                    color: activeTab === tab.id ? 'var(--color-brand)' : 'var(--color-text)'
                  }}
                >
                  <span className="text-xl">{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content Area */}
          <div
            className="flex-1 rounded-lg shadow-sm p-6 transition-colors duration-300"
            style={{ backgroundColor: 'var(--color-surface)' }}
          >
            {/* Theme Tab */}
            {activeTab === 'theme' && (
              <div className="space-y-8">
                <div className="border-b pb-4" style={{ borderColor: 'var(--color-border)' }}>
                  <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text)' }}>
                    테마 설정
                  </h2>
                  <p className="text-sm mt-1" style={{ color: 'var(--color-text-subtle)' }}>
                    원하는 테마를 선택하세요. 변경 사항은 즉시 적용됩니다.
                  </p>
                </div>

                {/* Basic Themes */}
                <div>
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--color-text)' }}>
                    <span>⚪</span> 기본 테마
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    {themesByCategory.basic.map((t) => (
                      <ThemeCard key={t.id} themeInfo={t} />
                    ))}
                  </div>
                </div>

                {/* Cool Themes */}
                <div>
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--color-text)' }}>
                    <span>🌙</span> 쿨 테마 (프로페셔널)
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    {themesByCategory.cool.map((t) => (
                      <ThemeCard key={t.id} themeInfo={t} />
                    ))}
                  </div>
                </div>

                {/* Cute Themes */}
                <div>
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-2" style={{ color: 'var(--color-text)' }}>
                    <span>🌸</span> 귀여운 테마
                  </h3>
                  <div className="grid grid-cols-4 gap-4">
                    {themesByCategory.cute.map((t) => (
                      <ThemeCard key={t.id} themeInfo={t} />
                    ))}
                  </div>
                </div>

                {/* Current Theme Info */}
                <div
                  className="p-4 rounded-lg"
                  style={{ backgroundColor: 'var(--color-surface-secondary)' }}
                >
                  <p style={{ color: 'var(--color-text-subtle)' }}>
                    현재 테마: <strong style={{ color: 'var(--color-brand)' }}>
                      {themes.find(t => t.id === theme)?.nameKo}
                    </strong>
                  </p>
                </div>
              </div>
            )}

            {/* Account Tab */}
            {activeTab === 'account' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  계정 관리
                </h2>

                {/* Profile Photo Section */}
                <div className="flex items-center gap-6 p-4 rounded-lg" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <div className="relative">
                    <div
                      className="w-24 h-24 rounded-full flex items-center justify-center overflow-hidden"
                      style={{
                        backgroundColor: profile.avatar ? 'transparent' : 'var(--color-brand)',
                        border: '3px solid var(--color-brand)'
                      }}
                    >
                      {profile.avatar ? (
                        <img
                          src={profile.avatar}
                          alt="프로필"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-3xl font-bold text-white">
                          {profile.name.charAt(0)}
                        </span>
                      )}
                    </div>
                    <label
                      className="absolute bottom-0 right-0 w-8 h-8 rounded-full flex items-center justify-center cursor-pointer transition-colors"
                      style={{ backgroundColor: 'var(--color-brand)' }}
                      title="사진 변경"
                    >
                      <span className="text-white text-sm">📷</span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            if (file.size > 5 * 1024 * 1024) {
                              setError('이미지 크기는 5MB 이하여야 합니다.');
                              return;
                            }
                            const reader = new FileReader();
                            reader.onload = (event) => {
                              const base64 = event.target?.result as string;
                              setProfile({ ...profile, avatar: base64 });
                              // Save to localStorage
                              localStorage.setItem('kis-profile-avatar', base64);
                              setSuccess('프로필 사진이 변경되었습니다.');
                            };
                            reader.readAsDataURL(file);
                          }
                        }}
                      />
                    </label>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg" style={{ color: 'var(--color-text)' }}>{profile.name}</h3>
                    <p className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>{profile.role} · {profile.company}</p>
                    <div className="flex gap-2 mt-3">
                      <label
                        className="px-3 py-1.5 text-sm rounded-lg cursor-pointer transition-colors"
                        style={{ backgroundColor: 'var(--color-brand)', color: 'white' }}
                      >
                        사진 업로드
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) {
                              if (file.size > 5 * 1024 * 1024) {
                                setError('이미지 크기는 5MB 이하여야 합니다.');
                                return;
                              }
                              const reader = new FileReader();
                              reader.onload = (event) => {
                                const base64 = event.target?.result as string;
                                setProfile({ ...profile, avatar: base64 });
                                localStorage.setItem('kis-profile-avatar', base64);
                                setSuccess('프로필 사진이 변경되었습니다.');
                              };
                              reader.readAsDataURL(file);
                            }
                          }}
                        />
                      </label>
                      {profile.avatar && (
                        <button
                          onClick={() => {
                            setProfile({ ...profile, avatar: undefined });
                            localStorage.removeItem('kis-profile-avatar');
                            setSuccess('프로필 사진이 삭제되었습니다.');
                          }}
                          className="px-3 py-1.5 text-sm rounded-lg transition-colors"
                          style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
                        >
                          사진 삭제
                        </button>
                      )}
                    </div>
                    <p className="text-xs mt-2" style={{ color: 'var(--color-text-subtle)' }}>
                      권장: 정사각형 이미지, 최대 5MB (JPG, PNG)
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>이름</label>
                    <input
                      type="text"
                      value={profile.name}
                      onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>이메일</label>
                    <input
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>회사</label>
                    <input
                      type="text"
                      value={profile.company}
                      onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>직책</label>
                    <input
                      type="text"
                      value={profile.role}
                      onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>전화번호</label>
                    <input
                      type="tel"
                      value={profile.phone}
                      onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>부서</label>
                    <input
                      type="text"
                      value={profile.department}
                      onChange={(e) => setProfile({ ...profile, department: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '프로필 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Quote Defaults Tab */}
            {activeTab === 'quote' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  견적 기본값
                </h2>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      기본 차단기 브랜드
                    </label>
                    <select
                      value={quoteDefaults.breakerBrand}
                      onChange={(e) => setQuoteDefaults({ ...quoteDefaults, breakerBrand: e.target.value as 'sangdo' | 'ls' })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="sangdo">상도차단기</option>
                      <option value="ls">LS차단기</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      기본 차단기 타입
                    </label>
                    <select
                      value={quoteDefaults.breakerType}
                      onChange={(e) => setQuoteDefaults({ ...quoteDefaults, breakerType: e.target.value as 'economy' | 'standard' })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="economy">경제형 (37kA)</option>
                      <option value="standard">표준형 (50kA)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      기본 외함 종류
                    </label>
                    <select
                      value={quoteDefaults.enclosureType}
                      onChange={(e) => setQuoteDefaults({ ...quoteDefaults, enclosureType: e.target.value as 'indoor' | 'outdoor' | 'standing' })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="indoor">옥내노출</option>
                      <option value="outdoor">옥외노출</option>
                      <option value="standing">자립형</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      기본 외함 재질
                    </label>
                    <select
                      value={quoteDefaults.enclosureMaterial}
                      onChange={(e) => setQuoteDefaults({ ...quoteDefaults, enclosureMaterial: e.target.value as 'steel16' | 'steel10' | 'sus201' })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="steel16">STEEL 1.6T</option>
                      <option value="steel10">STEEL 1.0T</option>
                      <option value="sus201">SUS201 1.2T</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      기본 마진율 (%)
                    </label>
                    <input
                      type="number"
                      value={quoteDefaults.marginPercent}
                      onChange={(e) => setQuoteDefaults({ ...quoteDefaults, marginPercent: parseInt(e.target.value) })}
                      min="0"
                      max="50"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>

                  <div className="flex items-center">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={quoteDefaults.includeVAT}
                        onChange={(e) => setQuoteDefaults({ ...quoteDefaults, includeVAT: e.target.checked })}
                        className="w-5 h-5 rounded"
                        style={{ accentColor: 'var(--color-brand)' }}
                      />
                      <span style={{ color: 'var(--color-text)' }}>부가세 포함 기본 표시</span>
                    </label>
                  </div>
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Shortcuts Tab */}
            {activeTab === 'shortcuts' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  단축키 설정
                </h2>

                <div className="space-y-4">
                  {Object.entries(shortcuts).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between p-4 rounded-lg" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                      <span style={{ color: 'var(--color-text)' }}>
                        {key === 'newQuote' && '새 견적 생성'}
                        {key === 'saveQuote' && '견적 저장'}
                        {key === 'exportPDF' && 'PDF 내보내기'}
                        {key === 'search' && '검색'}
                        {key === 'toggleSidebar' && '사이드바 토글'}
                      </span>
                      <input
                        type="text"
                        value={value}
                        onChange={(e) => setShortcuts({ ...shortcuts, [key]: e.target.value })}
                        className="w-32 px-3 py-1 text-center border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                      />
                    </div>
                  ))}
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Print Settings Tab */}
            {activeTab === 'print' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  인쇄/PDF 설정
                </h2>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      용지 크기
                    </label>
                    <select
                      value={printSettings.paperSize}
                      onChange={(e) => setPrintSettings({ ...printSettings, paperSize: e.target.value as 'A4' | 'A3' | 'Letter' })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="A4">A4</option>
                      <option value="A3">A3</option>
                      <option value="Letter">Letter</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      방향
                    </label>
                    <select
                      value={printSettings.orientation}
                      onChange={(e) => setPrintSettings({ ...printSettings, orientation: e.target.value as 'portrait' | 'landscape' })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="portrait">세로</option>
                      <option value="landscape">가로</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                      컬러 모드
                    </label>
                    <select
                      value={printSettings.colorMode}
                      onChange={(e) => setPrintSettings({ ...printSettings, colorMode: e.target.value as 'color' | 'grayscale' })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="color">컬러</option>
                      <option value="grayscale">흑백</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={printSettings.includeLogo}
                      onChange={(e) => setPrintSettings({ ...printSettings, includeLogo: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>회사 로고 포함</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={printSettings.includeTerms}
                      onChange={(e) => setPrintSettings({ ...printSettings, includeTerms: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>계약 조건 포함</span>
                  </label>
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Auto Save Tab */}
            {activeTab === 'autosave' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  자동 저장 설정
                </h2>

                <div className="space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoSave.enabled}
                      onChange={(e) => setAutoSave({ ...autoSave, enabled: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span className="font-medium" style={{ color: 'var(--color-text)' }}>자동 저장 활성화</span>
                  </label>

                  {autoSave.enabled && (
                    <>
                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                          저장 주기 (분)
                        </label>
                        <input
                          type="number"
                          value={autoSave.intervalMinutes}
                          onChange={(e) => setAutoSave({ ...autoSave, intervalMinutes: parseInt(e.target.value) })}
                          min="1"
                          max="60"
                          className="w-32 px-4 py-2 border rounded-lg focus:outline-none"
                          style={{
                            backgroundColor: 'var(--color-surface)',
                            borderColor: 'var(--color-border)',
                            color: 'var(--color-text)'
                          }}
                        />
                      </div>

                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={autoSave.showNotification}
                          onChange={(e) => setAutoSave({ ...autoSave, showNotification: e.target.checked })}
                          className="w-5 h-5 rounded"
                          style={{ accentColor: 'var(--color-brand)' }}
                        />
                        <span style={{ color: 'var(--color-text)' }}>저장 시 알림 표시</span>
                      </label>
                    </>
                  )}
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  알림 설정
                </h2>

                <div className="space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.quoteExpiry}
                      onChange={(e) => setNotifications({ ...notifications, quoteExpiry: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>견적 만료 알림</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.priceUpdate}
                      onChange={(e) => setNotifications({ ...notifications, priceUpdate: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>가격 업데이트 알림</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.systemUpdate}
                      onChange={(e) => setNotifications({ ...notifications, systemUpdate: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>시스템 업데이트 알림</span>
                  </label>

                  <div className="pt-4">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifications.dailyReport}
                        onChange={(e) => setNotifications({ ...notifications, dailyReport: e.target.checked })}
                        className="w-5 h-5 rounded"
                        style={{ accentColor: 'var(--color-brand)' }}
                      />
                      <span style={{ color: 'var(--color-text)' }}>일일 리포트 받기</span>
                    </label>

                    {notifications.dailyReport && (
                      <div className="ml-8 mt-2">
                        <label className="block text-sm mb-1" style={{ color: 'var(--color-text-subtle)' }}>
                          리포트 수신 시간
                        </label>
                        <input
                          type="time"
                          value={notifications.reportTime}
                          onChange={(e) => setNotifications({ ...notifications, reportTime: e.target.value })}
                          className="px-3 py-1 border rounded-lg focus:outline-none"
                          style={{
                            backgroundColor: 'var(--color-surface)',
                            borderColor: 'var(--color-border)',
                            color: 'var(--color-text)'
                          }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Export Tab */}
            {activeTab === 'export' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  내보내기 설정
                </h2>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                    기본 내보내기 형식
                  </label>
                  <select
                    value={exportSettings.defaultFormat}
                    onChange={(e) => setExportSettings({ ...exportSettings, defaultFormat: e.target.value as 'xlsx' | 'pdf' | 'both' })}
                    className="w-full max-w-xs px-4 py-2 border rounded-lg focus:outline-none"
                    style={{
                      backgroundColor: 'var(--color-surface)',
                      borderColor: 'var(--color-border)',
                      color: 'var(--color-text)'
                    }}
                  >
                    <option value="xlsx">Excel (.xlsx)</option>
                    <option value="pdf">PDF</option>
                    <option value="both">Excel + PDF 모두</option>
                  </select>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportSettings.includeImages}
                      onChange={(e) => setExportSettings({ ...exportSettings, includeImages: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>이미지 포함</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportSettings.compressFiles}
                      onChange={(e) => setExportSettings({ ...exportSettings, compressFiles: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>파일 압축 (ZIP)</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportSettings.autoOpen}
                      onChange={(e) => setExportSettings({ ...exportSettings, autoOpen: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>내보내기 후 자동 열기</span>
                  </label>
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Session Tab */}
            {activeTab === 'session' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  세션 설정
                </h2>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                    세션 타임아웃 (분)
                  </label>
                  <input
                    type="number"
                    value={sessionSettings.timeoutMinutes}
                    onChange={(e) => setSessionSettings({ ...sessionSettings, timeoutMinutes: parseInt(e.target.value) })}
                    min="5"
                    max="480"
                    className="w-32 px-4 py-2 border rounded-lg focus:outline-none"
                    style={{
                      backgroundColor: 'var(--color-surface)',
                      borderColor: 'var(--color-border)',
                      color: 'var(--color-text)'
                    }}
                  />
                  <p className="text-sm mt-1" style={{ color: 'var(--color-text-subtle)' }}>
                    비활성 상태로 {sessionSettings.timeoutMinutes}분 후 자동 로그아웃
                  </p>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sessionSettings.rememberLogin}
                      onChange={(e) => setSessionSettings({ ...sessionSettings, rememberLogin: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>로그인 상태 유지</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sessionSettings.showLastLogin}
                      onChange={(e) => setSessionSettings({ ...sessionSettings, showLastLogin: e.target.checked })}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ color: 'var(--color-text)' }}>마지막 로그인 시간 표시</span>
                  </label>
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Email Settings Tab */}
            {activeTab === 'email' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  이메일 설정 (NAVER WORKS SMTP)
                </h2>

                <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <p className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                    NAVER WORKS SMTP를 사용하여 이메일을 발송합니다.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>SMTP 서버</label>
                    <input
                      type="text"
                      value={smtpSettings.host}
                      onChange={(e) => setSmtpSettings({ ...smtpSettings, host: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>포트</label>
                    <input
                      type="number"
                      value={smtpSettings.port}
                      onChange={(e) => setSmtpSettings({ ...smtpSettings, port: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>사용자명</label>
                    <input
                      type="text"
                      value={smtpSettings.username}
                      onChange={(e) => setSmtpSettings({ ...smtpSettings, username: e.target.value })}
                      placeholder="이메일 계정"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>비밀번호</label>
                    <input
                      type="password"
                      value={smtpSettings.password}
                      onChange={(e) => setSmtpSettings({ ...smtpSettings, password: e.target.value })}
                      placeholder="********"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    />
                  </div>
                </div>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={smtpSettings.useTLS}
                    onChange={(e) => setSmtpSettings({ ...smtpSettings, useTLS: e.target.checked })}
                    className="w-5 h-5 rounded"
                    style={{ accentColor: 'var(--color-brand)' }}
                  />
                  <span style={{ color: 'var(--color-text)' }}>TLS 사용</span>
                </label>

                <div className="pt-4 border-t flex gap-4" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                  <button
                    disabled={loading}
                    className="px-6 py-2 rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-surface-secondary)', color: 'var(--color-text)' }}
                  >
                    테스트 이메일 발송
                  </button>
                </div>
              </div>
            )}

            {/* AI Settings Tab */}
            {activeTab === 'ai' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  AI 설정
                </h2>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>AI 모델</label>
                  <div className="flex items-center gap-4">
                    <select
                      value={aiSettings.model}
                      onChange={(e) => setAiSettings({ ...aiSettings, model: e.target.value as AISettings['model'] })}
                      className="w-full max-w-xs px-4 py-2 border rounded-lg focus:outline-none"
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text)'
                      }}
                    >
                      <option value="claude-haiku">Claude Haiku (빠름)</option>
                      <option value="claude-sonnet">Claude Sonnet (균형)</option>
                      <option value="claude-opus">Claude Opus (정확)</option>
                    </select>
                    <span className="text-sm font-medium" style={{ color: 'var(--color-brand)' }}>
                      {aiSettings.model === 'claude-haiku' && 'Claude Haiku 모델이 선택되었습니다'}
                      {aiSettings.model === 'claude-sonnet' && 'Claude Sonnet 모델이 선택되었습니다'}
                      {aiSettings.model === 'claude-opus' && 'Claude Opus 모델이 선택되었습니다'}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                    Temperature: {aiSettings.temperature}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={aiSettings.temperature}
                    onChange={(e) => setAiSettings({ ...aiSettings, temperature: parseFloat(e.target.value) })}
                    className="w-full max-w-xs"
                    style={{ accentColor: 'var(--color-brand)' }}
                  />
                  <p className="text-sm mt-1" style={{ color: 'var(--color-text-subtle)' }}>
                    낮을수록 일관된 응답, 높을수록 창의적인 응답
                  </p>
                </div>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={aiSettings.autoEstimate}
                    onChange={(e) => setAiSettings({ ...aiSettings, autoEstimate: e.target.checked })}
                    className="w-5 h-5 rounded"
                    style={{ accentColor: 'var(--color-brand)' }}
                  />
                  <span style={{ color: 'var(--color-text)' }}>자동 견적 생성</span>
                </label>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    onClick={handleSaveSettings}
                    disabled={loading}
                    className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-brand)' }}
                  >
                    {loading ? '저장 중...' : '설정 저장'}
                  </button>
                </div>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  보안
                </h2>

                <div className="p-4 border rounded-lg" style={{ borderColor: 'var(--color-border)' }}>
                  <h3 className="font-medium mb-4" style={{ color: 'var(--color-text)' }}>비밀번호 변경</h3>
                  <form onSubmit={handleChangePassword} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>현재 비밀번호</label>
                      <input
                        type="password"
                        value={passwordForm.current}
                        onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                        className="w-full max-w-md px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>새 비밀번호</label>
                      <input
                        type="password"
                        value={passwordForm.new}
                        onChange={(e) => setPasswordForm({ ...passwordForm, new: e.target.value })}
                        className="w-full max-w-md px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>새 비밀번호 확인</label>
                      <input
                        type="password"
                        value={passwordForm.confirm}
                        onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                        className="w-full max-w-md px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                        required
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-6 py-2 text-white rounded-lg transition disabled:opacity-50"
                      style={{ backgroundColor: 'var(--color-brand)' }}
                    >
                      {loading ? '변경 중...' : '비밀번호 변경'}
                    </button>
                  </form>
                </div>
              </div>
            )}

            {/* Users Management Tab (CEO Only) */}
            {activeTab === 'users' && authUser?.role === 'ceo' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  사용자 관리
                </h2>

                <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <p className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                    CEO만 접근 가능한 사용자 관리 페이지입니다. 직원 계정을 생성, 삭제하거나 비밀번호를 변경할 수 있습니다.
                  </p>
                </div>

                {/* User List */}
                <div className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--color-border)' }}>
                  <div className="p-4 border-b" style={{ backgroundColor: 'var(--color-surface-secondary)', borderColor: 'var(--color-border)' }}>
                    <h3 className="font-medium" style={{ color: 'var(--color-text)' }}>등록된 사용자 ({users.length}명)</h3>
                  </div>
                  <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
                    {users.map((user) => (
                      <div key={user.id} className="p-4 flex items-center justify-between hover:bg-gray-50" style={{ backgroundColor: 'var(--color-surface)' }}>
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold" style={{ backgroundColor: 'var(--color-brand)' }}>
                            {user.name.charAt(0)}
                          </div>
                          <div>
                            <div className="font-medium" style={{ color: 'var(--color-text)' }}>{user.name}</div>
                            <div className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                              @{user.username} · {user.role === 'ceo' ? '대표이사' : user.role === 'manager' ? '관리자' : '직원'}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {user.role !== 'ceo' && (
                            <>
                              <button
                                onClick={() => setEditPasswordForm({ userId: user.id, newPassword: '', confirmPassword: '' })}
                                className="px-3 py-1.5 text-sm rounded-lg transition-colors"
                                style={{ backgroundColor: 'var(--color-surface-secondary)', color: 'var(--color-text)' }}
                              >
                                비밀번호 변경
                              </button>
                              <button
                                onClick={async () => {
                                  if (confirm(`정말 ${user.name} 사용자를 삭제하시겠습니까?`)) {
                                    const result = await deleteUser(user.id);
                                    if (result.success) {
                                      setSuccess(`${user.name} 사용자가 삭제되었습니다.`);
                                    } else {
                                      setError(result.error || '사용자 삭제에 실패했습니다.');
                                    }
                                  }
                                }}
                                className="px-3 py-1.5 text-sm rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                              >
                                삭제
                              </button>
                            </>
                          )}
                          {user.role === 'ceo' && (
                            <span className="px-3 py-1.5 text-sm rounded-lg" style={{ backgroundColor: 'var(--color-brand)', color: 'white' }}>
                              시스템 관리자
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Password Change Modal */}
                {editPasswordForm.userId && (
                  <div className="p-4 border rounded-lg" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)' }}>
                    <h3 className="font-medium mb-4" style={{ color: 'var(--color-text)' }}>
                      비밀번호 변경: {users.find(u => u.id === editPasswordForm.userId)?.name}
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>새 비밀번호</label>
                        <input
                          type="password"
                          value={editPasswordForm.newPassword}
                          onChange={(e) => setEditPasswordForm({ ...editPasswordForm, newPassword: e.target.value })}
                          className="w-full max-w-md px-4 py-2 border rounded-lg focus:outline-none"
                          style={{
                            backgroundColor: 'var(--color-surface)',
                            borderColor: 'var(--color-border)',
                            color: 'var(--color-text)'
                          }}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>비밀번호 확인</label>
                        <input
                          type="password"
                          value={editPasswordForm.confirmPassword}
                          onChange={(e) => setEditPasswordForm({ ...editPasswordForm, confirmPassword: e.target.value })}
                          className="w-full max-w-md px-4 py-2 border rounded-lg focus:outline-none"
                          style={{
                            backgroundColor: 'var(--color-surface)',
                            borderColor: 'var(--color-border)',
                            color: 'var(--color-text)'
                          }}
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={async () => {
                            if (editPasswordForm.newPassword !== editPasswordForm.confirmPassword) {
                              setError('비밀번호가 일치하지 않습니다.');
                              return;
                            }
                            if (editPasswordForm.newPassword.length < 4) {
                              setError('비밀번호는 최소 4자 이상이어야 합니다.');
                              return;
                            }
                            const result = await updateUserPassword(editPasswordForm.userId, editPasswordForm.newPassword);
                            if (result.success) {
                              setSuccess('비밀번호가 변경되었습니다.');
                              setEditPasswordForm({ userId: '', newPassword: '', confirmPassword: '' });
                            } else {
                              setError(result.error || '비밀번호 변경에 실패했습니다.');
                            }
                          }}
                          className="px-4 py-2 text-white rounded-lg transition"
                          style={{ backgroundColor: 'var(--color-brand)' }}
                        >
                          변경
                        </button>
                        <button
                          onClick={() => setEditPasswordForm({ userId: '', newPassword: '', confirmPassword: '' })}
                          className="px-4 py-2 rounded-lg transition"
                          style={{ backgroundColor: 'var(--color-surface-secondary)', color: 'var(--color-text)' }}
                        >
                          취소
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Create New User */}
                <div className="p-4 border rounded-lg" style={{ borderColor: 'var(--color-border)' }}>
                  <h3 className="font-medium mb-4" style={{ color: 'var(--color-text)' }}>새 사용자 추가</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>아이디</label>
                      <input
                        type="text"
                        value={newUserForm.username}
                        onChange={(e) => setNewUserForm({ ...newUserForm, username: e.target.value })}
                        placeholder="로그인에 사용할 아이디"
                        className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>이름</label>
                      <input
                        type="text"
                        value={newUserForm.name}
                        onChange={(e) => setNewUserForm({ ...newUserForm, name: e.target.value })}
                        placeholder="실명"
                        className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>비밀번호</label>
                      <input
                        type="password"
                        value={newUserForm.password}
                        onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
                        placeholder="8자 이상, 대소문자+숫자+특수문자"
                        className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>비밀번호 확인</label>
                      <input
                        type="password"
                        value={newUserForm.confirmPassword}
                        onChange={(e) => setNewUserForm({ ...newUserForm, confirmPassword: e.target.value })}
                        placeholder="비밀번호 확인"
                        className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text)' }}>역할</label>
                      <select
                        value={newUserForm.role}
                        onChange={(e) => setNewUserForm({ ...newUserForm, role: e.target.value as 'manager' | 'staff' })}
                        className="w-full px-4 py-2 border rounded-lg focus:outline-none"
                        style={{
                          backgroundColor: 'var(--color-surface)',
                          borderColor: 'var(--color-border)',
                          color: 'var(--color-text)'
                        }}
                      >
                        <option value="staff">직원</option>
                        <option value="manager">관리자</option>
                      </select>
                    </div>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={async () => {
                        if (!newUserForm.username || !newUserForm.password || !newUserForm.name) {
                          setError('모든 필드를 입력해주세요.');
                          return;
                        }
                        if (newUserForm.password !== newUserForm.confirmPassword) {
                          setError('비밀번호가 일치하지 않습니다.');
                          return;
                        }
                        if (newUserForm.password.length < 8) {
                          setError('비밀번호는 최소 8자 이상, 대문자·소문자·숫자·특수문자를 포함해야 합니다.');
                          return;
                        }
                        const result = await createUser(newUserForm.username, newUserForm.password, newUserForm.name, newUserForm.role);
                        if (result.success) {
                          setSuccess(`${newUserForm.name} 사용자가 생성되었습니다.`);
                          setNewUserForm({ username: '', password: '', confirmPassword: '', name: '', role: 'staff' });
                        } else {
                          setError(result.error || '사용자 생성에 실패했습니다.');
                        }
                      }}
                      className="px-6 py-2 text-white rounded-lg transition"
                      style={{ backgroundColor: 'var(--color-brand)' }}
                    >
                      사용자 추가
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* About Tab */}
            {activeTab === 'about' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b pb-4" style={{ color: 'var(--color-text)', borderColor: 'var(--color-border)' }}>
                  정보
                </h2>

                <div className="text-center py-8">
                  <div className="text-6xl mb-4">🏭</div>
                  <h3 className="text-2xl font-bold mb-2" style={{ color: 'var(--color-text)' }}>
                    (주)한국산업 AI 견적 시스템
                  </h3>
                  <p className="mb-4" style={{ color: 'var(--color-text-subtle)' }}>NABERAL KIS Estimator</p>
                  <p className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>Version 2.0.0</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                    <h4 className="font-medium mb-2" style={{ color: 'var(--color-text)' }}>시스템 정보</h4>
                    <div className="space-y-1 text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                      <p>플랫폼: Next.js 14 + FastAPI</p>
                      <p>데이터베이스: PostgreSQL</p>
                      <p>AI 엔진: Claude (Anthropic)</p>
                      <p>빌드: 2025-12-10</p>
                    </div>
                  </div>
                  <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                    <h4 className="font-medium mb-2" style={{ color: 'var(--color-text)' }}>연락처</h4>
                    <div className="space-y-1 text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                      <p>이메일: support@koreaindustry.co.kr</p>
                      <p>전화: 02-1234-5678</p>
                      <p>웹사이트: www.koreaindustry.co.kr</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Navigation */}
        <div className="mt-6 flex gap-4">
          <a
            href="/ai-manager"
            className="flex-1 rounded-lg shadow-sm p-4 transition text-center"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
          >
            AI 매니저
          </a>
          <a
            href="/quote"
            className="flex-1 rounded-lg shadow-sm p-4 transition text-center"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
          >
            견적 작성
          </a>
          <a
            href="/erp"
            className="flex-1 rounded-lg shadow-sm p-4 transition text-center"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text)' }}
          >
            ERP
          </a>
        </div>
      </div>
    </div>
  );
}
