import json
import os
import re
import shutil
import ssl
import sys
import tempfile
import threading
import urllib.request
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import ctypes
import customtkinter as ctk
import uuid  # [v1.1.0] Added

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
POLYFILL_URL = "https://unpkg.com/webextension-polyfill/dist/browser-polyfill.min.js"
POLYFILL_FILENAME = "browser-polyfill.min.js"

BLOCKED_PERMISSIONS = [
    "gcm", "background", "experimental", "ttsEngine", 
    "declarativeContent", "pageCapture", "system.cpu", "system.memory"
]

UNSUPPORTED_KEYS = [
    "update_url", "key", "oauth2", "minimum_chrome_version", 
    "requirements", "nacl_modules"
]

DISCLAIMER_FILE = ".disclaimer_accepted"

# ---------------------------------------------------------
# Logic Engine
# ---------------------------------------------------------
class ConverterEngine:
    def __init__(self, log_callback):
        self.log = log_callback

    def download_polyfill(self, destination_dir: Path):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            target_path = destination_dir / POLYFILL_FILENAME
            self.log(f"Downloading polyfill library...")
            
            # Timeout set to 10 seconds
            with urllib.request.urlopen(POLYFILL_URL, context=ctx, timeout=10) as response:
                with open(target_path, 'wb') as f:
                    f.write(response.read())
            return POLYFILL_FILENAME
        except Exception as e:
            self.log(f"[Error] Polyfill download failed: {e}")
            return None

    def generate_gecko_id(self, extension_name: str):
        # [v1.1.0] Name-based deterministic UUID generation (supports updates)
        unique_id = uuid.uuid5(uuid.NAMESPACE_DNS, extension_name)
        return f"{{{str(unique_id)}}}"

    def patch_manifest(self, manifest_path: Path, polyfill_file: str):
        self.log(f"Processing manifest: {manifest_path.name}")
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Manifest file is invalid JSON.")

        app_name = data.get("name", "Unknown App")

        # 1. Add Gecko ID
        if "browser_specific_settings" not in data:
            data["browser_specific_settings"] = {
                "gecko": {
                    "id": self.generate_gecko_id(app_name),
                    "strict_min_version": "109.0"
                }
            }

        # 2. Service Worker -> Background Scripts
        background = data.get("background", {})
        if "service_worker" in background:
            self.log("Converting Service Worker to Background Scripts...")
            worker_script = background.pop("service_worker")
            scripts = background.get("scripts", [])
            if worker_script not in scripts:
                scripts.append(worker_script)
            background["scripts"] = scripts
            data["background"] = background

        ### [START CHANGE]
        # [v1.2.0] Convert Chrome Side Panel to Firefox Sidebar Action
        if "side_panel" in data:
            self.log("Converting Chrome Side Panel to Firefox Sidebar...")
            side_panel_data = data.pop("side_panel")
            default_path = side_panel_data.get("default_path", "")
            
            if default_path:
                sidebar_action = {
                    "default_panel": default_path,
                    "default_title": app_name
                }
                # Inherit icon if available
                if "icons" in data:
                    sidebar_action["default_icon"] = data["icons"]
                
                data["sidebar_action"] = sidebar_action
            
            # Remove 'side_panel' permission (unsupported in Firefox)
            if "permissions" in data and "side_panel" in data["permissions"]:
                data["permissions"].remove("side_panel")

        # [v1.2.0] Fix Incognito Compatibility (split -> spanning)
        if data.get("incognito") == "split":
            self.log("⚠️ Fixed: 'incognito: split' -> 'spanning'")
            data["incognito"] = "spanning"
        ### [END CHANGE]

        # 3. Inject Polyfill
        if polyfill_file:
            if "background" in data and "scripts" in data["background"]:
                if polyfill_file not in data["background"]["scripts"]:
                    data["background"]["scripts"].insert(0, polyfill_file)
            for script_item in data.get("content_scripts", []):
                if "js" in script_item and polyfill_file not in script_item["js"]:
                    script_item["js"].insert(0, polyfill_file)

        # 4. Filter Permissions
        if "permissions" in data:
            data["permissions"] = [p for p in data["permissions"] if p not in BLOCKED_PERMISSIONS]

        # 5. Remove Unnecessary Keys
        for key in UNSUPPORTED_KEYS:
            data.pop(key, None)

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def process(self, input_path: str, save_callback):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                work_dir = Path(temp_dir)
                input_path = Path(input_path)
                
                self.log("Extracting package...")
                if input_path.is_dir():
                    shutil.copytree(input_path, work_dir, dirs_exist_ok=True)
                elif zipfile.is_zipfile(input_path):
                    with zipfile.ZipFile(input_path, 'r') as zf:
                        zf.extractall(work_dir)
                else:
                    raise ValueError("Unsupported file format.")

                manifests = list(work_dir.rglob("manifest.json"))
                if not manifests:
                    raise FileNotFoundError("manifest.json not found.")
                
                manifest_path = manifests[0]
                root_dir = manifest_path.parent
                
                # --- [FIXED] Fail-safe Logic Start ---
                polyfill_file = self.download_polyfill(root_dir)
                
                if polyfill_file is None:
                    # Download failed! Stop everything.
                    error_msg = "인터넷 연결을 확인해주세요.\nPolyfill 파일을 다운로드할 수 없어 변환을 중단합니다."
                    self.log(f"❌ CRITICAL: {error_msg.replace(chr(10), ' ')}")
                    messagebox.showerror("Connection Error", error_msg)
                    return # Stop execution here
                # --- [FIXED] Fail-safe Logic End ---

                self.patch_manifest(manifest_path, polyfill_file)

                default_name = f"{input_path.stem}_firefox.xpi"
                save_path = save_callback(default_name)
                
                if not save_path:
                    self.log("Save operation cancelled.")
                    return

                self.log(f"Saving to: {Path(save_path).name}")
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for folder, _, files in os.walk(root_dir):
                        for file in files:
                            abs_path = Path(folder) / file
                            rel_path = abs_path.relative_to(root_dir)
                            zf.write(abs_path, rel_path)

            self.log("Conversion completed successfully.")
            messagebox.showinfo("Success", f"Done!\nSaved as: {Path(save_path).name}")

        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

