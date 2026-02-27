const { ipcRenderer } = require('electron');

let allApps = [];
let checkedApps = new Set();

// 잘 알려진 패키지명 -> 앱 이름 변환 맵
const appNameMap = {
    // 스토어류
    "com.android.vending": "Google Play 스토어",
    "com.skt.skaf.A000Z00040": "원스토어 (SKT)",
    "net.onestore.store": "원스토어 (KT/LGU+)",
    "com.sec.android.app.samsungapps": "갤럭시 스토어",
    "com.samsung.android.themestore": "갤럭시 테마",
    // 동영상 / 미디어류
    "com.google.android.youtube": "YouTube",
    "com.google.android.apps.youtube.music": "YouTube Music",
    "com.netflix.mediaclient": "Netflix",
    "com.zhiliaoapp.musically": "TikTok (Global)",
    "com.ss.android.ugc.trill": "TikTok",
    // 브라우저류
    "com.android.chrome": "Chrome",
    "com.sec.android.app.sbrowser": "삼성 인터넷",
    // SNS / 지도
    "com.instagram.android": "Instagram",
    "com.facebook.katana": "Facebook",
    "com.twitter.android": "Twitter/X",
    "com.google.android.apps.maps": "Google 지도",
    // 삼성/구글 잉여앱
    "com.samsung.android.bixby.wakeup": "빅스비 보이스 Wakeup",
    "com.samsung.android.bixby.agent": "빅스비 앱",
    "com.samsung.android.bixby.visionapp": "빅스비 비전",
    "com.samsung.android.arzone": "AR 존",
    "com.samsung.android.ardrawing": "AR 두들",
    "com.samsung.android.aremoji": "AR 이모지",
    "com.samsung.android.aremojieditor": "AR 이모지 에디터",
    "com.sec.android.mimage.avatarstickers": "AR 이모지 스티커",
    "com.google.android.gm": "Gmail",
    "com.google.android.googlequicksearchbox": "Google 앱",
    "com.google.android.apps.tachyon": "Google Meet",
    "com.google.android.apps.meetings": "Google Meet",
    "com.samsung.android.app.spage": "Samsung Free",
    "com.samsung.android.game.gamehome": "삼성 게임런처",
    "com.samsung.android.app.tips": "삼성 팁 (도움말)"
};

// 절대로 삭제하거나 비활성화하면 안 되는 핵심 시스템 앱 키워드 및 패키지
const criticalSystemApps = [
    "android",
    "com.android.systemui",
    "com.android.settings",
    "com.android.phone",
    "com.android.server.telecom",
    "com.android.providers.settings",
    "com.samsung.android.dialer",
    "com.samsung.android.messaging",
    "com.sec.android.app.launcher"
];

function isCriticalApp(pkg) {
    if (criticalSystemApps.includes(pkg)) return true;
    // 패키지명에 아래 키워드가 포함되면 중요 시스템 앱으로 간주
    if (pkg.includes("systemui") || pkg.includes("com.android.providers.") || pkg.includes("com.android.phone")) {
        return true;
    }
    return false;
}

// Elements
const btnLoad = document.getElementById('btn-load');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

const tbody = document.getElementById('app-list-body');
const searchInput = document.getElementById('search-input');
const checkAll = document.getElementById('check-all');
const lblCount = document.getElementById('selected-count');

// Buttons
const btnDisable = document.getElementById('btn-disable');
const btnEnable = document.getElementById('btn-enable');
const btnDelete = document.getElementById('btn-delete');
const btnRestore = document.getElementById('btn-restore');
const btnKongsin = document.getElementById('btn-kongsin');

let wasConnected = false;

// 주기적 장치 확인
setInterval(async () => {
    const res = await ipcRenderer.invoke('run-adb', 'devices');
    if (res.success) {
        const lines = res.output.split('\n');
        let connected = false;
        for (let i = 1; i < lines.length; i++) {
            if (lines[i].includes('device') && !lines[i].includes('offline') && !lines[i].includes('unauthorized')) {
                connected = true;
                break;
            }
        }
        
        if (connected) {
            statusDot.className = "status-dot bg-success";
            statusText.innerText = "스마트폰 연결됨";
            
            // 연결 시 자동 불러오기
            if (!wasConnected) {
                wasConnected = true;
                btnLoad.click();
            }
        } else {
            statusDot.className = "status-dot bg-danger";
            statusText.innerText = "연결 안됨 (USB 확인)";
            wasConnected = false;
        }
    }
}, 3000);

