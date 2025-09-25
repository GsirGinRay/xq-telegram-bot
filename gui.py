import tkinter as tk
from tkinter import messagebox
import json
import os
import subprocess
import time

class XQManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("XQ Telegram Manager")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        self.process = None
        self.is_running = False

        self.create_widgets()
        self.load_config()
        self.update_status()

    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="XQ Telegram Manager",
                        font=('Arial', 16, 'bold'))
        title.pack(pady=20)

        # Telegram Config
        config_frame = tk.LabelFrame(self.root, text="Telegram Settings", padx=10, pady=10)
        config_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(config_frame, text="Bot Token:").pack(anchor='w')
        self.token_entry = tk.Entry(config_frame, width=50, show='*')
        self.token_entry.pack(fill='x', pady=(0,10))

        tk.Label(config_frame, text="Chat ID:").pack(anchor='w')
        self.chat_entry = tk.Entry(config_frame, width=50)
        self.chat_entry.pack(fill='x', pady=(0,10))

        btn_frame1 = tk.Frame(config_frame)
        btn_frame1.pack(fill='x')

        tk.Button(btn_frame1, text="Save Config", command=self.save_config,
                 bg='#4CAF50', fg='white').pack(side='left', padx=(0,10))

        tk.Button(btn_frame1, text="Get Chat ID", command=self.get_chat_id,
                 bg='#2196F3', fg='white').pack(side='left')

        # Service Control
        service_frame = tk.LabelFrame(self.root, text="Service Control", padx=10, pady=10)
        service_frame.pack(fill='x', padx=20, pady=10)

        self.status_label = tk.Label(service_frame, text="Service Stopped",
                                   font=('Arial', 12, 'bold'), fg='red')
        self.status_label.pack(pady=10)

        btn_frame2 = tk.Frame(service_frame)
        btn_frame2.pack()

        self.start_btn = tk.Button(btn_frame2, text="Start", command=self.start_service,
                                  bg='#4CAF50', fg='white', width=10)
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(btn_frame2, text="Stop", command=self.stop_service,
                                 bg='#f44336', fg='white', width=10, state='disabled')
        self.stop_btn.pack(side='left', padx=5)

        # Test
        test_frame = tk.LabelFrame(self.root, text="Test", padx=10, pady=10)
        test_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(test_frame, text="Send Test Message", command=self.test_message,
                 bg='#FF9800', fg='white', width=20).pack(pady=5)

        # Quick Actions
        quick_frame = tk.LabelFrame(self.root, text="Quick Actions", padx=10, pady=10)
        quick_frame.pack(fill='x', padx=20, pady=10)

        btn_frame3 = tk.Frame(quick_frame)
        btn_frame3.pack()

        tk.Button(btn_frame3, text="Open Folder", command=self.open_directory,
                 width=10).pack(side='left', padx=2)

        tk.Button(btn_frame3, text="Auto Start", command=self.setup_autostart,
                 width=10).pack(side='left', padx=2)

        tk.Button(btn_frame3, text="Help", command=self.show_help,
                 width=10).pack(side='left', padx=2)

        # Info
        tk.Label(self.root, text="Monitoring: local/xq_trigger.txt",
                fg='gray').pack(pady=10)

    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self.token_entry.insert(0, config.get('telegram_bot_token', ''))
                self.chat_entry.insert(0, str(config.get('telegram_chat_id', '')))
        except:
            pass

    def save_config(self):
        token = self.token_entry.get().strip()
        chat_id = self.chat_entry.get().strip()

        if not token or not chat_id:
            messagebox.showerror("Error", "Please enter both Token and Chat ID")
            return

        try:
            chat_id = int(chat_id)
        except:
            pass

        config = {
            "telegram_bot_token": token,
            "telegram_chat_id": chat_id,
            "watch_directory": "./local"
        }

        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            os.makedirs('local', exist_ok=True)
            messagebox.showinfo("Success", "Config saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def get_chat_id(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter Bot Token first")
            return

        try:
            import requests
            response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result'):
                    updates = data['result']
                    if updates:
                        chat_id = updates[-1]['message']['chat']['id']
                        self.chat_entry.delete(0, tk.END)
                        self.chat_entry.insert(0, str(chat_id))
                        messagebox.showinfo("Success", f"Chat ID: {chat_id}")
                    else:
                        messagebox.showwarning("Notice", "Please send /start to your bot first")
                else:
                    messagebox.showerror("Error", "Failed to get updates")
        except ImportError:
            messagebox.showerror("Error", "Please install requests: pip install requests")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    def start_service(self):
        if self.is_running:
            return

        if not os.path.exists('config.json'):
            messagebox.showerror("Error", "Please save config first")
            return

        try:
            self.process = subprocess.Popen(
                ["python", "XQTelegramNotifier.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.is_running = True
            self.update_buttons()
            messagebox.showinfo("Success", "Service started!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start: {e}")

    def stop_service(self):
        if not self.is_running:
            return

        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)

            self.is_running = False
            self.update_buttons()
            messagebox.showinfo("Success", "Service stopped!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop: {e}")

    def test_message(self):
        try:
            os.makedirs('local', exist_ok=True)
            test_msg = f"Test message - {time.strftime('%H:%M:%S')}"

            with open('local/xq_trigger.txt', 'w', encoding='utf-8') as f:
                f.write(test_msg)

            messagebox.showinfo("Success", "Test message sent!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    def open_directory(self):
        try:
            os.makedirs('local', exist_ok=True)
            os.startfile('local')
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open: {e}")

    def setup_autostart(self):
        result = messagebox.askyesno("Auto Start", "Setup auto start on boot?")
        if result:
            try:
                startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
                bat_content = f'''@echo off
cd /d "{os.path.abspath('.')}"
python XQTelegramNotifier.py'''

                with open(os.path.join(startup_folder, "XQTelegram.bat"), 'w') as f:
                    f.write(bat_content)

                messagebox.showinfo("Success", "Auto start setup completed!")
            except Exception as e:
                messagebox.showerror("Error", f"Setup failed: {e}")

    def show_help(self):
        help_text = """Usage:

1. Enter Bot Token and Chat ID
2. Click 'Save Config'
3. Click 'Send Test Message' to verify
4. Click 'Start' to begin service

In XQ use:
print("message", file=r"path\\local\\xq_trigger.txt")"""

        messagebox.showinfo("Help", help_text)

    def update_buttons(self):
        if self.is_running:
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="Service Running", fg='green')
        else:
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_label.config(text="Service Stopped", fg='red')

    def update_status(self):
        if self.process and self.process.poll() is not None and self.is_running:
            self.is_running = False
            self.update_buttons()

        self.root.after(1000, self.update_status)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = XQManager()
    app.run()