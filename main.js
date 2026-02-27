const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { exec } = require('child_process');
const fs = require('fs');

// ADB 경로 탐색
let adb_exec = "adb";
const ADB_PATHS = [
    "/opt/homebrew/bin/adb",
    "/usr/local/bin/adb"
];

for (const p of ADB_PATHS) {
    if (fs.existsSync(p)) {
        adb_exec = p;
        break;
    }
}

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 800,
        title: "안드로이드 기본 앱 정리기",
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false // 간소화를 위해 isolation 해제
        },
        backgroundColor: '#f5f7fa',
        show: false
    });

    mainWindow.loadFile('src/index.html');
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

// IPC 통신 - ADB 명령어 실행
ipcMain.handle('run-adb', async (event, cmd) => {
    return new Promise((resolve) => {
        exec(`${adb_exec} ${cmd}`, (error, stdout, stderr) => {
            if (error) {
                resolve({ success: false, output: stderr || error.message });
            } else {
                resolve({ success: true, output: stdout.trim() });
            }
        });
    });
});
