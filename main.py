import os
import hashlib
import tkinter as tk
import customtkinter
import win32gui
import win32process
import win32con
import win32api
import psutil
import threading
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict
import pystray
from PIL import Image
import io

import reports

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("500x350")
        self._set_appearance_mode("System")

        # Load existing data
        self.app_data = defaultdict(lambda: {'total_time': 0.0, 'category': 'Uncategorized', 'exe_path': None, 'icon_path': None})
        self.category_data = defaultdict(float)
        self.current_app = None
        self.last_switch_time = datetime.now()
        self.time_unit = customtkinter.StringVar(value="hours")  # hours/minutes
        self.load_data()

        # Initialize icon cache
        self.cache_dir = "icon_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.icon_cache = {}
        self.default_icon = self.create_default_icon()

        # Tray icon setup
        self.tray_icon = None
        self.tray_running = False
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Add hourly logging structure
        self.hourly_log = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        self.load_hourly_data()

        # Configure GUI
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create tab view
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        # Create tabs
        self.realtime_tab = self.tabview.add("Real-time")
        self.daily_tab = self.tabview.add("Daily Report")
        self.weekly_tab = self.tabview.add("Weekly Report")

        # Real-time Tab Content
        self.setup_realtime_tab()

        # Daily Report Tab
        self.setup_daily_report_tab()

        # Weekly Report Tab
        self.setup_weekly_report_tab()

        # Create textbox with scrollbar
        self.textbox = customtkinter.CTkTextbox(self, wrap="none")
        self.textbox.pack(pady=20, padx=20, fill="both", expand=True)

        # Label
        self.label = customtkinter.CTkLabel(self)
        self.label.pack(pady=12, padx=60)

        # Control panel frame
        control_frame = customtkinter.CTkFrame(self)
        control_frame.pack(pady=10, padx=10, fill="x")

        # Time unit selector
        customtkinter.CTkLabel(control_frame, text="Display units:").pack(side="left", padx=5)
        unit_menu = customtkinter.CTkOptionMenu(control_frame,
                                      values=["hours", "minutes", "hh:mm:ss"],
                                      variable=self.time_unit,
                                      command=lambda _: self.update_gui())
        unit_menu.pack(side="left", padx=5)

        # Right-click context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Set Category", command=self.show_category_menu)
        self.context_menu.add_command(label="Create New Category", command=self.create_new_category)
        self.textbox.bind("<Button-3>", self.show_context_menu)
        self.selected_app = None

        # Start monitoring thread
        self.stop_thread = False
        self.monitor_thread = threading.Thread(target=self.monitor_active_window)
        self.monitor_thread.start()

        # Start GUI updates
        self.update_gui()

    def setup_realtime_tab(self):
        # ... [Keep existing real-time UI elements] ...
        pass

    def setup_daily_report_tab(self):
        # Date selection
        self.daily_date = customtkinter.CTkEntry(self.daily_tab, placeholder_text="YYYY-MM-DD")
        self.daily_date.pack(pady=5)

        # Report display
        self.daily_text = customtkinter.CTkTextbox(self.daily_tab, wrap="none")
        self.daily_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Buttons
        btn_frame = customtkinter.CTkFrame(self.daily_tab)
        btn_frame.pack(pady=5)

        customtkinter.CTkButton(btn_frame, text="Generate", command=reports.generate_daily_report).pack(side="left", padx=5)
        customtkinter.CTkButton(btn_frame, text="Export CSV", command=reports.export_daily_csv).pack(side="left", padx=5)

    def setup_weekly_report_tab(self):
        # Week selection
        self.weekly_date = customtkinter.CTkEntry(self.weekly_tab, placeholder_text="YYYY-MM-DD (any date in week)")
        self.weekly_date.pack(pady=5)

        # Report display
        self.weekly_text = customtkinter.CTkTextbox(self.weekly_tab, wrap="none")
        self.weekly_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Buttons
        btn_frame = customtkinter.CTkFrame(self.weekly_tab)
        btn_frame.pack(pady=5)

        customtkinter.CTkButton(btn_frame, text="Generate", command=reports.generate_weekly_report).pack(side="left", padx=5)
        customtkinter.CTkButton(btn_frame, text="Export CSV", command=reports.export_weekly_csv).pack(side="left", padx=5)

    def minimize_to_tray(self):
        """Hide window and create tray icon"""
        self.withdraw()
        self.create_tray_icon()

    def create_tray_icon(self):
        """Create system tray icon with menu"""
        if not self.tray_running:
            # Generate blank image for tray icon
            image = Image.new('RGB', (64, 64), (255, 255, 255))

            menu = pystray.Menu(
                pystray.MenuItem('Show App', self.show_window),
                pystray.MenuItem('Exit', self.clean_exit)
            )

            self.tray_icon = pystray.Icon("time_tracker", image, "Time Tracker", menu)
            self.tray_running = True

            # Run tray icon in separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        """Restore the main window"""
        self.after(0, self.deiconify)
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_running = False

    def get_active_process(self):
        _, pid = win32process.GetWindowThreadProcessId( win32gui.GetForegroundWindow())

        try:
            return psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Unknown"

    def create_default_icon(self):
        """Create a default icon for apps without available icons"""
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        return None
        #return customtkinter.CTkImage(light_image=img, size=(32, 32))

    def get_icon_from_hwnd(self, hwnd):
        try:
            # Try to get large icon first
            hicon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_BIG, 0)
            if not hicon:
                hicon = win32gui.GetClassLong(hwnd, win32con.GCL_HICON)

            if not hicon:
                # Fallback to executable icon
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                exe_path = process.exe()
                large_icons, _ = win32gui.ExtractIconEx(exe_path, 0)
                hicon = large_icons[0] if large_icons else 0

            if hicon:
                # Get icon info
                icon_info = win32gui.GetIconInfo(hicon)
                width = icon_info[5]  # xHotspot = width
                height = icon_info[6] # yHotspot = height

                # Create compatible DC
                hdc = win32gui.CreateCompatibleDC(0)
                hbmp = win32gui.CreateCompatibleBitmap(hdc, width, height)
                win32gui.SelectObject(hdc, hbmp)

                # Draw the icon
                win32gui.DrawIconEx(hdc, 0, 0, hicon, width, height, 0, 0, 0x0003)

                # Get bitmap using win32ui
                bmp = win32ui.CreateBitmapFromHandle(hbmp)
                bmp_info = bmp.GetInfo()
                bmp_str = bmp.GetBitmapBits(True)

                # Convert to PIL Image
                img = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_str, 'raw', 'BGRX', 0, 1
            )

                # Cleanup resources
                win32gui.DeleteObject(hbmp)
                win32gui.DeleteDC(hdc)
                win32gui.DestroyIcon(hicon)

            return img

        except Exception as e:
            print(f"Icon error: {e}")
        return None

    def cache_application_icon(self, hwnd, app_name, exe_path):
        """Capture and cache application icon"""
        # Generate unique cache key
        cache_key = hashlib.md5(f"{app_name}{exe_path}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")

        # Return cached icon if exists
        if os.path.exists(cache_path):
            return cache_path
            #return customtkinter.CTkImage(light_image=Image.open(cache_path), size=(32, 32))

        # Capture new icon
        icon_img = self.get_icon_from_hwnd(hwnd)
        if icon_img:
            try:
                icon_img.save(cache_path)
                return cache_path
                #return customtkinter.CTkImage(light_image=icon_img, size=(32, 32))
            except Exception as e:
                print(f"Save failed: {e}")

        # Fallback to default icon
        return self.default_icon

    def log_hourly_usage(self, app_name, start_time, end_time):
        """Log time spent in application across hourly intervals"""
        current = start_time
        while current < end_time:
            next_hour = (current + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            end_segment = min(next_hour, end_time)
            duration = (end_segment - current).total_seconds()

            date_str = current.strftime("%Y-%m-%d")
            hour_str = current.strftime("%H:00")

            self.hourly_log[date_str][hour_str][app_name] += duration
            current = next_hour

    def save_hourly_data(self):
        """Save hourly data to JSON file"""
        # Convert defaultdict to regular dict for JSON serialization
        save_data = {}
        for date, hours in self.hourly_log.items():
            save_data[date] = {}
            for hour, apps in hours.items():
                save_data[date][hour] = dict(apps)

        with open("hourly_usage.json", "w") as f:
            json.dump(save_data, f, indent=2)

    def load_hourly_data(self):
        """Load hourly data from JSON file"""
        if os.path.exists("hourly_usage.json"):
            with open("hourly_usage.json", "r") as f:
                data = json.load(f)
                for date, hours in data.items():
                    for hour, apps in hours.items():
                        self.hourly_log[date][hour] = defaultdict(float, apps)

    def monitor_active_window(self):
        last_title, last_process = None, None
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        while not self.stop_thread:
            current_process = self.get_active_process()
            now = datetime.now()

            if current_process != self.current_app:
                print(f"Window switched to: {current_process}")

                try:
                    process = psutil.Process(pid)
                    exe_path = process.exe()
                    app_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    app_name = "Unknown"
                    exe_path = None

                if self.current_app is not None:
                    # Calculate and log time spent
                    time_spent = (now - self.last_switch_time).total_seconds()
                    self.app_data[self.current_app]['total_time'] += time_spent

                    # Log to hourly data
                    self.log_hourly_usage(self.current_app, self.last_switch_time, now)

                    # Update category time
                    category = self.app_data[self.current_app]['category']
                    self.category_data[category] += time_spent

                # Update current app info
                self.current_app = current_process
                self.app_data[self.current_app]['exe_path'] = exe_path
                self.app_data[app_name]['icon_path'] = self.cache_application_icon(hwnd, app_name, exe_path)
                self.last_switch_time = now
                self.save_data()
                self.save_hourly_data()  # Save hourly data when switching apps
                self.label.configure(text=current_process)

            time.sleep(1)  # Check every second

    def update_gui(self):
        """Update the GUI with current tracking data"""
        # Calculate current session time
        display_data = {k: v.copy() for k, v in self.app_data.items()}
        if self.current_app:
            current_time = (datetime.now() - self.last_switch_time).total_seconds()
            display_data[self.current_app]['total_time'] += current_time

        # Organize data by category
        category_dict = defaultdict(list)
        for app, data in display_data.items():
            category_dict[data['category']].append((app, data['total_time']))

        # Update textbox
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")

        # Display categories and apps
        for category, apps in sorted(category_dict.items(), key=lambda x: sum(t[1] for t in x[1]), reverse=True):
            total_time = sum(t[1] for t in apps)
            self.textbox.insert("end", f"[ {category} ] - {self.format_time(total_time)}\n", "category_header")

            for app, time in sorted(apps, key=lambda x: x[1], reverse=True):
                self.textbox.insert("end", f"  {app.ljust(30)} {self.format_time(time)}\n")

            self.textbox.insert("end", "\n")

        self.textbox.configure(state="disabled")
        self.after(1000, self.update_gui)

    def show_context_menu(self, event):
        """Show right-click context menu"""
        index = self.textbox.index(f"@{event.x},{event.y}")
        line = int(index.split(".")[0])
        content = self.textbox.get(f"{line}.0", f"{line}.end")

        if "[" in content and "]" in content:
            self.selected_app = None
        else:
            self.selected_app = content.split("  ")[1].split()[0].strip()
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def show_category_menu(self):
        """Show category selection menu"""
        if not self.selected_app:
            return

        category_menu = customtkinter.CTkMenu(self.context_menu, tearoff=0)
        for category in sorted(self.category_data.keys()):
            category_menu.add_command(
                label=category,
                command=lambda c=category: self.set_app_category(c)
            )
        category_menu.add_separator()
        category_menu.add_command(label="Create New...", command=self.create_new_category)
        category_menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def set_app_category(self, category):
        """Assign selected app to a category"""
        if self.selected_app:
            # Remove old category time
            old_category = self.app_data[self.selected_app]['category']
            self.category_data[old_category] -= self.app_data[self.selected_app]['time']

            # Update to new category
            self.app_data[self.selected_app]['category'] = category
            self.category_data[category] += self.app_data[self.selected_app]['time']

            self.save_data()

    def create_new_category(self):
        """Create a new category through dialog"""
        dialog = customtkinter.CTkInputDialog(text="Enter new category name:", title="New Category")
        new_category = dialog.get_input()

        if new_category and new_category not in self.category_data:
            self.category_data[new_category] = 0.0
            if self.selected_app:
                self.set_app_category(new_category)

    def save_data(self):
        """Save tracking data to JSON file"""
        data = {
            'app_data': dict(self.app_data),
            'category_data': dict(self.category_data)
        }
        with open("app_usage.json", "w") as f:
            json.dump(data, f)

    def load_data(self):
        """Load tracking data from JSON file"""
        try:
            with open("app_usage.json", "r") as f:
                data = json.load(f)
                self.app_data.update(data.get('app_data', {}))
                self.category_data.update(data.get('category_data', {}))
        except FileNotFoundError:
            pass

    def format_time(self, seconds):
        """Convert seconds to human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def clean_exit(self):
        """Stop monitoring and exit completely"""
        self.stop_thread = True
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()


    def on_closing(self):
        """Handle window closing via tray exit"""
        self.clean_exit()

if __name__ == "__main__":
    app = App()
    app.mainloop()
