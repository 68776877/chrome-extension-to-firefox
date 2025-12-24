# Chrome to Firefox Extension Porter (Educational Tool)

A simple GUI tool to convert Chrome Manifest V3 extensions into Firefox-compatible `.xpi` format.
This tool automates the process of `service_worker` conversion and `browser-polyfill.js` injection.

## ⚠️ Legal Disclaimer (Important)

**This tool is intended ONLY for:**
* ✅ Converting your own extensions (Self-developed)
* ✅ Converting open-source extensions (MIT, GPL, etc.)
* ✅ Personal interoperability purposes (Using legally obtained extensions on a different browser)

**NOT for:**
* ❌ Converting proprietary/paid extensions without permission
* ❌ Redistributing converted extensions to public stores
* ❌ Violating Chrome Web Store Terms of Service

**You are solely responsible for ensuring you have the right to convert and use any extension.**

---

## ⚠️ Prerequisites & Limitations
1.  **Browser Requirement**: The converted extensions are **unsigned** and will **NOT work on standard Firefox**. You must use **Firefox Developer Edition** or **Nightly** and disable signature enforcement (`xpinstall.signatures.required = false` in `about:config`).
2.  **Compatibility**: Not all extensions are guaranteed to work.
    * Extensions relying heavily on **Chrome-specific APIs** (e.g., `chrome.gcm`, `chrome.identity`) may fail.
    * **Google Account Login (OAuth)** features may not function correctly after conversion.

---

## Features
* **Modern GUI**: User-friendly interface built with CustomTkinter.
* **MV3 Support**: Automatically converts `service_worker` to background scripts.
* **Polyfill Injection**: Downloads and injects Mozilla's `webextension-polyfill` for API compatibility.
* **Permission Cleanup**: Removes permissions that are incompatible with Firefox.

## Usage
1.  Download the latest release (`.exe`).
2.  Run the application.
    * You must accept the legal disclaimer on the first run.
    * Your acceptance is saved locally as a `.disclaimer_accepted` file.
3.  Select a Chrome extension file (`.crx`, `.zip`) or a folder.
4.  Click **START CONVERSION**.
5.  Install the generated `.xpi` file in a **compatible Firefox browser**:
    * **Option A**: Drag & Drop the file into the browser window.
    * **Option B**: Go to `about:addons`, click the **Gear icon (⚙️)**, and select **'Install Add-on From File...'**.

## License
This project is licensed under the [MIT License](LICENSE).

---
---

# 크롬 확장 프로그램 변환기 (교육용 도구)

크롬의 Manifest V3 확장 프로그램을 파이어폭스 호환 포맷(`.xpi`)으로 변환해주는 간단한 GUI 도구입니다.
`service_worker`를 백그라운드 스크립트로 변환하고 `browser-polyfill.js`를 주입하는 과정을 자동화합니다.

## ⚠️ 법적 고지 및 주의사항 (중요)

**이 도구는 오직 다음의 목적으로만 사용해야 합니다:**
* ✅ 본인이 직접 개발한 확장 프로그램 변환
* ✅ 오픈소스 라이선스(MIT, GPL 등)를 따르는 확장 프로그램 변환
* ✅ 개인적인 상호운용성 확보 (합법적으로 취득한 확장을 다른 브라우저에서 사용)

**다음의 행위는 엄격히 금지됩니다:**
* ❌ 타인의 유료/독점 확장 프로그램을 허가 없이 변환하는 행위
* ❌ 변환된 파일을 공공 저장소나 스토어에 무단으로 재배포하는 행위
* ❌ Chrome 웹 스토어 이용 약관을 위반하는 행위

**확장 프로그램을 변환하고 사용할 권리가 있는지 확인하는 것은 전적으로 사용자의 책임입니다.**

---

## ⚠️ 필수 준비사항 및 한계점
1.  **브라우저 요구사항**: 변환된 파일은 **서명되지 않았으므로**, 일반 파이어폭스에서는 작동하지 않습니다. **Firefox Developer Edition** 또는 **Nightly** 버전을 사용해야 하며, `about:config`에서 `xpinstall.signatures.required`를 `false`로 설정해야 합니다.
2.  **호환성 주의**: 모든 확장 프로그램이 완벽하게 작동하는 것은 아닙니다.
    * **Chrome 전용 API**(`chrome.gcm` 등)를 사용하는 기능은 작동하지 않을 수 있습니다.
    * **구글 로그인(OAuth)** 기능은 변환 후 정상적으로 작동하지 않을 가능성이 높습니다.

---

## 주요 기능
* **모던 GUI**: CustomTkinter로 제작된 깔끔하고 직관적인 인터페이스.
* **MV3 지원**: 크롬의 `service_worker`를 파이어폭스용 백그라운드 스크립트로 자동 변환.
* **폴리필 주입**: 모질라의 `webextension-polyfill`을 자동 다운로드 및 주입하여 API 호환성 확보.
* **권한 정리**: 파이어폭스에서 지원하지 않는 불필요한 권한 자동 제거.

## 사용 방법
1.  우측의 **Releases**에서 최신 버전의 `.exe` 파일을 다운로드하세요.
2.  프로그램을 실행합니다.
    * **최초 실행 시 법적 고지에 동의해야 합니다.**
    * 동의 내역은 같은 폴더에 `.disclaimer_accepted` 파일로 저장되며, 이후 실행부터는 팝업이 뜨지 않습니다.
3.  변환할 크롬 확장 프로그램 파일(`.crx`, `.zip`)이나 폴더를 선택하세요.
4.  **START CONVERSION** 버튼을 누르세요.
5.  생성된 `.xpi` 파일을 **호환되는 파이어폭스 브라우저**에 설치하세요:
    * **방법 A**: 파일을 브라우저 창으로 **드래그 앤 드롭**합니다.
    * **방법 B**: 주소창에 `about:addons`를 입력하고, 톱니바퀴(⚙️) 아이콘을 눌러 **'파일에서 부가 기능 설치...(Install Add-on From File...)'**를 선택합니다.

## 라이선스
이 프로젝트는 [MIT License](LICENSE)를 따릅니다.