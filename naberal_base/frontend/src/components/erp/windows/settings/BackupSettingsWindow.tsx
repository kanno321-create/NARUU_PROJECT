"use client";

import React, { useState, useEffect } from "react";
import {
    Save, RotateCcw, HardDrive, Cloud, Clock, Shield, FolderOpen,
    Download, Upload, Trash2, RefreshCw, AlertTriangle, CheckCircle,
    Calendar, Database, Lock, Unlock, Play, Pause, Settings, History,
    FileArchive, Server, Wifi, WifiOff, Eye, EyeOff, Plus, X, Edit2,
    Copy, ExternalLink, Info, Zap, Timer, Archive, BarChart2
} from "lucide-react";

// ============================================
// 타입 정의
// ============================================

interface BackupSchedule {
    id: string;
    name: string;
    type: "full" | "incremental" | "differential";
    frequency: "hourly" | "daily" | "weekly" | "monthly" | "custom";
    time: string;
    dayOfWeek?: number;
    dayOfMonth?: number;
    customCron?: string;
    enabled: boolean;
    retention: number;
    retentionUnit: "days" | "weeks" | "months" | "count";
    compression: boolean;
    compressionLevel: number;
    encryption: boolean;
    encryptionMethod: "AES-256" | "AES-128" | "3DES";
    targets: string[];
    excludePatterns: string[];
    preScript?: string;
    postScript?: string;
    notifyOnSuccess: boolean;
    notifyOnFailure: boolean;
    lastRun?: string;
    nextRun?: string;
    status: "idle" | "running" | "success" | "failed";
}

interface BackupLocation {
    id: string;
    name: string;
    type: "local" | "network" | "ftp" | "sftp" | "s3" | "azure" | "gcs" | "dropbox" | "onedrive" | "google-drive";
    path: string;
    host?: string;
    port?: number;
    username?: string;
    password?: string;
    accessKey?: string;
    secretKey?: string;
    bucket?: string;
    region?: string;
    containerName?: string;
    clientId?: string;
    clientSecret?: string;
    enabled: boolean;
    testStatus: "untested" | "success" | "failed";
    lastTestTime?: string;
    spaceUsed?: number;
    spaceTotal?: number;
    maxBackups?: number;
}

interface BackupHistory {
    id: string;
    scheduleName: string;
    type: "full" | "incremental" | "differential" | "manual";
    startTime: string;
    endTime?: string;
    status: "running" | "success" | "failed" | "cancelled";
    size?: number;
    filesCount?: number;
    location: string;
    errorMessage?: string;
    canRestore: boolean;
}

interface RestorePoint {
    id: string;
    name: string;
    date: string;
    type: "full" | "incremental" | "differential";
    size: number;
    location: string;
    verified: boolean;
    encryptionRequired: boolean;
}

interface BackupTarget {
    id: string;
    name: string;
    description: string;
    tableName?: string;
    filePath?: string;
    type: "database" | "file" | "folder" | "config";
    priority: "critical" | "high" | "medium" | "low";
    enabled: boolean;
    estimatedSize?: number;
}

interface BackupSettings {
    // 일반 설정
    autoBackupEnabled: boolean;
    defaultCompression: boolean;
    defaultCompressionLevel: number;
    defaultEncryption: boolean;
    defaultEncryptionMethod: "AES-256" | "AES-128" | "3DES";
    encryptionPassword: string;
    verifyAfterBackup: boolean;

    // 알림 설정
    notifyEmail: string;
    notifyOnSuccess: boolean;
    notifyOnFailure: boolean;
    notifyOnWarning: boolean;
    sendDailySummary: boolean;
    summaryTime: string;

    // 저장소 설정
    defaultLocation: string;
    keepLocalCopy: boolean;
    localCopyDays: number;

    // 성능 설정
    maxConcurrentBackups: number;
    bandwidthLimit: number;
    bandwidthLimitEnabled: boolean;
    cpuPriorityLevel: "low" | "normal" | "high";

    // 보안 설정
    requirePasswordForRestore: boolean;
    restorePassword: string;
    allowPartialRestore: boolean;
    logAllOperations: boolean;

    // 스케줄 목록
    schedules: BackupSchedule[];

    // 저장 위치 목록
    locations: BackupLocation[];

    // 백업 대상 목록
    targets: BackupTarget[];
}

// ============================================
// 기본값
// ============================================

