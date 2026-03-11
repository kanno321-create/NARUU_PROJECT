'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { AISupporter } from '@/components/ai-supporter';
import {
    ChevronLeft,
    ChevronRight,
    Plus,
    Calendar as CalendarIcon,
    Clock,
    MapPin,
    Users,
    X,
    Bell,
    Target,
    Search,
    LayoutGrid,
    CalendarDays,
    AlertCircle,
    CheckCircle2,
    Timer,
    Briefcase,
    GripVertical,
    Edit3,
    Trash2,
    Copy,
} from 'lucide-react';

interface CalendarEvent {
    id: string;
    title: string;
    start: string;
    end: string;
    description?: string;
    location?: string;
    attendees?: string[];
    type?: 'meeting' | 'deadline' | 'task' | 'reminder';
    priority?: 'high' | 'normal' | 'low';
    user_id?: string;
    is_shared?: boolean;
    completed?: boolean;
    customer?: string;
}

// 통일된 색상 팔레트 (브랜드 + 회색 + 강조 1색)
const priorityStyles = {
    high: 'border-l-red-500',
    normal: 'border-l-brand',
    low: 'border-l-slate-400',
};

const typeIcons = {
    meeting: Users,
    deadline: AlertCircle,
    task: CheckCircle2,
    reminder: Bell,
};

