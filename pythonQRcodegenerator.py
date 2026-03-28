import tkinter as tk
from tkinter import messagebox, colorchooser, filedialog
import customtkinter as ctk
import cv2
import qrcode
from PIL import Image, ImageTk, ImageDraw
import json
import os
import webbrowser
import winsound

# Appearance settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UltimateQRPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ultimate QR Pro - Email & WiFi Edition")
        self.geometry("1200x850")

        # Data and State
        self.history_file = os.path.join(os.path.dirname(__file__), "qr_pro_data.json")
        self.history_data = self.load_history()
        self.camera_running = False
        self.cap = None
        self.selected_color = "#1f538d"
        self.last_scanned = ""
        self.current_img = None
        self.mode = "Text/URL"

        self.setup_ui()
        self.qr_detector = cv2.QRCodeDetector()  # OpenCV QR Detector

    # ------------------- UI -------------------
    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Panel
        self.left_panel = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=5)

        ctk.CTkLabel(self.left_panel, text="GENERATE QR", font=("Arial", 20, "bold")).pack(pady=10)

        self.mode_selector = ctk.CTkSegmentedButton(self.left_panel, values=["Text/URL", "Email", "WiFi"], command=self.change_mode)
        self.mode_selector.set("Text/URL")
        self.mode_selector.pack(pady=10)

        self.input_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20)
        self.show_text_inputs()

        self.label_var = ctk.StringVar()
        ctk.CTkEntry(self.left_panel, placeholder_text="Add Label (Optional)", textvariable=self.label_var, width=250).pack(pady=10)

        self.color_btn = ctk.CTkButton(self.left_panel, text="Pick Color", fg_color=self.selected_color, command=self.pick_color)
        self.color_btn.pack(pady=5)

        self.gen_btn = ctk.CTkButton(self.left_panel, text="CREATE QR", fg_color="#2ecc71", command=self.generate_qr)
        self.gen_btn.pack(pady=10)

        self.save_btn = ctk.CTkButton(self.left_panel, text="SAVE IMAGE", fg_color="#3498db", state="disabled", command=self.save_qr)
        self.save_btn.pack(pady=5)

        self.theme_btn = ctk.CTkButton(self.left_panel, text="Switch Theme", fg_color="transparent", border_width=1, command=self.toggle_theme)
        self.theme_btn.pack(pady=10)

        self.exit_btn = ctk.CTkButton(self.left_panel, text="QUIT APP", fg_color="#e74c3c", command=self.on_closing)
        self.exit_btn.pack(side="bottom", pady=20)

        # Center Panel
        self.center_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        self.preview_label = ctk.CTkLabel(self.center_panel, text="QR PREVIEW AREA", width=300, height=300, fg_color="#1a1a1a", corner_radius=15)
        self.preview_label.pack(pady=15)

        self.cam_label = ctk.CTkLabel(self.center_panel, text="CAMERA STANDBY", width=550, height=350, fg_color="black", corner_radius=15)
        self.cam_label.pack(pady=10)

        self.scan_ctrl_frame = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        self.scan_ctrl_frame.pack()
        self.start_btn = ctk.CTkButton(self.scan_ctrl_frame, text="START SCANNER", fg_color="#2ecc71", command=self.start_camera)
        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn = ctk.CTkButton(self.scan_ctrl_frame, text="STOP SCANNER", fg_color="#e74c3c", command=self.stop_camera, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=10)

        # Right Panel
        self.right_panel = ctk.CTkFrame(self, width=280)
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.right_panel, text="SCANNED LINKS", font=("Arial", 16, "bold")).pack(pady=10)
        self.links_box = tk.Listbox(self.right_panel, height=8, bg="#1e1e1e", fg="#3498db", font=("Arial", 10, "underline"), borderwidth=0)
        self.links_box.pack(fill="x", padx=10)
        self.links_box.bind("<Double-Button-1>", self.open_browser)

        ctk.CTkLabel(self.right_panel, text="FULL HISTORY", font=("Arial", 16, "bold")).pack(pady=10)
        self.history_box = tk.Listbox(self.right_panel, bg="#1e1e1e", fg="white", borderwidth=0)
        self.history_box.pack(fill="both", expand=True, padx=10)

        self.clear_btn = ctk.CTkButton(self.right_panel, text="CLEAR LOGS", fg_color="#c0392b", command=self.clear_all)
        self.clear_btn.pack(pady=15)

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Paste", command=self.paste_from_clipboard)
        self.refresh_ui_logs()

        # Keyboard paste binding
        self.bind_all("<Control-v>", lambda e: self.paste_from_clipboard())
        self.bind_all("<Command-v>", lambda e: self.paste_from_clipboard())  # macOS

    # ------------------- Inputs -------------------
    def change_mode(self, mode):
        self.mode = mode
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        if mode == "Text/URL":
            self.show_text_inputs()
        elif mode == "Email":
            self.show_email_inputs()
        elif mode == "WiFi":
            self.show_wifi_inputs()

    def show_text_inputs(self):
        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter link or text...", width=250, height=40)
        self.entry.pack(pady=10)
        self.entry.bind("<Button-3>", lambda e: self.menu.post(e.x_root, e.y_root))

    def show_email_inputs(self):
        self.email_to = ctk.CTkEntry(self.input_frame, placeholder_text="Recipient Email", width=250)
        self.email_to.pack(pady=5)
        self.email_sub = ctk.CTkEntry(self.input_frame, placeholder_text="Subject", width=250)
        self.email_sub.pack(pady=5)
        self.email_msg = ctk.CTkTextbox(self.input_frame, width=250, height=80)
        self.email_msg.pack(pady=5)

    def show_wifi_inputs(self):
        self.wifi_ssid = ctk.CTkEntry(self.input_frame, placeholder_text="WiFi Name (SSID)", width=250)
        self.wifi_ssid.pack(pady=5)
        self.wifi_pass = ctk.CTkEntry(self.input_frame, placeholder_text="Password", width=250, show="*")
        self.wifi_pass.pack(pady=5)
        self.wifi_type = ctk.CTkComboBox(self.input_frame, values=["WPA", "WEP", "nopass"], width=250)
        self.wifi_type.pack(pady=5)
        self.wifi_type.set("WPA")

    # ------------------- QR Generation -------------------
    def generate_qr(self):
        qr_data = ""
        if self.mode == "Text/URL":
            qr_data = self.entry.get()
        elif self.mode == "Email":
            qr_data = f"MATMSG:TO:{self.email_to.get()};SUB:{self.email_sub.get()};BODY:{self.email_msg.get('0.0', tk.END).strip()};;"
        elif self.mode == "WiFi":
            qr_data = f"WIFI:S:{self.wifi_ssid.get()};T:{self.wifi_type.get()};P:{self.wifi_pass.get()};;"

        if not qr_data.strip():
            messagebox.showwarning("Warning", "Please enter some data!")
            return

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
        qr.add_data(qr_data)
        img = qr.make_image(fill_color=self.selected_color, back_color="white").convert('RGB')

        lbl = self.label_var.get()
        if lbl:
            draw = ImageDraw.Draw(img)
            draw.text((10, 2), lbl, fill=self.selected_color)

        self.current_img = img
        img_display = img.resize((280, 280), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_display)
        self.preview_label.configure(image=img_tk, text="")
        self.preview_label.image = img_tk
        self.save_btn.configure(state="normal")
        self.add_to_history(qr_data)

    # ------------------- Camera -------------------
    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened(): return
        self.camera_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.update_scanner()

    def update_scanner(self):
        if self.camera_running:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                # OpenCV QR Detector
                data, bbox, _ = self.qr_detector.detectAndDecode(frame)
                if data and data != self.last_scanned:
                    self.last_scanned = data
                    winsound.Beep(1000, 150)
                    messagebox.showinfo("Scanned", data)
                    self.add_to_history(data)
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((550, 350))
                img_tk = ImageTk.PhotoImage(img)
                self.cam_label.configure(image=img_tk, text="")
                self.cam_label.image = img_tk
            self.after(10, self.update_scanner)

    def stop_camera(self):
        self.camera_running = False
        if self.cap: self.cap.release()
        self.cam_label.configure(image="", text="CAMERA STANDBY")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    # ------------------- Utility -------------------
    def paste_from_clipboard(self):
        try:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.clipboard_get())
            clip = self.clipboard_get()
            if clip.startswith("http"):
                webbrowser.open(clip)
        except tk.TclError:
            pass

    def open_browser(self, event):
        sel = self.links_box.curselection()
        if sel: webbrowser.open(self.links_box.get(sel[0]))

    def add_to_history(self, data):
        if data not in self.history_data:
            self.history_data.insert(0, data)
            self.save_history()
            self.refresh_ui_logs()

    def refresh_ui_logs(self):
        self.history_box.delete(0, tk.END)
        self.links_box.delete(0, tk.END)
        for item in self.history_data:
            self.history_box.insert(tk.END, item)
            if any(s in str(item) for s in ["http", "WIFI:", "MATMSG:"]):
                self.links_box.insert(tk.END, item)

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f: return json.load(f)
        return []

    def save_history(self):
        with open(self.history_file, 'w') as f: json.dump(self.history_data, f)

    def clear_all(self):
        self.history_data = []
        self.save_history()
        self.refresh_ui_logs()

    def pick_color(self):
        color = colorchooser.askcolor(initialcolor=self.selected_color)[1]
        if color:
            self.selected_color = color
            self.color_btn.configure(fg_color=color)

    def toggle_theme(self):
        ctk.set_appearance_mode("Light" if ctk.get_appearance_mode() == "Dark" else "Dark")

    def save_qr(self):
        if self.current_img:
            f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if f: self.current_img.save(f)

    def on_closing(self):
        self.camera_running = False
        if self.cap: self.cap.release()
        self.destroy()


if __name__ == "__main__":
    app = UltimateQRPro()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()