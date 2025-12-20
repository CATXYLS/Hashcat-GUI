import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import threading
import os
import sys
import time
import re
import json
import shutil
import webbrowser

# --- 语言包 ---
LANG = {
    "cn": {
        "title": "Hashcat Pro v29.0 (交互优化版)",
        "grp_env": " 1. 基础环境配置 ",
        "lbl_hc": "Hashcat路径:",
        "lbl_jtr": "JtR Run目录:",
        "lbl_perl": "Perl解释器:",
        "chk_perl": "强制使用内置环境(自动修复DLL)",
        "btn_browse": "浏览",
        "lbl_target": "目标压缩包:",
        "btn_target_load": "📂 浏览并检测",
        "lbl_mode": "Mode ID (自动):",
        "grp_hw": " 2. 硬件与性能 ",
        "lbl_dev": "运算设备(Beta):",
        "btn_refresh": "刷新",
        "lbl_work": "负载配置 (-w):",
        "hint_work": "<-- 7z跑得慢? 选High",
        "tab_brute": "  🔨 暴力破解  ",
        "tab_dict": "  📖 字典攻击  ",
        "grp_char": "字符组合",
        "chk_num": "数字 0-9",
        "chk_low": "小写 a-z",
        "chk_up": "大写 A-Z",
        "chk_sym": "符号",
        "chk_space": "[空格]",
        "chk_all": "[全部 ?a]",
        "grp_len": "长度范围",
        "chk_min": "设最小:",
        "chk_max": "设最大:",
        "hint_min": "<-- 不勾默认1",
        "hint_max": "<-- 不勾默认50",
        "lbl_pre": "前缀:",
        "lbl_suf": "后缀:",
        "btn_start": "🚀 启动破解",
        "btn_stop": "🛑 停止",
        "btn_hist": "📜 历史管理",
        "btn_clean": "🧹 清理Temp",
        "menu_file": "文件",
        "menu_lang": "语言 (Language)",
        "menu_help": "帮助 (Help)",
        "menu_about": "关于 (About)",
        "msg_no_file": "❌ 请先选择文件",
        "msg_success": "🎉 破解成功",
        "msg_found": "秒破成功",
        "chk_export": "生成 password.txt",
        "chk_history": "启用历史记录/缓存",
        "hist_title": "历史记录管理",
        "col_file": "文件名",
        "col_pwd": "密码",
        "col_hash": "哈希",
        "btn_del": "删除选中",
        "first_run_title": "⚠️ 郑重声明 (Disclaimer)",
        "first_run_msg": "这是一个免费开源的 GitHub 项目！\n\n如果您是通过购买（淘宝/闲鱼等）获得此工具，\n请立即申请退款并给予差评！\n\n拒绝倒卖，从我做起。",
        "about_desc": "免费开源工具，禁止倒卖。\nFree & Open Source."
    },
    "en": {
        "title": "Hashcat Pro v29.0 (Interactive)",
        "grp_env": " 1. Environment Setup ",
        "lbl_hc": "Hashcat Path:",
        "lbl_jtr": "JtR Run Path:",
        "lbl_perl": "Perl Path:",
        "chk_perl": "Force Built-in Env (Fix DLL)",
        "btn_browse": "Browse",
        "lbl_target": "Target Archive:",
        "btn_target_load": "📂 Browse & Detect",
        "lbl_mode": "Mode ID (Auto):",
        "grp_hw": " 2. Hardware & Performance ",
        "lbl_dev": "Device(Beta):",
        "btn_refresh": "Refresh",
        "lbl_work": "Workload (-w):",
        "hint_work": "<-- Slow on 7z? Pick High",
        "tab_brute": "  🔨 Brute Force  ",
        "tab_dict": "  📖 Dictionary  ",
        "grp_char": "Charset",
        "chk_num": "Digits 0-9",
        "chk_low": "Lower a-z",
        "chk_up": "Upper A-Z",
        "chk_sym": "Symbols",
        "chk_space": "[Space]",
        "chk_all": "[All ?a]",
        "grp_len": "Length Range",
        "chk_min": "Set Min:",
        "chk_max": "Set Max:",
        "hint_min": "<-- Default 1",
        "hint_max": "<-- Default 50",
        "lbl_pre": "Prefix:",
        "lbl_suf": "Suffix:",
        "btn_start": "🚀 Start Cracking",
        "btn_stop": "🛑 Stop",
        "btn_hist": "📜 History",
        "btn_clean": "🧹 Clean Temp",
        "menu_file": "File",
        "menu_lang": "Language",
        "menu_help": "Help",
        "menu_about": "About",
        "msg_no_file": "❌ Select a file first",
        "msg_success": "🎉 Cracked Successfully",
        "msg_found": "Found in History",
        "chk_export": "Export password.txt",
        "chk_history": "Enable History/Cache",
        "hist_title": "History Manager",
        "col_file": "Filename",
        "col_pwd": "Password",
        "col_hash": "Hash",
        "btn_del": "Delete Selected",
        "first_run_title": "⚠️ Disclaimer",
        "first_run_msg": "This is a FREE open-source GitHub project.\n\nIf you purchased this tool, please request a refund immediately and leave a negative review!\n\nDo not support resellers.",
        "about_desc": "Free & Open Source. Do not resell."
    }
}