# ---------------------------------------------------------
# Modern UI
# ---------------------------------------------------------
class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Theme Setup
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Window Setup
        self.title("Chrome Extension Porter")
        self.geometry("600x550")
        self.resizable(False, False)
        
        self.engine = ConverterEngine(self.log_message)
        
        # Check disclaimer before showing UI
        if not self.check_disclaimer():
            self.destroy()
            return
            
        self.setup_ui()

    def check_disclaimer(self):
        """Show legal disclaimer on first run"""
        if os.path.exists(DISCLAIMER_FILE):
            return True
        
        disclaimer_text = """⚠️ LEGAL NOTICE ⚠️

This tool is intended ONLY for:

✅ Converting YOUR OWN extensions
✅ Converting open-source extensions (MIT, GPL, etc.)
✅ Educational and research purposes

NOT for:

❌ Converting proprietary extensions without permission
❌ Redistributing converted extensions
❌ Violating Chrome Web Store Terms of Service

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are solely responsible for ensuring you have 
the legal right to convert and use any extension.

The developer assumes NO LIABILITY for misuse.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do you understand and agree to these terms?"""
        
        result = messagebox.askyesno(
            "Legal Disclaimer - First Run",
            disclaimer_text,
            icon='warning'
        )
        
        if result:
            # Create marker file
            with open(DISCLAIMER_FILE, 'w') as f:
                f.write("User accepted disclaimer")
            return True
        else:
            messagebox.showinfo(
                "Application Closed",
                "You must accept the terms to use this application."
            )
            return False

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 1. Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self.header_frame, text="Chrome → Firefox Porter", 
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(self.header_frame, text="Educational MV3 Extension Converter", 
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w")

        # 2. Input Section
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.input_frame, text="Source Extension", 
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.entry_path = ctk.CTkEntry(self.input_frame, placeholder_text="Select .crx, .zip, or folder...")
        self.entry_path.grid(row=1, column=0, sticky="ew", padx=(15, 10), pady=(0, 15))

        # Split Buttons: File vs Folder
        btn_box = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        btn_box.grid(row=1, column=1, padx=(0, 15), pady=(0, 15))

        self.btn_file = ctk.CTkButton(btn_box, text="File", width=60, command=self.browse_file)
        self.btn_file.pack(side="left", padx=(0, 5))
        
        self.btn_folder = ctk.CTkButton(btn_box, text="Folder", width=60, command=self.browse_folder)
        self.btn_folder.pack(side="left")

        # 3. Action Section
        self.btn_convert = ctk.CTkButton(self, text="START CONVERSION", height=40, 
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         state="disabled", command=self.start_process)
        self.btn_convert.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        # 4. Log Section
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.log_frame, text="Activity Log", 
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.console = ctk.CTkTextbox(self.log_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.console.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.console.configure(state="disabled")

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.progress.set(0)
        
        # Legal notice at bottom
        legal_frame = ctk.CTkFrame(self, fg_color="transparent")
        legal_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 10))
        ctk.CTkLabel(legal_frame, text="⚠️ For educational use only. You are responsible for legal compliance.", 
                     text_color="gray", font=ctk.CTkFont(size=10)).pack()

    def log_message(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", f"> {message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Extensions", "*.zip *.crx"), ("All Files", "*.*")])
        if file_path:
            self.set_path(file_path)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.set_path(folder_path)

    def set_path(self, path):
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, path)
        self.btn_convert.configure(state="normal")
        self.log_message(f"Selected: {Path(path).name}")

    def get_save_path(self, default_name):
        return filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".xpi",
            filetypes=[("Firefox Extension", "*.xpi")]
        )

    def start_process(self):
        target_path = self.entry_path.get()
        if not target_path: return
        
        self.btn_convert.configure(state="disabled")
        self.progress.start()
        self.log_message("Starting conversion process...")
        
        thread = threading.Thread(target=self.run_engine, args=(target_path,))
        thread.start()

    def run_engine(self, target_path):
        self.engine.process(target_path, self.get_save_path)
        self.after(0, self.reset_ui)

    def reset_ui(self):
        self.progress.stop()
        self.progress.set(0)
        self.btn_convert.configure(state="normal")

if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()
