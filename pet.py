import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, Menu, simpledialog
from PIL import Image, ImageTk, ImageSequence
import webbrowser
import json
import random
import hashlib

class DogGIFPlayer:
    def __init__(self, master):
        # ---------------------- 1. 路径处理（适配开发/打包环境） ----------------------
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS  # 打包后资源路径
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))  # 开发时路径

        if getattr(sys, 'frozen', False):
            self.user_data_dir = os.path.join(os.environ.get('APPDATA', ''), 'CARLOS DENG的桌宠配置')
        else:
            self.user_data_dir = os.path.dirname(os.path.abspath(__file__))

        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

        self.gif_folder = os.path.join(self.base_dir, 'gif')  # 角色动图文件夹
        self.hash_file = os.path.join(self.base_dir, 'hash_verify.json')  # 哈希验证文件
        self.config_path = os.path.join(self.user_data_dir, 'config.json')  # 配置文件

        # ---------------------- 2. 窗口基础样式 ----------------------
        self.root = master
        self.root.title("CARLOS DENG专属桌宠")
        self.root.geometry("400x400")
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.attributes('-topmost', True)  # 窗口置顶
        self.root.attributes('-transparentcolor', '#000001')  # 透明色
        self.transparency = 1.0
        self.root.attributes('-alpha', self.transparency)
        self.is_fixed = False

        # ---------------------- 3. 核心变量初始化 ----------------------
        self.gif_files = []
        self.current_index = 0
        self.playing = True
        self.frames = []
        self.current_frame = 0
        self.animation_id = None
        self.auto_play_id = None
        self.is_auto_playing = False
        self.auto_play_interval = 5000
        self.control_bar_visible = False

        # ---------------------- 4. 初始化流程 ----------------------
        self.create_context_menu()
        self.create_control_bar()
        self.create_canvas()
        self.bind_drag_events()

        self.verify_and_update_hash()  # 校验并更新动图哈希
        self.load_local_gifs()
        self.load_config()

        self.root.protocol("WM_DELETE_WINDOW", self.save_on_exit)

    def create_canvas(self):
        """创建用于显示动图的画布"""
        self.canvas = tk.Canvas(
            self.root, 
            bg='#000001', 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-3>", self.show_context_menu)  # 绑定右键菜单
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # 绑定滚轮缩放

    def calculate_file_hash(self, file_path):
        """计算单个文件的MD5哈希值"""
        md5_hash = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            messagebox.showerror("哈希计算错误", f"文件 {os.path.basename(file_path)} 读取失败: {str(e)}")
            return None

    def save_gif_hashes(self):
        """保存gif文件夹中所有动图的哈希值"""
        if not os.path.exists(self.gif_folder):
            try:
                os.makedirs(self.gif_folder)
            except Exception as e:
                messagebox.showerror("错误", f"创建gif文件夹失败: {str(e)}")
                return False
            messagebox.showerror("错误", "未找到gif文件夹，请先放入动图！")
            return False

        valid_extensions = ('.gif', '.png', '.jpg', '.jpeg', '.bmp')
        self.gif_files = [
            os.path.join(self.gif_folder, f)
            for f in os.listdir(self.gif_folder)
            if f.lower().endswith(valid_extensions)
        ]
        if not self.gif_files:
            messagebox.showerror("错误", "gif文件夹中无有效动图文件！")
            return False

        hash_dict = {}
        for f in self.gif_files:
            filename = os.path.basename(f)
            file_hash = self.calculate_file_hash(f)
            if file_hash is None:
                return False
            hash_dict[filename] = file_hash

        try:
            with open(self.hash_file, 'w', encoding='utf-8') as f:
                json.dump(hash_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存哈希文件失败: {str(e)}")
            return False

    def verify_gif_hash(self):
        """验证当前动图文件的哈希值是否一致"""
        if not os.path.exists(self.hash_file):
            return True

        try:
            with open(self.hash_file, 'r', encoding='utf-8') as f:
                saved_hashes = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"哈希验证文件损坏: {str(e)}")
            return False

        valid_extensions = ('.gif', '.png', '.jpg', '.jpeg', '.bmp')
        current_files = [
            os.path.join(self.gif_folder, f)
            for f in os.listdir(self.gif_folder)
            if f.lower().endswith(valid_extensions)
        ]

        if len(current_files) != len(saved_hashes):
            return False

        for file_path in current_files:
            filename = os.path.basename(file_path)
            if filename not in saved_hashes:
                return False
            current_hash = self.calculate_file_hash(file_path)
            if current_hash != saved_hashes[filename]:
                return False
        return True

    def verify_and_update_hash(self):
        """验证哈希值，失败则自动更新"""
        if not os.path.exists(self.hash_file):
            self.save_gif_hashes()
            return

        if not self.verify_gif_hash():
            messagebox.showinfo(
                "哈希验证更新",
                "检测到动图已更新，正在重新计算哈希值..."
            )
            self.save_gif_hashes()
            messagebox.showinfo("完成", "哈希值已更新，当前动图文件已被认可")

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="显示/隐藏控制栏", command=self.toggle_control_bar)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="上一张", command=self.prev_gif)
        self.context_menu.add_command(label="下一张", command=self.next_gif)
        self.context_menu.add_command(label="随机显示", command=self.random_gif)
        self.context_menu.add_separator()

        self.gif_submenu = Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="选择角色动图", menu=self.gif_submenu)
        self.context_menu.add_separator()

        self.context_menu.add_command(label="固定窗口", command=self.fix_window)
        self.context_menu.add_command(label="取消固定", command=self.unfix_window)
        self.context_menu.add_separator()

        self.context_menu.add_command(label="开启循环播放", command=self.start_auto_play)
        self.context_menu.add_command(label="停止循环播放", command=self.stop_auto_play)
        self.context_menu.add_command(label="设置播放间隔", command=self.set_auto_play_interval)
        self.context_menu.add_separator()

        self.transparency_menu = Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="调节透明度", menu=self.transparency_menu)
        transparencies = [("100%", 1.0), ("75%", 0.75), ("50%", 0.5), ("25%", 0.25)]
        for label, value in transparencies:
            self.transparency_menu.add_command(
                label=label, 
                command=lambda v=value: self.set_transparency(v)
            )
        self.context_menu.add_separator()

        self.context_menu.add_command(label="关于作者", command=self.show_about)
        self.context_menu.add_command(
            label="更多桌宠", 
            command=lambda: webbrowser.open(
                "https://dianshudata.com/dataMarket?search=%E6%A1%8C%E5%AE%A0&mtm_campaign=zhuochonglink&mtm_kwd=%E6%A1%8C%E5%AE%A0"
            )
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(label="退出", command=self.save_on_exit)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def create_control_bar(self):
        """创建控制栏"""
        self.control_bar = ttk.Frame(self.root)
        self.btn_prev = ttk.Button(self.control_bar, text="上一张", command=self.prev_gif)
        self.btn_prev.pack(side=tk.LEFT, padx=5)
        self.btn_play_pause = ttk.Button(self.control_bar, text="暂停", command=self.toggle_play)
        self.btn_play_pause.pack(side=tk.LEFT, padx=5)
        self.btn_next = ttk.Button(self.control_bar, text="下一张", command=self.next_gif)
        self.btn_next.pack(side=tk.LEFT, padx=5)
        self.btn_stop_auto = ttk.Button(self.control_bar, text="停止自动播放", command=self.stop_auto_play)
        self.btn_stop_auto.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(self.control_bar, text="正在显示: 无 | 0/0")
        self.status_label.pack(side=tk.LEFT, padx=10)

    def toggle_control_bar(self):
        self.control_bar_visible = not self.control_bar_visible
        if self.control_bar_visible:
            self.control_bar.pack(fill=tk.X, side=tk.TOP)
        else:
            self.control_bar.pack_forget()

    def bind_drag_events(self):
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

    def start_drag(self, event):
        if not self.is_fixed:
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def on_drag(self, event):
        if self.dragging and not self.is_fixed:
            x = self.root.winfo_x() - self.drag_start_x + event.x
            y = self.root.winfo_y() - self.drag_start_y + event.y
            self.root.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        self.dragging = False

    def on_mouse_wheel(self, event):
        width, height = map(int, self.root.geometry().split("+")[0].split("x"))
        step = 20
        if event.num == 4 or event.delta > 0:
            new_width = width + step
            new_height = height + step
        else:
            new_width = max(100, width - step)
            new_height = max(100, height - step)
        self.root.geometry(f"{new_width}x{new_height}")
        self.save_config()

    def fix_window(self):
        self.is_fixed = True
        self.update_context_menu_state()

    def unfix_window(self):
        self.is_fixed = False
        self.update_context_menu_state()

    def update_context_menu_state(self):
        self.context_menu.entryconfig("固定窗口", state=tk.DISABLED if self.is_fixed else tk.NORMAL)
        self.context_menu.entryconfig("取消固定", state=tk.NORMAL if self.is_fixed else tk.DISABLED)

    def load_local_gifs(self):
        if not os.path.exists(self.gif_folder):
            messagebox.showerror("错误", "未找到gif文件夹，请检查程序完整性！")
            self.root.destroy()
            return
        valid_extensions = ('.gif', '.png', '.jpg', '.jpeg', '.bmp')
        self.gif_files = [
            os.path.join(self.gif_folder, f)
            for f in os.listdir(self.gif_folder)
            if f.lower().endswith(valid_extensions)
        ]
        if self.gif_files:
            self.load_gif(self.gif_files[0])
            self.update_gif_submenu()
        else:
            messagebox.showerror("错误", "gif文件夹中没有有效图片，请放入动图！")

    def update_gif_submenu(self):
        self.gif_submenu.delete(0, tk.END)
        for idx, path in enumerate(self.gif_files):
            filename = os.path.basename(path)
            self.gif_submenu.add_command(
                label=filename,
                command=lambda i=idx: self.select_gif(i)
            )

    def load_gif(self, gif_path):
        try:
            if self.animation_id:
                self.root.after_cancel(self.animation_id)
            self.gif = Image.open(gif_path)
            self.frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(self.gif)]
            self.current_frame = 0
            self.display_frame()
            self.animate()
            filename = os.path.basename(gif_path)
            self.status_label.config(
                text=f"正在显示: {filename} | {self.current_index + 1}/{len(self.gif_files)}"
            )
        except Exception as e:
            messagebox.showerror("加载失败", f"动图 {os.path.basename(gif_path)} 加载出错: {str(e)}")

    def display_frame(self):
        if not self.frames:
            return
        frame = self.frames[self.current_frame]
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width > 0 and canvas_height > 0:
            ratio = min(canvas_width / frame.width, canvas_height / frame.height)
            new_size = (int(frame.width * ratio), int(frame.height * ratio))
            frame = frame.resize(new_size, Image.LANCZOS)
            bg = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
            x = (canvas_width - new_size[0]) // 2
            y = (canvas_height - new_size[1]) // 2
            bg.paste(frame, (x, y), frame)
            self.photo = ImageTk.PhotoImage(bg)
        else:
            self.photo = ImageTk.PhotoImage(frame)
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.photo)

    def animate(self):
        if not self.playing or not self.frames:
            return
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.display_frame()
        delay = self.gif.info.get('duration', 100)
        self.animation_id = self.root.after(delay, self.animate)

    def toggle_play(self):
        self.playing = not self.playing
        self.btn_play_pause.config(text="播放" if self.playing else "暂停")
        if self.playing:
            self.animate()

    def prev_gif(self):
        if self.gif_files:
            self.current_index = (self.current_index - 1) % len(self.gif_files)
            self.load_gif(self.gif_files[self.current_index])

    def next_gif(self):
        if self.gif_files:
            self.current_index = (self.current_index + 1) % len(self.gif_files)
            self.load_gif(self.gif_files[self.current_index])

    def random_gif(self):
        if self.gif_files:
            self.current_index = random.randint(0, len(self.gif_files) - 1)
            self.load_gif(self.gif_files[self.current_index])

    def select_gif(self, index):
        if 0 <= index < len(self.gif_files):
            self.current_index = index
            self.load_gif(self.gif_files[index])

    def start_auto_play(self):
        if not self.is_auto_playing:
            self.is_auto_playing = True
            self.auto_play_next_gif()

    def auto_play_next_gif(self):
        if self.is_auto_playing:
            self.next_gif()
            self.auto_play_id = self.root.after(self.auto_play_interval, self.auto_play_next_gif)

    def stop_auto_play(self):
        if self.is_auto_playing:
            self.is_auto_playing = False
            if self.auto_play_id:
                self.root.after_cancel(self.auto_play_id)
                self.auto_play_id = None

    def set_auto_play_interval(self):
        try:
            seconds = simpledialog.askinteger(
                "设置间隔",
                "请输入自动播放间隔（秒，1-200）:",
                minvalue=1,
                maxvalue=200
            )
            if seconds:
                self.auto_play_interval = seconds * 1000
                self.save_config()
                messagebox.showinfo("成功", f"自动播放间隔已设置为 {seconds} 秒")
        except Exception as e:
            messagebox.showerror("错误", f"设置失败: {str(e)}")

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'window_size' in config:
                        self.root.geometry(config['window_size'])
                    if 'transparency' in config:
                        self.transparency = config['transparency']
                        self.root.attributes('-alpha', self.transparency)
                    if 'auto_play_interval' in config:
                        self.auto_play_interval = config['auto_play_interval']
        except Exception as e:
            print(f"加载配置出错: {e}")
            if os.path.exists(self.config_path):
                try:
                    os.remove(self.config_path)
                except:
                    pass

    def save_config(self):
        try:
            config = {
                'window_size': f"{self.root.winfo_width()}x{self.root.winfo_height()}",
                'transparency': self.transparency,
                'auto_play_interval': self.auto_play_interval
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置出错: {str(e)}")

    def save_on_exit(self):
        self.save_config()
        self.root.destroy()

    def set_transparency(self, value):
        self.transparency = value
        self.root.attributes('-alpha', self.transparency)
        self.save_config()

    def show_about(self):
        messagebox.showinfo(
            "关于作者",
            "此软件由Carlos Deng独立开发完成，想了解更多可联系carlos.dh.usfrcn0528@gmail.com\n\n严重声明：本软件禁止二次售卖！"
        )


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DogGIFPlayer(root)
        root.mainloop()
    except Exception as e:
        log_dir = (
            os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), '恋与深空桌宠配置')
            if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        )
        os.makedirs(log_dir, exist_ok=True)
        error_log_path = os.path.join(log_dir, 'error.log')
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(str(e))
        messagebox.showerror("程序异常", f"错误信息已保存到 {error_log_path}，可凭此排查问题")