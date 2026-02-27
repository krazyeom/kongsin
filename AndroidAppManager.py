import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os

# Mac에 설치된 ADB 경로 자동 탐색 (Apple Silicon 및 Intel Mac 대응)
ADB_PATHS = ["/opt/homebrew/bin/adb", "/usr/local/bin/adb", "adb"]
adb_exec = "adb"
for path in ADB_PATHS:
    if os.path.exists(path):
        adb_exec = path
        break

def run_adb_command(cmd):
    try:
        # 터미널 명령어 실행
        result = subprocess.run(f"{adb_exec} {cmd}", shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

class AndroidAppManager:
    def __init__(self, root):
        self.root = root
        self.root.title("안드로이드 기본 앱 정리기")
        self.root.geometry("650x700")
        
        # 깔끔한 테마 적용
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        # 상단 버튼 영역
        top_frame = ttk.Frame(root, padding=10)
        top_frame.pack(fill=tk.X)

        self.btn_load = ttk.Button(top_frame, text="📲 기기에서 앱 불러오기", command=self.load_apps)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_disable = ttk.Button(top_frame, text="🚫 비활성화 (숨기기)", command=self.disable_app)
        self.btn_disable.pack(side=tk.LEFT, padx=5)

        self.btn_enable = ttk.Button(top_frame, text="✅ 다시 활성화", command=self.enable_app)
        self.btn_enable.pack(side=tk.LEFT, padx=5)

        self.btn_delete = ttk.Button(top_frame, text="🗑 완전 삭제", command=self.delete_app)
        self.btn_delete.pack(side=tk.LEFT, padx=5)

        self.btn_restore = ttk.Button(top_frame, text="♻️ 완전 복원", command=self.restore_app)
        self.btn_restore.pack(side=tk.LEFT, padx=5)

        # 프리셋 버튼 영역
        preset_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        preset_frame.pack(fill=tk.X)

        self.btn_kongsin = ttk.Button(preset_frame, text="🎓 공신폰 모드 (방해앱 선택)", command=self.select_kongsin_apps)
        self.btn_kongsin.pack(side=tk.LEFT, padx=5)

        self.btn_delete_preset = ttk.Button(preset_frame, text="🧹 삼성/구글 기본앱 (삭제용 선택)", command=self.select_delete_apps)
        self.btn_delete_preset.pack(side=tk.LEFT, padx=5)

        # 검색 영역
        search_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        search_frame.pack(fill=tk.X)
        ttk.Label(search_frame, text="앱 검색: ").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list) # 글자가 입력될 때마다 필터링
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 선택된 개수 표시 라벨
        self.lbl_selected_count = tk.Label(search_frame, text="0개가 선택되었습니다.", fg="gray", font=("Helvetica", 14, "bold"))
        self.lbl_selected_count.pack(side=tk.RIGHT, padx=10)

        # 리스트 영역
        list_frame = ttk.Frame(root, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(list_frame, columns=("App",), show="tree", yscrollcommand=scrollbar.set, selectmode="none")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        style.configure("Treeview", rowheight=35, font=("Helvetica", 14))
        self.tree.column("#0", width=50, stretch=False, anchor="center")
        self.tree.column("App", stretch=True)
        self.tree.bind('<ButtonRelease-1>', self.toggle_check)

        # 선택 시 배경색상 적용을 위한 태그 설정
        self.tree.tag_configure("checked", background="#D3E8FF")
        self.tree.tag_configure("unchecked", background="white")

        self.all_apps = []
        self.checked_apps = set()

    def load_apps(self):
        # -u 인자를 추가하여 비활성화/삭제된 언인스톨 상태의 기본 앱도 모두 가져옵니다 (복원을 위함)
        output = run_adb_command("shell pm list packages -u")
        
        self.all_apps = []
        self.checked_apps.clear()
        for line in output.split('\n'):
            if line.startswith("package:"):
                # package:com.android.chrome 형태에서 실제 이름만 추출
                pkg = line.replace("package:", "").strip()
                self.all_apps.append(pkg)
                
        if not self.all_apps:
            messagebox.showerror("연결 오류", "Android 기기를 찾을거나 앱 리스트를 읽을 수 없습니다.\nUSB가 폰에 연결되었고, 'USB 디버깅'이 켜져 있는지 확인하세요.")
            return
            
        self.all_apps.sort()
        self.update_listbox(self.all_apps)
        self.update_selected_count_label()
        messagebox.showinfo("성공", f"총 {len(self.all_apps)}개의 앱을 불러왔습니다.")

    def update_selected_count_label(self):
        count = len(self.checked_apps)
        if count > 0:
            self.lbl_selected_count.config(text=f"{count}개가 선택되었습니다.", fg="red")
        else:
            self.lbl_selected_count.config(text="0개가 선택되었습니다.", fg="gray")

    def select_kongsin_apps(self):
        # 공신폰을 만들기 위해 비활성화해야 할 대표적인 방해 앱 패키지 목록
        kongsin_apps = [
            # 스토어류
            "com.android.vending",             # Google Play Store
            "com.skt.skaf.A000Z00040",         # SKT One Store
            "net.onestore.store",              # One Store (KT, LGU+)
            "com.sec.android.app.samsungapps", # Galaxy Store
            
            # 동영상 / 미디어류
            "com.google.android.youtube",      # YouTube
            "com.google.android.apps.youtube.music", # YouTube Music
            "com.netflix.mediaclient",         # Netflix
            "com.zhiliaoapp.musically",        # TikTok
            "com.ss.android.ugc.trill",        # TikTok
            
            # 브라우저류
            "com.android.chrome",              # Chrome
            "com.sec.android.app.sbrowser",    # Samsung Internet
            
            # SNS류
            "com.instagram.android",           # Instagram
            "com.facebook.katana",             # Facebook
            "com.twitter.android",             # Twitter/X
        ]
        
        found_count = 0
        for app in kongsin_apps:
            if app in self.all_apps:
                self.checked_apps.add(app)
                found_count += 1
                
        if found_count > 0:
            self.filter_list() # 리스트 갱신 (체크상태 화면에 반영)
            self.update_selected_count_label()
            messagebox.showinfo("공신폰 모드 준비", f"스터디 방해 앱 {found_count}개를 자동으로 체크했습니다!\n\n이제 상단의 [🚫 비활성화] 버튼을 눌러주시면 폰에서 사라집니다.")
        else:
            messagebox.showwarning("알림", "폰에서 해당되는 방해 앱을 찾을 수 없습니다. (이미 없거나 비활성화 상태일 수 있습니다)")

    def select_delete_apps(self):
        # 완전 삭제가 필요한 삼성/구글 등 기본 잉여앱 목록
        delete_apps = [
            "com.samsung.android.bixby.wakeup",        # 빅스비
            "com.samsung.android.bixby.agent",         # 빅스비
            "com.samsung.android.bixby.visionapp",     # 빅스비 비전
            "com.samsung.android.arzone",              # AR 존
            "com.samsung.android.ardrawing",           # AR 두들
            "com.samsung.android.aremoji",             # AR 이모지
            "com.samsung.android.aremojieditor",       # AR 이모지
            "com.sec.android.mimage.avatarstickers",   # AR 이모지 스티커
            "com.google.android.gm",                   # Gmail
            "com.google.android.googlequicksearchbox", # Google
            "com.android.vending",                     # Google Play 스토어
            "com.google.android.apps.tachyon",         # Google Meet / Duo
            "com.google.android.apps.meetings",        # Google Meet
            "com.samsung.android.app.spage",           # Samsung Free
            "com.google.android.youtube",              # Youtube
            "com.google.android.apps.youtube.music"    # Youtube music
        ]
        
        found_count = 0
        for app in delete_apps:
            if app in self.all_apps:
                self.checked_apps.add(app)
                found_count += 1
                
        if found_count > 0:
            self.filter_list()
            self.update_selected_count_label()
            messagebox.showinfo("삭제 목록 준비", f"삼성/구글 기본 앱 {found_count}개를 찾아 체크했습니다!\n\n이제 [🗑 완전 삭제] 버튼을 누르시면 폰에서 언인스톨됩니다.")
        else:
            messagebox.showwarning("알림", "폰에서 삭제될 잉여 앱을 찾을 수 없습니다. (이미 지워진 폰일 수 있습니다)")

    def toggle_check(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            # 클릭한 영역이 체크박스 영역 근처일 때만 반응하도록 x좌표 체크 (옵션)
            app_name = self.tree.item(item, "values")[0]
            current_text = self.tree.item(item, "text")
            if current_text == "⬜":
                self.tree.item(item, text="✅", tags=("checked",))
                self.checked_apps.add(app_name)
            else:
                self.tree.item(item, text="⬜", tags=("unchecked",))
                self.checked_apps.discard(app_name)
            self.update_selected_count_label()

    def update_listbox(self, app_list):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for app in app_list:
            chk = "✅" if app in self.checked_apps else "⬜"
            tag = "checked" if app in self.checked_apps else "unchecked"
            self.tree.insert("", "end", text=chk, values=(app,), tags=(tag,))

    def filter_list(self, *args):
        search_term = self.search_var.get().lower()
        if search_term:
            filtered = [app for app in self.all_apps if search_term in app.lower()]
        else:
            filtered = self.all_apps
        self.update_listbox(filtered)

    def get_selected_apps(self):
        if not self.checked_apps:
            messagebox.showwarning("알림", "목록에서 앱을 최소 하나 이상 체크해주세요.")
            return []
        return list(self.checked_apps)

    def disable_app(self):
        pkgs = self.get_selected_apps()
        if not pkgs: return
        
        msg = f"선택한 {len(pkgs)}개의 앱을 비활성화 하시겠습니까?\n\n(스마트폰 화면과 동작에서 완전히 숨겨집니다)"
        if messagebox.askyesno("비활성화 확인", msg):
            success_count = 0
            fail_list = []
            
            for pkg in pkgs:
                result = run_adb_command(f"shell pm disable-user --user 0 {pkg}")
                if "disabled" in result.lower():
                    success_count += 1
                else:
                    fail_list.append(pkg)
            
            res_msg = f"비활성화 성공: {success_count}개\n"
            if fail_list:
                res_msg += f"실패: {len(fail_list)}개\n\n(권한이 부족한 기본 시스템 앱일 수 있습니다)"
                messagebox.showwarning("결과", res_msg)
            else:
                messagebox.showinfo("성공", res_msg + "\n모든 분 앱이 비활성화 되었습니다.")

    def enable_app(self):
        pkgs = self.get_selected_apps()
        if not pkgs: return
        
        msg = f"선택한 {len(pkgs)}개의 앱을 다시 활성화 하시겠습니까?"
        if messagebox.askyesno("활성화 확인", msg):
            success_count = 0
            fail_list = []
            
            for pkg in pkgs:
                result = run_adb_command(f"shell pm enable {pkg}")
                if "enabled" in result.lower():
                    success_count += 1
                else:
                    fail_list.append(pkg)
            
            res_msg = f"활성화 성공: {success_count}개\n"
            if fail_list:
                res_msg += f"실패: {len(fail_list)}개"
                messagebox.showwarning("결과", res_msg)
            else:
                messagebox.showinfo("성공", res_msg + "\n모든 앱이 활성화 되었습니다.")

    def delete_app(self):
        pkgs = self.get_selected_apps()
        if not pkgs: return
        
        msg = f"선택한 {len(pkgs)}개의 앱을 기기에서 **'완전 삭제(Uninstall)'** 하시겠습니까?\n\n(완전 삭제 시 폰을 공장 초기화하지 않는 이상 복구가 어려울 수 있습니다. 무조건 신중하게 진행하세요!)"
        if messagebox.askyesno("⚠️ 강력 경고: 완전 삭제 ⚠️", msg):
            success_count = 0
            fail_list = []
            
            for pkg in pkgs:
                # --user 0 으로 메인 유저에게서 완전 삭제 (시스템 앱 언인스톨 트릭)
                result = run_adb_command(f"shell pm uninstall -k --user 0 {pkg}")
                if "success" in result.lower():
                    success_count += 1
                else:
                    fail_list.append(pkg)
            
            res_msg = f"삭제 완료: {success_count}개\n"
            if fail_list:
                res_msg += f"실패: {len(fail_list)}개\n\n(시스템 보호용 핵심 앱이라 지울 수 없거나 이미 지워졌을 수 있습니다)"
                messagebox.showwarning("결과", res_msg)
            else:
                messagebox.showinfo("성공", res_msg + "\n성공적으로 앱이 삭제되었습니다.")
                
            # 삭제 직후 앱 리스트를 다시 불러와 화면 갱신
            self.load_apps()

    def restore_app(self):
        pkgs = self.get_selected_apps()
        if not pkgs: return
        
        msg = f"선택한 {len(pkgs)}개의 앱을 기기에서 **'완전 복원(Install existing)'** 하시겠습니까?\n\n(완전 삭제했던 기본 시스템 앱을 다시 설치합니다.)"
        if messagebox.askyesno("복원 확인", msg):
            success_count = 0
            fail_list = []
            
            for pkg in pkgs:
                # 삭제된 내부 시스템 앱을 현재 사용자에 맞게 다시 복구
                result = run_adb_command(f"shell cmd package install-existing {pkg}")
                if "installed" in result.lower() or "success" in result.lower():
                    success_count += 1
                else:
                    fail_list.append(pkg)
            
            res_msg = f"복원 완료: {success_count}개\n"
            if fail_list:
                res_msg += f"실패: {len(fail_list)}개\n\n(기본 내장이 아닌 사용자가 직접 설치했던 일반 앱은 이 기능으로 복구할 수 없습니다. 플레이스토어에서 다시 받아야 합니다.)"
                messagebox.showwarning("결과", res_msg)
            else:
                messagebox.showinfo("성공", res_msg + "\n선택한 앱이 원래대로 폰에 복원되었습니다.")
                
            # 복원 직후 앱 리스트 갱신
            self.load_apps()

if __name__ == "__main__":
    root = tk.Tk()
    app = AndroidAppManager(root)
    root.mainloop()