// 앱 목록 불러오기
async function loadApps() {
    btnLoad.disabled = true;
    btnLoad.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>불러오는 중...';
    
    const res = await ipcRenderer.invoke('run-adb', 'shell pm list packages -u');
    let loadedCount = 0;
    
    if (res.success && res.output) {
        allApps = res.output.split('\n')
            .filter(line => line.startsWith('package:'))
            .map(line => line.replace('package:', '').trim())
            .sort();
            
        checkedApps.clear();
        updateCountUI();
        renderList(allApps);
        loadedCount = allApps.length;
    } else {
        alert("기기를 찾을 수 없거나 목록을 읽을 수 없습니다.\nUSB 디버깅이 켜져 있는지 확인하세요.");
    }
    
    btnLoad.disabled = false;
    btnLoad.innerHTML = '<i class="fas fa-plug me-2"></i>기기에서 앱 불러오기';
    
    return loadedCount;
}

btnLoad.addEventListener('click', async () => {
    const count = await loadApps();
    if (count > 0) {
        alert(`총 ${count}개의 앱을 성공적으로 불러왔습니다.`);
    }
});

// UI 렌더링
function renderList(listToRender) {
    if (listToRender.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted py-5">검색 결과가 없습니다.</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    listToRender.forEach(app => {
        const isCritical = isCriticalApp(app);
        const tr = document.createElement('tr');
        const isChecked = checkedApps.has(app) && !isCritical;
        
        if (isChecked) tr.classList.add('selected-row');
        if (isCritical) tr.classList.add('bg-light');
        
        const appName = appNameMap[app] || "-";

        const checkboxHtml = isCritical 
            ? `<i class="fas fa-lock text-danger" title="삭제 방지된 핵심 앱"></i>`
            : `<input class="form-check-input check-lg cursor-pointer row-check" type="checkbox" data-pkg="${app}" ${isChecked ? 'checked' : ''}>`;

        tr.innerHTML = `
            <td class="text-center">
                ${checkboxHtml}
            </td>
            <td class="fw-bold ${isCritical ? 'text-danger' : ''}">${app}</td>
            <td class="text-muted">${appName} ${isCritical ? '<span class="badge bg-danger ms-2">필수 시스템</span>' : ''}</td>
        `;

        // 행(Row) 전체 클릭 시 체크박스 토글
        tr.addEventListener('click', (e) => {
            if (isCritical) return; // 필수 앱은 클릭 무시
            if (e.target.type !== 'checkbox') {
                const cb = tr.querySelector('.row-check');
                if (cb) {
                    cb.checked = !cb.checked;
                    toggleCheck(app, cb.checked, tr);
                }
            }
        });

        if (!isCritical) {
            const cb = tr.querySelector('.row-check');
            if (cb) {
                cb.addEventListener('change', (e) => {
                    toggleCheck(app, e.target.checked, tr);
                });
            }
        }

        tbody.appendChild(tr);
    });
}

// 개별 체크 관리
function toggleCheck(pkg, isChecked, trElement) {
    if (isChecked) {
        checkedApps.add(pkg);
        if(trElement) trElement.classList.add('selected-row');
    } else {
        checkedApps.delete(pkg);
        if(trElement) trElement.classList.remove('selected-row');
    }
    updateCountUI();
}

// 전체 선택
checkAll.addEventListener('change', (e) => {
    const isChecked = e.target.checked;
    const checkboxes = document.querySelectorAll('.row-check');
    
    checkboxes.forEach(cb => {
        cb.checked = isChecked;
        const pkg = cb.getAttribute('data-pkg');
        toggleCheck(pkg, isChecked, cb.closest('tr'));
    });
});

// 검색 필터
searchInput.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = allApps.filter(app => {
        const name = appNameMap[app] ? appNameMap[app].toLowerCase() : "";
        return app.toLowerCase().includes(term) || name.includes(term);
    });
    renderList(filtered);
    checkAll.checked = false;
});

