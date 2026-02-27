# Kongsin (Android App Manager)

**Made by krazyeom**

스마트폰 하드웨어나 루팅 없이, 안드로이드 스마트폰에 기본 설치된 앱(통신사 앱, 제조사 앱 등)을 정리 할 수 있는 데스크탑 유틸리티입니다. 

## 🚀 기능 (Features)
* **앱 리스트 불러오기**: 클릭 한 번으로 내 폰에 설치된 모든 패키지 목록을 가져옵니다.
* **검색 기능**: `samsung`, `chrome` 등의 단어로 내가 원하는 앱을 빠르게 찾아줍니다.
* **멀티 셀렉트**: 앱을 여러 개 동시에 선택하여 일괄 처리할 수 있습니다. (Shift, Command 클릭 지원)
* **비활성화 (숨기기)**: 사용하지 않는 기본 시스템 앱을 즉시 비활성화하여 폰 화면 및 시스템 구동에서 숨깁니다.
* **활성화**: 비활성화된 앱을 다시 원상복구 시킬 수 있습니다.

## 💻 실행 방법 (How to use)

### Mac
* `AndroidManager.app` 을 실행합니다. (또는 파이썬 스크립트를 직접 실행: `python3 AndroidAppManager.py`)

### Windows
* `AndroidManager.exe` 를 실행합니다.

### 📱 스마트폰 준비사항
1. 휴대폰 설정 > 휴대전화 정보 > 소프트웨어 정보에서 `빌드 번호`를 7번 연타하여 **개발자 옵션**을 활성화시킵니다.
2. 설정 > 개발자 옵션으로 들어가서 **`USB 디버깅`**을 켭니다.
3. USB 케이블로 휴대폰을 PC에 연결합니다.
4. 본 프로그램을 켜고 `앱 불러오기` 버튼을 누릅니다. **(이때 폰 화면에서 반드시 [디버깅 허용]을 눌러야 합니다!)**

## 🛠 빌드 방법 (개발자용)
```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "AndroidManager" AndroidAppManager.py
```