class HashcatV29GUI:
    def __init__(self, root):
        self.root = root
        self.current_lang = "cn"

        # --- 路径核心 ---
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.temp_dir = os.path.join(self.base_dir, "temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        self.data_dir = os.path.join(self.base_dir, "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # 文件路径
        self.hash_file_path = os.path.join(self.temp_dir, "target.hash")
        self.cracked_file_path = os.path.join(self.temp_dir, "cracked_result.txt")
        self.mask_file_path = os.path.join(self.temp_dir, "job.hcmask")
        self.history_file_path = os.path.join(self.data_dir, "history.json")
        self.config_file_path = os.path.join(self.data_dir, "config.json")

        # --- 变量初始化 ---
        self.init_variables()

        # --- 加载配置 ---
        self.load_config()
        self.auto_detect_paths()

        # --- 构建 UI ---
        self.root.geometry("950x1000")
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        self.create_menu()
        self.rebuild_ui()

        self.root.after(500, self.scan_devices)
        self.root.after(800, self.check_first_run)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def init_variables(self):
        self.path_hashcat = tk.StringVar()
        self.path_jtr = tk.StringVar()
        self.path_perl = tk.StringVar()
        self.var_use_local_perl = tk.BooleanVar(value=True)

        self.path_archive = tk.StringVar()
        self.path_dictionary = tk.StringVar()
        self.hash_mode = tk.StringVar()

        self.var_prefix = tk.StringVar()
        self.var_suffix = tk.StringVar()
        self.var_use_min = tk.BooleanVar(value=False)
        self.var_use_max = tk.BooleanVar(value=True)
        self.var_min_len = tk.IntVar(value=4)
        self.var_max_len = tk.IntVar(value=8)

        self.var_digit = tk.BooleanVar(value=True)
        self.var_lower = tk.BooleanVar(value=False)
        self.var_upper = tk.BooleanVar(value=False)
        self.var_symbol = tk.BooleanVar(value=False)
        self.var_space = tk.BooleanVar(value=False)
        self.var_all = tk.BooleanVar(value=False)

        self.selected_device = tk.StringVar()
        self.workload_profile = tk.StringVar(value="3 - High (推荐)")

        self.var_enable_export = tk.BooleanVar(value=True)
        self.var_enable_history = tk.BooleanVar(value=True)

        self.is_first_run = True
        self.process = None
        self.stop_event = False

    def T(self, key):
        return LANG[self.current_lang].get(key, key)

    def switch_language(self, lang):
        self.current_lang = lang
        self.rebuild_ui()

    def rebuild_ui(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.root.title(self.T("title"))
        self.build_widgets(self.main_container)

    def create_menu(self):
        menubar = tk.Menu(self.root)

        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="中文 (Chinese)", command=lambda: self.switch_language("cn"))
        lang_menu.add_command(label="English", command=lambda: self.switch_language("en"))
        menubar.add_cascade(label="Language / 语言", menu=lang_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.T("menu_about"), command=self.show_about)
        menubar.add_cascade(label=self.T("menu_help"), menu=help_menu)

        self.root.config(menu=menubar)

    def build_widgets(self, parent):
        top = tk.LabelFrame(parent, text=self.T("grp_env"), padx=5, pady=5)
        top.pack(fill="x", padx=10, pady=5)

        self._create_path_row(top, self.T("lbl_hc"), self.path_hashcat, 0, "hashcat.exe")
        self._create_path_row(top, self.T("lbl_jtr"), self.path_jtr, 1, "dir")

        tk.Label(top, text=self.T("lbl_perl")).grid(row=2, column=0, sticky="e")
        pf = tk.Frame(top)
        pf.grid(row=2, column=1, sticky="w", padx=5)
        tk.Entry(pf, textvariable=self.path_perl, width=35).pack(side="left")
        tk.Checkbutton(pf, text=self.T("chk_perl"), variable=self.var_use_local_perl,
                       command=self.refresh_perl_path).pack(side="left", padx=5)
        tk.Button(top, text=self.T("btn_browse"), command=lambda: self.browse_file(self.path_perl, "perl.exe")).grid(
            row=2, column=2)

        tk.Label(top, text=self.T("lbl_target")).grid(row=3, column=0, sticky="e")
        tk.Entry(top, textvariable=self.path_archive, width=50).grid(row=3, column=1, padx=5, pady=2)
        tk.Button(top, text=self.T("btn_target_load"), bg="#87CEFA", command=self.select_archive).grid(row=3, column=2)

        act = tk.Frame(top)
        act.grid(row=4, column=1, sticky="w", pady=5)
        tk.Label(act, text=self.T("lbl_mode")).pack(side="left")
        tk.Entry(act, textvariable=self.hash_mode, width=10).pack(side="left", padx=5)

        hw = tk.LabelFrame(parent, text=self.T("grp_hw"), padx=5, pady=5, bg="#f0f8ff")
        hw.pack(fill="x", padx=10, pady=5)

        tk.Label(hw, text=self.T("lbl_dev"), bg="#f0f8ff").grid(row=0, column=0, sticky="e")
        self.combo_device = ttk.Combobox(hw, textvariable=self.selected_device, width=50, state="readonly")
        self.combo_device.grid(row=0, column=1, padx=5, sticky="w")
        tk.Button(hw, text=self.T("btn_refresh"), command=self.scan_devices).grid(row=0, column=2)

        tk.Label(hw, text=self.T("lbl_work"), bg="#f0f8ff").grid(row=1, column=0, sticky="e")
        self.combo_workload = ttk.Combobox(hw, textvariable=self.workload_profile, width=50, state="readonly")
        self.combo_workload['values'] = ("1 - Low", "2 - Default", "3 - High", "4 - Nightmare")
        self.combo_workload.grid(row=1, column=1, padx=5, sticky="w")
        tk.Label(hw, text=self.T("hint_work"), fg="red", bg="#f0f8ff").grid(row=1, column=2)

        tk.Label(hw, text="Options:", bg="#f0f8ff").grid(row=2, column=0, sticky="e")
        opt_frame = tk.Frame(hw, bg="#f0f8ff")
        opt_frame.grid(row=2, column=1, sticky="w", padx=5)
        tk.Checkbutton(opt_frame, text=self.T("chk_export"), variable=self.var_enable_export, bg="#f0f8ff").pack(
            side="left")
        tk.Checkbutton(opt_frame, text=self.T("chk_history"), variable=self.var_enable_history, bg="#f0f8ff").pack(
            side="left", padx=10)

        nb = ttk.Notebook(parent)
        nb.pack(fill="x", padx=10, pady=5)
        self.tab_brute = tk.Frame(nb, pady=10)
        nb.add(self.tab_brute, text=self.T("tab_brute"))
        self._build_brute_tab(self.tab_brute)
        self.tab_dict = tk.Frame(nb, pady=10)
        nb.add(self.tab_dict, text=self.T("tab_dict"))
        self._build_dict_tab(self.tab_dict)

        bf = tk.Frame(parent)
        bf.pack(pady=5)
        self.btn_start = tk.Button(bf, text=self.T("btn_start"), bg="#32CD32", fg="white", width=15,
                                   font=("Arial", 11, "bold"), command=self.start_dispatch)
        self.btn_start.pack(side="left", padx=10)
        self.btn_stop = tk.Button(bf, text=self.T("btn_stop"), bg="#CD5C5C", fg="white", width=10, font=("Arial", 11),
                                  command=self.stop_cracking, state="disabled")
        self.btn_stop.pack(side="left", padx=10)
        tk.Button(bf, text=self.T("btn_hist"), bg="#FFD700", command=self.show_history_manager).pack(side="left",
                                                                                                     padx=10)
        tk.Button(bf, text=self.T("btn_clean"), command=self.clear_temp).pack(side="right", padx=10)

        self.log_area = scrolledtext.ScrolledText(parent, height=12, bg="#2b2b2b", fg="#00FF00", font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def _create_path_row(self, p, l, v, r, t):
        tk.Label(p, text=l).grid(row=r, column=0, sticky="e")
        tk.Entry(p, textvariable=v, width=50).grid(row=r, column=1, padx=5, pady=2)
        cmd = lambda: self.browse_folder(v) if t == "dir" else self.browse_file(v, t)
        tk.Button(p, text=self.T("btn_browse"), command=cmd).grid(row=r, column=2)

    def _build_brute_tab(self, f):
        cf = tk.LabelFrame(f, text=self.T("grp_char"), padx=5)
        cf.pack(fill="x", padx=10)
        r1 = tk.Frame(cf)
        r1.pack(anchor="w")
        tk.Checkbutton(r1, text=self.T("chk_num"), variable=self.var_digit).pack(side="left")
        tk.Checkbutton(r1, text=self.T("chk_low"), variable=self.var_lower).pack(side="left")
        tk.Checkbutton(r1, text=self.T("chk_up"), variable=self.var_upper).pack(side="left")
        tk.Checkbutton(r1, text=self.T("chk_sym"), variable=self.var_symbol).pack(side="left")
        r2 = tk.Frame(cf)
        r2.pack(anchor="w", pady=5)
        tk.Checkbutton(r2, text=self.T("chk_space"), variable=self.var_space, fg="blue").pack(side="left")
        tk.Checkbutton(r2, text=self.T("chk_all"), variable=self.var_all, fg="red").pack(side="left", padx=10)

        lf = tk.LabelFrame(f, text=self.T("grp_len"), padx=5, pady=5)
        lf.pack(fill="x", padx=10, pady=5)
        tk.Checkbutton(lf, text=self.T("chk_min"), variable=self.var_use_min, command=self.update_len).grid(row=0,
                                                                                                            column=0)
        self.spin_min = tk.Spinbox(lf, from_=1, to=50, textvariable=self.var_min_len, width=5)
        self.spin_min.grid(row=0, column=1)
        tk.Label(lf, text=self.T("hint_min")).grid(row=0, column=2, padx=5)

        tk.Checkbutton(lf, text=self.T("chk_max"), variable=self.var_use_max, command=self.update_len).grid(row=1,
                                                                                                            column=0)
        self.spin_max = tk.Spinbox(lf, from_=1, to=50, textvariable=self.var_max_len, width=5)
        self.spin_max.grid(row=1, column=1)
        tk.Label(lf, text=self.T("hint_max")).grid(row=1, column=2, padx=5)

        tk.Label(lf, text=self.T("lbl_pre")).grid(row=0, column=3, padx=10)
        tk.Entry(lf, textvariable=self.var_prefix, width=10).grid(row=0, column=4)
        tk.Label(lf, text=self.T("lbl_suf")).grid(row=1, column=3, padx=10)
        tk.Entry(lf, textvariable=self.var_suffix, width=10).grid(row=1, column=4)
        self.update_len()

    def _build_dict_tab(self, f):
        tk.Entry(f, textvariable=self.path_dictionary, width=50).pack(side="left", padx=10)
        tk.Button(f, text=self.T("btn_browse"), command=lambda: self.browse_file(self.path_dictionary, "*.txt")).pack(
            side="left")

    def load_config(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.current_lang = cfg.get("lang", "cn")
                    self.path_hashcat.set(cfg.get("path_hc", ""))
                    self.path_jtr.set(cfg.get("path_jtr", ""))
                    self.path_perl.set(cfg.get("path_perl", ""))
                    self.var_use_local_perl.set(cfg.get("use_local_perl", True))
                    self.var_enable_export.set(cfg.get("enable_export", True))
                    self.var_enable_history.set(cfg.get("enable_history", True))
                    self.is_first_run = cfg.get("is_first_run", True)
            except:
                pass

    def save_config(self):
        cfg = {
            "lang": self.current_lang,
            "path_hc": self.path_hashcat.get(),
            "path_jtr": self.path_jtr.get(),
            "path_perl": self.path_perl.get(),
            "use_local_perl": self.var_use_local_perl.get(),
            "enable_export": self.var_enable_export.get(),
            "enable_history": self.var_enable_history.get(),
            "is_first_run": self.is_first_run
        }
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except:
            pass

    def on_close(self):
        self.save_config()
        self.root.destroy()

    def check_first_run(self):
        if self.is_first_run:
            messagebox.showwarning(self.T("first_run_title"), self.T("first_run_msg"))
            self.is_first_run = False
            self.save_config()

    def show_about(self):
        # 创建自定义弹窗
        about_win = tk.Toplevel(self.root)
        about_win.title(self.T("menu_about"))
        about_win.geometry("420x250")
        about_win.resizable(False, False)

        # 居中显示
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 125
        about_win.geometry(f"+{x}+{y}")

        # 文本信息
        txt_info = f"Version: v29.0 Final\nAuthor: CATXYLS\nProject: HashcatGUI\n\n{self.T('about_desc')}"
        tk.Label(about_win, text=txt_info, font=("Arial", 10), justify="center").pack(pady=20)

        # 蓝色高亮链接
        url = "https://github.com/CATXYLS/Hashcat-GUI"
        link_lbl = tk.Label(about_win, text=url, fg="blue", cursor="hand2", font=("Arial", 10, "underline"))
        link_lbl.pack(pady=5)

        # 绑定点击事件
        link_lbl.bind("<Button-1>", lambda e: webbrowser.open(url))

        # 确定按钮
        tk.Button(about_win, text="OK", width=10, command=about_win.destroy).pack(pady=20)

    def auto_detect_paths(self):
        if not self.path_hashcat.get():
            hc = os.path.join(self.base_dir, "hashcat", "hashcat.exe")
            if os.path.exists(hc):
                self.path_hashcat.set(hc)
        if not self.path_jtr.get():
            jr = os.path.join(self.base_dir, "john", "run")
            if os.path.exists(jr):
                self.path_jtr.set(jr)
        if not self.path_perl.get():
            self.refresh_perl_path()

    def refresh_perl_path(self):
        if self.var_use_local_perl.get():
            found_perl = self.find_file_recursive(self.base_dir, "perl.exe")
            if found_perl:
                self.path_perl.set(found_perl)
            else:
                self.path_perl.set("")
        else:
            sys_perl = shutil.which("perl")
            if sys_perl:
                self.path_perl.set(sys_perl)
            else:
                self.path_perl.set("")

    def find_file_recursive(self, root_dir, target_name):
        exclude_dirs = ["temp", "data", "hashcat", "john"]
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            if target_name in files:
                return os.path.join(root, target_name)
        return None

    def update_len(self):
        if self.var_use_min.get():
            self.spin_min.config(state="normal")
        else:
            self.spin_min.config(state="disabled")

        if self.var_use_max.get():
            self.spin_max.config(state="normal")
        else:
            self.spin_max.config(state="disabled")

    def select_archive(self):
        f = filedialog.askopenfilename(filetypes=[("Archives", "*.zip;*.rar;*.7z"), ("All", "*.*")])
        if f:
            self.path_archive.set(f)
            self.log("-" * 40)
            self.log(f"📂 {os.path.basename(f)}")
            self.log("⏳ ...")
            threading.Thread(target=self.process_archive_and_check_history, daemon=True).start()

    def process_archive_internal(self):
        path = self.path_archive.get()
        jtr_path = self.path_jtr.get()
        perl_path = self.path_perl.get()
        if not path or not jtr_path:
            return False

        ext = os.path.splitext(path)[1].lower()
        cmd = []
        env = os.environ.copy()

        if ext == ".7z":
            if not perl_path or not os.path.exists(perl_path):
                self.log("❌ Perl Error")
                return False
            pl = os.path.join(jtr_path, "7z2john.pl")
            if not os.path.exists(pl):
                self.log("❌ 7z2john.pl Missing")
                return False

            if self.var_use_local_perl.get():
                self.log(f"🔧 Perl: {perl_path}")
                dll_path = self.find_file_recursive(self.base_dir, "liblzma-5.dll")
                if dll_path:
                    d_dir = os.path.dirname(dll_path)
                    env["PATH"] = d_dir + os.pathsep + env["PATH"]
            cmd = [perl_path, pl, path]
        else:
            tool = "zip2john.exe" if ext == ".zip" else "rar2john.exe"
            full = os.path.join(jtr_path, tool)
            if not os.path.exists(full):
                return False
            cmd = [full, path]

        try:
            cf = 0x08000000 if os.name == 'nt' else 0
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=cf,
                                 errors='ignore', env=env)
            out, err = p.communicate()
            if out:
                raw = out.strip()
                final = raw
                if "$pkzip2$" in raw:
                    final = raw[raw.find("$pkzip2$"):]
                elif "$zip2$" in raw:
                    final = raw[raw.find("$zip2$"):]
                elif "$rar5$" in raw:
                    final = raw[raw.find("$rar5$"):]
                elif "$7z$" in raw:
                    final = raw[raw.find("$7z$"):]

                if not any(k in final for k in ["$pkzip2$", "$zip2$", "$rar5$", "$7z$"]):
                    return False

                with open(self.hash_file_path, "w", encoding="utf-8") as f:
                    f.write(final)
                self.log("✅ OK")
                if "$pkzip2$" in final:
                    self.hash_mode.set("17200")
                elif "$zip2$" in final:
                    self.hash_mode.set("13600")
                elif "$rar5$" in final:
                    self.hash_mode.set("13000")
                elif "$7z$" in final:
                    self.hash_mode.set("11600")
                return True
            else:
                return False
        except:
            return False

    def process_archive_and_check_history(self):
        if self.process_archive_internal():
            if not self.var_enable_history.get():
                return
            try:
                with open(self.hash_file_path, "r", encoding="utf-8") as f:
                    h = f.read().strip()
                hist = self.load_history()
                if h in hist:
                    d = hist[h]
                    p = d.get("pwd", "?")
                    f = d.get("file", "?")
                    self.log(f"⚡ {self.T('msg_found')}: {f} -> {p}")
                    self.create_password_txt(p)
                    messagebox.showinfo("Success", p)
            except:
                pass

    def start_dispatch(self):
        if not os.path.exists(self.hash_file_path):
            self.log(self.T("msg_no_file"))
            return
        if os.path.exists(self.cracked_file_path):
            try:
                os.remove(self.cracked_file_path)
            except:
                pass
        self.stop_event = False
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        threading.Thread(target=self.run_brute_maskfile, daemon=True).start()

    def run_brute_maskfile(self):
        # 熔断机制：无论发生什么错误，finally 块都会重置按钮
        try:
            charset = ""
            if self.var_all.get():
                charset = "?a " if self.var_space.get() else "?a"
            else:
                if self.var_digit.get(): charset += "?d"
                if self.var_lower.get(): charset += "?l"
                if self.var_upper.get(): charset += "?u"
                if self.var_symbol.get(): charset += "?s"
                if self.var_space.get(): charset += " "

            if not charset:
                self.log("❌ 未选字符集")
                return

            min_l = self.var_min_len.get() if self.var_use_min.get() else 1
            max_l = self.var_max_len.get() if self.var_use_max.get() else 50
            prefix = self.var_prefix.get()
            suffix = self.var_suffix.get()

            self.log(f"📝 Gen Task ({min_l}-{max_l})...")
            try:
                with open(self.mask_file_path, "w", encoding="utf-8") as f:
                    for l in range(min_l, max_l + 1):
                        f.write(f"{charset},{prefix + ('?1' * l) + suffix}\n")
            except Exception as e:
                self.log(f"❌ Error: {e}")
                return

            dev = []
            if "Device #" in self.selected_device.get():
                m = re.search(r"Device #(\d+)", self.selected_device.get())
                if m:
                    dev = ["-d", m.group(1)]

            w_profile = self.workload_profile.get().split(" ")[0] if self.workload_profile.get() else "2"
            hc = self.path_hashcat.get()
            cwd = os.path.dirname(hc)

            cmd = [hc, "-m", self.hash_mode.get(), "-a", "3", self.hash_file_path, self.mask_file_path,
                   "--outfile", self.cracked_file_path, "--status", "--status-timer", "5",
                   "--force", "--hwmon-disable", "--potfile-disable", "-w", w_profile] + dev

            self.log("🚀 Start Hashcat...")
            self.run_subprocess(cmd, cwd)
            self.check_success()
            self.log("🏁 Finish")

        finally:
            self.reset_ui()

    def run_subprocess(self, cmd, cwd):
        try:
            cf = 0x08000000 if os.name == 'nt' else 0
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                            creationflags=cf, cwd=cwd)
            for line in self.process.stdout:
                if self.stop_event:
                    self.process.terminate()
                    break
                ls = line.strip()
                if ls and "Initializing" not in ls:
                    self.log(ls)
            self.process.wait()
        except:
            pass

    def check_success(self):
        if os.path.exists(self.cracked_file_path) and os.path.getsize(self.cracked_file_path) > 0:
            try:
                with open(self.cracked_file_path, "r") as f:
                    c = f.read().strip()
                if ":" in c or len(c) > 0:
                    pwd = c.split(":")[-1] if ":" in c else c
                    self.log(f"🎉 {self.T('msg_success')}: {pwd}")
                    self.create_password_txt(pwd)
                    if self.var_enable_history.get():
                        with open(self.hash_file_path, "r") as f:
                            h = f.read().strip()
                        self.add_history_entry(h, pwd)
                    messagebox.showinfo("Success", pwd)
                    self.stop_event = True
                    return True
            except:
                pass
        return False

    def create_password_txt(self, pwd):
        if not self.var_enable_export.get():
            return
        try:
            p = self.path_archive.get()
            if p:
                f = os.path.join(os.path.dirname(p), "password.txt")
                with open(f, "w", encoding="utf-8") as file:
                    file.write(f"File: {os.path.basename(p)}\nPassword: {pwd}\nTime: {time.ctime()}")
        except:
            pass

    def load_history(self):
        if os.path.exists(self.history_file_path):
            try:
                with open(self.history_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def add_history_entry(self, hash_val, password):
        data = self.load_history()
        data[hash_val] = {
            "pwd": password,
            "file": os.path.basename(self.path_archive.get()),
            "time": time.strftime("%Y-%m-%d %H:%M")
        }
        self.save_history(data)

    def save_history(self, data):
        try:
            with open(self.history_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def show_history_manager(self):
        data = self.load_history()
        win = tk.Toplevel(self.root)
        win.title(self.T("hist_title"))
        win.geometry("800x500")
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=("file", "pwd", "hash"), show="headings")
        tree.pack(fill="both", expand=True)
        tree.heading("file", text=self.T("col_file"))
        tree.heading("pwd", text=self.T("col_pwd"))
        tree.heading("hash", text=self.T("col_hash"))
        item_map = {}
        for h, v in data.items():
            p = v.get("pwd") if isinstance(v, dict) else v
            f = v.get("file") if isinstance(v, dict) else "Old"
            iid = tree.insert("", "end", values=(f, p, h[:50]))
            item_map[iid] = h

        def delete():
            for i in tree.selection():
                if item_map[i] in data:
                    del data[item_map[i]]
                tree.delete(i)
            self.save_history(data)

        tk.Button(win, text=self.T("btn_del"), command=delete).pack()

    def clear_temp(self):
        try:
            for f in os.listdir(self.temp_dir):
                fp = os.path.join(self.temp_dir, f)
                if os.path.isfile(fp):
                    os.remove(fp)
            self.log("🧹 Cleaned")
        except:
            pass

    def scan_devices(self):
        hc = self.path_hashcat.get()
        if not hc or not os.path.exists(hc):
            return

        def _scan():
            try:
                cwd = os.path.dirname(hc)
                p = subprocess.Popen([hc, "-I"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                     creationflags=0x08000000, cwd=cwd)
                out, _ = p.communicate()
                devs = ["Default"]
                matches = re.findall(r"Device\s*#\s*(\d+):\s*(.+)", out)
                for i, n in matches:
                    devs.append(f"Device #{i}: {n.strip()}")
                self.root.after(0, lambda: self.combo_device.config(values=devs))
                if len(devs) > 1:
                    self.root.after(0, lambda: self.combo_device.current(1))
            except:
                pass

        threading.Thread(target=_scan, daemon=True).start()

    def stop_cracking(self):
        self.stop_event = True
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
        self.log("🛑 停止")

    def reset_ui(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")

    def browse_file(self, v, p):
        f = filedialog.askopenfilename(filetypes=[("Files", p), ("All", "*.*")])
        if f:
            v.set(f)

    def browse_folder(self, v):
        d = filedialog.askdirectory()
        if d:
            v.set(d)

    def log(self, t):
        self.log_area.insert(tk.END, t + "\n")
        self.log_area.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = HashcatV29GUI(root)
    root.mainloop()