export default function CalendarPage() {
    const [events, setEvents] = useState<CalendarEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentDate, setCurrentDate] = useState(new Date());
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);
    const [view, setView] = useState<'month' | 'week'>('month');
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState<string>('all');
    const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
    const [draggedEvent, setDraggedEvent] = useState<CalendarEvent | null>(null);
    const [newEvent, setNewEvent] = useState({
        title: '',
        start: '',
        end: '',
        description: '',
        location: '',
        type: 'meeting' as 'meeting' | 'deadline' | 'task' | 'reminder',
        priority: 'normal' as 'high' | 'normal' | 'low',
    });

    useEffect(() => {
        fetchEvents();
    }, [currentDate]);

    const fetchEvents = async () => {
        try {
            setLoading(true);
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth() + 1;
            const response = await fetch(`/api/calendar/events?year=${year}&month=${month}`);

            if (response.ok) {
                const data = await response.json();
                setEvents(data.events || []);
            } else {
                console.error('Failed to fetch events:', response.status);
                setEvents([]);
            }
        } catch (err) {
            console.error('Failed to fetch events:', err);
        } finally {
            setLoading(false);
        }
    };

    // 검색 및 필터 적용
    const filteredEvents = useMemo(() => {
        return events.filter(event => {
            const matchesSearch = searchQuery === '' ||
                event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                event.description?.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesType = filterType === 'all' || event.type === filterType;
            return matchesSearch && matchesType;
        });
    }, [events, searchQuery, filterType]);

    const handleAddEvent = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingEvent) {
                // 수정 모드 - API 호출
                const response = await fetch('/api/calendar/events', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: editingEvent.id, ...newEvent }),
                });
                if (response.ok) {
                    setEvents(events.map(ev =>
                        ev.id === editingEvent.id
                            ? { ...newEvent, id: editingEvent.id }
                            : ev
                    ));
                }
                setEditingEvent(null);
            } else {
                // 추가 모드 - API 호출
                const response = await fetch('/api/calendar/events', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newEvent),
                });
                if (response.ok) {
                    const data = await response.json();
                    setEvents([...events, data.event]);
                } else {
                    // 폴백: 로컬 추가
                    const newId = `event-${Date.now()}`;
                    setEvents([...events, { ...newEvent, id: newId }]);
                }
            }
        } catch (err) {
            console.error('Failed to save event:', err);
            // 폴백: 로컬 추가
            if (!editingEvent) {
                const newId = `event-${Date.now()}`;
                setEvents([...events, { ...newEvent, id: newId }]);
            }
        }
        setShowAddModal(false);
        setNewEvent({ title: '', start: '', end: '', description: '', location: '', type: 'meeting', priority: 'normal' });
    };

    const handleEditEvent = (event: CalendarEvent) => {
        setEditingEvent(event);
        setNewEvent({
            title: event.title,
            start: event.start.slice(0, 16),
            end: event.end.slice(0, 16),
            description: event.description || '',
            location: event.location || '',
            type: event.type || 'meeting',
            priority: event.priority || 'normal',
        });
        setShowAddModal(true);
    };

    const handleDeleteEvent = async (eventId: string) => {
        try {
            const response = await fetch(`/api/calendar/events?id=${eventId}`, {
                method: 'DELETE',
            });
            if (response.ok) {
                setEvents(events.filter(ev => ev.id !== eventId));
            }
        } catch (err) {
            console.error('Failed to delete event:', err);
            // 폴백: 로컬 삭제
            setEvents(events.filter(ev => ev.id !== eventId));
        }
    };

    const handleDuplicateEvent = async (event: CalendarEvent) => {
        try {
            const duplicatedData = {
                title: `${event.title} (복사)`,
                start: event.start,
                end: event.end,
                description: event.description,
                location: event.location,
                type: event.type,
                priority: event.priority,
            };
            const response = await fetch('/api/calendar/events', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(duplicatedData),
            });
            if (response.ok) {
                const data = await response.json();
                setEvents([...events, data.event]);
            } else {
                // 폴백: 로컬 복사
                const newId = `event-${Date.now()}`;
                setEvents([...events, { ...event, id: newId, title: `${event.title} (복사)` }]);
            }
        } catch (err) {
            console.error('Failed to duplicate event:', err);
            // 폴백: 로컬 복사
            const newId = `event-${Date.now()}`;
            setEvents([...events, { ...event, id: newId, title: `${event.title} (복사)` }]);
        }
    };

    // 드래그 앤 드롭으로 날짜 변경
    const handleDragStart = (event: CalendarEvent) => {
        setDraggedEvent(event);
    };

    const handleDrop = async (date: Date) => {
        if (!draggedEvent) return;

        const originalStart = new Date(draggedEvent.start);
        const originalEnd = new Date(draggedEvent.end);
        const duration = originalEnd.getTime() - originalStart.getTime();

        const newStart = new Date(date);
        newStart.setHours(originalStart.getHours(), originalStart.getMinutes());
        const newEnd = new Date(newStart.getTime() + duration);

        try {
            const response = await fetch('/api/calendar/events', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: draggedEvent.id,
                    start: newStart.toISOString(),
                    end: newEnd.toISOString(),
                }),
            });
            if (response.ok) {
                setEvents(events.map(ev =>
                    ev.id === draggedEvent.id
                        ? { ...ev, start: newStart.toISOString(), end: newEnd.toISOString() }
                        : ev
                ));
            }
        } catch (err) {
            console.error('Failed to update event:', err);
            // 폴백: 로컬 업데이트
            setEvents(events.map(ev =>
                ev.id === draggedEvent.id
                    ? { ...ev, start: newStart.toISOString(), end: newEnd.toISOString() }
                    : ev
            ));
        }
        setDraggedEvent(null);
    };

    const getDaysInMonth = (date: Date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const days: (Date | null)[] = [];

        for (let i = 0; i < firstDay.getDay(); i++) {
            days.push(null);
        }

        for (let i = 1; i <= lastDay.getDate(); i++) {
            days.push(new Date(year, month, i));
        }

        return days;
    };

    const getWeekDays = (date: Date) => {
        const start = new Date(date);
        start.setDate(start.getDate() - start.getDay());
        const days: Date[] = [];
        for (let i = 0; i < 7; i++) {
            days.push(new Date(start.getTime() + i * 24 * 60 * 60 * 1000));
        }
        return days;
    };

    const getEventsForDate = (date: Date) => {
        return filteredEvents.filter(event => {
            const eventDate = new Date(event.start);
            return eventDate.toDateString() === date.toDateString();
        });
    };

    const formatTime = (dateString: string) => {
        return new Date(dateString).toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const navigateMonth = (direction: number) => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + direction, 1));
    };

    const navigateWeek = (direction: number) => {
        setCurrentDate(new Date(currentDate.getTime() + direction * 7 * 24 * 60 * 60 * 1000));
    };

    const days = getDaysInMonth(currentDate);
    const weekDays = ['일', '월', '화', '수', '목', '금', '토'];
    const today = new Date();

    // 통계
    const todayEvents = getEventsForDate(today);
    const upcomingDeadlines = filteredEvents.filter(e => e.type === 'deadline' && new Date(e.start) > today).length;
    const thisWeekMeetings = filteredEvents.filter(e => {
        const eventDate = new Date(e.start);
        const weekFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
        return e.type === 'meeting' && eventDate >= today && eventDate <= weekFromNow;
    }).length;
    const highPriorityCount = filteredEvents.filter(e => e.priority === 'high' && new Date(e.start) >= today).length;

    const typeLabels = { meeting: '미팅', deadline: '마감', task: '업무', reminder: '알림' };
    const priorityLabels = { high: '높음', normal: '보통', low: '낮음' };

    return (
        <div className="flex h-full bg-bg">
            {/* Left Sidebar - 모던 미니멀 디자인 */}
            <div className="w-72 flex-shrink-0 border-r border-border/30 bg-surface/50 p-5">
                {/* Add Event Button */}
                <button
                    onClick={() => {
                        setEditingEvent(null);
                        setNewEvent({ title: '', start: '', end: '', description: '', location: '', type: 'meeting', priority: 'normal' });
                        setShowAddModal(true);
                    }}
                    className="mb-6 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-3.5 font-medium text-white shadow-sm transition-all hover:bg-brand-dark hover:shadow-md"
                >
                    <Plus className="h-5 w-5" />
                    새 일정 추가
                </button>

                {/* Search */}
                <div className="mb-5">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="일정 검색..."
                            className="w-full rounded-lg border border-border/40 bg-surface py-2.5 pl-10 pr-4 text-sm text-text placeholder:text-text-subtle focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/30"
                        />
                    </div>
                </div>

                {/* Mini Calendar */}
                <div className="mb-5 rounded-xl border border-border/30 bg-surface p-4">
                    <div className="mb-3 flex items-center justify-between">
                        <span className="text-sm font-semibold text-text-strong">
                            {currentDate.getFullYear()}. {String(currentDate.getMonth() + 1).padStart(2, '0')}
                        </span>
                        <div className="flex gap-1">
                            <button
                                onClick={() => navigateMonth(-1)}
                                className="rounded-md p-1 text-text-subtle transition-colors hover:bg-surface-secondary hover:text-text"
                            >
                                <ChevronLeft className="h-4 w-4" />
                            </button>
                            <button
                                onClick={() => navigateMonth(1)}
                                className="rounded-md p-1 text-text-subtle transition-colors hover:bg-surface-secondary hover:text-text"
                            >
                                <ChevronRight className="h-4 w-4" />
                            </button>
                        </div>
                    </div>
                    <div className="grid grid-cols-7 gap-0.5 text-center text-xs">
                        {weekDays.map((day, i) => (
                            <div key={day} className={cn(
                                "py-1 font-medium text-text-subtle"
                            )}>
                                {day}
                            </div>
                        ))}
                        {getDaysInMonth(currentDate).map((date, index) => {
                            const hasEvents = date ? getEventsForDate(date).length > 0 : false;
                            return (
                                <button
                                    key={index}
                                    onClick={() => date && setSelectedDate(date)}
                                    disabled={!date}
                                    className={cn(
                                        "relative rounded-md py-1 text-xs transition-colors",
                                        !date && "invisible",
                                        date?.toDateString() === today.toDateString() &&
                                            "bg-brand font-bold text-white",
                                        date && date.toDateString() !== today.toDateString() &&
                                            "hover:bg-surface-secondary text-text",
                                        selectedDate?.toDateString() === date?.toDateString() &&
                                            date?.toDateString() !== today.toDateString() &&
                                            "ring-2 ring-brand/50"
                                    )}
                                >
                                    {date?.getDate()}
                                    {hasEvents && date?.toDateString() !== today.toDateString() && (
                                        <span className="absolute bottom-0 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-brand" />
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Filter by Type */}
                <div className="mb-5">
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-subtle">
                        유형 필터
                    </h3>
                    <div className="space-y-1">
                        {['all', 'meeting', 'deadline', 'task', 'reminder'].map(type => {
                            const Icon = type === 'all' ? LayoutGrid : typeIcons[type as keyof typeof typeIcons];
                            const label = type === 'all' ? '전체' : typeLabels[type as keyof typeof typeLabels];
                            return (
                                <button
                                    key={type}
                                    onClick={() => setFilterType(type)}
                                    className={cn(
                                        "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                                        filterType === type
                                            ? "bg-brand/10 text-brand font-medium"
                                            : "text-text-subtle hover:bg-surface-secondary hover:text-text"
                                    )}
                                >
                                    <Icon className="h-4 w-4" />
                                    {label}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Quick Stats - 모노크롬 */}
                <div className="space-y-2">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-text-subtle">
                        요약
                    </h3>
                    <div className="grid grid-cols-2 gap-2">
                        <div className="rounded-lg bg-surface-secondary/50 p-3 text-center">
                            <p className="text-2xl font-bold text-text-strong">{todayEvents.length}</p>
                            <p className="text-xs text-text-subtle">오늘</p>
                        </div>
                        <div className="rounded-lg bg-surface-secondary/50 p-3 text-center">
                            <p className="text-2xl font-bold text-text-strong">{highPriorityCount}</p>
                            <p className="text-xs text-text-subtle">중요</p>
                        </div>
                        <div className="rounded-lg bg-surface-secondary/50 p-3 text-center">
                            <p className="text-2xl font-bold text-text-strong">{upcomingDeadlines}</p>
                            <p className="text-xs text-text-subtle">마감</p>
                        </div>
                        <div className="rounded-lg bg-surface-secondary/50 p-3 text-center">
                            <p className="text-2xl font-bold text-text-strong">{thisWeekMeetings}</p>
                            <p className="text-xs text-text-subtle">미팅</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-border/30 bg-surface/50 px-6 py-4">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <CalendarIcon className="h-5 w-5 text-brand" />
                            <h1 className="text-lg font-bold text-text-strong">일정 관리</h1>
                        </div>
                        <span className="text-text-subtle">|</span>
                        <span className="font-medium text-text">
                            {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월
                        </span>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* View Toggle */}
                        <div className="flex rounded-lg border border-border/40 bg-surface p-1">
                            <button
                                onClick={() => setView('month')}
                                className={cn(
                                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                                    view === 'month'
                                        ? "bg-brand text-white"
                                        : "text-text-subtle hover:text-text"
                                )}
                            >
                                <LayoutGrid className="h-4 w-4" />
                                월간
                            </button>
                            <button
                                onClick={() => setView('week')}
                                className={cn(
                                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                                    view === 'week'
                                        ? "bg-brand text-white"
                                        : "text-text-subtle hover:text-text"
                                )}
                            >
                                <CalendarDays className="h-4 w-4" />
                                주간
                            </button>
                        </div>

                        <div className="h-6 w-px bg-border/40" />

                        {/* Navigation */}
                        <button
                            onClick={() => view === 'month' ? navigateMonth(-1) : navigateWeek(-1)}
                            className="rounded-lg p-2 text-text-subtle transition-colors hover:bg-surface-secondary hover:text-text"
                        >
                            <ChevronLeft className="h-5 w-5" />
                        </button>
                        <button
                            onClick={() => setCurrentDate(new Date())}
                            className="rounded-lg px-4 py-2 text-sm font-medium text-brand transition-colors hover:bg-brand/10"
                        >
                            오늘
                        </button>
                        <button
                            onClick={() => view === 'month' ? navigateMonth(1) : navigateWeek(1)}
                            className="rounded-lg p-2 text-text-subtle transition-colors hover:bg-surface-secondary hover:text-text"
                        >
                            <ChevronRight className="h-5 w-5" />
                        </button>
                    </div>
                </div>

                {/* Calendar Grid */}
                <div className="flex-1 overflow-auto p-4">
                    <div className="rounded-xl border border-border/30 bg-surface overflow-hidden shadow-sm">
                        {/* Week Headers */}
                        <div className="grid grid-cols-7 border-b border-border/30 bg-surface-secondary/30">
                            {(view === 'week' ? getWeekDays(currentDate) : weekDays).map((day, i) => (
                                <div
                                    key={i}
                                    className="py-3 text-center text-sm font-medium text-text-subtle"
                                >
                                    {view === 'week' ? (
                                        <div>
                                            <div className="text-xs">{weekDays[i]}요일</div>
                                            <div className={cn(
                                                "mt-1 text-lg font-semibold",
                                                (day as Date).toDateString() === today.toDateString()
                                                    ? "text-brand"
                                                    : "text-text-strong"
                                            )}>
                                                {(day as Date).getDate()}
                                            </div>
                                        </div>
                                    ) : (
                                        `${day}요일`
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Days Grid */}
                        {loading ? (
                            <div className="flex h-96 items-center justify-center">
                                <div className="text-center">
                                    <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-brand border-t-transparent" />
                                    <p className="text-sm text-text-subtle">일정을 불러오는 중...</p>
                                </div>
                            </div>
                        ) : view === 'month' ? (
                            <div className="grid grid-cols-7">
                                {days.map((date, index) => {
                                    const dayEvents = date ? getEventsForDate(date) : [];
                                    const isToday = date?.toDateString() === today.toDateString();
                                    const isSelected = selectedDate?.toDateString() === date?.toDateString();

                                    return (
                                        <div
                                            key={index}
                                            onClick={() => date && setSelectedDate(date)}
                                            onDragOver={(e) => e.preventDefault()}
                                            onDrop={() => date && handleDrop(date)}
                                            className={cn(
                                                "min-h-[110px] border-b border-r border-border/20 p-2 transition-colors",
                                                date ? "cursor-pointer hover:bg-surface-secondary/20" : "bg-surface-secondary/10",
                                                isToday && "bg-brand/5",
                                                isSelected && !isToday && "bg-brand/5"
                                            )}
                                        >
                                            {date && (
                                                <>
                                                    <div className="mb-1 flex items-center justify-between">
                                                        <span
                                                            className={cn(
                                                                "flex h-7 w-7 items-center justify-center rounded-full text-sm",
                                                                isToday && "bg-brand font-bold text-white",
                                                                !isToday && "font-medium text-text"
                                                            )}
                                                        >
                                                            {date.getDate()}
                                                        </span>
                                                        {dayEvents.length > 0 && (
                                                            <span className="text-xs text-text-subtle">
                                                                {dayEvents.length}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="space-y-1">
                                                        {dayEvents.slice(0, 3).map(event => {
                                                            const Icon = typeIcons[event.type || 'meeting'];
                                                            return (
                                                                <div
                                                                    key={event.id}
                                                                    draggable
                                                                    onDragStart={() => handleDragStart(event)}
                                                                    className={cn(
                                                                        "group flex cursor-grab items-center gap-1 truncate rounded border-l-2 bg-surface-secondary/50 px-2 py-1 text-xs active:cursor-grabbing",
                                                                        priorityStyles[event.priority || 'normal']
                                                                    )}
                                                                    title={event.title}
                                                                >
                                                                    <Icon className="h-3 w-3 flex-shrink-0 text-text-subtle" />
                                                                    <span className="truncate text-text">{event.title}</span>
                                                                </div>
                                                            );
                                                        })}
                                                        {dayEvents.length > 3 && (
                                                            <div className="text-center text-xs font-medium text-brand">
                                                                +{dayEvents.length - 3}
                                                            </div>
                                                        )}
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            /* Week View */
                            <div className="grid grid-cols-7 min-h-[500px]">
                                {getWeekDays(currentDate).map((date, index) => {
                                    const dayEvents = getEventsForDate(date);
                                    const isToday = date.toDateString() === today.toDateString();

                                    return (
                                        <div
                                            key={index}
                                            onDragOver={(e) => e.preventDefault()}
                                            onDrop={() => handleDrop(date)}
                                            className={cn(
                                                "border-r border-border/20 p-2",
                                                isToday && "bg-brand/5"
                                            )}
                                        >
                                            <div className="space-y-2">
                                                {dayEvents.map(event => {
                                                    const Icon = typeIcons[event.type || 'meeting'];
                                                    return (
                                                        <div
                                                            key={event.id}
                                                            draggable
                                                            onDragStart={() => handleDragStart(event)}
                                                            className={cn(
                                                                "group cursor-grab rounded-lg border-l-2 bg-surface-secondary/50 p-2 active:cursor-grabbing",
                                                                priorityStyles[event.priority || 'normal']
                                                            )}
                                                        >
                                                            <div className="mb-1 flex items-center gap-1.5">
                                                                <Icon className="h-3.5 w-3.5 text-text-subtle" />
                                                                <span className="text-xs font-medium text-text">{event.title}</span>
                                                            </div>
                                                            <div className="flex items-center gap-1 text-xs text-text-subtle">
                                                                <Clock className="h-3 w-3" />
                                                                {formatTime(event.start)}
                                                            </div>
                                                            {/* Quick actions on hover */}
                                                            <div className="mt-2 hidden gap-1 group-hover:flex">
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); handleEditEvent(event); }}
                                                                    className="rounded p-1 text-text-subtle hover:bg-surface hover:text-text"
                                                                >
                                                                    <Edit3 className="h-3 w-3" />
                                                                </button>
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); handleDuplicateEvent(event); }}
                                                                    className="rounded p-1 text-text-subtle hover:bg-surface hover:text-text"
                                                                >
                                                                    <Copy className="h-3 w-3" />
                                                                </button>
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); handleDeleteEvent(event.id); }}
                                                                    className="rounded p-1 text-text-subtle hover:bg-red-50 hover:text-red-500"
                                                                >
                                                                    <Trash2 className="h-3 w-3" />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>

                {/* Today's Schedule Footer */}
                <div className="border-t border-border/30 bg-surface/50 px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10">
                                <Target className="h-5 w-5 text-brand" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-text-strong">오늘의 일정</h3>
                                <p className="text-sm text-text-subtle">
                                    {todayEvents.length > 0 ? `${todayEvents.length}개의 일정` : '예정된 일정 없음'}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {todayEvents.slice(0, 4).map(event => {
                                const Icon = typeIcons[event.type || 'meeting'];
                                return (
                                    <div
                                        key={event.id}
                                        onClick={() => handleEditEvent(event)}
                                        className={cn(
                                            "flex cursor-pointer items-center gap-2 rounded-lg border-l-2 bg-surface-secondary/50 px-3 py-2 transition-colors hover:bg-surface-secondary",
                                            priorityStyles[event.priority || 'normal']
                                        )}
                                    >
                                        <Icon className="h-4 w-4 text-text-subtle" />
                                        <span className="text-sm font-medium text-text">{event.title}</span>
                                        <span className="text-xs text-text-subtle">{formatTime(event.start)}</span>
                                    </div>
                                );
                            })}
                            {todayEvents.length === 0 && (
                                <span className="rounded-lg bg-surface-secondary/50 px-4 py-2 text-sm text-text-subtle">
                                    여유로운 하루 되세요
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* AI 서포터 */}
            <AISupporter
                tabContext="calendar"
                onCalendarAction={(action, data) => {
                    console.log("Calendar AI Action:", action, data);
                    if (action === "addEvent" && data.event) {
                        const event = data.event as CalendarEvent;
                        setEvents(prev => [...prev, event]);
                    }
                    if (action === "showAddModal") {
                        setShowAddModal(true);
                    }
                }}
            />

            {/* Add/Edit Event Modal */}
            {showAddModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                    <div className="w-full max-w-md rounded-2xl border border-border/30 bg-surface p-6 shadow-xl">
                        <div className="mb-5 flex items-center justify-between">
                            <h2 className="text-lg font-bold text-text-strong">
                                {editingEvent ? '일정 수정' : '새 일정 추가'}
                            </h2>
                            <button
                                onClick={() => { setShowAddModal(false); setEditingEvent(null); }}
                                className="rounded-lg p-2 text-text-subtle transition-colors hover:bg-surface-secondary hover:text-text"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        <form onSubmit={handleAddEvent} className="space-y-4">
                            <div>
                                <label className="mb-1.5 block text-sm font-medium text-text">제목</label>
                                <input
                                    type="text"
                                    value={newEvent.title}
                                    onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                                    className="w-full rounded-lg border border-border/40 bg-surface-secondary/30 px-4 py-2.5 text-text placeholder:text-text-subtle focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/30"
                                    placeholder="일정 제목"
                                    required
                                />
                            </div>

                            {/* Type Selection */}
                            <div>
                                <label className="mb-1.5 block text-sm font-medium text-text">유형</label>
                                <div className="grid grid-cols-4 gap-2">
                                    {(['meeting', 'deadline', 'task', 'reminder'] as const).map(type => {
                                        const Icon = typeIcons[type];
                                        return (
                                            <button
                                                key={type}
                                                type="button"
                                                onClick={() => setNewEvent({ ...newEvent, type })}
                                                className={cn(
                                                    "flex flex-col items-center gap-1 rounded-lg py-2.5 text-xs font-medium transition-all",
                                                    newEvent.type === type
                                                        ? "bg-brand text-white"
                                                        : "bg-surface-secondary/50 text-text-subtle hover:bg-surface-secondary"
                                                )}
                                            >
                                                <Icon className="h-4 w-4" />
                                                {typeLabels[type]}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Priority Selection */}
                            <div>
                                <label className="mb-1.5 block text-sm font-medium text-text">우선순위</label>
                                <div className="grid grid-cols-3 gap-2">
                                    {(['high', 'normal', 'low'] as const).map(priority => (
                                        <button
                                            key={priority}
                                            type="button"
                                            onClick={() => setNewEvent({ ...newEvent, priority })}
                                            className={cn(
                                                "rounded-lg border-l-2 py-2 text-xs font-medium transition-all",
                                                priorityStyles[priority],
                                                newEvent.priority === priority
                                                    ? "bg-brand/10 text-brand"
                                                    : "bg-surface-secondary/50 text-text-subtle hover:bg-surface-secondary"
                                            )}
                                        >
                                            {priorityLabels[priority]}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-text">시작</label>
                                    <input
                                        type="datetime-local"
                                        value={newEvent.start}
                                        onChange={(e) => setNewEvent({ ...newEvent, start: e.target.value })}
                                        className="w-full rounded-lg border border-border/40 bg-surface-secondary/30 px-3 py-2.5 text-sm text-text focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/30"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-text">종료</label>
                                    <input
                                        type="datetime-local"
                                        value={newEvent.end}
                                        onChange={(e) => setNewEvent({ ...newEvent, end: e.target.value })}
                                        className="w-full rounded-lg border border-border/40 bg-surface-secondary/30 px-3 py-2.5 text-sm text-text focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/30"
                                        required
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="mb-1.5 block text-sm font-medium text-text">장소 (선택)</label>
                                <input
                                    type="text"
                                    value={newEvent.location}
                                    onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                                    className="w-full rounded-lg border border-border/40 bg-surface-secondary/30 px-4 py-2.5 text-text placeholder:text-text-subtle focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/30"
                                    placeholder="장소"
                                />
                            </div>
                            <div>
                                <label className="mb-1.5 block text-sm font-medium text-text">메모 (선택)</label>
                                <textarea
                                    value={newEvent.description}
                                    onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                                    className="w-full resize-none rounded-lg border border-border/40 bg-surface-secondary/30 px-4 py-2.5 text-text placeholder:text-text-subtle focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/30"
                                    rows={2}
                                    placeholder="메모"
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => { setShowAddModal(false); setEditingEvent(null); }}
                                    className="flex-1 rounded-lg bg-surface-secondary py-2.5 font-medium text-text transition-colors hover:bg-surface-secondary/80"
                                >
                                    취소
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 rounded-lg bg-brand py-2.5 font-medium text-white transition-colors hover:bg-brand-dark"
                                >
                                    {editingEvent ? '수정' : '추가'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
