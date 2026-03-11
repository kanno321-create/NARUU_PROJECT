'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { cn } from '@/lib/utils';
import {
    Mail, Send, FileText, Trash2, Star, Archive, Tag, Search,
    Plus, Paperclip, ChevronDown, ChevronRight, MoreHorizontal,
    Reply, ReplyAll, Forward, Clock, AlertCircle, CheckCircle,
    X, Filter, RefreshCw, Settings, Users, Inbox, Edit3,
    Download, Eye, FolderPlus, Check, Circle, ArrowLeft,
    Pin, Calendar, SlidersHorizontal, Bookmark, Loader2, Wifi, WifiOff
} from 'lucide-react';
import { AISupporter } from '@/components/ai-supporter';
import { API_BASE_URL } from '@/config/api';
import DOMPurify from 'dompurify';
import { fetchAPI } from '@/lib/api';
import { useToast } from '@/components/ui/Toast';

// 타입 정의
interface Email {
    id: string;
    from: string;
    fromName: string;
    to: string[];
    cc?: string[];
    subject: string;
    body: string;
    preview: string;
    date: Date;
    read: boolean;
    starred: boolean;
    important: boolean;
    pinned?: boolean;
    labels: string[];
    attachments?: { name: string; size: string; type: string }[];
    folder: 'inbox' | 'sent' | 'drafts' | 'trash' | 'archive';
}

interface EmailTemplate {
    id: string;
    name: string;
    subject: string;
    body: string;
    category: string;
}

interface Contact {
    id: string;
    name: string;
    email: string;
    company: string;
    category: 'customer' | 'vendor' | 'partner' | 'internal';
}

interface Label {
    id: string;
    name: string;
}

// SMTP 설정 인터페이스
interface SmtpConfig {
    smtp_host: string;
    smtp_port: number;
    smtp_username: string;
    smtp_password: string;
    from_email: string;
    from_name: string;
    use_tls: boolean;
}

const defaultLabels: Label[] = [
    { id: '1', name: '견적요청' },
    { id: '2', name: '견적발송' },
    { id: '3', name: '발주' },
    { id: '4', name: '납품' },
    { id: '5', name: '긴급' },
    { id: '6', name: '공급사' },
];