const defaultSettings: BackupSettings = {
    autoBackupEnabled: true,
    defaultCompression: true,
    defaultCompressionLevel: 6,
    defaultEncryption: true,
    defaultEncryptionMethod: "AES-256",
    encryptionPassword: "",
    verifyAfterBackup: true,

    notifyEmail: "",
    notifyOnSuccess: false,
    notifyOnFailure: true,
    notifyOnWarning: true,
    sendDailySummary: true,
    summaryTime: "08:00",

    defaultLocation: "",
    keepLocalCopy: true,
    localCopyDays: 7,

    maxConcurrentBackups: 1,
    bandwidthLimit: 0,
    bandwidthLimitEnabled: false,
    cpuPriorityLevel: "normal",

    requirePasswordForRestore: true,
    restorePassword: "",
    allowPartialRestore: true,
    logAllOperations: true,

    schedules: [
        {
            id: "1",
            name: "일일 전체 백업",
            type: "full",
            frequency: "daily",
            time: "02:00",
            enabled: true,
            retention: 30,
            retentionUnit: "days",
            compression: true,
            compressionLevel: 6,
            encryption: true,
            encryptionMethod: "AES-256",
            targets: ["all"],
            excludePatterns: ["*.log", "*.tmp"],
            notifyOnSuccess: false,
            notifyOnFailure: true,
            status: "idle"
        },
        {
            id: "2",
            name: "주간 증분 백업",
            type: "incremental",
            frequency: "weekly",
            time: "03:00",
            dayOfWeek: 0,
            enabled: true,
            retention: 4,
            retentionUnit: "weeks",
            compression: true,
            compressionLevel: 9,
            encryption: true,
            encryptionMethod: "AES-256",
            targets: ["all"],
            excludePatterns: [],
            notifyOnSuccess: false,
            notifyOnFailure: true,
            status: "idle"
        }
    ],

    locations: [
        {
            id: "1",
            name: "로컬 백업 드라이브",
            type: "local",
            path: "D:\\Backup\\ERP",
            enabled: true,
            testStatus: "success",
            spaceUsed: 15.5 * 1024 * 1024 * 1024,
            spaceTotal: 500 * 1024 * 1024 * 1024
        }
    ],

    targets: [
        { id: "1", name: "거래처 데이터", description: "모든 거래처 정보", tableName: "customers", type: "database", priority: "critical", enabled: true, estimatedSize: 50 * 1024 * 1024 },
        { id: "2", name: "상품 데이터", description: "상품 및 재고 정보", tableName: "products", type: "database", priority: "critical", enabled: true, estimatedSize: 120 * 1024 * 1024 },
        { id: "3", name: "거래 내역", description: "매출/매입 전표", tableName: "transactions", type: "database", priority: "critical", enabled: true, estimatedSize: 500 * 1024 * 1024 },
        { id: "4", name: "회계 데이터", description: "회계 원장 및 전표", tableName: "accounting", type: "database", priority: "critical", enabled: true, estimatedSize: 200 * 1024 * 1024 },
        { id: "5", name: "첨부 파일", description: "문서 첨부 파일", filePath: "attachments/", type: "folder", priority: "high", enabled: true, estimatedSize: 2 * 1024 * 1024 * 1024 },
        { id: "6", name: "설정 파일", description: "시스템 설정", filePath: "config/", type: "config", priority: "high", enabled: true, estimatedSize: 5 * 1024 * 1024 },
        { id: "7", name: "양식 템플릿", description: "인쇄 양식 템플릿", filePath: "templates/", type: "folder", priority: "medium", enabled: true, estimatedSize: 50 * 1024 * 1024 },
        { id: "8", name: "보고서 데이터", description: "저장된 보고서", filePath: "reports/", type: "folder", priority: "low", enabled: false, estimatedSize: 100 * 1024 * 1024 }
    ]
};

const mockBackupHistory: BackupHistory[] = [
    { id: "1", scheduleName: "일일 전체 백업", type: "full", startTime: "2025-12-05 02:00:00", endTime: "2025-12-05 02:15:32", status: "success", size: 850 * 1024 * 1024, filesCount: 12543, location: "로컬 백업 드라이브", canRestore: true },
    { id: "2", scheduleName: "수동 백업", type: "manual", startTime: "2025-12-04 15:30:00", endTime: "2025-12-04 15:45:18", status: "success", size: 850 * 1024 * 1024, filesCount: 12540, location: "로컬 백업 드라이브", canRestore: true },
    { id: "3", scheduleName: "일일 전체 백업", type: "full", startTime: "2025-12-04 02:00:00", endTime: "2025-12-04 02:14:55", status: "success", size: 848 * 1024 * 1024, filesCount: 12538, location: "로컬 백업 드라이브", canRestore: true },
    { id: "4", scheduleName: "일일 전체 백업", type: "full", startTime: "2025-12-03 02:00:00", endTime: "2025-12-03 02:05:12", status: "failed", size: 0, filesCount: 0, location: "로컬 백업 드라이브", errorMessage: "디스크 공간 부족", canRestore: false },
    { id: "5", scheduleName: "주간 증분 백업", type: "incremental", startTime: "2025-12-01 03:00:00", endTime: "2025-12-01 03:05:22", status: "success", size: 125 * 1024 * 1024, filesCount: 1542, location: "로컬 백업 드라이브", canRestore: true }
];

// ============================================
// 유틸리티 함수
// ============================================

const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleString("ko-KR");
};

// ============================================
// 메인 컴포넌트
// ============================================

