'use client';

import React, { useState, useRef, useMemo, useEffect, useCallback } from 'react';
import {
    FileText, Upload, Search, Filter, Grid, List, Download, Trash2,
    Eye, Send, FolderOpen, Clock, Plus, X,
    Check, Star, Zap, History, Columns,
    Building2, Folder, FolderPlus, Mail, RefreshCw,
    FileImage, File, ChevronRight, CheckCircle2, AlertCircle, Loader2
} from 'lucide-react';
import { AISupporter } from '@/components/ai-supporter';
import { api, ERPDrawingFile } from '@/lib/api';

// 유틸리티
function cn(...classes: (string | boolean | undefined)[]) {
    return classes.filter(Boolean).join(' ');
}

// 타입 정의
interface Drawing {
    id: string;
    name: string;
    projectName: string;
    projectId: string;
    fileType: 'pdf' | 'dwg' | 'dxf' | 'jpg' | 'png' | 'xlsx';
    fileSize: number;
    uploadedAt: Date;
    updatedAt: Date;
    version: number;
    status: 'pending' | 'analyzed' | 'approved' | 'rejected';
    starred: boolean;
    tags: string[];
    folder: string;
    analysisResult?: {
        panels: number;
        breakers: number;
        mainBreaker?: string;
        estimatedCost?: number;
    };
    sharedWith?: string[];
    uploadedBy: string;
    viewedAt?: Date; // 새로운 필드: 마지막 조회 시간
    versionHistory?: { version: number; date: Date; uploadedBy: string }[]; // 버전 히스토리
}

interface Project {
    id: string;
    name: string;
    client: string;
    drawingCount: number;
}

interface Contact {
    id: string;
    name: string;
    email: string;
    company: string;
    category: 'customer' | 'vendor' | 'internal';
}

// 샘플 데이터
const sampleDrawings: Drawing[] = [
    {
        id: '1',
        name: 'OO빌딩_분전반도면_v3.pdf',
        projectName: 'OO빌딩 신축공사',
        projectId: 'p1',
        fileType: 'pdf',
        fileSize: 2500000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
        updatedAt: new Date(Date.now() - 1000 * 60 * 30),
        version: 3,
        status: 'analyzed',
        starred: true,
        tags: ['분전반', '신축', '상도'],
        folder: '진행중',
        analysisResult: {
            panels: 3,
            breakers: 24,
            mainBreaker: 'SBE-104 100A',
            estimatedCost: 4500000
        },
        sharedWith: ['park@vendor.kr', 'kim@partner.co.kr'],
        uploadedBy: '홍길동',
        viewedAt: new Date(Date.now() - 1000 * 60 * 5),
        versionHistory: [
            { version: 1, date: new Date(Date.now() - 1000 * 60 * 60 * 72), uploadedBy: '홍길동' },
            { version: 2, date: new Date(Date.now() - 1000 * 60 * 60 * 48), uploadedBy: '홍길동' },
            { version: 3, date: new Date(Date.now() - 1000 * 60 * 60 * 2), uploadedBy: '홍길동' },
        ]
    },
    {
        id: '2',
        name: 'XX공장_배전반도면.dwg',
        projectName: 'XX공장 증설',
        projectId: 'p2',
        fileType: 'dwg',
        fileSize: 4500000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 12),
        version: 2,
        status: 'analyzed',
        starred: false,
        tags: ['배전반', '공장', 'LS'],
        folder: '진행중',
        analysisResult: {
            panels: 5,
            breakers: 48,
            mainBreaker: 'SBE-403 300A',
            estimatedCost: 12500000
        },
        uploadedBy: '김철수',
        viewedAt: new Date(Date.now() - 1000 * 60 * 30),
        versionHistory: [
            { version: 1, date: new Date(Date.now() - 1000 * 60 * 60 * 48), uploadedBy: '김철수' },
            { version: 2, date: new Date(Date.now() - 1000 * 60 * 60 * 24), uploadedBy: '김철수' },
        ]
    },
    {
        id: '3',
        name: '현장사진_전기실.jpg',
        projectName: 'YY아파트 리모델링',
        projectId: 'p3',
        fileType: 'jpg',
        fileSize: 1200000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 48),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 48),
        version: 1,
        status: 'pending',
        starred: false,
        tags: ['현장사진', '리모델링'],
        folder: '진행중',
        uploadedBy: '이영희'
    },
    {
        id: '4',
        name: 'ZZ오피스_단선결선도.pdf',
        projectName: 'ZZ오피스 인테리어',
        projectId: 'p4',
        fileType: 'pdf',
        fileSize: 3200000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 72),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
        version: 1,
        status: 'approved',
        starred: true,
        tags: ['단선결선도', '오피스'],
        folder: '완료',
        analysisResult: {
            panels: 2,
            breakers: 16,
            mainBreaker: 'SBE-103 75A',
            estimatedCost: 2800000
        },
        uploadedBy: '홍길동',
        viewedAt: new Date(Date.now() - 1000 * 60 * 60 * 2)
    },
    {
        id: '5',
        name: 'AA센터_변전실배치도.dwg',
        projectName: 'AA센터 신축',
        projectId: 'p5',
        fileType: 'dwg',
        fileSize: 5800000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 96),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 72),
        version: 4,
        status: 'analyzed',
        starred: false,
        tags: ['변전실', '배치도', '대형'],
        folder: '진행중',
        analysisResult: {
            panels: 8,
            breakers: 96,
            mainBreaker: 'SBE-603 500A',
            estimatedCost: 45000000
        },
        uploadedBy: '박지민',
        versionHistory: [
            { version: 1, date: new Date(Date.now() - 1000 * 60 * 60 * 120), uploadedBy: '박지민' },
            { version: 2, date: new Date(Date.now() - 1000 * 60 * 60 * 108), uploadedBy: '박지민' },
            { version: 3, date: new Date(Date.now() - 1000 * 60 * 60 * 84), uploadedBy: '박지민' },
            { version: 4, date: new Date(Date.now() - 1000 * 60 * 60 * 72), uploadedBy: '박지민' },
        ]
    }
];

const sampleProjects: Project[] = [
    { id: 'p1', name: 'OO빌딩 신축공사', client: '파트너건설', drawingCount: 5 },
    { id: 'p2', name: 'XX공장 증설', client: '대한전기', drawingCount: 3 },
    { id: 'p3', name: 'YY아파트 리모델링', client: '주택개발', drawingCount: 2 },
    { id: 'p4', name: 'ZZ오피스 인테리어', client: '오피스건축', drawingCount: 4 },
    { id: 'p5', name: 'AA센터 신축', client: '대형건설', drawingCount: 8 },
];

