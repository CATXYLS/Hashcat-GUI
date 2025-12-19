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


class HashcatFinalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hashcat GUI")#catxyls
        self.root.geometry("950x1000")

        # --- 1. 路径核心 ---
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # --- 2. 文件夹初始化 ---
        self.temp_dir = os.path.join(self.base_dir, "temp")
        if not os.path.exists(self.temp_dir): os.makedirs(self.temp_dir)

        self.data_dir = os.path.join(self.base_dir, "data")
        if not os.path.exists(self.data_dir): os.makedirs(self.data_dir)

        # --- 3. 路径变量 ---
        self.hash_file_path = os.path.join(self.temp_dir, "target.hash")
        self.cracked_file_path = os.path.join(self.temp_dir, "cracked_result.txt")
        self.history_file_path = os.path.join(self.data_dir, "history.json")

        # --- UI 绑定变量 ---
        self.path_hashcat = tk.StringVar()
        self.path_jtr = tk.StringVar()
        self.path_perl = tk.StringVar()

        # 默认勾选：自动搜索并注入依赖
        self.var_use_local_perl = tk.BooleanVar(value=True)

        self.path_archive = tk.StringVar()
        self.path_dictionary = tk.StringVar()
        self.hash_mode = tk.StringVar()

        # 爆破参数
        self.var_prefix = tk.StringVar()
        self.var_suffix = tk.StringVar()
        self.var_use_min = tk.BooleanVar(value=False)
        self.var_use_max = tk.BooleanVar(value=True)
        self.var_min_len = tk.IntVar(value=4)
        self.var_max_len = tk.IntVar(value=8)

        # 字符集
        self.var_digit = tk.BooleanVar(value=True)
        self.var_lower = tk.BooleanVar(value=False)
        self.var_upper = tk.BooleanVar(value=False)
        self.var_symbol = tk.BooleanVar(value=False)
        self.var_space = tk.BooleanVar(value=False)
        self.var_all = tk.BooleanVar(value=False)

        self.selected_device = tk.StringVar()
        self.process = None
        self.stop_event = False

        self.create_ui()
        self.auto_detect_paths()
        self.root.after(500, self.scan_devices)

    def auto_detect_paths(self):
        # 1. Hashcat
        hc = os.path.join(self.base_dir, "hashcat", "hashcat.exe")
        if os.path.exists(hc): self.path_hashcat.set(hc)

        # 2. JtR
        jr = os.path.join(self.base_dir, "john", "run")
        if os.path.exists(jr): self.path_jtr.set(jr)

        # 3. Perl (智能检测)
        self.refresh_perl_path()

    def refresh_perl_path(self):
        """根据用户选择切换 Perl 路径"""
        if self.var_use_local_perl.get():
            # 搜索本地 perl.exe
            found_perl = self.find_file_recursive(self.base_dir, "perl.exe")
            if found_perl:
                self.path_perl.set(found_perl)
            else:
                self.path_perl.set("")  # 未找到
        else:
            # 使用系统环境
            sys_perl = shutil.which("perl")
            if sys_perl:
                self.path_perl.set(sys_perl)
            else:
                self.path_perl.set("")

    def find_file_recursive(self, root_dir, target_name):
        """递归查找文件 (排除无关目录以提速)"""
        exclude_dirs = ["temp", "data", "hashcat", "john"]  # 排除已知不含perl的目录
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            if target_name in files:
                return os.path.join(root, target_name)
        return None

    def create_ui(self):
        # 1. 基础配置
        top = tk.LabelFrame(self.root, text=" 1. 基础环境配置 ", padx=5, pady=5)
        top.pack(fill="x", padx=10, pady=5)

        self.create_row(top, "Hashcat路径:", self.path_hashcat, 0, "exe")
        self.create_row(top, "JtR Run目录:", self.path_jtr, 1, "dir")

        tk.Label(top, text="Perl解释器:").grid(row=2, column=0, sticky="e")
        pf = tk.Frame(top)
        pf.grid(row=2, column=1, sticky="w", padx=5)
        tk.Entry(pf, textvariable=self.path_perl, width=35).pack(side="left")
        tk.Checkbutton(pf, text="强制使用内置环境(自动修复DLL)", variable=self.var_use_local_perl,
                       command=self.refresh_perl_path).pack(side="left", padx=5)
        tk.Button(top, text="浏览", command=lambda: self.browse_file(self.path_perl, "perl.exe")).grid(row=2, column=2)

        tk.Label(top, text="目标压缩包:").grid(row=3, column=0, sticky="e")
        tk.Entry(top, textvariable=self.path_archive, width=50).grid(row=3, column=1, padx=5, pady=2)
        tk.Button(top, text="📂 浏览并检测", bg="#87CEFA", command=self.select_archive).grid(row=3, column=2)

        act = tk.Frame(top)
        act.grid(row=4, column=1, sticky="w", pady=5)
        tk.Label(act, text="Mode ID (自动):").pack(side="left")
        tk.Entry(act, textvariable=self.hash_mode, width=10).pack(side="left", padx=5)

        # 2. 硬件
        hw = tk.LabelFrame(self.root, text=" 2. 硬件选择(Beta) ", padx=5, pady=5, bg="#f0f8ff")
        hw.pack(fill="x", padx=10, pady=5)
        tk.Label(hw, text="运算设备:", bg="#f0f8ff").grid(row=0, column=0, sticky="e")
        self.combo_device = ttk.Combobox(hw, textvariable=self.selected_device, width=60, state="readonly")
        self.combo_device.grid(row=0, column=1, padx=5)
        tk.Button(hw, text="刷新", command=self.scan_devices).grid(row=0, column=2)

        # 3. 模式
        nb = ttk.Notebook(self.root)
        nb.pack(fill="x", padx=10, pady=5)
        self.tab_brute = tk.Frame(nb, pady=10);
        nb.add(self.tab_brute, text="  🔨 暴力破解  ")
        self.create_brute_tab()
        self.tab_dict = tk.Frame(nb, pady=10);
        nb.add(self.tab_dict, text="  📖 字典攻击  ")
        self.create_dict_tab()

        # 4. 控制台
        bf = tk.Frame(self.root)
        bf.pack(pady=5)
        self.btn_start = tk.Button(bf, text="🚀 启动破解", bg="#32CD32", fg="white", width=15,
                                   font=("Arial", 11, "bold"), command=self.start_dispatch)
        self.btn_start.pack(side="left", padx=10)
        self.btn_stop = tk.Button(bf, text="🛑 停止", bg="#CD5C5C", fg="white", width=10, font=("Arial", 11),
                                  command=self.stop_cracking, state="disabled")
        self.btn_stop.pack(side="left", padx=10)
        tk.Button(bf, text="📜 历史记录", bg="#FFD700", command=self.show_history_manager).pack(side="left", padx=10)
        tk.Button(bf, text="🧹 清理Temp", command=self.clear_temp).pack(side="right", padx=10)

        self.log_area = scrolledtext.ScrolledText(self.root, height=12, bg="#2b2b2b", fg="#00FF00",
                                                  font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def create_row(self, p, l, v, r, t):
        tk.Label(p, text=l).grid(row=r, column=0, sticky="e")
        tk.Entry(p, textvariable=v, width=50).grid(row=r, column=1, padx=5, pady=2)
        if t == "dir":
            cmd = lambda: self.browse_folder(v)
        else:
            cmd = lambda: self.browse_file(v, "hashcat.exe")
        tk.Button(p, text="浏览", command=cmd).grid(row=r, column=2)

    def create_brute_tab(self):
        f = self.tab_brute
        cf = tk.LabelFrame(f, text="字符组合", padx=5)
        cf.pack(fill="x", padx=10)
        r1 = tk.Frame(cf);
        r1.pack(anchor="w")
        tk.Checkbutton(r1, text="数字 (0-9)", variable=self.var_digit).pack(side="left")
        tk.Checkbutton(r1, text="小写 (a-z)", variable=self.var_lower).pack(side="left")
        tk.Checkbutton(r1, text="大写 (A-Z)", variable=self.var_upper).pack(side="left")
        tk.Checkbutton(r1, text="符号", variable=self.var_symbol).pack(side="left")
        r2 = tk.Frame(cf);
        r2.pack(anchor="w", pady=5)
        tk.Checkbutton(r2, text="[空格]", variable=self.var_space, fg="blue").pack(side="left")
        tk.Checkbutton(r2, text="[全部 ?a]", variable=self.var_all, fg="red").pack(side="left", padx=10)

        lf = tk.LabelFrame(f, text="长度范围", padx=5, pady=5)
        lf.pack(fill="x", padx=10, pady=5)
        tk.Checkbutton(lf, text="设最小:", variable=self.var_use_min, command=self.update_len).grid(row=0, column=0)
        self.spin_min = tk.Spinbox(lf, from_=1, to=50, textvariable=self.var_min_len, width=5)
        self.spin_min.grid(row=0, column=1)
        tk.Label(lf, text="<-- 不勾默认1").grid(row=0, column=2, padx=5)
        tk.Checkbutton(lf, text="设最大:", variable=self.var_use_max, command=self.update_len).grid(row=1, column=0)
        self.spin_max = tk.Spinbox(lf, from_=1, to=50, textvariable=self.var_max_len, width=5)
        self.spin_max.grid(row=1, column=1)
        tk.Label(lf, text="<-- 不勾默认50").grid(row=1, column=2, padx=5)
        tk.Label(lf, text="前缀:").grid(row=0, column=3, padx=10)
        tk.Entry(lf, textvariable=self.var_prefix, width=10).grid(row=0, column=4)
        tk.Label(lf, text="后缀:").grid(row=1, column=3, padx=10)
        tk.Entry(lf, textvariable=self.var_suffix, width=10).grid(row=1, column=4)
        self.update_len()

    def create_dict_tab(self):
        f = self.tab_dict
        tk.Entry(f, textvariable=self.path_dictionary, width=50).pack(side="left", padx=10)
        tk.Button(f, text="浏览", command=lambda: self.browse_file(self.path_dictionary, "*.txt")).pack(side="left")

    def update_len(self):
        self.spin_min.config(state="normal" if self.var_use_min.get() else "disabled")
        self.spin_max.config(state="normal" if self.var_use_max.get() else "disabled")

    def select_archive(self):
        f = filedialog.askopenfilename(filetypes=[("Archives", "*.zip;*.rar;*.7z"), ("All", "*.*")])
        if f:
            self.path_archive.set(f)
            self.log("-" * 40)
            self.log(f"📂 已选择: {os.path.basename(f)}")
            self.log("⏳ 后台提取中...")
            threading.Thread(target=self.process_archive_and_check_history, daemon=True).start()

    # --- 核心：提取逻辑 (全盘搜索 DLL) ---
    def process_archive_internal(self):
        path = self.path_archive.get()
        jtr_path = self.path_jtr.get()
        perl_path = self.path_perl.get()

        if not path or not jtr_path:
            self.log("⚠️ 请配置 JtR 路径")
            return False

        ext = os.path.splitext(path)[1].lower()
        cmd = []
        my_env = os.environ.copy()

        # 1. Perl 模式 (.7z)
        if ext == ".7z":
            if not perl_path or not os.path.exists(perl_path):
                self.log("❌ 错误: Perl 路径无效");
                return False

            pl_script = os.path.join(jtr_path, "7z2john.pl")
            if not os.path.exists(pl_script): self.log("❌ 错误: 找不到 7z2john.pl"); return False

            # --- 智能 DLL 注入 (全局搜索) ---
            if self.var_use_local_perl.get():
                self.log(f"🔧 准备调用 Perl: {perl_path}")

                # 目标：找到 liblzma-5.dll
                target_dll = "liblzma-5.dll"

                # 从 base_dir (软件根目录) 开始地毯式搜索
                # 优先在 perl 目录搜，搜不到再搜全盘
                perl_root = os.path.dirname(os.path.dirname(perl_path))  # ../perl/bin -> ../perl
                dll_full_path = self.find_file_recursive(perl_root, target_dll)
                if not dll_full_path:
                    self.log(f"🔍 扩展搜索范围至根目录...")
                    dll_full_path = self.find_file_recursive(self.base_dir, target_dll)

                if dll_full_path:
                    dll_dir = os.path.dirname(dll_full_path)
                    self.log(f"✅ 找到依赖库于: {dll_dir}")
                    # 注入环境变量
                    my_env["PATH"] = dll_dir + os.pathsep + my_env["PATH"]
                else:
                    self.log("⚠️ 警告: 全盘搜索未找到 liblzma-5.dll！")

            cmd = [perl_path, pl_script, path]
        else:
            tool = "zip2john.exe" if ext == ".zip" else "rar2john.exe"
            full = os.path.join(jtr_path, tool)
            if not os.path.exists(full): self.log(f"❌ 找不到: {tool}"); return False
            cmd = [full, path]

        try:
            cflags = 0x08000000 if os.name == 'nt' else 0
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=cflags,
                                 errors='ignore', env=my_env)
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
                    self.log(f"⚠️ 提取无效:\n{out[:100]}...")
                    if err: self.log(f"ERR: {err}")
                    return False

                with open(self.hash_file_path, "w", encoding="utf-8") as f:
                    f.write(final)
                self.log("✅ 哈希提取成功")
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
                self.log(f"❌ 提取失败: {err}");
                return False
        except Exception as e:
            self.log(f"运行出错: {e}");
            return False

    def process_archive_and_check_history(self):
        success = self.process_archive_internal()
        if not success: return
        try:
            with open(self.hash_file_path, "r", encoding="utf-8") as f:
                current_hash = f.read().strip()
            history = self.load_history()
            if current_hash in history:
                data = history[current_hash]
                pwd = data.get("pwd", "???")
                old_file = data.get("file", "未知")
                self.log(f"⚡ 命中历史! {old_file}")
                self.log(f"✅ 密码: {pwd}")
                self.create_password_txt(pwd)
                messagebox.showinfo("秒破", f"发现历史记录\n密码: {pwd}")
            else:
                self.log("暂无记录，请启动。")
        except:
            pass

    # --- 通用函数 ---
    def load_history(self):
        if os.path.exists(self.history_file_path):
            try:
                with open(self.history_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_history(self, data):
        try:
            with open(self.history_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add_history_entry(self, hash_val, password):
        data = self.load_history()
        data[hash_val] = {"pwd": password, "file": os.path.basename(self.path_archive.get()),
                          "time": time.strftime("%Y-%m-%d %H:%M")}
        self.save_history(data)

    def show_history_manager(self):
        data = self.load_history()
        win = tk.Toplevel(self.root);
        win.title(f"历史 ({len(data)})");
        win.geometry("800x500")
        frame = tk.Frame(win);
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=("file", "pwd", "hash"), show="headings");
        tree.pack(fill="both", expand=True)
        tree.heading("file", text="文件");
        tree.heading("pwd", text="密码");
        tree.heading("hash", text="哈希")
        item_map = {}
        for h, v in data.items():
            p = v.get("pwd") if isinstance(v, dict) else v
            f = v.get("file") if isinstance(v, dict) else "Old"
            iid = tree.insert("", "end", values=(f, p, h[:50]))
            item_map[iid] = h

        def delete():
            for i in tree.selection():
                if item_map[i] in data: del data[item_map[i]]
                tree.delete(i)
            self.save_history(data)

        tk.Button(win, text="删除选中", command=delete).pack()

    def start_dispatch(self):
        if not os.path.exists(self.hash_file_path): self.log("❌ 请先选文件"); return
        if os.path.exists(self.cracked_file_path):
            try:
                os.remove(self.cracked_file_path)
            except:
                pass
        self.stop_event = False;
        self.btn_start.config(state="disabled");
        self.btn_stop.config(state="normal")
        threading.Thread(target=self.run_brute, daemon=True).start()

    def run_brute(self):
        charset = ""
        if self.var_all.get():
            charset = "?a " if self.var_space.get() else "?a"
        else:
            if self.var_digit.get(): charset += "?d"
            if self.var_lower.get(): charset += "?l"
            if self.var_upper.get(): charset += "?u"
            if self.var_symbol.get(): charset += "?s"
            if self.var_space.get(): charset += " "
        if not charset: self.reset_ui(); return
        s = self.var_min_len.get() if self.var_use_min.get() else 1
        e = self.var_max_len.get() if self.var_use_max.get() else 50
        p = self.var_prefix.get();
        suf = self.var_suffix.get()
        dev = []
        if "Device #" in self.selected_device.get():
            m = re.search(r"Device #(\d+)", self.selected_device.get())
            if m: dev = ["-d", m.group(1)]
        hc = self.path_hashcat.get();
        cwd = os.path.dirname(hc)
        for l in range(s, e + 1):
            if self.stop_event: break
            mask = p + ("?1" * l) + suf
            self.log(f"⚡ 长度: {l} | 掩码: {mask}")
            cmd = [hc, "-m", self.hash_mode.get(), "-a", "3", "-1", charset, self.hash_file_path, mask, "--outfile",
                   self.cracked_file_path, "--status", "--status-timer", "5", "--force", "--hwmon-disable", "-w", "1",
                   "--potfile-disable"] + dev
            self.run_subprocess(cmd, cwd)
            if self.check_success(): break
            if l < e: time.sleep(2)
        self.reset_ui()

    def run_subprocess(self, cmd, cwd):
        try:
            cf = 0x08000000 if os.name == 'nt' else 0
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                            creationflags=cf, cwd=cwd)
            for line in self.process.stdout:
                if self.stop_event: self.process.terminate(); break
                if line.strip(): self.log(line.strip())
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
                    self.log(f"🎉 密码: {pwd}");
                    self.create_password_txt(pwd)
                    with open(self.hash_file_path, "r") as f: h = f.read().strip()
                    self.add_history_entry(h, pwd)
                    messagebox.showinfo("成功", pwd);
                    self.stop_event = True;
                    return True
            except:
                pass
        return False

    def create_password_txt(self, pwd):
        try:
            p = self.path_archive.get()
            if p:
                f = os.path.join(os.path.dirname(p), "password.txt")
                with open(f, "w", encoding="utf-8") as file: file.write(
                    f"File: {os.path.basename(p)}\nPassword: {pwd}\nTime: {time.ctime()}")
        except:
            pass

    def clear_temp(self):
        try:
            for f in os.listdir(self.temp_dir):
                fp = os.path.join(self.temp_dir, f)
                if os.path.isfile(fp): os.remove(fp)
            self.log("🧹 Temp 已清空")
        except:
            pass

    def scan_devices(self):
        hc = self.path_hashcat.get()
        if not hc or not os.path.exists(hc): return

        def _scan():
            try:
                cwd = os.path.dirname(hc)
                p = subprocess.Popen([hc, "-I"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                     creationflags=0x08000000, cwd=cwd)
                out, _ = p.communicate()
                devs = ["默认"];
                matches = re.findall(r"Device\s*#\s*(\d+):\s*(.+)", out)
                for i, n in matches: devs.append(f"Device #{i}: {n.strip()}")
                self.root.after(0, lambda: self.combo_device.config(values=devs))
                if len(devs) > 1: self.root.after(0, lambda: self.combo_device.current(1))
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
        self.btn_start.config(state="normal");
        self.btn_stop.config(state="disabled")

    def browse_file(self, v, p):
        f = filedialog.askopenfilename(filetypes=[("Files", p), ("All", "*.*")])
        if f: v.set(f)

    def browse_folder(self, v):
        d = filedialog.askdirectory()
        if d: v.set(d)

    def log(self, t):
        self.log_area.insert(tk.END, t + "\n");
        self.log_area.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = HashcatFinalGUI(root)
    root.mainloop()