export function BackupSettingsWindow() {
    const [activeTab, setActiveTab] = useState("general");
    const [settings, setSettings] = useState<BackupSettings>(defaultSettings);
    const [backupHistory, setBackupHistory] = useState<BackupHistory[]>(mockBackupHistory);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [selectedSchedule, setSelectedSchedule] = useState<BackupSchedule | null>(null);
    const [selectedLocation, setSelectedLocation] = useState<BackupLocation | null>(null);
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [showLocationModal, setShowLocationModal] = useState(false);
    const [showRestoreModal, setShowRestoreModal] = useState(false);
    const [selectedRestore, setSelectedRestore] = useState<BackupHistory | null>(null);
    const [restorePassword, setRestorePassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [backupRunning, setBackupRunning] = useState(false);
    const [backupProgress, setBackupProgress] = useState(0);

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_backup_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "백업 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "설정 저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    // 설정 불러오기
    useEffect(() => {
        const saved = localStorage.getItem("erp_backup_settings");
        if (saved) {
            try {
                setSettings(JSON.parse(saved));
            } catch (e) {
                console.error("설정 불러오기 실패:", e);
            }
        }
    }, []);

    // 수동 백업 실행
    const handleManualBackup = () => {
        setBackupRunning(true);
        setBackupProgress(0);

        const interval = setInterval(() => {
            setBackupProgress(prev => {
                if (prev >= 100) {
                    clearInterval(interval);
                    setBackupRunning(false);
                    setMessage({ type: "success", text: "백업이 완료되었습니다." });
                    setTimeout(() => setMessage(null), 3000);
                    return 100;
                }
                return prev + Math.random() * 15;
            });
        }, 500);
    };

    // 복원 실행
    const handleRestore = () => {
        if (settings.requirePasswordForRestore && restorePassword !== settings.restorePassword) {
            setMessage({ type: "error", text: "복원 비밀번호가 올바르지 않습니다." });
            return;
        }

        setShowRestoreModal(false);
        setMessage({ type: "success", text: "복원이 시작되었습니다. 완료 시 알림이 전송됩니다." });
        setTimeout(() => setMessage(null), 5000);
    };

    // 저장 위치 테스트
    const handleTestLocation = (location: BackupLocation) => {
        setMessage({ type: "success", text: `${location.name} 연결 테스트 성공` });
        setTimeout(() => setMessage(null), 3000);
    };

    const tabs = [
        { id: "general", label: "일반 설정", icon: Settings },
        { id: "schedule", label: "스케줄 관리", icon: Calendar },
        { id: "locations", label: "저장 위치", icon: FolderOpen },
        { id: "targets", label: "백업 대상", icon: Database },
        { id: "history", label: "백업 이력", icon: History },
        { id: "restore", label: "복원", icon: Download },
        { id: "security", label: "보안", icon: Shield },
        { id: "notifications", label: "알림", icon: AlertTriangle },
        { id: "advanced", label: "고급 설정", icon: Zap }
    ];

    return (
        <div className="flex h-full flex-col">
            {/* 툴바 */}
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50"
                >
                    <Save className="h-4 w-4" />
                    {saving ? "저장 중..." : "설정 저장"}
                </button>
                <button
                    onClick={handleManualBackup}
                    disabled={backupRunning}
                    className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                >
                    {backupRunning ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    {backupRunning ? "백업 중..." : "지금 백업"}
                </button>
                <button
                    onClick={() => setSettings(defaultSettings)}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <RotateCcw className="h-4 w-4" />
                    초기화
                </button>

                {backupRunning && (
                    <div className="ml-4 flex items-center gap-2">
                        <div className="h-2 w-48 rounded-full bg-gray-200">
                            <div
                                className="h-2 rounded-full bg-green-500 transition-all"
                                style={{ width: `${Math.min(backupProgress, 100)}%` }}
                            />
                        </div>
                        <span className="text-sm text-text-subtle">{Math.round(backupProgress)}%</span>
                    </div>
                )}

                {message && (
                    <span className={`ml-4 text-sm ${
                        message.type === "success" ? "text-green-600" :
                        message.type === "warning" ? "text-yellow-600" : "text-red-600"
                    }`}>
                        {message.text}
                    </span>
                )}
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* 탭 메뉴 */}
                <div className="w-48 border-r bg-surface-secondary p-2 overflow-y-auto">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm ${
                                    activeTab === tab.id
                                        ? "bg-brand text-white"
                                        : "hover:bg-surface"
                                }`}
                            >
                                <Icon className="h-4 w-4" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* 설정 내용 */}
                <div className="flex-1 overflow-auto p-4">
                    {/* 일반 설정 탭 */}
                    {activeTab === "general" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Settings className="h-5 w-5" />
                                일반 백업 설정
                            </h3>

                            {/* 자동 백업 상태 카드 */}
                            <div className="rounded-lg border bg-surface p-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-3 rounded-full ${settings.autoBackupEnabled ? "bg-green-100" : "bg-gray-100"}`}>
                                            <HardDrive className={`h-6 w-6 ${settings.autoBackupEnabled ? "text-green-600" : "text-gray-400"}`} />
                                        </div>
                                        <div>
                                            <h4 className="font-medium">자동 백업</h4>
                                            <p className="text-sm text-text-subtle">
                                                {settings.autoBackupEnabled ? "활성화됨 - 스케줄에 따라 자동 백업" : "비활성화됨"}
                                            </p>
                                        </div>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.autoBackupEnabled}
                                            onChange={(e) => setSettings({ ...settings, autoBackupEnabled: e.target.checked })}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                                    </label>
                                </div>
                            </div>

                            {/* 기본 압축 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium flex items-center gap-2">
                                    <FileArchive className="h-4 w-4" />
                                    압축 설정
                                </h4>

                                <div className="flex items-center gap-4">
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.defaultCompression}
                                            onChange={(e) => setSettings({ ...settings, defaultCompression: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">기본 압축 사용</span>
                                    </label>
                                </div>

                                {settings.defaultCompression && (
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium">
                                            압축 레벨 (1-9)
                                        </label>
                                        <div className="flex items-center gap-4">
                                            <input
                                                type="range"
                                                min="1"
                                                max="9"
                                                value={settings.defaultCompressionLevel}
                                                onChange={(e) => setSettings({ ...settings, defaultCompressionLevel: Number(e.target.value) })}
                                                className="flex-1"
                                            />
                                            <span className="w-8 text-center font-medium">{settings.defaultCompressionLevel}</span>
                                        </div>
                                        <div className="flex justify-between text-xs text-text-subtle">
                                            <span>빠른 속도</span>
                                            <span>높은 압축률</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* 기본 암호화 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium flex items-center gap-2">
                                    <Lock className="h-4 w-4" />
                                    암호화 설정
                                </h4>

                                <div className="flex items-center gap-4">
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.defaultEncryption}
                                            onChange={(e) => setSettings({ ...settings, defaultEncryption: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">기본 암호화 사용</span>
                                    </label>
                                </div>

                                {settings.defaultEncryption && (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">암호화 방식</label>
                                            <select
                                                value={settings.defaultEncryptionMethod}
                                                onChange={(e) => setSettings({ ...settings, defaultEncryptionMethod: e.target.value as any })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="AES-256">AES-256 (권장)</option>
                                                <option value="AES-128">AES-128</option>
                                                <option value="3DES">3DES</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">암호화 비밀번호</label>
                                            <div className="relative">
                                                <input
                                                    type={showPassword ? "text" : "password"}
                                                    value={settings.encryptionPassword}
                                                    onChange={(e) => setSettings({ ...settings, encryptionPassword: e.target.value })}
                                                    className="w-full rounded border px-3 py-2 pr-10 text-sm"
                                                    placeholder="암호화에 사용할 비밀번호"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => setShowPassword(!showPassword)}
                                                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                                >
                                                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* 백업 후 검증 */}
                            <div className="rounded border p-4">
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.verifyAfterBackup}
                                        onChange={(e) => setSettings({ ...settings, verifyAfterBackup: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm font-medium">백업 후 무결성 검증</span>
                                </label>
                                <p className="mt-1 ml-6 text-xs text-text-subtle">
                                    백업 완료 후 데이터 무결성을 자동으로 검증합니다. (권장)
                                </p>
                            </div>
                        </div>
                    )}

                    {/* 스케줄 관리 탭 */}
                    {activeTab === "schedule" && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-medium flex items-center gap-2">
                                    <Calendar className="h-5 w-5" />
                                    백업 스케줄 관리
                                </h3>
                                <button
                                    onClick={() => {
                                        setSelectedSchedule(null);
                                        setShowScheduleModal(true);
                                    }}
                                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                >
                                    <Plus className="h-4 w-4" />
                                    스케줄 추가
                                </button>
                            </div>

                            {/* 스케줄 목록 */}
                            <div className="space-y-3">
                                {settings.schedules.map((schedule) => (
                                    <div
                                        key={schedule.id}
                                        className="rounded-lg border p-4 hover:bg-surface-secondary transition-colors"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className={`p-2 rounded-full ${schedule.enabled ? "bg-green-100" : "bg-gray-100"}`}>
                                                    <Clock className={`h-5 w-5 ${schedule.enabled ? "text-green-600" : "text-gray-400"}`} />
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h4 className="font-medium">{schedule.name}</h4>
                                                        <span className={`px-2 py-0.5 rounded text-xs ${
                                                            schedule.type === "full" ? "bg-blue-100 text-blue-700" :
                                                            schedule.type === "incremental" ? "bg-green-100 text-green-700" :
                                                            "bg-yellow-100 text-yellow-700"
                                                        }`}>
                                                            {schedule.type === "full" ? "전체" :
                                                             schedule.type === "incremental" ? "증분" : "차등"}
                                                        </span>
                                                        {schedule.encryption && (
                                                            <Lock className="h-3 w-3 text-blue-500" />
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-text-subtle">
                                                        {schedule.frequency === "daily" && `매일 ${schedule.time}`}
                                                        {schedule.frequency === "weekly" && `매주 ${["일", "월", "화", "수", "목", "금", "토"][schedule.dayOfWeek || 0]}요일 ${schedule.time}`}
                                                        {schedule.frequency === "monthly" && `매월 ${schedule.dayOfMonth}일 ${schedule.time}`}
                                                        {schedule.frequency === "hourly" && `매시간`}
                                                        {schedule.frequency === "custom" && `커스텀: ${schedule.customCron}`}
                                                        {" | "}
                                                        보관: {schedule.retention}{schedule.retentionUnit === "days" ? "일" : schedule.retentionUnit === "weeks" ? "주" : schedule.retentionUnit === "months" ? "개월" : "개"}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className={`px-2 py-1 rounded text-xs ${
                                                    schedule.status === "running" ? "bg-blue-100 text-blue-700" :
                                                    schedule.status === "success" ? "bg-green-100 text-green-700" :
                                                    schedule.status === "failed" ? "bg-red-100 text-red-700" :
                                                    "bg-gray-100 text-gray-700"
                                                }`}>
                                                    {schedule.status === "running" ? "실행 중" :
                                                     schedule.status === "success" ? "성공" :
                                                     schedule.status === "failed" ? "실패" : "대기"}
                                                </span>
                                                <button
                                                    onClick={() => {
                                                        setSelectedSchedule(schedule);
                                                        setShowScheduleModal(true);
                                                    }}
                                                    className="p-1 hover:bg-gray-200 rounded"
                                                >
                                                    <Edit2 className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        const updated = settings.schedules.map(s =>
                                                            s.id === schedule.id ? { ...s, enabled: !s.enabled } : s
                                                        );
                                                        setSettings({ ...settings, schedules: updated });
                                                    }}
                                                    className="p-1 hover:bg-gray-200 rounded"
                                                >
                                                    {schedule.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        const updated = settings.schedules.filter(s => s.id !== schedule.id);
                                                        setSettings({ ...settings, schedules: updated });
                                                    }}
                                                    className="p-1 hover:bg-red-100 rounded text-red-500"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {settings.schedules.length === 0 && (
                                <div className="text-center py-12 text-text-subtle">
                                    <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>등록된 백업 스케줄이 없습니다.</p>
                                    <p className="text-sm">새 스케줄을 추가하여 자동 백업을 설정하세요.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 저장 위치 탭 */}
                    {activeTab === "locations" && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-medium flex items-center gap-2">
                                    <FolderOpen className="h-5 w-5" />
                                    백업 저장 위치
                                </h3>
                                <button
                                    onClick={() => {
                                        setSelectedLocation(null);
                                        setShowLocationModal(true);
                                    }}
                                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                >
                                    <Plus className="h-4 w-4" />
                                    위치 추가
                                </button>
                            </div>

                            {/* 저장 위치 목록 */}
                            <div className="grid grid-cols-2 gap-4">
                                {settings.locations.map((location) => (
                                    <div
                                        key={location.id}
                                        className="rounded-lg border p-4"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className={`p-2 rounded-lg ${
                                                    location.type === "local" ? "bg-blue-100" :
                                                    location.type === "network" ? "bg-purple-100" :
                                                    location.type.includes("s3") || location.type.includes("azure") || location.type.includes("gcs") ? "bg-orange-100" :
                                                    "bg-green-100"
                                                }`}>
                                                    {location.type === "local" ? <HardDrive className="h-5 w-5 text-blue-600" /> :
                                                     location.type === "network" ? <Server className="h-5 w-5 text-purple-600" /> :
                                                     <Cloud className="h-5 w-5 text-orange-600" />}
                                                </div>
                                                <div>
                                                    <h4 className="font-medium">{location.name}</h4>
                                                    <p className="text-xs text-text-subtle truncate max-w-[200px]">{location.path}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                {location.testStatus === "success" ? (
                                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                                ) : location.testStatus === "failed" ? (
                                                    <AlertTriangle className="h-4 w-4 text-red-500" />
                                                ) : (
                                                    <Info className="h-4 w-4 text-gray-400" />
                                                )}
                                            </div>
                                        </div>

                                        {/* 용량 표시 */}
                                        {location.spaceUsed !== undefined && location.spaceTotal !== undefined && (
                                            <div className="mt-3">
                                                <div className="flex justify-between text-xs text-text-subtle mb-1">
                                                    <span>{formatBytes(location.spaceUsed)} 사용</span>
                                                    <span>{formatBytes(location.spaceTotal)} 전체</span>
                                                </div>
                                                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full ${
                                                            (location.spaceUsed / location.spaceTotal) > 0.9 ? "bg-red-500" :
                                                            (location.spaceUsed / location.spaceTotal) > 0.7 ? "bg-yellow-500" :
                                                            "bg-green-500"
                                                        }`}
                                                        style={{ width: `${(location.spaceUsed / location.spaceTotal) * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        )}

                                        <div className="mt-3 flex items-center gap-2">
                                            <button
                                                onClick={() => handleTestLocation(location)}
                                                className="flex items-center gap-1 text-xs px-2 py-1 rounded border hover:bg-gray-50"
                                            >
                                                <RefreshCw className="h-3 w-3" />
                                                연결 테스트
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setSelectedLocation(location);
                                                    setShowLocationModal(true);
                                                }}
                                                className="flex items-center gap-1 text-xs px-2 py-1 rounded border hover:bg-gray-50"
                                            >
                                                <Edit2 className="h-3 w-3" />
                                                편집
                                            </button>
                                            <button
                                                onClick={() => {
                                                    const updated = settings.locations.filter(l => l.id !== location.id);
                                                    setSettings({ ...settings, locations: updated });
                                                }}
                                                className="flex items-center gap-1 text-xs px-2 py-1 rounded border hover:bg-red-50 text-red-500"
                                            >
                                                <Trash2 className="h-3 w-3" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* 기본 저장 위치 설정 */}
                            <div className="rounded border p-4">
                                <h4 className="font-medium mb-3">기본 저장 위치</h4>
                                <select
                                    value={settings.defaultLocation}
                                    onChange={(e) => setSettings({ ...settings, defaultLocation: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                >
                                    <option value="">선택하세요</option>
                                    {settings.locations.map((loc) => (
                                        <option key={loc.id} value={loc.id}>{loc.name}</option>
                                    ))}
                                </select>
                            </div>

                            {/* 로컬 복사본 설정 */}
                            <div className="rounded border p-4 space-y-3">
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.keepLocalCopy}
                                        onChange={(e) => setSettings({ ...settings, keepLocalCopy: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm font-medium">로컬 복사본 유지</span>
                                </label>
                                {settings.keepLocalCopy && (
                                    <div>
                                        <label className="block text-sm mb-1">보관 기간 (일)</label>
                                        <input
                                            type="number"
                                            value={settings.localCopyDays}
                                            onChange={(e) => setSettings({ ...settings, localCopyDays: Number(e.target.value) })}
                                            className="w-32 rounded border px-3 py-2 text-sm"
                                            min="1"
                                            max="365"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* 백업 대상 탭 */}
                    {activeTab === "targets" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Database className="h-5 w-5" />
                                백업 대상 관리
                            </h3>

                            {/* 우선순위별 그룹 */}
                            {["critical", "high", "medium", "low"].map((priority) => {
                                const targets = settings.targets.filter(t => t.priority === priority);
                                if (targets.length === 0) return null;

                                return (
                                    <div key={priority} className="space-y-2">
                                        <h4 className={`text-sm font-medium px-2 py-1 rounded ${
                                            priority === "critical" ? "bg-red-100 text-red-700" :
                                            priority === "high" ? "bg-orange-100 text-orange-700" :
                                            priority === "medium" ? "bg-yellow-100 text-yellow-700" :
                                            "bg-gray-100 text-gray-700"
                                        }`}>
                                            {priority === "critical" ? "필수 (Critical)" :
                                             priority === "high" ? "높음 (High)" :
                                             priority === "medium" ? "중간 (Medium)" : "낮음 (Low)"}
                                        </h4>
                                        <div className="space-y-2">
                                            {targets.map((target) => (
                                                <div
                                                    key={target.id}
                                                    className="flex items-center justify-between rounded border p-3 hover:bg-surface-secondary"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <input
                                                            type="checkbox"
                                                            checked={target.enabled}
                                                            onChange={(e) => {
                                                                const updated = settings.targets.map(t =>
                                                                    t.id === target.id ? { ...t, enabled: e.target.checked } : t
                                                                );
                                                                setSettings({ ...settings, targets: updated });
                                                            }}
                                                            className="h-4 w-4"
                                                        />
                                                        <div className={`p-1.5 rounded ${
                                                            target.type === "database" ? "bg-blue-100" :
                                                            target.type === "folder" ? "bg-green-100" :
                                                            "bg-purple-100"
                                                        }`}>
                                                            {target.type === "database" ? <Database className="h-4 w-4 text-blue-600" /> :
                                                             target.type === "folder" ? <FolderOpen className="h-4 w-4 text-green-600" /> :
                                                             <Settings className="h-4 w-4 text-purple-600" />}
                                                        </div>
                                                        <div>
                                                            <p className="font-medium text-sm">{target.name}</p>
                                                            <p className="text-xs text-text-subtle">{target.description}</p>
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        <p className="text-sm text-text-subtle">
                                                            {target.tableName || target.filePath}
                                                        </p>
                                                        {target.estimatedSize && (
                                                            <p className="text-xs text-text-subtle">
                                                                예상 크기: {formatBytes(target.estimatedSize)}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}

                            {/* 전체 예상 크기 */}
                            <div className="rounded-lg border bg-surface p-4">
                                <div className="flex items-center justify-between">
                                    <span className="font-medium">선택된 항목의 총 예상 크기</span>
                                    <span className="text-lg font-bold text-brand">
                                        {formatBytes(
                                            settings.targets
                                                .filter(t => t.enabled)
                                                .reduce((sum, t) => sum + (t.estimatedSize || 0), 0)
                                        )}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 백업 이력 탭 */}
                    {activeTab === "history" && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-medium flex items-center gap-2">
                                    <History className="h-5 w-5" />
                                    백업 이력
                                </h3>
                                <div className="flex items-center gap-2">
                                    <select className="rounded border px-3 py-1.5 text-sm">
                                        <option value="all">전체</option>
                                        <option value="success">성공</option>
                                        <option value="failed">실패</option>
                                    </select>
                                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary">
                                        <RefreshCw className="h-4 w-4" />
                                        새로고침
                                    </button>
                                </div>
                            </div>

                            {/* 이력 목록 */}
                            <div className="rounded border overflow-hidden">
                                <table className="w-full text-sm">
                                    <thead className="bg-surface-secondary">
                                        <tr>
                                            <th className="text-left px-4 py-2">시작 시간</th>
                                            <th className="text-left px-4 py-2">스케줄명</th>
                                            <th className="text-left px-4 py-2">유형</th>
                                            <th className="text-left px-4 py-2">상태</th>
                                            <th className="text-right px-4 py-2">크기</th>
                                            <th className="text-right px-4 py-2">파일 수</th>
                                            <th className="text-center px-4 py-2">작업</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {backupHistory.map((history) => (
                                            <tr key={history.id} className="border-t hover:bg-surface-secondary">
                                                <td className="px-4 py-2">
                                                    <div>
                                                        <p>{formatDate(history.startTime)}</p>
                                                        {history.endTime && (
                                                            <p className="text-xs text-text-subtle">
                                                                완료: {formatDate(history.endTime)}
                                                            </p>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-4 py-2">{history.scheduleName}</td>
                                                <td className="px-4 py-2">
                                                    <span className={`px-2 py-0.5 rounded text-xs ${
                                                        history.type === "full" ? "bg-blue-100 text-blue-700" :
                                                        history.type === "incremental" ? "bg-green-100 text-green-700" :
                                                        history.type === "differential" ? "bg-yellow-100 text-yellow-700" :
                                                        "bg-purple-100 text-purple-700"
                                                    }`}>
                                                        {history.type === "full" ? "전체" :
                                                         history.type === "incremental" ? "증분" :
                                                         history.type === "differential" ? "차등" : "수동"}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-2">
                                                    <span className={`flex items-center gap-1 ${
                                                        history.status === "success" ? "text-green-600" :
                                                        history.status === "failed" ? "text-red-600" :
                                                        history.status === "running" ? "text-blue-600" :
                                                        "text-gray-600"
                                                    }`}>
                                                        {history.status === "success" ? <CheckCircle className="h-4 w-4" /> :
                                                         history.status === "failed" ? <AlertTriangle className="h-4 w-4" /> :
                                                         history.status === "running" ? <RefreshCw className="h-4 w-4 animate-spin" /> :
                                                         <X className="h-4 w-4" />}
                                                        {history.status === "success" ? "성공" :
                                                         history.status === "failed" ? "실패" :
                                                         history.status === "running" ? "진행중" : "취소됨"}
                                                    </span>
                                                    {history.errorMessage && (
                                                        <p className="text-xs text-red-500">{history.errorMessage}</p>
                                                    )}
                                                </td>
                                                <td className="px-4 py-2 text-right">
                                                    {history.size ? formatBytes(history.size) : "-"}
                                                </td>
                                                <td className="px-4 py-2 text-right">
                                                    {history.filesCount?.toLocaleString() || "-"}
                                                </td>
                                                <td className="px-4 py-2 text-center">
                                                    {history.canRestore && (
                                                        <button
                                                            onClick={() => {
                                                                setSelectedRestore(history);
                                                                setShowRestoreModal(true);
                                                            }}
                                                            className="text-brand hover:underline text-sm"
                                                        >
                                                            복원
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* 복원 탭 */}
                    {activeTab === "restore" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Download className="h-5 w-5" />
                                데이터 복원
                            </h3>

                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                                    <div>
                                        <h4 className="font-medium text-yellow-800">복원 전 주의사항</h4>
                                        <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside space-y-1">
                                            <li>복원 전 현재 데이터를 반드시 백업하세요.</li>
                                            <li>복원 중에는 시스템 사용을 중단해 주세요.</li>
                                            <li>부분 복원 시 데이터 일관성에 주의하세요.</li>
                                            <li>복원 비밀번호를 분실하면 복원이 불가능합니다.</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            {/* 복원 가능한 백업 목록 */}
                            <div className="space-y-3">
                                <h4 className="font-medium">복원 가능한 백업</h4>
                                {backupHistory
                                    .filter(h => h.canRestore)
                                    .slice(0, 10)
                                    .map((history) => (
                                        <div
                                            key={history.id}
                                            className="flex items-center justify-between rounded border p-3 hover:bg-surface-secondary"
                                        >
                                            <div className="flex items-center gap-3">
                                                <Archive className="h-5 w-5 text-blue-500" />
                                                <div>
                                                    <p className="font-medium">{history.scheduleName}</p>
                                                    <p className="text-sm text-text-subtle">
                                                        {formatDate(history.startTime)} | {formatBytes(history.size || 0)}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => {
                                                        setSelectedRestore(history);
                                                        setShowRestoreModal(true);
                                                    }}
                                                    className="flex items-center gap-1 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
                                                >
                                                    <Download className="h-4 w-4" />
                                                    복원
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                            </div>

                            {/* 부분 복원 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">부분 복원 설정</h4>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allowPartialRestore}
                                        onChange={(e) => setSettings({ ...settings, allowPartialRestore: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">부분 복원 허용</span>
                                </label>
                                <p className="text-xs text-text-subtle">
                                    특정 테이블이나 파일만 선택적으로 복원할 수 있습니다.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* 보안 탭 */}
                    {activeTab === "security" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Shield className="h-5 w-5" />
                                보안 설정
                            </h3>

                            {/* 복원 비밀번호 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">복원 보호</h4>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.requirePasswordForRestore}
                                        onChange={(e) => setSettings({ ...settings, requirePasswordForRestore: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">복원 시 비밀번호 필요</span>
                                </label>

                                {settings.requirePasswordForRestore && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">복원 비밀번호</label>
                                        <div className="relative">
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                value={settings.restorePassword}
                                                onChange={(e) => setSettings({ ...settings, restorePassword: e.target.value })}
                                                className="w-full rounded border px-3 py-2 pr-10 text-sm"
                                                placeholder="복원 시 필요한 비밀번호"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                            >
                                                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* 로깅 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">감사 로깅</h4>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.logAllOperations}
                                        onChange={(e) => setSettings({ ...settings, logAllOperations: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">모든 백업/복원 작업 기록</span>
                                </label>
                                <p className="text-xs text-text-subtle">
                                    누가, 언제, 어떤 작업을 수행했는지 상세히 기록합니다.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* 알림 탭 */}
                    {activeTab === "notifications" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5" />
                                알림 설정
                            </h3>

                            <div className="rounded border p-4 space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">알림 이메일</label>
                                    <input
                                        type="email"
                                        value={settings.notifyEmail}
                                        onChange={(e) => setSettings({ ...settings, notifyEmail: e.target.value })}
                                        className="w-full rounded border px-3 py-2 text-sm"
                                        placeholder="admin@company.com"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.notifyOnSuccess}
                                            onChange={(e) => setSettings({ ...settings, notifyOnSuccess: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">백업 성공 시 알림</span>
                                    </label>
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.notifyOnFailure}
                                            onChange={(e) => setSettings({ ...settings, notifyOnFailure: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">백업 실패 시 알림</span>
                                    </label>
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.notifyOnWarning}
                                            onChange={(e) => setSettings({ ...settings, notifyOnWarning: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">경고 발생 시 알림</span>
                                    </label>
                                </div>
                            </div>

                            {/* 일일 요약 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">일일 요약 보고서</h4>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.sendDailySummary}
                                        onChange={(e) => setSettings({ ...settings, sendDailySummary: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">매일 백업 요약 보고서 발송</span>
                                </label>

                                {settings.sendDailySummary && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">발송 시간</label>
                                        <input
                                            type="time"
                                            value={settings.summaryTime}
                                            onChange={(e) => setSettings({ ...settings, summaryTime: e.target.value })}
                                            className="rounded border px-3 py-2 text-sm"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* 고급 설정 탭 */}
                    {activeTab === "advanced" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Zap className="h-5 w-5" />
                                고급 설정
                            </h3>

                            {/* 성능 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">성능 설정</h4>

                                <div>
                                    <label className="block text-sm font-medium mb-1">
                                        최대 동시 백업 작업 수
                                    </label>
                                    <input
                                        type="number"
                                        value={settings.maxConcurrentBackups}
                                        onChange={(e) => setSettings({ ...settings, maxConcurrentBackups: Number(e.target.value) })}
                                        className="w-32 rounded border px-3 py-2 text-sm"
                                        min="1"
                                        max="5"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">
                                        CPU 우선순위
                                    </label>
                                    <select
                                        value={settings.cpuPriorityLevel}
                                        onChange={(e) => setSettings({ ...settings, cpuPriorityLevel: e.target.value as any })}
                                        className="w-full rounded border px-3 py-2 text-sm"
                                    >
                                        <option value="low">낮음 (시스템 부하 최소화)</option>
                                        <option value="normal">보통</option>
                                        <option value="high">높음 (빠른 백업)</option>
                                    </select>
                                </div>
                            </div>

                            {/* 대역폭 제한 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">네트워크 대역폭 제한</h4>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.bandwidthLimitEnabled}
                                        onChange={(e) => setSettings({ ...settings, bandwidthLimitEnabled: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">대역폭 제한 사용</span>
                                </label>

                                {settings.bandwidthLimitEnabled && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">
                                            최대 대역폭 (MB/s)
                                        </label>
                                        <input
                                            type="number"
                                            value={settings.bandwidthLimit}
                                            onChange={(e) => setSettings({ ...settings, bandwidthLimit: Number(e.target.value) })}
                                            className="w-32 rounded border px-3 py-2 text-sm"
                                            min="1"
                                            max="1000"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 복원 확인 모달 */}
            {showRestoreModal && selectedRestore && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg w-[500px] p-6">
                        <h3 className="text-lg font-medium mb-4">데이터 복원 확인</h3>

                        <div className="space-y-4">
                            <div className="bg-surface-secondary rounded p-3">
                                <p className="text-sm"><strong>백업 이름:</strong> {selectedRestore.scheduleName}</p>
                                <p className="text-sm"><strong>백업 시간:</strong> {formatDate(selectedRestore.startTime)}</p>
                                <p className="text-sm"><strong>백업 크기:</strong> {formatBytes(selectedRestore.size || 0)}</p>
                            </div>

                            {settings.requirePasswordForRestore && (
                                <div>
                                    <label className="block text-sm font-medium mb-1">복원 비밀번호</label>
                                    <input
                                        type="password"
                                        value={restorePassword}
                                        onChange={(e) => setRestorePassword(e.target.value)}
                                        className="w-full rounded border px-3 py-2 text-sm"
                                        placeholder="복원 비밀번호를 입력하세요"
                                    />
                                </div>
                            )}

                            <div className="bg-red-50 border border-red-200 rounded p-3">
                                <p className="text-sm text-red-700">
                                    <strong>경고:</strong> 복원을 진행하면 현재 데이터가 선택한 백업 시점의 데이터로 대체됩니다.
                                    이 작업은 되돌릴 수 없습니다.
                                </p>
                            </div>
                        </div>

                        <div className="flex justify-end gap-2 mt-6">
                            <button
                                onClick={() => {
                                    setShowRestoreModal(false);
                                    setRestorePassword("");
                                }}
                                className="px-4 py-2 text-sm rounded border hover:bg-surface-secondary"
                            >
                                취소
                            </button>
                            <button
                                onClick={handleRestore}
                                className="px-4 py-2 text-sm rounded bg-red-600 text-white hover:bg-red-700"
                            >
                                복원 실행
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