const sampleContacts: Contact[] = [
    { id: '1', name: '김건설 부장', email: 'kim@partner.co.kr', company: '파트너건설', category: 'customer' },
    { id: '2', name: '박차장', email: 'park@vendor.kr', company: '상도전기', category: 'vendor' },
    { id: '3', name: '이대리', email: 'lee@bigcorp.com', company: '대한전기', category: 'customer' },
    { id: '4', name: '최과장', email: 'choi@supplier.com', company: 'LS산전', category: 'vendor' },
];

const folders = ['전체', '진행중', '완료', '보류', '보관'];
const allTags = ['분전반', '배전반', '신축', '리모델링', '상도', 'LS', '단선결선도', '현장사진', '공장', '오피스', '대형'];

export default function DrawingsPage() {
    // State
    const [drawings, setDrawings] = useState<Drawing[]>(sampleDrawings);
    const [projects] = useState<Project[]>(sampleProjects);
    const [contacts] = useState<Contact[]>(sampleContacts);

    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedFolder, setSelectedFolder] = useState('전체');
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'date' | 'name' | 'size'>('date');

    const [selectedDrawings, setSelectedDrawings] = useState<string[]>([]);
    const [selectedDrawing, setSelectedDrawing] = useState<Drawing | null>(null);

    const [showShareModal, setShowShareModal] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(true);

    // 새로운 기능들을 위한 state
    const [showRecentView, setShowRecentView] = useState(false); // 최근 조회 기록
    const [showVersionHistory, setShowVersionHistory] = useState(false); // 버전 히스토리
    const [compareMode, setCompareMode] = useState(false); // 비교 모드
    const [compareDrawings, setCompareDrawings] = useState<string[]>([]); // 비교할 도면들

    const fileInputRef = useRef<HTMLInputElement>(null);

    // 도면 파일을 Railway DB에 업로드
    const handleFileUpload = useCallback(async (files: FileList | null) => {
        if (!files || files.length === 0) return;
        setLoading(true);

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            try {
                const formData = new FormData();
                formData.append("file", file);
                formData.append("drawing_name", file.name);
                await api.erp.drawingFiles.upload(formData);
            } catch (err) {
                console.error("도면 업로드 실패:", file.name, err);
            }
        }

        setLoading(false);
        fetchDrawings();
    }, []);

    // Railway DB에서 도면 목록 로드
    const fetchDrawings = useCallback(async () => {
        try {
            const dbFiles = await api.erp.drawingFiles.list({ limit: 100 });
            if (Array.isArray(dbFiles) && dbFiles.length > 0) {
                const mapped: Drawing[] = dbFiles.map((f: ERPDrawingFile) => ({
                    id: f.id,
                    name: f.drawing_name || f.file_name,
                    projectName: f.project_name || '',
                    projectId: f.project_name || '',
                    fileType: (f.file_type || 'pdf') as Drawing['fileType'],
                    fileSize: f.file_size || 0,
                    uploadedAt: new Date(f.created_at || Date.now()),
                    updatedAt: new Date(f.updated_at || f.created_at || Date.now()),
                    version: f.version || 1,
                    status: (f.status === 'analyzed' || f.status === 'approved' || f.status === 'rejected')
                        ? f.status : 'pending' as Drawing['status'],
                    starred: false,
                    tags: f.tags || [],
                    folder: '전체',
                    uploadedBy: f.customer_name || '시스템',
                    description: f.description,
                }));
                setDrawings(mapped);
            }
        } catch (error) {
            console.error('Failed to fetch drawings from DB:', error);
            // DB 실패 시 샘플 데이터 유지
        } finally {
            setInitialLoading(false);
        }
    }, []);

    // 초기 데이터 로드
    useEffect(() => {
        fetchDrawings();
    }, [fetchDrawings]);

    // 최근 조회한 도면들
    const recentlyViewed = useMemo(() => {
        return drawings
            .filter(d => d.viewedAt)
            .sort((a, b) => (b.viewedAt?.getTime() || 0) - (a.viewedAt?.getTime() || 0))
            .slice(0, 5);
    }, [drawings]);

    // 필터링된 도면 목록
    const filteredDrawings = useMemo(() => {
        let result = drawings;

        // 폴더 필터
        if (selectedFolder !== '전체') {
            result = result.filter(d => d.folder === selectedFolder);
        }

        // 검색 필터
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            result = result.filter(d =>
                d.name.toLowerCase().includes(query) ||
                d.projectName.toLowerCase().includes(query) ||
                d.tags.some(t => t.toLowerCase().includes(query))
            );
        }

        // 태그 필터
        if (selectedTags.length > 0) {
            result = result.filter(d =>
                selectedTags.some(tag => d.tags.includes(tag))
            );
        }

        // 상태 필터
        if (selectedStatus) {
            result = result.filter(d => d.status === selectedStatus);
        }

        // 정렬 (별표 항목 먼저)
        result.sort((a, b) => {
            // 별표 먼저
            if (a.starred && !b.starred) return -1;
            if (!a.starred && b.starred) return 1;

            switch (sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'size':
                    return b.fileSize - a.fileSize;
                default:
                    return b.updatedAt.getTime() - a.updatedAt.getTime();
            }
        });

        return result;
    }, [drawings, selectedFolder, searchQuery, selectedTags, selectedStatus, sortBy]);

    // 통계
    const stats = useMemo(() => ({
        total: drawings.length,
        analyzed: drawings.filter(d => d.status === 'analyzed').length,
        pending: drawings.filter(d => d.status === 'pending').length,
        totalSize: drawings.reduce((acc, d) => acc + d.fileSize, 0)
    }), [drawings]);

    // 액션
    const toggleStar = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const drawing = drawings.find(d => d.id === id);
        if (!drawing) return;

        // 낙관적 업데이트
        setDrawings(prev => prev.map(d => d.id === id ? { ...d, starred: !d.starred } : d));

        try {
            const response = await fetch('/api/drawings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, starred: !drawing.starred }),
            });

            if (!response.ok) {
                // 실패 시 롤백
                setDrawings(prev => prev.map(d => d.id === id ? { ...d, starred: drawing.starred } : d));
            }
        } catch (error) {
            console.error('Failed to toggle star:', error);
            // 롤백
            setDrawings(prev => prev.map(d => d.id === id ? { ...d, starred: drawing.starred } : d));
        }
    };

    const handleSelectDrawing = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();

        // 비교 모드일 때
        if (compareMode) {
            setCompareDrawings(prev => {
                if (prev.includes(id)) {
                    return prev.filter(did => did !== id);
                }
                if (prev.length < 2) {
                    return [...prev, id];
                }
                return prev;
            });
            return;
        }

        setSelectedDrawings(prev =>
            prev.includes(id) ? prev.filter(did => did !== id) : [...prev, id]
        );
    };

    const handleSelectAll = () => {
        if (selectedDrawings.length === filteredDrawings.length) {
            setSelectedDrawings([]);
        } else {
            setSelectedDrawings(filteredDrawings.map(d => d.id));
        }
    };

    const handleDelete = async (ids: string[]) => {
        if (!confirm(`${ids.length}개의 도면을 삭제하시겠습니까?`)) return;

        // 낙관적 업데이트
        const deletedDrawings = drawings.filter(d => ids.includes(d.id));
        setDrawings(prev => prev.filter(d => !ids.includes(d.id)));
        setSelectedDrawings([]);
        setSelectedDrawing(null);

        try {
            // Railway DB에서 각 파일 삭제
            await Promise.all(ids.map(id => api.erp.drawingFiles.delete(id).catch(() => {})));
        } catch (error) {
            console.error('Failed to delete drawings:', error);
            // 롤백
            setDrawings(prev => [...prev, ...deletedDrawings]);
        }
    };

    const handleAnalyze = async (id: string) => {
        const drawing = drawings.find(d => d.id === id);
        if (!drawing) return;

        setLoading(true);

        try {
            // AI 분석 API 호출
            const analyzeResponse = await fetch('/api/drawings/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    drawingId: id,
                    fileType: drawing.fileType,
                    fileName: drawing.name
                }),
            });

            if (analyzeResponse.ok) {
                const analyzeData = await analyzeResponse.json();

                if (analyzeData.success && analyzeData.analysisResult) {
                    // 도면 상태 업데이트
                    const updateResponse = await fetch('/api/drawings', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id,
                            status: 'analyzed',
                            analysisResult: analyzeData.analysisResult
                        }),
                    });

                    if (updateResponse.ok) {
                        setDrawings(prev => prev.map(d => d.id === id ? {
                            ...d,
                            status: 'analyzed' as const,
                            analysisResult: analyzeData.analysisResult
                        } : d));

                        // 선택된 도면 업데이트
                        if (selectedDrawing?.id === id) {
                            setSelectedDrawing(prev => prev ? {
                                ...prev,
                                status: 'analyzed' as const,
                                analysisResult: analyzeData.analysisResult
                            } : null);
                        }
                    }
                }
            } else {
                // 폴백: 로컬 시뮬레이션
                setDrawings(prev => prev.map(d => d.id === id ? {
                    ...d,
                    status: 'analyzed' as const,
                    analysisResult: {
                        panels: Math.floor(Math.random() * 5) + 1,
                        breakers: Math.floor(Math.random() * 30) + 10,
                        mainBreaker: 'SBE-104 100A',
                        estimatedCost: Math.floor(Math.random() * 10000000) + 1000000
                    }
                } : d));
            }
        } catch (error) {
            console.error('Failed to analyze drawing:', error);
            // 폴백: 로컬 시뮬레이션
            setDrawings(prev => prev.map(d => d.id === id ? {
                ...d,
                status: 'analyzed' as const,
                analysisResult: {
                    panels: Math.floor(Math.random() * 5) + 1,
                    breakers: Math.floor(Math.random() * 30) + 10,
                    mainBreaker: 'SBE-104 100A',
                    estimatedCost: Math.floor(Math.random() * 10000000) + 1000000
                }
            } : d));
        } finally {
            setLoading(false);
        }
    };

    // 도면 열기 (최근 조회 기록 업데이트)
    const handleOpenDrawing = async (drawing: Drawing) => {
        // 로컬 상태 먼저 업데이트
        const viewedAt = new Date();
        setDrawings(prev => prev.map(d => d.id === drawing.id ? { ...d, viewedAt } : d));
        setSelectedDrawing({ ...drawing, viewedAt });

        // API 호출 (비동기)
        try {
            await fetch('/api/drawings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: drawing.id, viewed: true }),
            });
        } catch (error) {
            console.error('Failed to update viewedAt:', error);
        }
    };

    // 도면 파일 다운로드 (Railway DB에서)
    const handleDownload = async (ids: string[]) => {
        for (const id of ids) {
            try {
                const res = await api.erp.drawingFiles.download(id);
                if (res.ok) {
                    const blob = await res.blob();
                    const drawing = drawings.find(d => d.id === id);
                    const fileName = drawing?.name || `drawing_${id}`;
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
            } catch (err) {
                console.error("다운로드 실패:", id, err);
            }
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const formatDate = (date: Date) => {
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) {
            const hours = Math.floor(diff / (1000 * 60 * 60));
            if (hours === 0) {
                const minutes = Math.floor(diff / (1000 * 60));
                return `${minutes}분 전`;
            }
            return `${hours}시간 전`;
        } else if (days === 1) {
            return '어제';
        } else if (days < 7) {
            return `${days}일 전`;
        } else {
            return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
        }
    };

    // 파일 아이콘 (색상 제거, 아이콘만)
    const getFileIcon = (fileType: string) => {
        switch (fileType.toLowerCase()) {
            case 'pdf':
                return FileText;
            case 'dwg':
            case 'dxf':
                return File;
            case 'jpg':
            case 'jpeg':
            case 'png':
                return FileImage;
            default:
                return File;
        }
    };

    // 상태 아이콘과 스타일 (색상 통일)
    const getStatusInfo = (status: string) => {
        switch (status) {
            case 'analyzed':
                return { icon: CheckCircle2, label: '분석완료', className: 'text-text-subtle' };
            case 'pending':
                return { icon: AlertCircle, label: '분석필요', className: 'text-red-500' };
            case 'approved':
                return { icon: Check, label: '승인됨', className: 'text-brand' };
            case 'rejected':
                return { icon: X, label: '반려됨', className: 'text-text-subtle' };
            default:
                return { icon: Clock, label: '대기중', className: 'text-text-subtle' };
        }
    };

    // 비교 모드 도면 정보
    const compareDrawingData = useMemo(() => {
        return compareDrawings.map(id => drawings.find(d => d.id === id)).filter(Boolean) as Drawing[];
    }, [compareDrawings, drawings]);

    return (
        <div className="h-screen flex flex-col bg-bg overflow-hidden">
            {/* Top Header */}
            <div className="flex-shrink-0 h-14 bg-surface border-b border-border/40 flex items-center justify-between px-4">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-brand/10">
                            <FileText className="w-5 h-5 text-brand" />
                        </div>
                        <h1 className="text-lg font-semibold text-text-strong">도면관리</h1>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-text-subtle">
                        <span className="px-2 py-0.5 bg-surface-secondary rounded">{stats.total}개 파일</span>
                        {stats.pending > 0 && (
                            <span className="px-2 py-0.5 bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 rounded">
                                {stats.pending}개 분석필요
                            </span>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {/* 비교 모드 토글 */}
                    <button
                        onClick={() => {
                            setCompareMode(!compareMode);
                            setCompareDrawings([]);
                        }}
                        className={cn(
                            "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition",
                            compareMode
                                ? "bg-brand text-white"
                                : "text-text-subtle hover:text-text hover:bg-surface-secondary border border-border/30"
                        )}
                    >
                        <Columns className="w-4 h-4" />
                        비교
                    </button>
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition font-medium text-sm"
                    >
                        <Upload className="w-4 h-4" />
                        도면 업로드
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.dwg,.dxf,.jpg,.jpeg,.png,.xlsx,.svg,.bmp,.tiff"
                        className="hidden"
                        onChange={(e) => handleFileUpload(e.target.files)}
                    />
                </div>
            </div>

            {/* 비교 모드 안내 바 */}
            {compareMode && (
                <div className="flex-shrink-0 h-10 bg-brand/10 border-b border-brand/20 flex items-center justify-between px-4">
                    <div className="flex items-center gap-2 text-sm">
                        <Columns className="w-4 h-4 text-brand" />
                        <span className="text-text-strong font-medium">비교 모드</span>
                        <span className="text-text-subtle">
                            {compareDrawings.length}/2개 선택됨
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        {compareDrawings.length === 2 && (
                            <button
                                onClick={() => {/* 비교 뷰 열기 */}}
                                className="px-3 py-1 bg-brand text-white rounded text-sm font-medium"
                            >
                                비교하기
                            </button>
                        )}
                        <button
                            onClick={() => { setCompareMode(false); setCompareDrawings([]); }}
                            className="px-3 py-1 text-sm text-text-subtle hover:text-text"
                        >
                            취소
                        </button>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <div className="w-56 flex-shrink-0 bg-surface border-r border-border/40 flex flex-col">
                    {/* Search */}
                    <div className="p-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
                            <input
                                type="text"
                                placeholder="도면 검색..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 bg-surface-secondary border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand/50"
                            />
                        </div>
                    </div>

                    {/* Folders */}
                    <nav className="flex-1 overflow-y-auto px-2">
                        {/* 최근 조회 (새로운 기능) */}
                        <div className="mb-4">
                            <button
                                onClick={() => setShowRecentView(!showRecentView)}
                                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-text hover:bg-surface-secondary transition"
                            >
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-text-subtle" />
                                    <span>최근 조회</span>
                                </div>
                                <ChevronRight className={cn("w-4 h-4 text-text-subtle transition-transform", showRecentView && "rotate-90")} />
                            </button>
                            {showRecentView && recentlyViewed.length > 0 && (
                                <div className="mt-1 pl-6 space-y-0.5">
                                    {recentlyViewed.map((drawing) => (
                                        <button
                                            key={drawing.id}
                                            onClick={() => handleOpenDrawing(drawing)}
                                            className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs text-text-subtle hover:text-text hover:bg-surface-secondary transition truncate"
                                        >
                                            {React.createElement(getFileIcon(drawing.fileType), { className: "w-3 h-3 flex-shrink-0" })}
                                            <span className="truncate">{drawing.name}</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="mb-4">
                            <div className="flex items-center justify-between px-3 mb-2">
                                <span className="text-xs font-medium text-text-subtle uppercase tracking-wide">폴더</span>
                                <button className="p-1 text-text-subtle hover:text-text rounded">
                                    <FolderPlus className="w-3.5 h-3.5" />
                                </button>
                            </div>
                            <div className="space-y-0.5">
                                {folders.map((folder) => {
                                    const count = folder === '전체' ? drawings.length : drawings.filter(d => d.folder === folder).length;
                                    return (
                                        <button
                                            key={folder}
                                            onClick={() => setSelectedFolder(folder)}
                                            className={cn(
                                                "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition",
                                                selectedFolder === folder
                                                    ? 'bg-brand/10 text-brand font-medium'
                                                    : 'text-text hover:bg-surface-secondary'
                                            )}
                                        >
                                            <Folder className={cn("w-4 h-4", selectedFolder === folder ? 'text-brand' : 'text-text-subtle')} />
                                            <span className="flex-1 text-left">{folder}</span>
                                            <span className="text-xs text-text-subtle">{count}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Projects */}
                        <div className="mb-4 pt-4 border-t border-border/30">
                            <div className="flex items-center justify-between px-3 mb-2">
                                <span className="text-xs font-medium text-text-subtle uppercase tracking-wide">프로젝트</span>
                            </div>
                            <div className="space-y-0.5">
                                {projects.slice(0, 4).map((project) => (
                                    <button
                                        key={project.id}
                                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text hover:bg-surface-secondary transition"
                                    >
                                        <Building2 className="w-4 h-4 text-text-subtle" />
                                        <span className="flex-1 text-left truncate">{project.name}</span>
                                        <span className="text-xs text-text-subtle">{project.drawingCount}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Tags */}
                        <div className="pt-4 border-t border-border/30">
                            <div className="flex items-center justify-between px-3 mb-2">
                                <span className="text-xs font-medium text-text-subtle uppercase tracking-wide">태그</span>
                            </div>
                            <div className="flex flex-wrap gap-1 px-3">
                                {allTags.slice(0, 8).map((tag) => (
                                    <button
                                        key={tag}
                                        onClick={() => setSelectedTags(prev =>
                                            prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
                                        )}
                                        className={cn(
                                            "px-2 py-1 text-xs rounded-full transition",
                                            selectedTags.includes(tag)
                                                ? 'bg-brand/10 text-brand'
                                                : 'bg-surface-secondary text-text-subtle hover:text-text'
                                        )}
                                    >
                                        {tag}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </nav>

                    {/* Storage Info */}
                    <div className="p-3 border-t border-border/30">
                        <div className="text-xs text-text-subtle mb-1">저장공간</div>
                        <div className="w-full h-1.5 bg-surface-secondary rounded-full overflow-hidden">
                            <div className="h-full w-1/3 bg-brand rounded-full" />
                        </div>
                        <div className="text-xs text-text-subtle mt-1">{formatFileSize(stats.totalSize)} 사용중</div>
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col">
                    {/* Toolbar */}
                    <div className="flex-shrink-0 h-12 bg-surface border-b border-border/30 flex items-center justify-between px-4">
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleSelectAll}
                                className={cn(
                                    "w-5 h-5 rounded border-2 flex items-center justify-center transition",
                                    selectedDrawings.length === filteredDrawings.length && filteredDrawings.length > 0
                                        ? 'bg-brand border-brand text-white'
                                        : 'border-border hover:border-brand/50'
                                )}
                            >
                                {selectedDrawings.length === filteredDrawings.length && filteredDrawings.length > 0 && (
                                    <Check className="w-3 h-3" />
                                )}
                            </button>

                            {selectedDrawings.length > 0 ? (
                                <>
                                    <span className="text-sm text-text-subtle ml-2">{selectedDrawings.length}개 선택됨</span>
                                    <div className="w-px h-5 bg-border/50 mx-2" />
                                    <button
                                        onClick={() => setShowShareModal(true)}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                    >
                                        <Send className="w-4 h-4" />
                                        전송
                                    </button>
                                    <button
                                        onClick={() => handleDownload(selectedDrawings)}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                    >
                                        <Download className="w-4 h-4" />
                                        다운로드
                                    </button>
                                    <button
                                        onClick={() => handleDelete(selectedDrawings)}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                        삭제
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition">
                                        <RefreshCw className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => setShowFilters(!showFilters)}
                                        className={cn(
                                            "flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition",
                                            showFilters || selectedStatus
                                                ? 'bg-brand/10 text-brand'
                                                : 'text-text-subtle hover:text-text hover:bg-surface-secondary'
                                        )}
                                    >
                                        <Filter className="w-4 h-4" />
                                        필터
                                        {selectedStatus && <span className="w-1.5 h-1.5 rounded-full bg-brand" />}
                                    </button>
                                </>
                            )}
                        </div>

                        <div className="flex items-center gap-2">
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value as 'date' | 'name' | 'size')}
                                className="px-3 py-1.5 text-sm bg-surface-secondary border border-border/30 rounded-lg text-text focus:outline-none focus:ring-2 focus:ring-brand/30"
                            >
                                <option value="date">최근 수정순</option>
                                <option value="name">이름순</option>
                                <option value="size">크기순</option>
                            </select>
                            <div className="flex bg-surface-secondary rounded-lg p-0.5">
                                <button
                                    onClick={() => setViewMode('grid')}
                                    className={cn(
                                        "p-1.5 rounded transition",
                                        viewMode === 'grid' ? 'bg-surface shadow-sm text-text' : 'text-text-subtle hover:text-text'
                                    )}
                                >
                                    <Grid className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => setViewMode('list')}
                                    className={cn(
                                        "p-1.5 rounded transition",
                                        viewMode === 'list' ? 'bg-surface shadow-sm text-text' : 'text-text-subtle hover:text-text'
                                    )}
                                >
                                    <List className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Filter Bar */}
                    {showFilters && (
                        <div className="flex-shrink-0 h-10 bg-surface-secondary/50 border-b border-border/30 flex items-center gap-2 px-4">
                            <span className="text-xs text-text-subtle">상태:</span>
                            {['analyzed', 'pending', 'approved'].map((status) => {
                                const info = getStatusInfo(status);
                                return (
                                    <button
                                        key={status}
                                        onClick={() => setSelectedStatus(selectedStatus === status ? null : status)}
                                        className={cn(
                                            "flex items-center gap-1 px-2 py-1 text-xs rounded transition",
                                            selectedStatus === status
                                                ? 'bg-brand/10 text-brand'
                                                : 'text-text-subtle hover:bg-surface-secondary'
                                        )}
                                    >
                                        {React.createElement(info.icon, { className: "w-3 h-3" })}
                                        {info.label}
                                    </button>
                                );
                            })}
                            {(selectedTags.length > 0 || selectedStatus) && (
                                <button
                                    onClick={() => { setSelectedTags([]); setSelectedStatus(null); }}
                                    className="ml-auto text-xs text-text-subtle hover:text-text"
                                >
                                    필터 초기화
                                </button>
                            )}
                        </div>
                    )}

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-4">
                        {filteredDrawings.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-text-subtle">
                                <div className="w-20 h-20 rounded-2xl bg-surface flex items-center justify-center mb-4">
                                    <FolderOpen className="w-10 h-10 opacity-30" />
                                </div>
                                <h3 className="text-lg font-medium text-text-strong mb-1">도면이 없습니다</h3>
                                <p className="text-sm mb-4">도면을 업로드하여 AI 분석을 시작하세요</p>
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition text-sm font-medium"
                                >
                                    <Upload className="w-4 h-4" />
                                    도면 업로드
                                </button>
                            </div>
                        ) : viewMode === 'grid' ? (
                            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                {filteredDrawings.map((drawing) => {
                                    const IconComponent = getFileIcon(drawing.fileType);
                                    const statusInfo = getStatusInfo(drawing.status);
                                    const isCompareSelected = compareDrawings.includes(drawing.id);

                                    return (
                                        <div
                                            key={drawing.id}
                                            onClick={() => handleOpenDrawing(drawing)}
                                            className={cn(
                                                "group bg-surface rounded-xl border transition cursor-pointer overflow-hidden",
                                                isCompareSelected
                                                    ? 'border-brand ring-2 ring-brand/20'
                                                    : selectedDrawings.includes(drawing.id)
                                                        ? 'border-brand ring-2 ring-brand/20'
                                                        : 'border-border/30 hover:border-border hover:shadow-md'
                                            )}
                                        >
                                            {/* Thumbnail */}
                                            <div className="relative h-32 bg-surface-secondary flex items-center justify-center">
                                                <div className="w-16 h-16 rounded-xl bg-surface flex items-center justify-center">
                                                    <IconComponent className="w-8 h-8 text-text-subtle" />
                                                </div>

                                                {/* 선택 체크박스 */}
                                                <div className="absolute top-2 left-2">
                                                    <button
                                                        onClick={(e) => handleSelectDrawing(drawing.id, e)}
                                                        className={cn(
                                                            "w-5 h-5 rounded border-2 flex items-center justify-center transition",
                                                            selectedDrawings.includes(drawing.id) || isCompareSelected
                                                                ? 'bg-brand border-brand text-white'
                                                                : 'bg-white/80 border-border opacity-0 group-hover:opacity-100'
                                                        )}
                                                    >
                                                        {(selectedDrawings.includes(drawing.id) || isCompareSelected) && <Check className="w-3 h-3" />}
                                                    </button>
                                                </div>

                                                {/* 즐겨찾기 */}
                                                <div className="absolute top-2 right-2 flex items-center gap-1">
                                                    <button
                                                        onClick={(e) => toggleStar(drawing.id, e)}
                                                        className={cn(
                                                            "p-1 rounded transition",
                                                            drawing.starred
                                                                ? 'text-brand bg-brand/10'
                                                                : 'text-text-subtle/50 bg-white/80 opacity-0 group-hover:opacity-100 hover:text-brand'
                                                        )}
                                                    >
                                                        <Star className={cn("w-4 h-4", drawing.starred && 'fill-current')} />
                                                    </button>
                                                </div>

                                                {/* 상태 배지 */}
                                                <div className="absolute bottom-2 right-2">
                                                    <span className={cn(
                                                        "flex items-center gap-1 px-2 py-0.5 text-xs rounded-full font-medium bg-surface",
                                                        statusInfo.className
                                                    )}>
                                                        {React.createElement(statusInfo.icon, { className: "w-3 h-3" })}
                                                        {statusInfo.label}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Info */}
                                            <div className="p-3">
                                                <div className="flex items-start justify-between gap-2 mb-1">
                                                    <h3 className="text-sm font-medium text-text-strong truncate" title={drawing.name}>
                                                        {drawing.name}
                                                    </h3>
                                                    <span className="text-xs text-text-subtle whitespace-nowrap">v{drawing.version}</span>
                                                </div>
                                                <p className="text-xs text-text-subtle truncate mb-2">{drawing.projectName}</p>
                                                <div className="flex items-center justify-between text-xs text-text-subtle">
                                                    <span>{formatFileSize(drawing.fileSize)}</span>
                                                    <span>{formatDate(drawing.updatedAt)}</span>
                                                </div>
                                                {drawing.tags.length > 0 && (
                                                    <div className="flex items-center gap-1 mt-2 overflow-hidden">
                                                        {drawing.tags.slice(0, 2).map((tag) => (
                                                            <span key={tag} className="px-1.5 py-0.5 text-[10px] bg-surface-secondary rounded text-text-subtle">
                                                                {tag}
                                                            </span>
                                                        ))}
                                                        {drawing.tags.length > 2 && (
                                                            <span className="text-[10px] text-text-subtle">+{drawing.tags.length - 2}</span>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            /* 리스트 뷰 */
                            <div className="bg-surface rounded-xl border border-border/30 overflow-hidden">
                                <table className="w-full">
                                    <thead className="bg-surface-secondary/50">
                                        <tr>
                                            <th className="w-10 px-4 py-3">
                                                <button
                                                    onClick={handleSelectAll}
                                                    className={cn(
                                                        "w-4 h-4 rounded border flex items-center justify-center transition",
                                                        selectedDrawings.length === filteredDrawings.length
                                                            ? 'bg-brand border-brand text-white'
                                                            : 'border-border hover:border-brand/50'
                                                    )}
                                                >
                                                    {selectedDrawings.length === filteredDrawings.length && <Check className="w-2.5 h-2.5" />}
                                                </button>
                                            </th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-text-subtle uppercase">파일명</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-text-subtle uppercase">프로젝트</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-text-subtle uppercase">크기</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-text-subtle uppercase">수정일</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-text-subtle uppercase">상태</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-text-subtle uppercase">작업</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/20">
                                        {filteredDrawings.map((drawing) => {
                                            const IconComponent = getFileIcon(drawing.fileType);
                                            const statusInfo = getStatusInfo(drawing.status);

                                            return (
                                                <tr
                                                    key={drawing.id}
                                                    onClick={() => handleOpenDrawing(drawing)}
                                                    className={cn(
                                                        "cursor-pointer transition",
                                                        selectedDrawings.includes(drawing.id)
                                                            ? 'bg-brand/5'
                                                            : 'hover:bg-surface-secondary/50'
                                                    )}
                                                >
                                                    <td className="px-4 py-3">
                                                        <button
                                                            onClick={(e) => handleSelectDrawing(drawing.id, e)}
                                                            className={cn(
                                                                "w-4 h-4 rounded border flex items-center justify-center transition",
                                                                selectedDrawings.includes(drawing.id)
                                                                    ? 'bg-brand border-brand text-white'
                                                                    : 'border-border hover:border-brand/50'
                                                            )}
                                                        >
                                                            {selectedDrawings.includes(drawing.id) && <Check className="w-2.5 h-2.5" />}
                                                        </button>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-8 h-8 rounded-lg bg-surface-secondary flex items-center justify-center">
                                                                <IconComponent className="w-4 h-4 text-text-subtle" />
                                                            </div>
                                                            <div>
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm font-medium text-text-strong">{drawing.name}</span>
                                                                    {drawing.starred && <Star className="w-3 h-3 text-brand fill-current" />}
                                                                </div>
                                                                <div className="flex items-center gap-1 mt-0.5">
                                                                    {drawing.tags.slice(0, 2).map((tag) => (
                                                                        <span key={tag} className="px-1 py-0.5 text-[10px] bg-surface-secondary rounded text-text-subtle">
                                                                            {tag}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-text-subtle">{drawing.projectName}</td>
                                                    <td className="px-4 py-3 text-sm text-text-subtle">{formatFileSize(drawing.fileSize)}</td>
                                                    <td className="px-4 py-3 text-sm text-text-subtle">{formatDate(drawing.updatedAt)}</td>
                                                    <td className="px-4 py-3">
                                                        <span className={cn(
                                                            "flex items-center gap-1 text-xs font-medium",
                                                            statusInfo.className
                                                        )}>
                                                            {React.createElement(statusInfo.icon, { className: "w-3 h-3" })}
                                                            {statusInfo.label}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <div className="flex items-center justify-end gap-1">
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); }}
                                                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition"
                                                                title="미리보기"
                                                            >
                                                                <Eye className="w-4 h-4" />
                                                            </button>
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); setShowShareModal(true); setSelectedDrawings([drawing.id]); }}
                                                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition"
                                                                title="전송"
                                                            >
                                                                <Send className="w-4 h-4" />
                                                            </button>
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); }}
                                                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition"
                                                                title="다운로드"
                                                            >
                                                                <Download className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                {/* Detail Panel */}
                {selectedDrawing && (
                    <div className="w-80 flex-shrink-0 bg-surface border-l border-border/40 flex flex-col">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-border/30">
                            <h3 className="font-medium text-text-strong">상세정보</h3>
                            <button
                                onClick={() => setSelectedDrawing(null)}
                                className="p-1 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4">
                            {/* Preview */}
                            <div className="mb-4">
                                <div className="h-40 rounded-xl bg-surface-secondary flex items-center justify-center">
                                    {React.createElement(getFileIcon(selectedDrawing.fileType), { className: "w-16 h-16 text-text-subtle" })}
                                </div>
                            </div>

                            {/* File Info */}
                            <h4 className="font-medium text-text-strong mb-2">{selectedDrawing.name}</h4>
                            <div className="flex items-center gap-2 mb-4">
                                {(() => {
                                    const info = getStatusInfo(selectedDrawing.status);
                                    return (
                                        <span className={cn("flex items-center gap-1 px-2 py-0.5 text-xs rounded-full font-medium bg-surface-secondary", info.className)}>
                                            {React.createElement(info.icon, { className: "w-3 h-3" })}
                                            {info.label}
                                        </span>
                                    );
                                })()}
                                <span className="text-xs text-text-subtle">v{selectedDrawing.version}</span>
                            </div>

                            {/* Details */}
                            <div className="space-y-3 text-sm">
                                <div className="flex items-center justify-between">
                                    <span className="text-text-subtle">프로젝트</span>
                                    <span className="text-text font-medium">{selectedDrawing.projectName}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-text-subtle">파일 크기</span>
                                    <span className="text-text">{formatFileSize(selectedDrawing.fileSize)}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-text-subtle">업로드일</span>
                                    <span className="text-text">{selectedDrawing.uploadedAt.toLocaleDateString('ko-KR')}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-text-subtle">업로드</span>
                                    <span className="text-text">{selectedDrawing.uploadedBy}</span>
                                </div>
                            </div>

                            {/* 버전 히스토리 (새로운 기능) */}
                            {selectedDrawing.versionHistory && selectedDrawing.versionHistory.length > 1 && (
                                <div className="mt-4 pt-4 border-t border-border/30">
                                    <button
                                        onClick={() => setShowVersionHistory(!showVersionHistory)}
                                        className="flex items-center justify-between w-full text-xs font-medium text-text-subtle uppercase mb-2"
                                    >
                                        <div className="flex items-center gap-1">
                                            <History className="w-3 h-3" />
                                            버전 히스토리
                                        </div>
                                        <ChevronRight className={cn("w-3 h-3 transition-transform", showVersionHistory && "rotate-90")} />
                                    </button>
                                    {showVersionHistory && (
                                        <div className="space-y-2">
                                            {selectedDrawing.versionHistory.map((v, idx) => (
                                                <div
                                                    key={v.version}
                                                    className={cn(
                                                        "flex items-center justify-between p-2 rounded-lg text-xs",
                                                        idx === selectedDrawing.versionHistory!.length - 1
                                                            ? "bg-brand/10 border border-brand/20"
                                                            : "bg-surface-secondary"
                                                    )}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-medium text-text">v{v.version}</span>
                                                        {idx === selectedDrawing.versionHistory!.length - 1 && (
                                                            <span className="text-brand text-[10px]">현재</span>
                                                        )}
                                                    </div>
                                                    <span className="text-text-subtle">{formatDate(v.date)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Tags */}
                            <div className="mt-4 pt-4 border-t border-border/30">
                                <div className="text-xs font-medium text-text-subtle uppercase mb-2">태그</div>
                                <div className="flex flex-wrap gap-1">
                                    {selectedDrawing.tags.map((tag) => (
                                        <span key={tag} className="px-2 py-1 text-xs bg-surface-secondary rounded text-text">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* Analysis Result */}
                            {selectedDrawing.analysisResult && (
                                <div className="mt-4 pt-4 border-t border-border/30">
                                    <div className="text-xs font-medium text-text-subtle uppercase mb-3">AI 분석 결과</div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="bg-surface-secondary rounded-lg p-3 text-center">
                                            <div className="text-xl font-bold text-brand">{selectedDrawing.analysisResult.panels}</div>
                                            <div className="text-xs text-text-subtle">분전반</div>
                                        </div>
                                        <div className="bg-surface-secondary rounded-lg p-3 text-center">
                                            <div className="text-xl font-bold text-brand">{selectedDrawing.analysisResult.breakers}</div>
                                            <div className="text-xs text-text-subtle">차단기</div>
                                        </div>
                                    </div>
                                    {selectedDrawing.analysisResult.mainBreaker && (
                                        <div className="mt-3 p-3 bg-surface-secondary rounded-lg">
                                            <div className="text-xs text-text-subtle">메인차단기</div>
                                            <div className="font-medium text-text">{selectedDrawing.analysisResult.mainBreaker}</div>
                                        </div>
                                    )}
                                    {selectedDrawing.analysisResult.estimatedCost && (
                                        <div className="mt-3 p-3 bg-brand/10 rounded-lg">
                                            <div className="text-xs text-brand">예상 견적가</div>
                                            <div className="font-bold text-brand">
                                                {selectedDrawing.analysisResult.estimatedCost.toLocaleString()}원
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Shared With */}
                            {selectedDrawing.sharedWith && selectedDrawing.sharedWith.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-border/30">
                                    <div className="text-xs font-medium text-text-subtle uppercase mb-2">공유됨</div>
                                    <div className="space-y-2">
                                        {selectedDrawing.sharedWith.map((email) => (
                                            <div key={email} className="flex items-center gap-2 text-sm">
                                                <div className="w-6 h-6 rounded-full bg-brand/10 flex items-center justify-center text-brand text-xs font-medium">
                                                    {email.charAt(0).toUpperCase()}
                                                </div>
                                                <span className="text-text-subtle truncate">{email}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="p-4 border-t border-border/30 space-y-2">
                            {selectedDrawing.status === 'pending' && (
                                <button
                                    onClick={() => handleAnalyze(selectedDrawing.id)}
                                    disabled={loading}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition text-sm font-medium disabled:opacity-50"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            분석중...
                                        </>
                                    ) : (
                                        <>
                                            <Zap className="w-4 h-4" />
                                            AI 분석
                                        </>
                                    )}
                                </button>
                            )}
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={() => { setShowShareModal(true); setSelectedDrawings([selectedDrawing.id]); }}
                                    className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary rounded-lg transition border border-border/30"
                                >
                                    <Send className="w-4 h-4" />
                                    전송
                                </button>
                                <button className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary rounded-lg transition border border-border/30">
                                    <Download className="w-4 h-4" />
                                    다운로드
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* 비교 뷰 패널 (새로운 기능) */}
                {compareMode && compareDrawingData.length === 2 && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                        <div className="bg-surface rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
                            <div className="flex items-center justify-between px-5 py-4 border-b border-border/30">
                                <h3 className="font-semibold text-text-strong flex items-center gap-2">
                                    <Columns className="w-5 h-5 text-brand" />
                                    도면 비교
                                </h3>
                                <button
                                    onClick={() => { setCompareMode(false); setCompareDrawings([]); }}
                                    className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                            <div className="flex-1 overflow-auto p-5">
                                <div className="grid grid-cols-2 gap-6">
                                    {compareDrawingData.map((drawing) => (
                                        <div key={drawing.id} className="bg-surface-secondary rounded-xl p-4">
                                            {/* 미리보기 */}
                                            <div className="h-40 bg-surface rounded-lg flex items-center justify-center mb-4">
                                                {React.createElement(getFileIcon(drawing.fileType), { className: "w-16 h-16 text-text-subtle" })}
                                            </div>
                                            {/* 정보 */}
                                            <h4 className="font-medium text-text-strong mb-2 truncate">{drawing.name}</h4>
                                            <div className="space-y-2 text-sm">
                                                <div className="flex justify-between">
                                                    <span className="text-text-subtle">버전</span>
                                                    <span className="text-text">v{drawing.version}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-text-subtle">파일 크기</span>
                                                    <span className="text-text">{formatFileSize(drawing.fileSize)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-text-subtle">수정일</span>
                                                    <span className="text-text">{formatDate(drawing.updatedAt)}</span>
                                                </div>
                                                {drawing.analysisResult && (
                                                    <>
                                                        <div className="pt-2 mt-2 border-t border-border/30">
                                                            <div className="flex justify-between">
                                                                <span className="text-text-subtle">분전반</span>
                                                                <span className="text-text font-medium">{drawing.analysisResult.panels}개</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-text-subtle">차단기</span>
                                                                <span className="text-text font-medium">{drawing.analysisResult.breakers}개</span>
                                                            </div>
                                                            {drawing.analysisResult.estimatedCost && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-text-subtle">예상 견적가</span>
                                                                    <span className="text-brand font-bold">{drawing.analysisResult.estimatedCost.toLocaleString()}원</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-border/30 bg-surface-secondary/50">
                                <button
                                    onClick={() => { setCompareMode(false); setCompareDrawings([]); }}
                                    className="px-4 py-2 text-sm text-text-subtle hover:text-text transition"
                                >
                                    닫기
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Share Modal */}
            {showShareModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-surface rounded-2xl shadow-2xl w-full max-w-md">
                        <div className="flex items-center justify-between px-5 py-4 border-b border-border/30">
                            <h3 className="font-semibold text-text-strong">도면 전송</h3>
                            <button
                                onClick={() => { setShowShareModal(false); setSelectedDrawings([]); }}
                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-5">
                            <div className="mb-4">
                                <div className="text-sm text-text-subtle mb-2">{selectedDrawings.length}개 파일 선택됨</div>
                                <div className="max-h-24 overflow-y-auto bg-surface-secondary rounded-lg p-2 space-y-1">
                                    {selectedDrawings.map((id) => {
                                        const drawing = drawings.find(d => d.id === id);
                                        return drawing && (
                                            <div key={id} className="text-sm text-text truncate">{drawing.name}</div>
                                        );
                                    })}
                                </div>
                            </div>
                            <div className="mb-4">
                                <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">받는 사람</label>
                                <input
                                    type="email"
                                    placeholder="이메일 주소 입력"
                                    className="w-full mt-1 px-4 py-2.5 bg-surface-secondary border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-2 focus:ring-brand/30"
                                />
                            </div>
                            <div className="mb-4">
                                <label className="text-xs font-medium text-text-subtle uppercase tracking-wide mb-2 block">빠른 선택</label>
                                <div className="space-y-1 max-h-32 overflow-y-auto">
                                    {contacts.map((contact) => (
                                        <button
                                            key={contact.id}
                                            className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-surface-secondary transition text-left"
                                        >
                                            <div className="w-8 h-8 rounded-full bg-brand/10 flex items-center justify-center text-brand text-sm font-medium">
                                                {contact.name.charAt(0)}
                                            </div>
                                            <div className="flex-1">
                                                <div className="text-sm font-medium text-text">{contact.name}</div>
                                                <div className="text-xs text-text-subtle">{contact.company}</div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="mb-4">
                                <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">메시지 (선택)</label>
                                <textarea
                                    placeholder="전송 시 메시지를 추가하세요..."
                                    rows={3}
                                    className="w-full mt-1 px-4 py-2.5 bg-surface-secondary border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-2 focus:ring-brand/30 resize-none"
                                />
                            </div>
                        </div>
                        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-border/30 bg-surface-secondary/50">
                            <button
                                onClick={() => { setShowShareModal(false); setSelectedDrawings([]); }}
                                className="px-4 py-2 text-sm text-text-subtle hover:text-text transition"
                            >
                                취소
                            </button>
                            <button className="flex items-center gap-2 px-5 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition text-sm font-medium">
                                <Mail className="w-4 h-4" />
                                이메일로 전송
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* AI 서포터 */}
            <AISupporter
                tabContext="drawings"
                onDrawingsAction={(action, data) => {
                    if (action === "analyze" && data.drawingId) {
                        handleAnalyze(data.drawingId as string);
                    }
                    if (action === "selectDrawing" && data.drawingId) {
                        const drawing = drawings.find(d => d.id === data.drawingId);
                        if (drawing) handleOpenDrawing(drawing);
                    }
                    if (action === "share" && data.drawingIds) {
                        setSelectedDrawings(data.drawingIds as string[]);
                        setShowShareModal(true);
                    }
                    if (action === "setFolder" && data.folder) {
                        setSelectedFolder(data.folder as string);
                    }
                    if (action === "search" && data.query) {
                        setSearchQuery(data.query as string);
                    }
                    if (action === "filterByTag" && data.tag) {
                        setSelectedTags(prev =>
                            prev.includes(data.tag as string)
                                ? prev
                                : [...prev, data.tag as string]
                        );
                    }
                }}
            />
        </div>
    );
}
