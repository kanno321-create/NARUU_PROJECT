'use strict';

const { app, BrowserWindow, shell, ipcMain, session, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { autoUpdater } = require('electron-updater');

// Fix: Disable Chromium sandbox for Windows 11 24H2 compatibility
app.commandLine.appendSwitch('no-sandbox');

const API_BASE = 'https://naberalproject-production.up.railway.app';

const isDev = !app.isPackaged;

let mainWindow;
let localServer;
let localServerPort = 0;  // 로컬 서버 포트 (자식 윈도우에서 재사용)
const childWindows = new Map();  // ERP 자식 윈도우 관리

// ============= 자동 업데이트 =============
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

function setupAutoUpdater() {
    if (isDev) return; // 개발 모드에서는 비활성화

    autoUpdater.on('update-available', (info) => {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: '업데이트 알림',
            message: `새 버전 (v${info.version})이 있습니다.\n다운로드하시겠습니까?`,
            buttons: ['업데이트', '나중에'],
            defaultId: 0,
        }).then((result) => {
            if (result.response === 0) {
                autoUpdater.downloadUpdate();
                if (mainWindow) {
                    mainWindow.webContents.send('update-status', { status: 'downloading', version: info.version });
                }
            }
        });
    });

    autoUpdater.on('update-not-available', () => {
        // 최신 버전 — 별도 알림 없음
    });

    autoUpdater.on('download-progress', (progress) => {
        if (mainWindow) {
            mainWindow.webContents.send('update-status', {
                status: 'progress',
                percent: Math.round(progress.percent),
            });
        }
    });

    autoUpdater.on('update-downloaded', () => {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: '업데이트 완료',
            message: '업데이트가 다운로드되었습니다.\n지금 재시작하시겠습니까?',
            buttons: ['재시작', '나중에'],
            defaultId: 0,
        }).then((result) => {
            if (result.response === 0) {
                autoUpdater.quitAndInstall();
            }
        });
    });

    autoUpdater.on('error', (err) => {
        console.error('Auto-update error:', err);
    });

    // 앱 시작 후 3초 뒤 업데이트 확인
    setTimeout(() => {
        autoUpdater.checkForUpdates().catch((err) => {
            console.error('Update check failed:', err);
        });
    }, 3000);
}

const MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.txt': 'text/plain; charset=utf-8',
    '.map': 'application/json',
    '.webp': 'image/webp',
};

// 데스크톱앱 전용 내부 페이지 (공개 홈페이지 제외)
const INTERNAL_PAGES = ['/login', '/dashboard', '/ai-manager', '/quote', '/erp', '/calendar', '/email', '/drawings', '/settings', '/signup'];

function startLocalServer(outDir) {
    return new Promise((resolve, reject) => {
        const server = http.createServer((req, res) => {
            let pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);

            // 공개 페이지 접근 시 로그인으로 리다이렉트
            // _next, favicon, images 등 정적 리소스는 허용
            if (!pathname.startsWith('/_next') && !pathname.startsWith('/favicon') &&
                !pathname.startsWith('/images') && !pathname.startsWith('/icon') &&
                pathname !== '/') {
                const isInternal = INTERNAL_PAGES.some(p => pathname.startsWith(p));
                if (!isInternal && !path.extname(pathname)) {
                    res.writeHead(302, { 'Location': '/login/' });
                    res.end();
                    return;
                }
            }

            // 루트 → 로그인으로 리다이렉트
            if (pathname === '/') {
                res.writeHead(302, { 'Location': '/login/' });
                res.end();
                return;
            }

            let filePath = path.join(outDir, pathname);

            if (!path.extname(filePath)) {
                const withIndex = path.join(filePath, 'index.html');
                if (fs.existsSync(withIndex)) {
                    filePath = withIndex;
                } else {
                    filePath = path.join(outDir, 'login', 'index.html');
                }
            }

            if (!fs.existsSync(filePath)) {
                filePath = path.join(outDir, 'login', 'index.html');
            }

            const ext = path.extname(filePath).toLowerCase();
            const contentType = MIME_TYPES[ext] || 'application/octet-stream';

            try {
                const data = fs.readFileSync(filePath);
                res.writeHead(200, { 'Content-Type': contentType });
                res.end(data);
            } catch (err) {
                res.writeHead(404);
                res.end('Not Found');
            }
        });

        server.listen(0, '127.0.0.1', () => {
            const port = server.address().port;
            resolve({ server, port });
        });
        server.on('error', reject);
    });
}