export default function EmailPage() {
    const { showToast } = useToast();

    // State
    const [emails, setEmails] = useState<Email[]>([]);
    const [inboxEmails, setInboxEmails] = useState<Email[]>([]);
    const [templates, setTemplates] = useState<EmailTemplate[]>([]);
    const [contacts] = useState<Contact[]>([]);
    const [labels] = useState<Label[]>(defaultLabels);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isLoadingInbox, setIsLoadingInbox] = useState(false);

    const [activeFolder, setActiveFolder] = useState<string>('sent');
    const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
    const [selectedEmails, setSelectedEmails] = useState<string[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [showCompose, setShowCompose] = useState(false);
    const [showTemplates, setShowTemplates] = useState(false);
    const [showContacts, setShowContacts] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [filterLabel, setFilterLabel] = useState<string | null>(null);
    const [showSchedulePicker, setShowSchedulePicker] = useState(false);

    // 로딩 및 SMTP 상태
    const [isLoadingEmails, setIsLoadingEmails] = useState(true);
    const [isLoadingTemplates, setIsLoadingTemplates] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [smtpConfigured, setSmtpConfigured] = useState<boolean | null>(null);
    const [showSmtpSettings, setShowSmtpSettings] = useState(false);
    const [isTestingSmtp, setIsTestingSmtp] = useState(false);
    const [smtpConfig, setSmtpConfig] = useState<SmtpConfig>({
        smtp_host: 'smtp.worksmobile.com',
        smtp_port: 587,
        smtp_username: '',
        smtp_password: '',
        from_email: '',
        from_name: '',
        use_tls: true,
    });
    const [sendError, setSendError] = useState<string | null>(null);

    // Compose form state
    const [composeData, setComposeData] = useState({
        to: '',
        cc: '',
        bcc: '',
        subject: '',
        body: '',
        attachments: [] as File[],
        scheduledTime: null as Date | null
    });

    // 이메일 로드 에러 상태
    const [emailLoadError, setEmailLoadError] = useState<string | null>(null);

    // API: 이메일 발송 내역 가져오기
    const fetchEmails = useCallback(async () => {
        setIsLoadingEmails(true);
        setEmailLoadError(null);
        try {
            const data = await fetchAPI<any>('/v1/email/history');
            // Backend returns list[EmailHistory] directly (array),
            // or possibly wrapped in {history: [...]} or {items: [...]}
            const history: Array<Record<string, unknown>> = Array.isArray(data)
                ? data
                : (data.history || data.items || []);
            const mapped: Email[] = history.map((item: Record<string, unknown>, idx: number) => {
                // Extract recipient emails
                let toEmails: string[] = [];
                if (Array.isArray(item.recipients)) {
                    toEmails = (item.recipients as Array<Record<string, string>>)
                        .filter(r => !r.type || r.type === 'to')
                        .map(r => r.email || (r as unknown as string));
                } else if (Array.isArray(item.to)) {
                    toEmails = item.to as string[];
                } else if (typeof item.to === 'string') {
                    toEmails = [item.to];
                }

                // Determine status label
                const status = (item.status as string) || 'sent';

                // Build labels from status
                const statusLabels: string[] = [];
                if (status === 'failed') statusLabels.push('발송실패');
                if (status === 'pending') statusLabels.push('발송중');
                if (status === 'scheduled') statusLabels.push('예약발송');
                if ((item.priority as string) === 'urgent' || (item.priority as string) === 'high') {
                    statusLabels.push('긴급');
                }

                return {
                    id: (item.id as string) || String(idx + 1),
                    from: (item.from_email as string) || (item.from as string) || '',
                    fromName: (item.from_name as string) || (item.fromName as string) || '나',
                    to: toEmails.length > 0 ? toEmails : [''],
                    cc: item.cc ? (Array.isArray(item.cc) ? item.cc as string[] : []) : undefined,
                    subject: (item.subject as string) || '(제목 없음)',
                    body: (item.body as string) || (item.body_preview as string) || '',
                    preview: ((item.body_preview as string) || (item.body as string) || '').slice(0, 80),
                    date: item.sent_at ? new Date(item.sent_at as string) : item.created_at ? new Date(item.created_at as string) : new Date(),
                    read: true,
                    starred: false,
                    important: status === 'failed',
                    labels: statusLabels,
                    folder: 'sent' as const,
                };
            });
            setEmails(mapped);
        } catch (e) {
            const errorMsg = e instanceof Error ? e.message : '네트워크 연결을 확인해주세요.';
            setEmailLoadError(`이메일을 불러올 수 없습니다: ${errorMsg}`);
            console.error("이메일 내역 불러오기 실패:", e);
        } finally {
            setIsLoadingEmails(false);
        }
    }, []);

    // API: 템플릿 가져오기
    const fetchTemplates = useCallback(async () => {
        setIsLoadingTemplates(true);
        try {
            const data = await fetchAPI<any>('/v1/email/templates');
            const items = data.templates || data.items || data;
            if (Array.isArray(items)) {
                setTemplates(items.map((t: Record<string, unknown>, idx: number) => ({
                    id: (t.id as string) || String(idx + 1),
                    name: (t.name as string) || '템플릿',
                    subject: (t.subject as string) || '',
                    body: (t.body as string) || '',
                    category: (t.category as string) || '일반',
                })));
            }
        } catch (e) {
            console.error("템플릿 불러오기 실패:", e);
        } finally {
            setIsLoadingTemplates(false);
        }
    }, []);

    // API: SMTP 설정 확인
    const checkSmtpConfig = useCallback(async () => {
        try {
            const data = await fetchAPI<any>('/v1/email/config');
            if (data.configured || data.smtp_host) {
                setSmtpConfigured(true);
                if (data.smtp_host) {
                    setSmtpConfig(prev => ({
                        ...prev,
                        smtp_host: data.smtp_host || prev.smtp_host,
                        smtp_port: data.smtp_port || prev.smtp_port,
                        smtp_username: data.smtp_username || prev.smtp_username,
                        from_email: data.from_email || prev.from_email,
                        from_name: data.from_name || prev.from_name,
                        use_tls: data.use_tls !== undefined ? data.use_tls : prev.use_tls,
                    }));
                }
            } else {
                setSmtpConfigured(false);
            }
        } catch {
            setSmtpConfigured(false);
        }
    }, []);

    // IMAP 폴더명 매핑
    const getImapFolderName = (folder: string): string => {
        const folderMap: Record<string, string> = {
            inbox: 'INBOX',
            sent: 'Sent',
            drafts: 'Drafts',
            trash: 'Trash',
            archive: 'Archive',
        };
        return folderMap[folder] || 'INBOX';
    };

    // API: IMAP 메일함 가져오기
    const fetchInboxEmails = useCallback(async (folder: string = 'INBOX') => {
        setIsLoadingInbox(true);
        try {
            const res = await fetch(`${API_BASE_URL}/v1/email/imap/emails?folder=${encodeURIComponent(folder)}&limit=20`);
            if (!res.ok) {
                const errBody = await res.text();
                throw new Error(errBody || `IMAP 요청 실패 (${res.status})`);
            }
            const data = await res.json();
            const items: Array<Record<string, unknown>> = Array.isArray(data)
                ? data
                : (data.emails || data.items || []);

            const mapped: Email[] = items.map((item: Record<string, unknown>, idx: number) => {
                // from이 {name, email} 객체 또는 문자열일 수 있음
                let fromName = '(알 수 없음)';
                let fromEmail = '';
                const fromField = item.from;
                if (fromField && typeof fromField === 'object' && 'email' in (fromField as Record<string, unknown>)) {
                    const fromObj = fromField as Record<string, string>;
                    fromEmail = fromObj.email || '';
                    fromName = fromObj.name || fromEmail.split('@')[0] || '(알 수 없음)';
                } else {
                    const fromRaw = (fromField as string) || (item.from_email as string) || '';
                    const nameMatch = fromRaw.match(/^(.+?)\s*<(.+?)>$/);
                    fromName = nameMatch ? nameMatch[1].trim() : (item.from_name as string) || fromRaw.split('@')[0] || '(알 수 없음)';
                    fromEmail = nameMatch ? nameMatch[2].trim() : fromRaw;
                }

                let toEmails: string[] = [];
                if (Array.isArray(item.to)) {
                    toEmails = (item.to as Array<unknown>).map((t: unknown) => {
                        if (typeof t === 'string') return t;
                        if (t && typeof t === 'object' && 'email' in (t as Record<string, unknown>)) return (t as Record<string, string>).email;
                        return String(t);
                    });
                } else if (typeof item.to === 'string') {
                    toEmails = [item.to];
                }

                const bodyText = (item.body_text as string) || (item.body as string) || (item.text as string) || (item.body_preview as string) || (item.snippet as string) || '';
                const flags = Array.isArray(item.flags) ? item.flags as string[] : [];
                const isRead = item.is_read !== undefined ? Boolean(item.is_read) : (item.read !== undefined ? Boolean(item.read) : !!(item.seen || flags.includes('\\Seen')));

                return {
                    id: String(item.id ?? item.uid ?? item.message_id ?? idx),
                    from: fromEmail,
                    fromName,
                    to: toEmails.length > 0 ? toEmails : [''],
                    cc: item.cc ? (Array.isArray(item.cc) ? item.cc as string[] : []) : undefined,
                    subject: (item.subject as string) || '(제목 없음)',
                    body: bodyText,
                    preview: ((item.snippet as string) || (item.preview as string) || bodyText).slice(0, 80),
                    date: item.date ? new Date(item.date as string) : new Date(),
                    read: isRead,
                    starred: false,
                    important: false,
                    labels: [],
                    attachments: Array.isArray(item.attachments) ? (item.attachments as Array<Record<string, string>>).map(a => ({
                        name: a.filename || a.name || 'file',
                        size: a.size || '',
                        type: (a.content_type || a.type || '').split('/').pop() || 'file',
                    })) : undefined,
                    folder: 'inbox' as const,
                };
            });

            setInboxEmails(mapped);
            setUnreadCount(mapped.filter(e => !e.read).length);
        } catch (e) {
            console.error('IMAP 받은편지함 로드 실패:', e);
            showToast(`받은편지함 로드 실패: ${e instanceof Error ? e.message : '네트워크 오류'}`, 'error');
        } finally {
            setIsLoadingInbox(false);
        }
    }, [showToast]);

    // 초기 데이터 로드
    useEffect(() => {
        fetchEmails();
        fetchTemplates();
        checkSmtpConfig();
    }, [fetchEmails, fetchTemplates, checkSmtpConfig]);

    // 폴더 전환 시 IMAP 데이터 로드
    useEffect(() => {
        const imapFolders = ['inbox', 'drafts', 'trash', 'archive'];
        if (imapFolders.includes(activeFolder)) {
            fetchInboxEmails(getImapFolderName(activeFolder));
        }
    }, [activeFolder, fetchInboxEmails]);

    // 이메일 설정 변경 이벤트 리스너
    useEffect(() => {
        const handleEmailSettingsChanged = () => {
            checkSmtpConfig();
        };
        window.addEventListener('kis-email-settings-changed', handleEmailSettingsChanged);
        return () => {
            window.removeEventListener('kis-email-settings-changed', handleEmailSettingsChanged);
        };
    }, [checkSmtpConfig]);

    // 폴더별 이메일 카운트
    const folderCounts = useMemo(() => ({
        inbox: emails.filter(e => e.folder === 'inbox' && !e.read).length,
        sent: emails.filter(e => e.folder === 'sent').length,
        drafts: emails.filter(e => e.folder === 'drafts').length,
        starred: emails.filter(e => e.starred).length,
        trash: emails.filter(e => e.folder === 'trash').length,
        archive: emails.filter(e => e.folder === 'archive').length,
    }), [emails]);

    // 필터링된 이메일 목록 (고정된 메일 상단 표시)
    const filteredEmails = useMemo(() => {
        // IMAP 폴더(inbox, drafts, trash, archive)는 inboxEmails에서, sent는 emails(sent history)에서
        const imapFolders = ['inbox', 'drafts', 'trash', 'archive'];
        let result = imapFolders.includes(activeFolder) ? inboxEmails : emails;

        // 폴더 필터
        if (activeFolder === 'starred') {
            result = result.filter(e => e.starred);
        } else if (activeFolder === 'important') {
            result = result.filter(e => e.important);
        } else if (activeFolder === 'all') {
            result = result.filter(e => e.folder === 'sent');
        } else {
            result = result.filter(e => e.folder === activeFolder);
        }

        // 검색 필터
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            result = result.filter(e =>
                e.subject.toLowerCase().includes(query) ||
                e.fromName.toLowerCase().includes(query) ||
                e.from.toLowerCase().includes(query) ||
                e.body.toLowerCase().includes(query)
            );
        }

        // 라벨 필터
        if (filterLabel) {
            result = result.filter(e => e.labels.includes(filterLabel));
        }

        // 정렬: 고정 메일 먼저, 그 다음 날짜순
        return result.sort((a, b) => {
            if (a.pinned && !b.pinned) return -1;
            if (!a.pinned && b.pinned) return 1;
            return b.date.getTime() - a.date.getTime();
        });
    }, [emails, inboxEmails, activeFolder, searchQuery, filterLabel]);

    // 이메일 액션
    const markAsRead = (id: string) => {
        setEmails(prev => prev.map(e => e.id === id ? { ...e, read: true } : e));
    };

    const toggleStar = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        // Update local state for both sent and inbox emails
        setEmails(prev => prev.map(email => email.id === id ? { ...email, starred: !email.starred } : email));
        setInboxEmails(prev => prev.map(email => email.id === id ? { ...email, starred: !email.starred } : email));
        // Persist star flag via IMAP API
        fetch(`${API_BASE_URL}/v1/email/imap/emails/${id}/mark?action=star&folder=INBOX`, { method: 'PATCH' })
            .catch(err => console.error('별표 처리 실패:', err));
    };

    const togglePin = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setEmails(prev => prev.map(email => email.id === id ? { ...email, pinned: !email.pinned } : email));
    };

    const toggleImportant = (id: string) => {
        setEmails(prev => prev.map(e => e.id === id ? { ...e, important: !e.important } : e));
    };

    const moveToTrash = (ids: string[]) => {
        setEmails(prev => prev.map(e => ids.includes(e.id) ? { ...e, folder: 'trash' } : e));
        setSelectedEmails([]);
        setSelectedEmail(null);
    };

    const archiveEmails = (ids: string[]) => {
        setEmails(prev => prev.map(e => ids.includes(e.id) ? { ...e, folder: 'archive' } : e));
        setSelectedEmails([]);
    };

    const markAsUnread = (ids: string[]) => {
        setEmails(prev => prev.map(e => ids.includes(e.id) ? { ...e, read: false } : e));
        setSelectedEmails([]);
    };

    const handleSelectAll = () => {
        if (selectedEmails.length === filteredEmails.length) {
            setSelectedEmails([]);
        } else {
            setSelectedEmails(filteredEmails.map(e => e.id));
        }
    };

    const handleSelectEmail = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setSelectedEmails(prev =>
            prev.includes(id) ? prev.filter(eid => eid !== id) : [...prev, id]
        );
    };

    const openEmail = async (email: Email) => {
        setSelectedEmail(email);

        if (email.folder === 'inbox') {
            // Fetch full email detail from IMAP
            try {
                const detailRes = await fetch(`${API_BASE_URL}/v1/email/imap/emails/${email.id}?folder=INBOX`);
                if (detailRes.ok) {
                    const detail = await detailRes.json();
                    const fullBody = (detail.body_html as string) || (detail.body_text as string) || (detail.body as string) || (detail.html as string) || (detail.text as string) || email.body;
                    setSelectedEmail(prev => prev && prev.id === email.id ? { ...prev, body: fullBody } : prev);
                }
            } catch (e) {
                console.error('이메일 상세 로드 실패:', e);
            }

            // Mark as read via IMAP
            if (!email.read) {
                try {
                    await fetch(`${API_BASE_URL}/v1/email/imap/emails/${email.id}/mark?action=read&folder=INBOX`, { method: 'PATCH' });
                    setInboxEmails(prev => prev.map(e => e.id === email.id ? { ...e, read: true } : e));
                    setUnreadCount(prev => Math.max(0, prev - 1));
                } catch (e) {
                    console.error('읽음 처리 실패:', e);
                }
            }
        } else {
            markAsRead(email.id);
        }
    };

    const applyTemplate = (template: EmailTemplate) => {
        setComposeData(prev => ({
            ...prev,
            subject: template.subject,
            body: template.body
        }));
        setShowTemplates(false);
    };

    const selectContact = (contact: Contact) => {
        setComposeData(prev => ({
            ...prev,
            to: prev.to ? `${prev.to}, ${contact.email}` : contact.email
        }));
        setShowContacts(false);
    };

    const handleSend = async () => {
        if (!composeData.to.trim()) {
            setSendError('받는 사람을 입력해주세요.');
            return;
        }
        if (!composeData.subject.trim()) {
            setSendError('제목을 입력해주세요.');
            return;
        }

        setIsSending(true);
        setSendError(null);

        try {
            const recipients = composeData.to.split(',').map(e => e.trim()).filter(Boolean).map(email => ({
                email: email,
                name: email.split('@')[0],
            }));

            const payload: Record<string, unknown> = {
                recipients,
                subject: composeData.subject,
                body: composeData.body,
            };

            if (composeData.cc.trim()) {
                payload.cc = composeData.cc.split(',').map(e => e.trim()).filter(Boolean);
            }
            if (composeData.bcc.trim()) {
                payload.bcc = composeData.bcc.split(',').map(e => e.trim()).filter(Boolean);
            }

            await fetchAPI<any>('/v1/email/send', {
                method: 'POST',
                body: JSON.stringify(payload),
            });

            setShowCompose(false);
            setComposeData({ to: '', cc: '', bcc: '', subject: '', body: '', attachments: [], scheduledTime: null });
            setSendError(null);
            // 전송 후 내역 새로고침
            fetchEmails();
            showToast('메일이 전송되었습니다.', 'success');
        } catch (err) {
            console.error('Email send error:', err);
            setSendError(err instanceof Error ? err.message : '메일 전송 중 오류가 발생했습니다.');
        } finally {
            setIsSending(false);
        }
    };

    // 빠른 답장 전송
    const handleQuickReply = async (replyText: string) => {
        if (!selectedEmail || !replyText.trim()) return;
        setIsSending(true);
        try {
            const replySubject = selectedEmail.subject.startsWith('Re: ') ? selectedEmail.subject : `Re: ${selectedEmail.subject}`;
            const payload = {
                recipients: [{ email: selectedEmail.from, name: selectedEmail.fromName }],
                subject: replySubject,
                body: replyText,
            };
            await fetchAPI<any>('/v1/email/send', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            showToast('답장이 전송되었습니다.', 'success');
            fetchEmails();
        } catch (err) {
            console.error('Quick reply error:', err);
            showToast(err instanceof Error ? err.message : '답장 전송 중 오류가 발생했습니다.', 'error');
        } finally {
            setIsSending(false);
        }
    };

    // SMTP 설정 저장
    const handleSaveSmtpConfig = async () => {
        try {
            await fetchAPI<any>('/v1/email/config', {
                method: 'POST',
                body: JSON.stringify(smtpConfig),
            });

            setSmtpConfigured(true);
            setShowSmtpSettings(false);
            showToast('SMTP 설정이 저장되었습니다.', 'success');
        } catch (err) {
            console.error('SMTP config save error:', err);
            showToast('SMTP 설정 저장 중 오류가 발생했습니다.', 'error');
        }
    };

    // SMTP 연결 테스트
    const handleTestSmtp = async () => {
        setIsTestingSmtp(true);
        try {
            await fetchAPI<any>('/v1/email/config/test', {
                method: 'POST',
                body: JSON.stringify(smtpConfig),
            });

            showToast('SMTP 연결 테스트 성공!', 'success');
        } catch (err) {
            console.error('SMTP test error:', err);
            showToast('SMTP 연결 테스트 중 오류가 발생했습니다.', 'error');
        } finally {
            setIsTestingSmtp(false);
        }
    };

    const formatDate = (date: Date) => {
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) {
            return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
        } else if (days === 1) {
            return '어제';
        } else if (days < 7) {
            return `${days}일 전`;
        } else {
            return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
        }
    };

    const categoryLabels = {
        customer: '고객사',
        vendor: '공급사',
        partner: '협력사',
        internal: '내부',
    };

    return (
        <div className="h-screen flex flex-col bg-bg overflow-hidden">
            {/* Top Header - 입체감 */}
            <div className="flex-shrink-0 h-14 bg-surface border-b border-border/50 flex items-center justify-between px-4" style={{boxShadow: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)'}}>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Mail className="w-5 h-5 text-brand" />
                        <h1 className="text-lg font-semibold text-text-strong">이메일</h1>
                    </div>
                    <span className="text-xs text-text-subtle px-2 py-0.5 bg-surface-secondary/50 rounded">NAVER WORKS</span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowCompose(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition font-medium text-sm"
                        style={{boxShadow: '0 2px 6px rgba(16,163,127,0.3), 0 1px 2px rgba(16,163,127,0.2)'}}
                    >
                        <Edit3 className="w-4 h-4" />
                        새 메일
                    </button>
                    <button
                        onClick={() => { if (activeFolder === 'inbox') fetchInboxEmails(); else fetchEmails(); }}
                        className="p-2 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                        title="새로고침"
                    >
                        <RefreshCw className={cn("w-5 h-5", (isLoadingEmails || isLoadingInbox) && "animate-spin")} />
                    </button>
                    <button
                        onClick={() => setShowSmtpSettings(true)}
                        className="p-2 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                        title="SMTP 설정"
                    >
                        <Settings className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* SMTP 미설정 배너 */}
            {smtpConfigured === false && (
                <div className="flex-shrink-0 flex items-center gap-3 px-4 py-2.5 bg-amber-50 border-b border-amber-200 dark:bg-amber-950/30 dark:border-amber-800">
                    <WifiOff className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                    <span className="text-sm text-amber-800 dark:text-amber-300">
                        네이버웍스 메일을 사용하려면 SMTP 설정이 필요합니다.
                    </span>
                    <button
                        onClick={() => setShowSmtpSettings(true)}
                        className="ml-auto text-sm font-medium text-amber-700 dark:text-amber-300 hover:underline"
                    >
                        설정하기
                    </button>
                </div>
            )}

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar - 입체감 */}
                <div className="w-56 flex-shrink-0 bg-surface border-r border-border/40 flex flex-col" style={{boxShadow: '2px 0 8px rgba(0,0,0,0.04)'}}>
                    {/* Search */}
                    <div className="p-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
                            <input
                                type="text"
                                placeholder="메일 검색..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 bg-surface border border-border rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
                            />
                        </div>
                    </div>

                    {/* Folders */}
                    <nav className="flex-1 overflow-y-auto px-2">
                        <div className="space-y-0.5">
                            {[
                                { id: 'inbox', icon: Inbox, label: '받은편지함', count: unreadCount },
                                { id: 'starred', icon: Star, label: '중요편지함', count: folderCounts.starred },
                                { id: 'sent', icon: Send, label: '보낸편지함', count: 0 },
                                { id: 'drafts', icon: FileText, label: '임시보관함', count: folderCounts.drafts },
                                { id: 'archive', icon: Archive, label: '보관함', count: 0 },
                                { id: 'trash', icon: Trash2, label: '휴지통', count: 0 },
                            ].map((folder) => (
                                <button
                                    key={folder.id}
                                    disabled={'disabled' in folder && !!folder.disabled}
                                    onClick={() => { if ('disabled' in folder && folder.disabled) return; setActiveFolder(folder.id); setSelectedEmail(null); }}
                                    className={cn(
                                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150",
                                        'disabled' in folder && folder.disabled
                                            ? 'opacity-50 cursor-not-allowed'
                                            : activeFolder === folder.id
                                            ? 'bg-brand/10 text-brand font-semibold shadow-sm'
                                            : 'text-text hover:bg-surface-secondary/80'
                                    )}
                                >
                                    <folder.icon className={cn(
                                        "w-4 h-4",
                                        activeFolder === folder.id ? 'text-brand' : 'text-text-subtle'
                                    )} />
                                    <span className="flex-1 text-left">{folder.label}</span>
                                    {folder.count > 0 && (
                                        <span className={cn(
                                            "text-xs px-1.5 py-0.5 rounded-full",
                                            activeFolder === folder.id
                                                ? 'bg-brand text-white'
                                                : 'bg-brand/10 text-brand'
                                        )}>
                                            {folder.count}
                                        </span>
                                    )}
                                </button>
                            ))}
                        </div>

                        {/* Labels - 통일된 스타일 */}
                        <div className="mt-4 pt-4 border-t border-border/50">
                            <div className="flex items-center justify-between px-3 mb-2">
                                <span className="text-xs font-medium text-text-subtle uppercase tracking-wide">라벨</span>
                                <button className="p-1 text-text-subtle hover:text-text rounded">
                                    <Plus className="w-3 h-3" />
                                </button>
                            </div>
                            <div className="space-y-0.5">
                                {labels.map((label) => (
                                    <button
                                        key={label.id}
                                        onClick={() => setFilterLabel(filterLabel === label.name ? null : label.name)}
                                        className={cn(
                                            "w-full flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm transition",
                                            filterLabel === label.name
                                                ? 'bg-brand/10 text-brand font-medium'
                                                : 'text-text-subtle hover:bg-surface-secondary hover:text-text'
                                        )}
                                    >
                                        <Tag className="w-3.5 h-3.5" />
                                        <span>{label.name}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Quick Links */}
                        <div className="mt-4 pt-4 border-t border-border/50">
                            <button
                                onClick={() => setShowContacts(true)}
                                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text-subtle hover:bg-surface-secondary hover:text-text transition"
                            >
                                <Users className="w-4 h-4" />
                                <span>주소록</span>
                            </button>
                            <button
                                onClick={() => setShowTemplates(true)}
                                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text-subtle hover:bg-surface-secondary hover:text-text transition"
                            >
                                <FileText className="w-4 h-4" />
                                <span>템플릿</span>
                            </button>
                        </div>
                    </nav>

                    {/* Storage Info */}
                    <div className="p-3 border-t border-border/50">
                        <div className="text-xs text-text-subtle mb-1">저장공간</div>
                        <div className="w-full h-1 bg-surface-secondary rounded-full overflow-hidden">
                            <div className="h-full w-1/4 bg-brand rounded-full" />
                        </div>
                        <div className="text-xs text-text-subtle mt-1">2.5GB / 10GB</div>
                    </div>
                </div>

                {/* Email List */}
                <div className={cn(
                    "flex-1 flex flex-col border-r border-border/30 bg-surface",
                    selectedEmail ? 'hidden lg:flex' : 'flex'
                )} style={{boxShadow: '2px 0 12px rgba(0,0,0,0.03)'}}>
                    {/* List Header */}
                    <div className="flex-shrink-0 h-12 border-b border-border/40 flex items-center justify-between px-3 bg-surface-tertiary/50">
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleSelectAll}
                                className={cn(
                                    "w-5 h-5 rounded border-2 flex items-center justify-center transition",
                                    selectedEmails.length === filteredEmails.length && filteredEmails.length > 0
                                        ? 'bg-brand border-brand text-white'
                                        : 'border-border/50 hover:border-brand/50'
                                )}
                            >
                                {selectedEmails.length === filteredEmails.length && filteredEmails.length > 0 && (
                                    <Check className="w-3 h-3" />
                                )}
                            </button>
                            <button className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition">
                                <RefreshCw className="w-4 h-4" />
                            </button>
                            {selectedEmails.length > 0 && (
                                <>
                                    <div className="w-px h-5 bg-border/30 mx-1" />
                                    <button
                                        onClick={() => markAsUnread(selectedEmails)}
                                        className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition"
                                        title="읽지 않음 표시"
                                    >
                                        <Mail className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => archiveEmails(selectedEmails)}
                                        className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded transition"
                                        title="보관"
                                    >
                                        <Archive className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => moveToTrash(selectedEmails)}
                                        className="p-1.5 text-text-subtle hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition"
                                        title="삭제"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </>
                            )}
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-text-subtle">
                                {filteredEmails.length}개
                            </span>
                            <button
                                onClick={() => setShowFilters(!showFilters)}
                                className={cn(
                                    "p-1.5 rounded transition",
                                    showFilters
                                        ? 'bg-brand/10 text-brand'
                                        : 'text-text-subtle hover:text-text hover:bg-surface-secondary'
                                )}
                            >
                                <SlidersHorizontal className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* Filter Bar */}
                    {showFilters && (
                        <div className="flex-shrink-0 h-10 border-b border-border/50 flex items-center gap-2 px-3 bg-surface-secondary/30">
                            <span className="text-xs text-text-subtle">필터:</span>
                            <button
                                onClick={() => setFilterLabel(null)}
                                className={cn(
                                    "px-2 py-1 text-xs rounded transition",
                                    !filterLabel
                                        ? 'bg-brand/10 text-brand font-medium'
                                        : 'text-text-subtle hover:bg-surface-secondary'
                                )}
                            >
                                전체
                            </button>
                            {labels.map((label) => (
                                <button
                                    key={label.id}
                                    onClick={() => setFilterLabel(label.name)}
                                    className={cn(
                                        "px-2 py-1 text-xs rounded transition",
                                        filterLabel === label.name
                                            ? 'bg-brand/10 text-brand font-medium'
                                            : 'text-text-subtle hover:bg-surface-secondary'
                                    )}
                                >
                                    {label.name}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Email List */}
                    <div className="flex-1 overflow-y-auto">
                        {(isLoadingEmails || (activeFolder === 'inbox' && isLoadingInbox)) ? (
                            <div className="flex flex-col items-center justify-center h-full text-text-subtle">
                                <Loader2 className="w-8 h-8 mb-3 animate-spin text-brand" />
                                <p className="text-sm">메일을 불러오는 중...</p>
                            </div>
                        ) : filteredEmails.length > 0 ? (
                            filteredEmails.map((email) => (
                                <div
                                    key={email.id}
                                    onClick={() => openEmail(email)}
                                    className={cn(
                                        "group flex items-start gap-3 pl-4 pr-3 py-3 cursor-pointer transition-all duration-150 relative",
                                        "border-l-[3px]",
                                        selectedEmail?.id === email.id
                                            ? 'bg-brand/8 border-l-brand'
                                            : email.read
                                                ? 'border-l-transparent hover:bg-surface-secondary/40 border-b border-b-border/5'
                                                : 'border-l-brand bg-gradient-to-r from-brand/[0.06] to-transparent hover:from-brand/[0.10] border-b border-b-brand/10'
                                    )}
                                >
                                    {/* Unread dot indicator */}
                                    {!email.read && (
                                        <div className="absolute left-[5px] top-1/2 -translate-y-1/2 w-[5px] h-[5px] rounded-full bg-brand" style={{boxShadow: '0 0 4px rgba(16,163,127,0.6)'}} />
                                    )}

                                    {/* Checkbox & Star & Pin */}
                                    <div className="flex items-center gap-1 pt-0.5">
                                        <button
                                            onClick={(e) => handleSelectEmail(email.id, e)}
                                            className={cn(
                                                "w-4 h-4 rounded border flex items-center justify-center transition",
                                                selectedEmails.includes(email.id)
                                                    ? 'bg-brand border-brand text-white'
                                                    : 'border-border/50 group-hover:border-brand/50'
                                            )}
                                        >
                                            {selectedEmails.includes(email.id) && <Check className="w-2.5 h-2.5" />}
                                        </button>
                                        <button
                                            onClick={(e) => toggleStar(email.id, e)}
                                            className={cn(
                                                "p-0.5 transition",
                                                email.starred ? 'text-amber-500' : 'text-text-subtle/30 hover:text-amber-400'
                                            )}
                                        >
                                            <Star className={cn("w-4 h-4", email.starred && 'fill-current')} />
                                        </button>
                                        <button
                                            onClick={(e) => togglePin(email.id, e)}
                                            className={cn(
                                                "p-0.5 transition",
                                                email.pinned ? 'text-brand' : 'text-text-subtle/30 hover:text-brand/50'
                                            )}
                                        >
                                            <Pin className={cn("w-3.5 h-3.5", email.pinned && 'fill-current')} />
                                        </button>
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <span className={cn(
                                                "text-sm truncate",
                                                email.read ? 'text-text-subtle' : 'text-text-strong font-bold'
                                            )}>
                                                {email.fromName}
                                            </span>
                                            {!email.read && (
                                                <span className="flex-shrink-0 px-1.5 py-px text-[9px] font-bold rounded-sm bg-brand/15 text-brand tracking-wide leading-tight">NEW</span>
                                            )}
                                            {email.important && (
                                                <AlertCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                                            )}
                                            {email.attachments && email.attachments.length > 0 && (
                                                <Paperclip className="w-3.5 h-3.5 text-text-subtle flex-shrink-0" />
                                            )}
                                        </div>
                                        <div className={cn(
                                            "text-sm truncate",
                                            email.read ? 'text-text-subtle/70' : 'text-text font-medium'
                                        )}>
                                            {email.subject}
                                        </div>
                                        <div className={cn(
                                            "text-xs truncate mt-0.5",
                                            email.read ? 'text-text-subtle/50' : 'text-text-subtle/80'
                                        )}>
                                            {email.preview}
                                        </div>
                                        {email.labels.length > 0 && (
                                            <div className="flex items-center gap-1 mt-1.5">
                                                {email.labels.map((label) => (
                                                    <span
                                                        key={label}
                                                        className={cn(
                                                            "px-1.5 py-0.5 text-[10px] rounded font-medium",
                                                            label === '긴급'
                                                                ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                                                                : 'bg-surface-secondary text-text-subtle'
                                                        )}
                                                    >
                                                        {label}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Date */}
                                    <div className={cn(
                                        "flex-shrink-0 text-xs",
                                        email.read ? 'text-text-subtle/50' : 'text-text-subtle font-medium'
                                    )}>
                                        {formatDate(email.date)}
                                    </div>
                                </div>
                            ))
                        ) : emailLoadError ? (
                            <div className="flex flex-col items-center justify-center h-full text-text-subtle px-4">
                                <AlertCircle className="w-10 h-10 mb-3 text-red-400 opacity-60" />
                                <p className="text-sm text-red-500 text-center mb-3">{emailLoadError}</p>
                                <button
                                    onClick={fetchEmails}
                                    className="flex items-center gap-2 px-4 py-2 text-sm text-brand hover:bg-brand/10 rounded-lg transition"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    다시 시도
                                </button>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-text-subtle px-4">
                                <Mail className="w-12 h-12 mb-3 opacity-20" />
                                <p className="text-sm font-medium text-text mb-1">
                                    {activeFolder === 'sent' ? '발송된 이메일이 없습니다' :
                                     activeFolder === 'inbox' ? '받은 메일이 없습니다' :
                                     activeFolder === 'drafts' ? '임시 저장된 메일이 없습니다' :
                                     activeFolder === 'starred' ? '중요 표시된 메일이 없습니다' :
                                     activeFolder === 'trash' ? '휴지통이 비어있습니다' :
                                     activeFolder === 'archive' ? '보관된 메일이 없습니다' :
                                     '메일이 없습니다'}
                                </p>
                                <p className="text-xs text-center">
                                    {activeFolder === 'sent'
                                        ? '이메일 작성 버튼을 클릭하여 시작하세요.'
                                        : activeFolder === 'inbox'
                                        ? '새로고침 버튼을 눌러 메일을 확인하세요.'
                                        : ''}
                                </p>
                                {activeFolder === 'sent' && (
                                    <button
                                        onClick={() => setShowCompose(true)}
                                        className="mt-3 flex items-center gap-2 px-4 py-2 text-sm bg-brand text-white rounded-lg hover:bg-brand-dark transition"
                                    >
                                        <Edit3 className="w-4 h-4" />
                                        새 메일 작성
                                    </button>
                                )}
                                {activeFolder === 'inbox' && (
                                    <button
                                        onClick={() => fetchInboxEmails(getImapFolderName(activeFolder))}
                                        className="mt-3 flex items-center gap-2 px-4 py-2 text-sm text-brand hover:bg-brand/10 rounded-lg transition"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        새로고침
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Email Detail / Welcome Screen */}
                <div className={cn("flex-1 flex flex-col bg-bg/80", selectedEmail ? 'flex' : 'hidden lg:flex')}>
                    {selectedEmail ? (
                        <>
                            {/* Detail Header */}
                            <div className="flex-shrink-0 h-14 bg-surface border-b border-border/40 flex items-center justify-between px-4" style={{boxShadow: '0 1px 3px rgba(0,0,0,0.04)'}}>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => setSelectedEmail(null)}
                                        className="lg:hidden p-2 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                    >
                                        <ArrowLeft className="w-5 h-5" />
                                    </button>
                                    <button className="p-2 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition" title="보관">
                                        <Archive className="w-5 h-5" />
                                    </button>
                                    <button
                                        onClick={() => moveToTrash([selectedEmail.id])}
                                        className="p-2 text-text-subtle hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                                        title="삭제"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                    <button
                                        onClick={() => toggleImportant(selectedEmail.id)}
                                        className={cn(
                                            "p-2 rounded-lg transition",
                                            selectedEmail.important
                                                ? 'text-red-500 bg-red-50 dark:bg-red-900/20'
                                                : 'text-text-subtle hover:text-text hover:bg-surface-secondary'
                                        )}
                                        title="중요"
                                    >
                                        <AlertCircle className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => {
                                            const quotedBody = `\n\n--- 원본 메시지 ---\n보낸사람: ${selectedEmail.fromName} <${selectedEmail.from}>\n날짜: ${selectedEmail.date.toLocaleString('ko-KR')}\n\n${selectedEmail.body.replace(/<[^>]*>/g, '')}`;
                                            setComposeData({
                                                to: selectedEmail.from,
                                                cc: '',
                                                bcc: '',
                                                subject: selectedEmail.subject.startsWith('Re: ') ? selectedEmail.subject : `Re: ${selectedEmail.subject}`,
                                                body: quotedBody,
                                                attachments: [],
                                                scheduledTime: null,
                                            });
                                            setShowCompose(true);
                                        }}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                    >
                                        <Reply className="w-4 h-4" />
                                        답장
                                    </button>
                                    <button
                                        onClick={() => {
                                            const quotedBody = `\n\n--- 원본 메시지 ---\n보낸사람: ${selectedEmail.fromName} <${selectedEmail.from}>\n날짜: ${selectedEmail.date.toLocaleString('ko-KR')}\n\n${selectedEmail.body.replace(/<[^>]*>/g, '')}`;
                                            const ccRecipients = [
                                                ...(selectedEmail.to || []),
                                                ...(selectedEmail.cc || []),
                                            ].filter(addr => addr && addr !== selectedEmail.from);
                                            setComposeData({
                                                to: selectedEmail.from,
                                                cc: ccRecipients.join(', '),
                                                bcc: '',
                                                subject: selectedEmail.subject.startsWith('Re: ') ? selectedEmail.subject : `Re: ${selectedEmail.subject}`,
                                                body: quotedBody,
                                                attachments: [],
                                                scheduledTime: null,
                                            });
                                            setShowCompose(true);
                                        }}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                    >
                                        <ReplyAll className="w-4 h-4" />
                                        전체
                                    </button>
                                    <button
                                        onClick={() => {
                                            const forwardBody = `\n\n--- 전달된 메시지 ---\n보낸사람: ${selectedEmail.fromName} <${selectedEmail.from}>\n받는사람: ${selectedEmail.to.join(', ')}\n날짜: ${selectedEmail.date.toLocaleString('ko-KR')}\n제목: ${selectedEmail.subject}\n\n${selectedEmail.body.replace(/<[^>]*>/g, '')}`;
                                            setComposeData({
                                                to: '',
                                                cc: '',
                                                bcc: '',
                                                subject: selectedEmail.subject.startsWith('Fwd: ') ? selectedEmail.subject : `Fwd: ${selectedEmail.subject}`,
                                                body: forwardBody,
                                                attachments: [],
                                                scheduledTime: null,
                                            });
                                            setShowCompose(true);
                                        }}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                    >
                                        <Forward className="w-4 h-4" />
                                        전달
                                    </button>
                                </div>
                            </div>

                            {/* Email Content */}
                            <div className="flex-1 overflow-y-auto p-6">
                                <div className="max-w-3xl mx-auto">
                                    {/* Subject */}
                                    <h2 className="text-xl font-semibold text-text-strong mb-4">
                                        {selectedEmail.subject}
                                    </h2>

                                    {/* Sender Info */}
                                    <div className="flex items-start justify-between mb-6">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-brand/10 flex items-center justify-center text-brand font-semibold">
                                                {selectedEmail.fromName.charAt(0)}
                                            </div>
                                            <div>
                                                <div className="font-medium text-text-strong">{selectedEmail.fromName}</div>
                                                <div className="text-sm text-text-subtle">{selectedEmail.from}</div>
                                            </div>
                                        </div>
                                        <div className="text-sm text-text-subtle">
                                            {selectedEmail.date.toLocaleString('ko-KR', {
                                                year: 'numeric',
                                                month: 'long',
                                                day: 'numeric',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </div>
                                    </div>

                                    {/* To/CC */}
                                    <div className="text-sm text-text-subtle mb-6 pb-4 border-b border-border/20">
                                        <div>받는사람: {selectedEmail.to.join(', ')}</div>
                                        {selectedEmail.cc && selectedEmail.cc.length > 0 && (
                                            <div>참조: {selectedEmail.cc.join(', ')}</div>
                                        )}
                                    </div>

                                    {/* Labels */}
                                    {selectedEmail.labels.length > 0 && (
                                        <div className="flex items-center gap-2 mb-6">
                                            {selectedEmail.labels.map((label) => (
                                                <span
                                                    key={label}
                                                    className={cn(
                                                        "px-2 py-1 text-xs rounded-md font-medium",
                                                        label === '긴급'
                                                            ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                                                            : 'bg-surface-secondary text-text-subtle'
                                                    )}
                                                >
                                                    {label}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {/* Body */}
                                    <div className="bg-surface rounded-xl p-6 border border-border/20" style={{boxShadow: '0 2px 8px rgba(0,0,0,0.04), 0 0 1px rgba(0,0,0,0.06)'}}>
                                        {selectedEmail.body && selectedEmail.body.includes('<') ? (
                                            <div
                                                className="text-text email-html-content"
                                                dangerouslySetInnerHTML={{
                                                    __html: DOMPurify.sanitize(selectedEmail.body, {
                                                        ALLOWED_TAGS: ['p', 'br', 'div', 'span', 'a', 'b', 'strong', 'i', 'em', 'u',
                                                            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'thead',
                                                            'tbody', 'tr', 'td', 'th', 'img', 'hr', 'blockquote', 'pre', 'code', 'header', 'footer'],
                                                        ALLOWED_ATTR: ['href', 'src', 'alt', 'style', 'class', 'width', 'height',
                                                            'border', 'cellspacing', 'cellpadding', 'align', 'valign', 'colspan', 'rowspan', 'target'],
                                                    }),
                                                }}
                                            />
                                        ) : (
                                            <div className="whitespace-pre-wrap text-text">
                                                {selectedEmail.body || '(본문 없음)'}
                                            </div>
                                        )}
                                    </div>

                                    {/* Attachments */}
                                    {selectedEmail.attachments && selectedEmail.attachments.length > 0 && (
                                        <div className="mt-6">
                                            <div className="text-sm font-medium text-text-strong mb-3">
                                                첨부파일 ({selectedEmail.attachments.length})
                                            </div>
                                            <div className="grid grid-cols-2 gap-3">
                                                {selectedEmail.attachments.map((att, idx) => (
                                                    <div
                                                        key={idx}
                                                        className="flex items-center gap-3 p-3 bg-surface border border-border/20 rounded-lg hover:bg-surface-secondary transition cursor-pointer group"
                                                        style={{boxShadow: '0 1px 3px rgba(0,0,0,0.04)'}}
                                                    >
                                                        <div className="w-10 h-10 rounded-lg bg-surface-secondary flex items-center justify-center text-xs font-bold text-text-subtle">
                                                            {att.type.toUpperCase()}
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <div className="text-sm font-medium text-text truncate">{att.name}</div>
                                                            <div className="text-xs text-text-subtle">{att.size}</div>
                                                        </div>
                                                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    window.open(
                                                                        `${API_BASE_URL}/v1/email/imap/emails/${selectedEmail.id}/attachments/${encodeURIComponent(att.name)}?folder=INBOX`,
                                                                        '_blank'
                                                                    );
                                                                }}
                                                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-tertiary rounded"
                                                                title="미리보기"
                                                            >
                                                                <Eye className="w-4 h-4" />
                                                            </button>
                                                            <a
                                                                href={`${API_BASE_URL}/v1/email/imap/emails/${selectedEmail.id}/attachments/${encodeURIComponent(att.name)}?folder=INBOX`}
                                                                download={att.name}
                                                                onClick={(e) => e.stopPropagation()}
                                                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-tertiary rounded"
                                                                title="다운로드"
                                                            >
                                                                <Download className="w-4 h-4" />
                                                            </a>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Quick Reply */}
                            <div className="flex-shrink-0 border-t border-border/40 bg-surface p-4" style={{boxShadow: '0 -2px 8px rgba(0,0,0,0.03)'}}>
                                <div className="max-w-3xl mx-auto">
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="text"
                                            placeholder="빠른 답장..."
                                            className="flex-1 px-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
                                            id="quick-reply-input"
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' && !e.shiftKey) {
                                                    e.preventDefault();
                                                    const input = e.currentTarget;
                                                    const text = input.value.trim();
                                                    if (!text) return;
                                                    handleQuickReply(text);
                                                    input.value = '';
                                                }
                                            }}
                                        />
                                        <button
                                            onClick={() => {
                                                const input = document.getElementById('quick-reply-input') as HTMLInputElement;
                                                const text = input?.value?.trim();
                                                if (!text) return;
                                                handleQuickReply(text);
                                                input.value = '';
                                            }}
                                            disabled={isSending}
                                            className="px-4 py-2.5 bg-brand text-white rounded-lg hover:bg-brand-dark transition text-sm font-medium disabled:opacity-50"
                                        >
                                            {isSending ? '전송중...' : '전송'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-text-subtle">
                            <div className="w-16 h-16 rounded-2xl bg-brand/10 flex items-center justify-center mb-4">
                                <Mail className="w-8 h-8 text-brand" />
                            </div>
                            <h3 className="text-lg font-medium text-text-strong mb-1">메일을 선택하세요</h3>
                            <p className="text-sm">왼쪽 목록에서 읽을 메일을 선택해주세요</p>
                            <button
                                onClick={() => setShowCompose(true)}
                                className="mt-4 flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition text-sm font-medium"
                            >
                                <Edit3 className="w-4 h-4" />
                                새 메일 작성
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Compose Modal - 모던 디자인 */}
            {showCompose && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
                    <div className="bg-surface rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col border border-border/30">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-border/20">
                            <h3 className="font-semibold text-text-strong">새 메일 작성</h3>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setShowTemplates(!showTemplates)}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                >
                                    <FileText className="w-4 h-4" />
                                    템플릿
                                </button>
                                <button
                                    onClick={() => setShowContacts(!showContacts)}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                >
                                    <Users className="w-4 h-4" />
                                    주소록
                                </button>
                                <button
                                    onClick={() => setShowCompose(false)}
                                    className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        {/* Form */}
                        <div className="flex-1 overflow-y-auto p-5">
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">받는사람</label>
                                    <input
                                        type="text"
                                        value={composeData.to}
                                        onChange={(e) => setComposeData(prev => ({ ...prev, to: e.target.value }))}
                                        placeholder="이메일 주소"
                                        className="w-full mt-1 px-4 py-2.5 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand/50"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">참조 (CC)</label>
                                        <input
                                            type="text"
                                            value={composeData.cc}
                                            onChange={(e) => setComposeData(prev => ({ ...prev, cc: e.target.value }))}
                                            placeholder="참조"
                                            className="w-full mt-1 px-4 py-2.5 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand/50"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">숨은참조 (BCC)</label>
                                        <input
                                            type="text"
                                            value={composeData.bcc}
                                            onChange={(e) => setComposeData(prev => ({ ...prev, bcc: e.target.value }))}
                                            placeholder="숨은참조"
                                            className="w-full mt-1 px-4 py-2.5 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand/50"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">제목</label>
                                    <input
                                        type="text"
                                        value={composeData.subject}
                                        onChange={(e) => setComposeData(prev => ({ ...prev, subject: e.target.value }))}
                                        placeholder="메일 제목"
                                        className="w-full mt-1 px-4 py-2.5 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand/50"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">내용</label>
                                    <textarea
                                        value={composeData.body}
                                        onChange={(e) => setComposeData(prev => ({ ...prev, body: e.target.value }))}
                                        placeholder="메일 내용을 입력하세요..."
                                        rows={12}
                                        className="w-full mt-1 px-4 py-3 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-1 focus:ring-brand/30 focus:border-brand/50 resize-none"
                                    />
                                </div>

                                {/* Schedule Picker */}
                                {showSchedulePicker && (
                                    <div className="p-4 bg-surface-secondary/30 rounded-lg border border-border/30">
                                        <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">예약 발송 시간</label>
                                        <div className="mt-2 flex items-center gap-3">
                                            <input
                                                type="datetime-local"
                                                onChange={(e) => setComposeData(prev => ({
                                                    ...prev,
                                                    scheduledTime: e.target.value ? new Date(e.target.value) : null
                                                }))}
                                                className="flex-1 px-3 py-2 bg-surface border border-border/30 rounded-lg text-sm text-text focus:outline-none focus:ring-1 focus:ring-brand/30"
                                            />
                                            <button
                                                onClick={() => setShowSchedulePicker(false)}
                                                className="px-3 py-2 text-sm text-text-subtle hover:text-text"
                                            >
                                                취소
                                            </button>
                                        </div>
                                        {composeData.scheduledTime && (
                                            <p className="mt-2 text-xs text-brand">
                                                예약됨: {composeData.scheduledTime.toLocaleString('ko-KR')}
                                            </p>
                                        )}
                                    </div>
                                )}

                                <div className="flex items-center justify-between pt-2 border-t border-border/20">
                                    <div className="flex items-center gap-2">
                                        <button className="flex items-center gap-1.5 px-3 py-2 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition">
                                            <Paperclip className="w-4 h-4" />
                                            첨부
                                        </button>
                                        <button
                                            onClick={() => setShowSchedulePicker(!showSchedulePicker)}
                                            className={cn(
                                                "flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg transition",
                                                showSchedulePicker || composeData.scheduledTime
                                                    ? "text-brand bg-brand/10"
                                                    : "text-text-subtle hover:text-text hover:bg-surface-secondary"
                                            )}
                                        >
                                            <Calendar className="w-4 h-4" />
                                            예약
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Send Error */}
                        {sendError && (
                            <div className="mx-5 mb-0 flex items-center gap-2 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700 dark:bg-rose-950/30 dark:border-rose-800 dark:text-rose-400">
                                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                <span>{sendError}</span>
                                <button onClick={() => setSendError(null)} className="ml-auto">
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        )}

                        {/* Modal Footer */}
                        <div className="flex items-center justify-between px-5 py-4 border-t border-border/20 bg-surface-secondary/30">
                            <button
                                onClick={() => { setShowCompose(false); setSendError(null); }}
                                className="px-4 py-2 text-sm text-text-subtle hover:text-text transition"
                            >
                                취소
                            </button>
                            <div className="flex items-center gap-2">
                                <button className="px-4 py-2 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition">
                                    임시저장
                                </button>
                                <button
                                    onClick={handleSend}
                                    disabled={isSending}
                                    className={cn(
                                        "flex items-center gap-2 px-5 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition text-sm font-medium",
                                        isSending && "opacity-70 cursor-not-allowed"
                                    )}
                                >
                                    {isSending ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Send className="w-4 h-4" />
                                    )}
                                    {isSending ? '전송 중...' : composeData.scheduledTime ? '예약' : '보내기'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Templates Modal */}
            {showTemplates && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
                    <div className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col border border-border/30">
                        <div className="flex items-center justify-between px-5 py-4 border-b border-border/20">
                            <h3 className="font-semibold text-text-strong">이메일 템플릿</h3>
                            <button
                                onClick={() => setShowTemplates(false)}
                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4">
                            {isLoadingTemplates ? (
                                <div className="flex flex-col items-center justify-center py-12 text-text-subtle">
                                    <Loader2 className="w-6 h-6 mb-2 animate-spin text-brand" />
                                    <p className="text-sm">템플릿 불러오는 중...</p>
                                </div>
                            ) : templates.length > 0 ? (
                                <div className="space-y-2">
                                    {templates.map((template) => (
                                        <button
                                            key={template.id}
                                            onClick={() => applyTemplate(template)}
                                            className="w-full text-left p-4 rounded-xl border border-border/20 hover:border-brand/50 hover:bg-brand/5 transition group"
                                        >
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="font-medium text-text-strong">{template.name}</span>
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-surface-secondary text-text-subtle">
                                                    {template.category}
                                                </span>
                                            </div>
                                            <div className="text-sm text-text-subtle truncate">{template.subject}</div>
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center py-12 text-text-subtle">
                                    <FileText className="w-8 h-8 mb-2 opacity-30" />
                                    <p className="text-sm">등록된 템플릿이 없습니다</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Contacts Modal */}
            {showContacts && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
                    <div className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col border border-border/30">
                        <div className="flex items-center justify-between px-5 py-4 border-b border-border/20">
                            <h3 className="font-semibold text-text-strong">주소록</h3>
                            <button
                                onClick={() => setShowContacts(false)}
                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-3 border-b border-border/20">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
                                <input
                                    type="text"
                                    placeholder="연락처 검색..."
                                    className="w-full pl-9 pr-3 py-2 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text placeholder:text-text-subtle focus:outline-none focus:ring-1 focus:ring-brand/30"
                                />
                            </div>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4">
                            <div className="space-y-2">
                                {contacts.map((contact) => (
                                    <button
                                        key={contact.id}
                                        onClick={() => selectContact(contact)}
                                        className="w-full flex items-center gap-3 p-3 rounded-xl border border-border/20 hover:border-brand/50 hover:bg-brand/5 transition"
                                    >
                                        <div className="w-10 h-10 rounded-full bg-brand/10 flex items-center justify-center text-brand font-semibold">
                                            {contact.name.charAt(0)}
                                        </div>
                                        <div className="flex-1 text-left">
                                            <div className="font-medium text-text-strong">{contact.name}</div>
                                            <div className="text-sm text-text-subtle">{contact.email}</div>
                                        </div>
                                        <span className="text-xs px-2 py-0.5 rounded-full bg-surface-secondary text-text-subtle">
                                            {categoryLabels[contact.category]}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* SMTP Settings Modal */}
            {showSmtpSettings && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
                    <div className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col border border-border/30">
                        <div className="flex items-center justify-between px-5 py-4 border-b border-border/20">
                            <div className="flex items-center gap-2">
                                <Settings className="w-5 h-5 text-brand" />
                                <h3 className="font-semibold text-text-strong">SMTP 설정</h3>
                            </div>
                            <button
                                onClick={() => setShowSmtpSettings(false)}
                                className="p-1.5 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-5">
                            <p className="text-sm text-text-subtle mb-4">
                                네이버웍스 SMTP 서버를 통해 이메일을 발송합니다.
                            </p>
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">SMTP 호스트</label>
                                        <input
                                            type="text"
                                            value={smtpConfig.smtp_host}
                                            onChange={(e) => setSmtpConfig(prev => ({ ...prev, smtp_host: e.target.value }))}
                                            placeholder="smtp.worksmobile.com"
                                            className="w-full mt-1 px-3 py-2 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text focus:outline-none focus:ring-1 focus:ring-brand/30"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">포트</label>
                                        <input
                                            type="number"
                                            value={smtpConfig.smtp_port}
                                            onChange={(e) => setSmtpConfig(prev => ({ ...prev, smtp_port: parseInt(e.target.value) || 587 }))}
                                            placeholder="587"
                                            className="w-full mt-1 px-3 py-2 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text focus:outline-none focus:ring-1 focus:ring-brand/30"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">이메일 (로그인 ID)</label>
                                    <input
                                        type="email"
                                        value={smtpConfig.smtp_username}
                                        onChange={(e) => setSmtpConfig(prev => ({ ...prev, smtp_username: e.target.value }))}
                                        placeholder="user@company.com"
                                        className="w-full mt-1 px-3 py-2 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text focus:outline-none focus:ring-1 focus:ring-brand/30"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">비밀번호</label>
                                    <input
                                        type="password"
                                        value={smtpConfig.smtp_password}
                                        onChange={(e) => setSmtpConfig(prev => ({ ...prev, smtp_password: e.target.value }))}
                                        placeholder="앱 비밀번호"
                                        className="w-full mt-1 px-3 py-2 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text focus:outline-none focus:ring-1 focus:ring-brand/30"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">보내는 이름</label>
                                        <input
                                            type="text"
                                            value={smtpConfig.from_name}
                                            onChange={(e) => setSmtpConfig(prev => ({ ...prev, from_name: e.target.value }))}
                                            placeholder="한국산업"
                                            className="w-full mt-1 px-3 py-2 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text focus:outline-none focus:ring-1 focus:ring-brand/30"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-medium text-text-subtle uppercase tracking-wide">보내는 이메일</label>
                                        <input
                                            type="email"
                                            value={smtpConfig.from_email}
                                            onChange={(e) => setSmtpConfig(prev => ({ ...prev, from_email: e.target.value }))}
                                            placeholder="sales@company.com"
                                            className="w-full mt-1 px-3 py-2 bg-surface-secondary/30 border border-border/30 rounded-lg text-sm text-text focus:outline-none focus:ring-1 focus:ring-brand/30"
                                        />
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        id="use_tls"
                                        checked={smtpConfig.use_tls}
                                        onChange={(e) => setSmtpConfig(prev => ({ ...prev, use_tls: e.target.checked }))}
                                        className="rounded border-border text-brand focus:ring-brand"
                                    />
                                    <label htmlFor="use_tls" className="text-sm text-text">TLS 사용</label>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center justify-between px-5 py-4 border-t border-border/20 bg-surface-secondary/30">
                            <button
                                onClick={handleTestSmtp}
                                disabled={isTestingSmtp}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary rounded-lg transition"
                            >
                                {isTestingSmtp ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Wifi className="w-4 h-4" />
                                )}
                                연결 테스트
                            </button>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setShowSmtpSettings(false)}
                                    className="px-4 py-2 text-sm text-text-subtle hover:text-text transition"
                                >
                                    취소
                                </button>
                                <button
                                    onClick={handleSaveSmtpConfig}
                                    className="flex items-center gap-2 px-5 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition text-sm font-medium"
                                >
                                    <Check className="w-4 h-4" />
                                    저장
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* AI 서포터 */}
            <AISupporter
                tabContext="email"
                onEmailAction={(action, data) => {
                    if (action === "compose") {
                        setShowCompose(true);
                        if (data.to) setComposeData(prev => ({ ...prev, to: data.to as string }));
                        if (data.subject) setComposeData(prev => ({ ...prev, subject: data.subject as string }));
                        if (data.body) setComposeData(prev => ({ ...prev, body: data.body as string }));
                    }
                    if (action === "applyTemplate" && data.templateId) {
                        const template = templates.find(t => t.id === data.templateId);
                        if (template) {
                            setComposeData(prev => ({
                                ...prev,
                                subject: template.subject,
                                body: template.body
                            }));
                            setShowCompose(true);
                        }
                    }
                    if (action === "adjustTone" && data.newBody) {
                        setComposeData(prev => ({ ...prev, body: data.newBody as string }));
                    }
                    if (action === "showContacts") {
                        setShowContacts(true);
                    }
                }}
            />
        </div>
    );
}