// 카운트 UI 갱신
function updateCountUI() {
    lblCount.innerText = `${checkedApps.size}개 선택됨`;
    if (checkedApps.size > 0) {
        lblCount.classList.add('active');
    } else {
        lblCount.classList.remove('active');
    }
}

// 공신폰 모드 (프리셋 선택)
btnKongsin.addEventListener('click', async () => {
    if (allApps.length === 0) {
        const count = await loadApps();
        if (count === 0) return;
    }

    const kongsin_apps = [
        "com.android.vending", "com.skt.skaf.A000Z00040", "net.onestore.store", "com.sec.android.app.samsungapps",
        "com.google.android.youtube", "com.google.android.apps.youtube.music", "com.netflix.mediaclient", "com.zhiliaoapp.musically", "com.ss.android.ugc.trill",
        "com.android.chrome", "com.sec.android.app.sbrowser",
        "com.instagram.android", "com.facebook.katana", "com.twitter.android",
        "com.samsung.android.bixby.wakeup", "com.samsung.android.bixby.agent", "com.samsung.android.bixby.visionapp",
        "com.samsung.android.themestore", "com.google.android.apps.maps",
        "com.samsung.android.arzone", "com.samsung.android.ardrawing", "com.samsung.android.aremoji", "com.samsung.android.aremojieditor", "com.sec.android.mimage.avatarstickers",
        "com.google.android.gm", "com.google.android.googlequicksearchbox",
        "com.google.android.apps.tachyon", "com.google.android.apps.meetings",
        "com.samsung.android.app.spage", "com.samsung.android.game.gamehome", "com.samsung.android.app.tips"
    ];

    let count = 0;
    kongsin_apps.forEach(app => {
        if (allApps.includes(app)) {
            checkedApps.add(app);
            count++;
        }
    });

    if (count > 0) {
        checkAll.checked = false;
        searchInput.value = "";
        renderList(allApps); // 재렌더링하여 하이라이트 표시
        updateCountUI();
        alert(`방해/잉여앱 ${count}개를 찾아 체크했습니다.\n상단의 원하는 액션(비활성화/완전삭제)을 클릭하세요.`);
    } else {
        alert("처리할 앱을 폰에서 찾을 수 없습니다.");
    }
});

// 공통 처리 함수 (비활성화/활성화/삭제/복원)
async function processAction(actionName, cmdTemplate, successKeyword) {
    if (checkedApps.size === 0) {
        alert("체크된 앱이 없습니다.");
        return;
    }

    if (!confirm(`선택한 ${checkedApps.size}개의 앱을 기기에서 [${actionName}] 하시겠습니까?`)) {
        return;
    }

    let success = 0;
    let fails = [];

    const pkgs = Array.from(checkedApps);
    
    for (const pkg of pkgs) {
        const cmd = cmdTemplate.replace("{pkg}", pkg);
        const res = await ipcRenderer.invoke('run-adb', cmd);
        
        if (res.output.toLowerCase().includes(successKeyword.toLowerCase())) {
            success++;
        } else {
            fails.push(pkg);
        }
    }

    let msg = `${actionName} 완료: ${success}개 성공\n`;
    if (fails.length > 0) {
        msg += `\n실패: ${fails.length}개\n(권한 부족 또는 이미 처리된 앱)`;
    }
    
    alert(msg);
    btnLoad.click(); // 리스트 새로고침
}

btnDisable.addEventListener('click', () => processAction("비활성화", "shell pm disable-user --user 0 {pkg}", "disabled"));
btnEnable.addEventListener('click', () => processAction("활성화", "shell pm enable {pkg}", "enabled"));
btnDelete.addEventListener('click', () => {
    alert("⚠️ 강력 경고 ⚠️\n완전 삭제 시 공장초기화 전에는 일반적인 방법으로 복구가 불가능할 수 있습니다. 시스템 구동에 필요한 핵심앱인지 한 번 더 확인하세요.");
    processAction("완전 삭제", "shell pm uninstall -k --user 0 {pkg}", "success");
});
btnRestore.addEventListener('click', () => processAction("완전 복원", "shell cmd package install-existing {pkg}", "installed"));