function createWindow(startUrl) {
    mainWindow = new BrowserWindow({
        width: 1600,
        height: 1000,
        minWidth: 1024,
        minHeight: 768,
        icon: path.join(__dirname, '../public/icon.ico'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: false,
            preload: path.join(__dirname, 'preload.js'),
        },
        titleBarStyle: 'default',
        show: true,
        backgroundColor: '#1a1a2e',
        title: 'NABERAL KIS Estimator',
    });

    // CORS bypass for Railway API
    session.defaultSession.webRequest.onBeforeSendHeaders((details, callback) => {
        const { requestHeaders } = details;
        if (details.url.startsWith(API_BASE)) {
            requestHeaders['Origin'] = API_BASE;
        }
        callback({ requestHeaders });
    });

    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
        const { responseHeaders } = details;
        if (details.url.startsWith(API_BASE)) {
            responseHeaders['access-control-allow-origin'] = ['*'];
            responseHeaders['access-control-allow-headers'] = ['*'];
            responseHeaders['access-control-allow-methods'] = ['GET, POST, PUT, DELETE, PATCH, OPTIONS'];
            // OPTIONS preflight returns 400 from Railway — override to 200
            if (details.method === 'OPTIONS' || details.statusCode === 400) {
                callback({ responseHeaders, statusLine: 'HTTP/1.1 200 OK' });
                return;
            }
        }
        callback({ responseHeaders });
    });

    mainWindow.loadURL(startUrl);

    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('http')) {
            shell.openExternal(url);
            return { action: 'deny' };
        }
        return { action: 'allow' };
    });

    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(async () => {
    let startUrl;

    if (isDev) {
        startUrl = 'http://localhost:3000';
    } else {
        const outDir = path.join(__dirname, '../out');
        const { server, port } = await startLocalServer(outDir);
        localServer = server;
        localServerPort = port;
        startUrl = `http://127.0.0.1:${port}/login/`;
    }

    createWindow(startUrl);
    setupAutoUpdater();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow(startUrl);
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        if (localServer) { localServer.close(); }
        app.quit();
    }
});

app.on('before-quit', () => {
    if (localServer) { localServer.close(); }
});

ipcMain.handle('get-app-version', () => app.getVersion());
ipcMain.handle('get-platform', () => process.platform);
ipcMain.handle('get-api-base', () => API_BASE);

// ERP 독립 윈도우 열기
ipcMain.handle('open-erp-window', (event, { type, title, width, height }) => {
    // 같은 타입 윈도우가 이미 열려있으면 포커스
    if (childWindows.has(type)) {
        const existing = childWindows.get(type);
        if (existing && !existing.isDestroyed()) {
            existing.focus();
            return { success: true, action: 'focused' };
        }
        childWindows.delete(type);
    }

    const baseUrl = isDev
        ? 'http://localhost:3000'
        : `http://127.0.0.1:${localServerPort}`;

    const windowUrl = `${baseUrl}/erp/window/?type=${encodeURIComponent(type)}&title=${encodeURIComponent(title)}`;

    const childWindow = new BrowserWindow({
        width: width || 1350,
        height: height || 850,
        minWidth: 600,
        minHeight: 400,
        icon: path.join(__dirname, '../public/icon.ico'),
        parent: null,  // 독립 윈도우 (부모에 종속되지 않음)
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: false,
            preload: path.join(__dirname, 'preload.js'),
        },
        title: `${title} - KIS ERP`,
        show: true,
        backgroundColor: '#f5f5f5',
    });

    childWindow.loadURL(windowUrl);

    // 외부 링크는 기본 브라우저로
    childWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('http') && !url.includes('127.0.0.1') && !url.includes('localhost')) {
            shell.openExternal(url);
            return { action: 'deny' };
        }
        return { action: 'allow' };
    });

    // 로드 실패 시 로깅
    childWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error(`[ERP Window] Load failed: ${errorCode} ${errorDescription} URL: ${windowUrl}`);
    });

    childWindow.on('closed', () => {
        childWindows.delete(type);
        // 메인 윈도우에 알림
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('child-window-closed', { type });
        }
    });

    console.log('[ERP Window] Opening:', windowUrl);
    childWindows.set(type, childWindow);
    return { success: true, action: 'opened' };
});
