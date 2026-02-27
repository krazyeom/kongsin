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
        self.root.geometry("500x600")
        
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

        self.btn_kongsin = ttk.Button(top_frame, text="🎓 공신폰 방해앱 자동선택", command=self.select_kongsin_apps)
        self.btn_kongsin.pack(side=tk.LEFT, padx=20)

        # 검색 영역
        search_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        search_frame.pack(fill=tk.X)
        ttk.Label(search_frame, text="앱 검색: ").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list) # 글자가 입력될 때마다 필터링
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 리스트 영역
        list_frame = ttk.Frame(root, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(list_frame, columns=("App",), show="tree", yscrollcommand=scrollbar.set, selectmode="none")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        style.configure("Treeview", rowheight=30, font=("Helvetica", 14))
        self.tree.column("#0", width=40, stretch=False, anchor="center")
        self.tree.column("App", stretch=True)
        self.tree.bind('<ButtonRelease-1>', self.toggle_check)

        self.all_apps = []
        self.checked_apps = set()

    def load_apps(self):
        output = run_adb_command("shell pm list packages")
        
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
        messagebox.showinfo("성공", f"총 {len(self.all_apps)}개의 앱을 불러왔습니다.")

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
            messagebox.showinfo("공신폰 모드 준비", f"스터디 방해 앱 {found_count}개를 자동으로 체크했습니다!\n\n이제 [🚫 비활성화] 버튼을 눌러주시면 폰에서 사라집니다.")
        else:
            messagebox.showwarning("알림", "폰에서 해당되는 방해 앱을 찾을 수 없습니다. (이미 없거나 비활성화 상태일 수 있습니다)")

    def toggle_check(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            # 클릭한 영역이 체크박스 영역 근처일 때만 반응하도록 x좌표 체크 (옵션)
            app_name = self.tree.item(item, "values")[0]
            current_text = self.tree.item(item, "text")
            if current_text == "☐":
                self.tree.item(item, text="☑")
                self.checked_apps.add(app_name)
            else:
                self.tree.item(item, text="☐")
                self.checked_apps.discard(app_name)

    def update_listbox(self, app_list):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for app in app_list:
            chk = "☑" if app in self.checked_apps else "☐"
            self.tree.insert("", "end", text=chk, values=(app,))

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

if __name__ == "__main__":
    root = tk.Tk()
    app = AndroidAppManager(root)
    root.mainloop()
