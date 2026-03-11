/** @type {import('next').NextConfig} */

// Electron 환경인지 체크
const isElectron = process.env.ELECTRON === 'true';

const nextConfig = {
    // Electron 빌드 시 static export
    ...(isElectron && {
        output: 'export',
        distDir: 'out',
        trailingSlash: true,
    }),

    // 보안 헤더 설정 (CSP는 production에서만 적용)
    async headers() {
        const isDev = process.env.NODE_ENV === 'development';
        return [
            {
                source: "/:path*",
                headers: [
                    // 개발 환경에서는 CSP 비활성화 (다음 우편번호 등 외부 서비스 호환성)
                    ...(!isDev ? [{
                        key: "Content-Security-Policy",
                        value: [
                            "default-src 'self'",
                            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.daumcdn.net http://*.daumcdn.net https://*.daum.net https://*.kakao.com",
                            "style-src 'self' 'unsafe-inline'",
                            "img-src 'self' data: blob: https://naberalproject-production.up.railway.app https://*.daumcdn.net https://*.daum.net",
                            "font-src 'self' data:",
                            "connect-src 'self' https://naberalproject-production.up.railway.app https://*.daum.net https://*.kakao.com",
                            "frame-src 'self' https://*.daum.net https://*.kakao.com https://*.daumcdn.net https://*.google.com",
                            "frame-ancestors 'self'",
                            "base-uri 'self'",
                            "form-action 'self'",
                        ].join("; "),
                    }] : []),
                    {
                        key: "X-Content-Type-Options",
                        value: "nosniff",
                    },
                    {
                        key: "X-Frame-Options",
                        value: "SAMEORIGIN",
                    },
                    {
                        key: "X-XSS-Protection",
                        value: "1; mode=block",
                    },
                    {
                        key: "Referrer-Policy",
                        value: "strict-origin-when-cross-origin",
                    },
                    {
                        key: "Permissions-Policy",
                        value: "camera=(), microphone=(), geolocation=()",
                    },
                ],
            },
        ];
    },

    // API 요청을 백엔드로 프록시 (CORS 우회)
    ...(!isElectron && {
        async rewrites() {
            const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            return {
                // fallback: Next.js 페이지/API routes에 매칭되지 않은 요청만 백엔드로 프록시
                fallback: [
                    {
                        source: "/api/v1/:path*",
                        destination: `${backendUrl}/v1/:path*`,
                    },
                    {
                        source: "/api/erp/:path*",
                        destination: `${backendUrl}/erp/:path*`,
                    },
                    {
                        source: "/api/docs",
                        destination: `${backendUrl}/docs`,
                    },
                ],
            };
        },
    }),

    // 이미지 최적화 설정
    images: {
        unoptimized: isElectron, // Electron에서는 이미지 최적화 비활성화
        remotePatterns: [
            {
                protocol: "http",
                hostname: "localhost",
                port: "8000",
                pathname: "/uploads/**",
            },
            {
                protocol: "http",
                hostname: "127.0.0.1",
                port: "8000",
                pathname: "/uploads/**",
            },
            {
                protocol: "https",
                hostname: "naberalproject-production.up.railway.app",
                pathname: "/uploads/**",
            },
        ],
    },

    // 실험적 기능
    experimental: {
        // 서버 액션 활성화
        serverActions: {
            allowedOrigins: [
                "localhost:3000",
                "hkkor.com",
                "www.hkkor.com",
                "*.vercel.app",
            ],
        },
    },

    // 타입스크립트 설정
    typescript: {
        // 빌드 시 타입 에러 무시 (개발 중에만)
        ignoreBuildErrors: true,
    },

    // ESLint 설정
    eslint: {
        // 빌드 시 ESLint 에러 무시 (개발 중에만)
        ignoreDuringBuilds: true,
    },
};

export default nextConfig;
