const { contextBridge, ipcRenderer } = require('electron');

// 안전한 API를 렌더러 프로세스에 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // 앱 정보
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),

  // 메뉴 이벤트 리스너
  onMenuNewQuote: (callback) => {
    ipcRenderer.on('menu-new-quote', callback);
  },

  // 자동 업데이트 상태 수신
  onUpdateStatus: (callback) => {
    ipcRenderer.on('update-status', (_event, data) => callback(data));
  },

  // ERP 독립 윈도우 열기 (새 OS 창)
  openERPWindow: (type, title, width, height) => {
    return ipcRenderer.invoke('open-erp-window', { type, title, width, height });
  },

  // 플랫폼 체크
  isElectron: true
});

// 윈도우 로드 완료 시
window.addEventListener('DOMContentLoaded', () => {
  console.log('NABERAL KIS Estimator - Electron App Loaded');
});
