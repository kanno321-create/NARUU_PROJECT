/**
 * API 설정
 * 모든 파일에서 이 상수를 사용하여 백엔드 URL 참조
 */

// 브라우저: Next.js rewrite 프록시(/api/v1/* → Railway), Electron: 직접 호출
const IS_ELECTRON = typeof window !== "undefined" && !!(window as any).electronAPI;
const IS_BROWSER = typeof window !== "undefined" && !IS_ELECTRON;
export const API_BASE_URL = IS_BROWSER ? "/api" : (process.env.NEXT_PUBLIC_API_URL || "https://naberalproject-production.up.railway.app");

// 파일 다운로드 URL 생성 헬퍼
export function getFileUrl(path: string): string {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    return `${API_BASE_URL}${path}`;
}
