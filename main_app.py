import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os
import datetime
import sys
import subprocess
import threading
import json
import shutil
import db_handler
import confidence_calculator # <-- Module tính độ tin cậy tùy chỉnh

# Thư viện để vẽ biểu đồ
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Thử import cv2, nếu thất bại sẽ được xử lý ở main
try:
    import cv2
except ImportError:
    cv2 = None

# --- CÁC BIẾN TOÀN CỤC VÀ CÀI ĐẶT BAN ĐẦU ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def init_db():
    """Gọi hàm khởi tạo CSDL từ module db_handler."""
    print("Initializing database schema via db_handler...")
    print("If the database and tables already exist, this will have no effect.")
    # Giả sử db_handler có hàm này để tạo bảng nếu chưa có
    # db_handler.init_db()


def lighten_color(hex_color, amount=0.15):
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(min(255, r + (255 - r) * amount))
        g = int(min(255, g + (255 - g) * amount))
        b = int(min(255, b + (255 - b) * amount))
        return f'#{r:02x}{g:02x}{b:02x}'
    except:
        return hex_color


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ Thống Phân Loại Rác Thải Thông Minh")
        self.width = 1280
        self.height = 720
        self.geometry(f"{self.width}x{self.height}")
        self.minsize(1100, 700)

        # --- Khởi tạo các biến trạng thái ---
        self.current_user = None
        self.current_user_id = None
        self.current_role = None
        self.cap = None
        self.current_frame_np = None
        self.trash_category_photos = {}
        self.camera_photo = None
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.create_login_frame()

    # --- CÁC HÀM TẠO GIAO DIỆN (VIEW) ---
    def create_login_frame(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        view_container = ctk.CTkFrame(self, fg_color="transparent")
        view_container.grid(row=0, column=0, sticky="nsew")
        view_container.grid_columnconfigure(0, weight=2)
        view_container.grid_columnconfigure(1, weight=3)
        view_container.grid_rowconfigure(0, weight=1)
        left_panel = ctk.CTkFrame(view_container, corner_radius=0, fg_color=("#0077b6", "#005a8c"))
        left_panel.grid(row=0, column=0, sticky="nsew")
        right_panel = ctk.CTkFrame(view_container, corner_radius=0, fg_color=("gray92", "gray14"))
        right_panel.grid(row=0, column=1, sticky="nsew")
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        brand_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=40, pady=40)
        try:
            icon_path = os.path.join(APP_DIR, "images", "app_icon.png")
            app_icon_img = Image.open(icon_path)
            app_icon = ctk.CTkImage(light_image=app_icon_img, dark_image=app_icon_img, size=(128, 128))
            ctk.CTkLabel(brand_frame, image=app_icon, text="").pack(pady=(20, 15))
        except FileNotFoundError:
            pass
        ctk.CTkLabel(brand_frame, text="Hệ Thống Phân Loại Rác", font=ctk.CTkFont(family="Arial", size=32, weight="bold"), text_color="white").pack(pady=10)
        ctk.CTkLabel(brand_frame, text="Thông Minh & Hiệu Quả", font=ctk.CTkFont(family="Arial", size=16), text_color="white").pack(pady=5)
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        login_form_frame = ctk.CTkFrame(right_panel, fg_color=("white", "gray20"), width=350, corner_radius=10)
        login_form_frame.grid(row=0, column=0, padx=20, pady=20)
        ctk.CTkLabel(login_form_frame, text="Đăng Nhập", font=ctk.CTkFont(family="Arial", size=24, weight="bold")).pack(pady=(30, 20), padx=50)
        self.ent_user = ctk.CTkEntry(login_form_frame, placeholder_text="Tên đăng nhập", width=280, height=40)
        self.ent_user.pack(pady=10, padx=30, fill="x")
        self.ent_pass = ctk.CTkEntry(login_form_frame, placeholder_text="Mật khẩu", show="*", width=280, height=40)
        self.ent_pass.pack(pady=10, padx=30, fill="x")
        self.show_var = tk.BooleanVar()
        ctk.CTkCheckBox(login_form_frame, text="Hiện mật khẩu", variable=self.show_var, command=self.toggle_show).pack(anchor="w", pady=10, padx=30)
        ctk.CTkButton(login_form_frame, text="Đăng nhập", command=self.login, height=40, font=ctk.CTkFont(weight="bold")).pack(pady=(15, 10), padx=30, fill="x")
        ctk.CTkButton(login_form_frame, text="Đăng kí", command=self.register_window, height=40, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(pady=10, padx=30, fill="x")
        ctk.CTkLabel(login_form_frame, text="").pack(pady=5)

    def create_main_frame(self):
        """Tạo và hiển thị màn hình chính của ứng dụng."""
        for widget in self.winfo_children():
            widget.destroy()

        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=0)
        main_container.grid_rowconfigure(2, weight=1)
        header_frame = ctk.CTkFrame(main_container, corner_radius=0, height=70)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        action_frame = ctk.CTkFrame(main_container)
        action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        action_frame.grid_columnconfigure(0, weight=1)
        info_frame = ctk.CTkFrame(main_container)
        info_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        info_frame.grid_columnconfigure((0, 1, 2), weight=1)
        info_frame.grid_rowconfigure(1, weight=1)
        title = ctk.CTkLabel(header_frame, text=f"Xin chào {self.current_user} ({self.current_role})", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        logout_button = ctk.CTkButton(header_frame, text="Đăng xuất", width=120, height=35, command=self.logout, fg_color="#e5383b", hover_color="#c92a2a")
        logout_button.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        button_font = ctk.CTkFont(size=12, weight="bold")
        button_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        button_container.grid(row=0, column=0)
        ctk.CTkButton(button_container, text="⬆ Upload Ảnh", width=140, height=35, command=self.upload_image, font=button_font).pack(side="left", padx=7)
        ctk.CTkButton(button_container, text="Mở Camera", width=140, height=35, command=self.open_camera, font=button_font).pack(side="left", padx=7)
        ctk.CTkButton(button_container, text="Lịch sử phân loại", width=140, height=35, command=self.get_history_classification, font=button_font).pack(side="left", padx=7)
        if self.current_role == 'admin':
            ctk.CTkButton(button_container, text="Train Model", width=140, height=35, command=self.start_training, font=button_font, fg_color="#2b9348").pack(side="left", padx=7)
            ctk.CTkButton(button_container, text="Dashboard", width=140, height=35, command=self.open_admin_dashboard, font=button_font, fg_color="#f9c74f").pack(side="left", padx=7)
        ctk.CTkLabel(info_frame, text="Thông Tin Phân Loại Cơ Bản", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="ew", pady=(10, 5), padx=20)
        trash_categories = { "PLASTIC": ("Nhựa", "Chai, lọ, túi, hộp nhựa...", "#0077b6"), "PAPER": ("Giấy", "Sách, báo, bìa carton...", "#f9a620"), "ORGANIC": ("Hữu cơ", "Thức ăn thừa, rau củ quả...", "#52b788") }
        for i, (key, (title_vn, desc, color)) in enumerate(trash_categories.items()):
            self.create_category_box(info_frame, key, title_vn, desc, color, i)

    # --- CÁC HÀM XỬ LÝ LOGIC VÀ SỰ KIỆN ---

    def login(self):
        u = self.ent_user.get().strip()
        p = self.ent_pass.get().strip()
        
        conn = db_handler.get_db_connection()

        if not conn:
            messagebox.showwarning("Cảnh báo", "Vui lòng kiểm tra kết nối cơ sở dữ liệu.")
            return
        
        try:
            cursor = conn.cursor(dictionary=True)
        finally:
            if conn and conn.is_connected():
                conn.close()
        # Sử dụng db_handler để xác thực
        # Giả sử bạn có hàm `authenticate_user` trong db_handler
        user_data = self.db.authenticate_user(u, p) 
        
        if user_data:
            self.current_user_id = user_data['id']
            self.current_user = user_data['username']
            self.current_role = user_data['role']
            self.create_main_frame()
        else:
            messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu!")

    def logout(self):
        self.current_user = None
        self.current_user_id = None
        self.current_role = None
        self.trash_category_photos = {}
        if self.cap and self.cap.isOpened():
            self.close_camera_window()
        self.create_login_frame()

    def toggle_show(self):
        self.ent_pass.configure(show="" if self.show_var.get() else "*")

    def register_window(self):
        rw = ctk.CTkToplevel(self)
        rw.title("Đăng Ký Tài Khoản")
        
        rw.geometry("400x350")
        rw.transient(self)
        rw.grab_set()
        rw.resizable(True, True)
        ctk.CTkLabel(rw, text="username:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5), padx=20)
        eu = ctk.CTkEntry(rw, width=250)
        eu.pack()
        ctk.CTkLabel(rw, text="password:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5), padx=20)
        ep = ctk.CTkEntry(rw, width=250)
        ep.pack()
        
        def do_register(self):
            un = eu.get().strip()
            pw = ep.get().strip()
            
            if not un or not pw:
                    messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin.", parent=rw)
                    return
                
            success = db_handler.add_user(un, pw)
            
            if success:
                messagebox.showinfo("Thành công", "Đăng ký tài khoản thành công!", parent=rw)
                rw.destroy()
            else:
                    messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại hoặc không thể đăng ký.", parent=rw)

            
        ctk.CTkButton(rw, text="Đăng ký", command=do_register, height=40).pack(pady=20, padx=20, fill="x")

    def create_category_box(self, parent, key, title_vn, desc, color, column):
        box = ctk.CTkFrame(parent, fg_color=color, border_width=2, border_color="gray50")
        box.grid(row=1, column=column, padx=15, pady=10, sticky="nsew")
        box.grid_rowconfigure(2, weight=1)
        box.grid_columnconfigure(0, weight=1)
        img_size = 150
        try:
            img_path = os.path.join(APP_DIR, "images", f"{key.lower()}.png")
            img = Image.open(img_path)
        except FileNotFoundError:
            img = Image.new('RGB', (img_size, img_size), color=color)
        self.trash_category_photos[key] = ctk.CTkImage(light_image=img, dark_image=img, size=(img_size, img_size))
        lbl_img = ctk.CTkLabel(box, image=self.trash_category_photos[key], text="")
        lbl_img.grid(row=0, column=0, pady=15)
        ctk.CTkLabel(box, text=title_vn.upper(), font=ctk.CTkFont(size=18, weight="bold"), text_color="white").grid(row=1, column=0, pady=5)
        desc_label = ctk.CTkLabel(box, text=desc, font=ctk.CTkFont(size=12), text_color="white", justify="left")
        desc_label.grid(row=2, column=0, padx=10, pady=(5, 15), sticky="n")
        def update_wraplength(event):
            desc_label.configure(wraplength=event.width - 30)
        box.bind('<Configure>', update_wraplength)
        hover_color = lighten_color(color)
        def on_enter(event): box.configure(fg_color=hover_color)
        def on_leave(event): box.configure(fg_color=color)
        box.bind("<Enter>", on_enter)
        box.bind("<Leave>", on_leave)

    def start_training(self):
        messagebox.showinfo("Bắt đầu Huấn luyện", "Quá trình huấn luyện model đã bắt đầu.\n"
                                                  "Vui lòng theo dõi cửa sổ console để xem tiến trình.\n"
                                                  "Ứng dụng có thể bị treo trong quá trình này.")
        def _run_train():
            try:
                train_script_path = os.path.join(APP_DIR, "train.py")
                if not os.path.exists(train_script_path):
                    if self.winfo_exists(): self.after(0, lambda: messagebox.showerror("Lỗi", "Không tìm thấy tệp train.py."))
                    return
                proc = subprocess.Popen([sys.executable, train_script_path], cwd=APP_DIR, 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                for line in iter(proc.stdout.readline, ''): print(f"[TRAIN] {line.strip()}")
                proc.wait()
                stderr = proc.stderr.read()
                if self.winfo_exists():
                    if proc.returncode != 0: self.after(0, lambda: messagebox.showerror("Lỗi Huấn luyện", f"Đã xảy ra lỗi:\n{stderr}"))
                    else: self.after(0, lambda: messagebox.showinfo("Hoàn tất", "Quá trình huấn luyện đã kết thúc thành công!"))
            except Exception as e:
                if self.winfo_exists(): self.after(0, lambda err=e: messagebox.showerror("Lỗi", f"Không thể bắt đầu quá trình huấn luyện: {err}"))
        threading.Thread(target=_run_train, daemon=True).start()

    def open_admin_dashboard(self):
        # Giả sử bạn có các hàm này trong db_handler
        stats = self.db.get_dashboard_stats() 
        if stats is None:
            messagebox.showerror("Lỗi", "Không thể lấy dữ liệu thống kê từ CSDL.")
            return

        db_win = ctk.CTkToplevel(self)
        db_win.title("Admin Dashboard - Bảng Điều Khiển")
        db_win.geometry("1000x600")
        db_win.transient(self)
        db_win.grab_set()
        db_win.grid_columnconfigure(0, weight=1)
        db_win.grid_rowconfigure(1, weight=1)
        
        stats_frame = ctk.CTkFrame(db_win)
        stats_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkLabel(stats_frame, text=f"👥\nTổng Người Dùng\n{stats['total_users']}", font=ctk.CTkFont(size=16)).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(stats_frame, text=f"🖼️\nTổng Số Ảnh\n{stats['total_images']}", font=ctk.CTkFont(size=16)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(stats_frame, text=f"🗑️\nTổng Số Lượt Phân Loại\n{stats['total_classifications']}", font=ctk.CTkFont(size=16)).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        chart_frame = ctk.CTkFrame(db_win)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        results = stats['classification_by_label']
        if results:
            labels = [r[0] for r in results]
            sizes = [r[1] for r in results]
            fig, ax = plt.subplots(facecolor='#2B2B2B')
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'color':"w"})
            ax.axis('equal')
            plt.title("Tỷ Lệ Phân Loại Rác", color="white")
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        else:
            ctk.CTkLabel(chart_frame, text="Chưa có dữ liệu phân loại để hiển thị.", font=ctk.CTkFont(size=16)).pack(expand=True)

    def open_history_window(self):
        history = self.db.get_classification_history(self.current_user_id)
        if history is None:
            messagebox.showerror("Lỗi", "Không thể lấy lịch sử phân loại từ CSDL.")
            return
        history_win = ctk.CTkToplevel(self)
        history_win.title("Lịch Sử Phân Loại Ảnh")
        history_win.geometry("800x500")
        history_win.transient(self)
        history_win.grab_set()
        history_frame = ctk.CTkFrame(history_win)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = ctk.CTkCanvas(history_frame)
        scrollbar = ctk.CTkScrollbar(history_frame, orientation="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for record in history:
            rec_frame = ctk.CTkFrame(scrollable_frame, fg_color=("white", "gray20"), border_width=1, border_color="gray50")
            rec_frame.pack(fill="x", pady=5, padx=5)
            timestamp_str = record['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            ctk.CTkLabel(rec_frame, text=f"Ảnh ID: {record['image_id']} | Nhãn: {record['predicted_label']} | Độ tin cậy: {record['confidence']*100:.2f}% | Thời gian: {timestamp_str}", font=ctk.CTkFont(size=12)).pack(pady=10, padx=10)   
            
    def upload_image(self):
        file_path = filedialog.askopenfilename(title="Chọn một ảnh để phân loại", filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if not file_path: return
        self.show_prediction_window(file_path)

    def open_camera(self):
        if self.cap and self.cap.isOpened():
            messagebox.showwarning("Cảnh báo", "Camera đang mở. Vui lòng đóng cửa sổ camera hiện tại.")
            return
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened(): raise ConnectionError
            self.open_camera_window()
        except Exception:
            messagebox.showerror("Lỗi", "Không mở được camera. Hãy kiểm tra kết nối hoặc driver.")
            if self.cap: self.cap.release()
            self.cap = None
    
    def open_camera_window(self):
        self.camera_window = ctk.CTkToplevel(self)
        self.camera_window.title("Mở Camera & Chụp Ảnh")
        self.camera_window.geometry("900x700")
        self.camera_window.protocol("WM_DELETE_WINDOW", self.close_camera_window)
        self.camera_window.transient(self)
        self.camera_window.grab_set()
        main_frame = ctk.CTkFrame(self.camera_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="Camera Feed", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        self.video_label = ctk.CTkLabel(main_frame, text="")
        self.video_label.pack(padx=10, pady=5, fill="both", expand=True)
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", pady=15)
        ctk.CTkButton(button_frame, text="📸 Chụp Ảnh", command=self.capture_photo, height=40).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Đóng", command=self.close_camera_window, height=40, fg_color="gray50").pack(side="left", padx=10)
        self.update_camera_frame()

    def update_camera_frame(self):
        if not self.cap or not self.cap.isOpened() or not hasattr(self, 'camera_window') or not self.camera_window.winfo_exists(): return
        ret, frame = self.cap.read()
        if ret:
            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.current_frame_np = cv_img
            label_width, label_height = self.video_label.winfo_width(), self.video_label.winfo_height()
            if label_width > 10 and label_height > 10:
                resized_img = Image.fromarray(cv_img).resize((label_width, label_height), Image.Resampling.LANCZOS)
                self.camera_photo = ImageTk.PhotoImage(image=resized_img)
                self.video_label.configure(image=self.camera_photo, text="")
        self.after(15, self.update_camera_frame)

    def capture_photo(self):
        if self.current_frame_np is None:
            messagebox.showwarning("Cảnh báo", "Không có hình ảnh để chụp.", parent=self.camera_window)
            return
        save_dir = os.path.join(APP_DIR, "captured")
        os.makedirs(save_dir, exist_ok=True)
        now = datetime.datetime.now()
        save_filename = f"capture_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        save_path = os.path.join(save_dir, save_filename)
        frame_to_save = cv2.cvtColor(self.current_frame_np, cv2.COLOR_RGB2BGR)
        cv2.imwrite(save_path, frame_to_save)
        messagebox.showinfo("Thành công", f"Ảnh đã được lưu tại:\n{save_path}", parent=self.camera_window)
        self.close_camera_window()
        self.show_prediction_window(save_path)
        
    def close_camera_window(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if hasattr(self, 'camera_window') and self.camera_window.winfo_exists():
            self.camera_window.destroy()
        self.current_frame_np = None

    def show_prediction_window(self, image_path):
        pred_win = ctk.CTkToplevel(self)
        pred_win.title("Đang Phát Hiện Đối Tượng...")
        pred_win.geometry("1100x700")
        pred_win.resizable(True, True)
        pred_win.transient(self)
        pred_win.grab_set()
        pred_win.grid_columnconfigure(0, weight=3)
        pred_win.grid_columnconfigure(1, weight=2)
        pred_win.grid_rowconfigure(0, weight=1)
        left_frame = ctk.CTkFrame(pred_win, fg_color=("gray90", "gray15"))
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        lbl_image = ctk.CTkLabel(left_frame, text="Đang xử lý ảnh...")
        lbl_image.pack(pady=20, padx=20, expand=True)
        right_frame = ctk.CTkFrame(pred_win)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(right_frame, text="Các Đối Tượng Tìm Thấy", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=10, padx=20, sticky="w")
        results_scroll_frame = ctk.CTkScrollableFrame(right_frame, label_text="Kết quả")
        results_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        pred_win.close_button = ctk.CTkButton(right_frame, text="Đóng", command=pred_win.destroy, state="disabled")
        pred_win.close_button.grid(row=2, column=0, sticky="ew", pady=10, padx=10)

        def prediction_thread():
            try:
                # 1. Gọi script dự đoán để lấy nhãn
                predict_script_path = os.path.join(APP_DIR, "trash_detection.py")
                if not os.path.exists(predict_script_path):
                    raise FileNotFoundError("Không tìm thấy tệp trash_detection.py.")

                cmd = [sys.executable, predict_script_path, "--img_path", image_path]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', cwd=APP_DIR)
                stdout, stderr = proc.communicate(timeout=120)

                if proc.returncode != 0:
                    raise Exception(f"Lỗi script dự đoán:\n{stderr}")
                
                result = json.loads(stdout)
                annotated_img_path = result.get("annotated_image_path")
                detections = result.get("detections", [])

                # 2. Cập nhật giao diện với ảnh kết quả
                if not pred_win.winfo_exists(): return
                def update_image():
                    try:
                        img = Image.open(annotated_img_path)
                        # Tính toán size ảnh cho vừa frame
                        w, h = img.size
                        max_w, max_h = left_frame.winfo_width() - 40, left_frame.winfo_height() - 40
                        ratio = min(max_w/w, max_h/h)
                        new_size = (int(w*ratio), int(h*ratio))

                        photo = ctk.CTkImage(light_image=img, dark_image=img, size=new_size)
                        lbl_image.configure(image=photo, text="")
                    except Exception as e:
                        lbl_image.configure(text=f"Lỗi hiển thị ảnh kết quả:\n{e}")
                self.after(0, update_image)
                
                # 3. Gọi thuật toán riêng để tính độ tin cậy cho TOÀN BỘ BỨC ẢNH
                final_confidence = confidence_calculator.calculate_confidence(image_path)
                print(f"Độ tin cậy được tính toán từ thuật toán riêng: {final_confidence:.2%}")

                # 4. Lưu ảnh vào CSDL (bảng `images`)
                image_id = self.db.add_image(image_path, self.current_user_id)
                if not image_id:
                    raise Exception("Không thể lưu thông tin ảnh vào CSDL.")

                if not detections and pred_win.winfo_exists():
                    self.after(0, lambda: ctk.CTkLabel(results_scroll_frame, text="Không tìm thấy đối tượng nào.").pack(pady=10))
                
                # 5. Lặp qua các đối tượng và lưu kết quả
                for detection in detections:
                    if not pred_win.winfo_exists(): break
                    label_name = detection['label']
                    
                    # Lấy thông tin nhãn từ CSDL
                    label_info = self.db.get_label_by_name(label_name)
                    
                    if label_info:
                        label_id = label_info['id']
                        proc_text = label_info.get('description', 'Chưa có hướng dẫn xử lý.')
                        
                        # Lưu kết quả phân loại vào CSDL
                        self.db.add_classification_result(image_id, label_id, final_confidence)
                    else:
                        proc_text = f"Nhãn '{label_name}' chưa có trong CSDL."

                    def create_result_entry(parent, _label, _conf, _proc):
                        entry_frame = ctk.CTkFrame(parent, border_width=1)
                        entry_frame.pack(fill="x", pady=5)
                        ctk.CTkLabel(entry_frame, text=f"{_label.upper()} - Độ tin cậy: {_conf:.1%}", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
                        ctk.CTkLabel(entry_frame, text=f"Gợi ý: {_proc}", justify="left", wraplength=300).pack(anchor="w", padx=10, pady=(0,5))

                    self.after(0, lambda l=label_name, c=final_confidence, p=proc_text: create_result_entry(results_scroll_frame, l, c, p))
                
                if pred_win.winfo_exists():
                    self.after(0, lambda: pred_win.title("Phát Hiện Hoàn Tất"))

            except Exception as e:
                if pred_win.winfo_exists():
                    self.after(0, lambda err=e: messagebox.showerror("Lỗi Phân Loại", str(err), parent=pred_win))
                    self.after(0, lambda: pred_win.title("Phát Hiện Thất Bại"))
            finally:
                if pred_win.winfo_exists():
                    self.after(0, lambda: pred_win.close_button.configure(state="normal"))
        
        threading.Thread(target=prediction_thread, daemon=True).start()
    
    def on_closing(self):
        # Đảm bảo đóng kết nối CSDL khi thoát ứng dụng
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát chương trình?"):
            self.destroy()

if __name__ == '__main__':
    if cv2 is None:
        messagebox.showerror("Thiếu thư viện", "Vui lòng cài đặt OpenCV để sử dụng tính năng camera.\nChạy lệnh: pip install opencv-python")
        sys.exit(1)
        
    init_db()
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing) # Xử lý sự kiện đóng cửa sổ
    app.mainloop()