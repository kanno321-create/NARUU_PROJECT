// Electron 테스트
console.log('Testing Electron...');
console.log('process.versions:', process.versions);
console.log('process.type:', process.type);

try {
  const electron = require('electron');
  console.log('electron module keys:', Object.keys(electron));
  console.log('app:', electron.app);
  console.log('BrowserWindow:', electron.BrowserWindow);
} catch (e) {
  console.error('Error loading electron:', e);
}
