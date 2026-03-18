import sys
import zipfile
import shutil
import re
from pathlib import Path
import importlib.util
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# ====================== LOAD PATHS ======================
spec = importlib.util.spec_from_file_location("paths", "paths.py")
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ImporterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KiCad SamacSys Importer")
        self.geometry("680x480")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="SamacSys → My KiCad Library", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)

        # ZIP selection
        self.zip_var = tk.StringVar()
        frame = ctk.CTkFrame(self)
        frame.pack(pady=10, padx=30, fill="x")
        ctk.CTkLabel(frame, text="SamacSys ZIP:").pack(side="left", padx=10)
        ctk.CTkEntry(frame, textvariable=self.zip_var, width=420).pack(side="left", padx=10)
        ctk.CTkButton(frame, text="Browse", width=90, command=self.browse).pack(side="left")

        ctk.CTkLabel(self, text="💡 Tip: Use Browse button (drag-and-drop needs extra extension)", font=ctk.CTkFont(size=12)).pack(pady=8)

        # Library choice
        ctk.CTkLabel(self, text="Import into:").pack(pady=(15,5))
        self.lib_var = tk.StringVar(value="MyPower")
        self.combo = ctk.CTkComboBox(self, values=["MyPassives", "MyConnectors", "MyPower", "MyAmplifiers", "MyICs"],
                                     variable=self.lib_var, width=300)
        self.combo.pack()

        # Big Import button
        self.btn = ctk.CTkButton(self, text="🚀 Import Part Now", height=50, font=ctk.CTkFont(size=18, weight="bold"),
                                 command=self.start_import)
        self.btn.pack(pady=30)

        # Status box
        self.logbox = ctk.CTkTextbox(self, height=160, wrap="word")
        self.logbox.pack(pady=10, padx=30, fill="both")
        self.log("Ready. Click Browse and pick a SamacSys ZIP.")

    def browse(self):
        f = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if f:
            self.zip_var.set(f)
            self.log(f"Selected: {Path(f).name}")

    def log(self, msg):
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")
        self.update_idletasks()

    # ====================== FULL IMPORT LOGIC (identical to your working CLI) ======================
    def start_import(self):
        zip_path = Path(self.zip_var.get().strip('"'))
        if not zip_path.exists():
            messagebox.showerror("Error", "ZIP file not found!")
            return

        self.btn.configure(state="disabled")
        self.log(f"\n🔄 Processing: {zip_path.name}")

        temp_dir = Path("temp_samacsys")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_dir)

        fp_file = next(temp_dir.rglob("*.kicad_mod"), None)
        sym_file = next(temp_dir.rglob("*.kicad_sym"), None)
        step_file = next((f for f in temp_dir.rglob("*") if f.suffix.lower() in (".step", ".stp")), None)

        if not fp_file or not sym_file:
            self.log("❌ Missing symbol or footprint")
            return

        footprint_name = fp_file.stem
        with open(sym_file, "r", encoding="utf-8") as f:
            data = f.read()

        m = re.search(r'\(symbol "([^"]+)"', data)
        symbol_name = m.group(1) if m else footprint_name

        sym_lib = self.lib_var.get()
        target_sym = paths.YOUR_LIBRARY_ROOT / "symbols" / f"{sym_lib}.kicad_sym"
        target_fp  = paths.YOUR_LIBRARY_ROOT / "footprints" / f"{sym_lib}.pretty" / f"{footprint_name}.kicad_mod"
        target_3d  = paths.YOUR_LIBRARY_ROOT / "3dmodels" / sym_lib / f"{footprint_name}.step"

        # Duplicate check
        def extract_symbols(content):
            symbols = []
            i = 0
            while True:
                start = content.find('(symbol "', i)
                if start == -1: break
                depth = 0
                for j in range(start, len(content)):
                    if content[j] == '(': depth += 1
                    elif content[j] == ')':
                        depth -= 1
                        if depth == 0:
                            symbols.append(content[start:j+1])
                            i = j + 1
                            break
                else: break
            return symbols

        if target_sym.exists() and target_sym.stat().st_size > 10:
            with open(target_sym, "r", encoding="utf-8") as f:
                lib_data = f.read()
            existing = extract_symbols(lib_data)
            exists = any(symbol_name in b[:300] for b in existing)
        else:
            existing = []
            exists = False

        if exists:
            ans = messagebox.askyesnocancel("Duplicate Found", f"'{symbol_name}' already exists.\nReplace it?")
            if ans is None:
                self.log("Cancelled by user")
                self.btn.configure(state="normal")
                return
            if ans:
                existing = [b for b in existing if symbol_name not in b[:300]]
                self.log("✅ Old symbol removed")
            else:
                self.log("✅ Kept existing symbol")
        else:
            self.log(f"✅ New part: {symbol_name}")

        # Add new symbol
        new_blocks = extract_symbols(data)
        if new_blocks:
            block = new_blocks[0]
            full_fp = f"{sym_lib}:{footprint_name}"
            block = re.sub(r'(\(property "Footprint" )"[^"]*"', rf'\1"{full_fp}"', block)
            existing.append(block)

        # Write clean library
        header = '''(kicad_symbol_lib
  (version 20241209)
  (generator "kicad_symbol_editor")
  (generator_version "9.0")
'''
        final = header + "\n".join(existing) + "\n)"
        target_sym.write_text(final, encoding="utf-8")
        self.log(f"   Library now has {len(existing)} symbols")

        # Footprint
        target_fp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fp_file, target_fp)
        self.log("✅ Footprint copied")

        # 3D + path fix
        if step_file:
            target_3d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(step_file, target_3d)
            with open(target_fp, "r", encoding="utf-8") as f:
                txt = f.read()
            full_3d_path = str(target_3d).replace("\\", "/")
            txt = re.sub(r'\(model .*?\)', f'(model "{full_3d_path}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))', txt, flags=re.DOTALL)
            target_fp.write_text(txt, encoding="utf-8")
            self.log("✅ 3D model copied and path fixed automatically")

        shutil.rmtree(temp_dir, ignore_errors=True)
        self.log(f"\n🎉 SUCCESS! {symbol_name} is ready in {sym_lib}")
        messagebox.showinfo("Done", f"{symbol_name} imported successfully!")
        self.btn.configure(state="normal")

if __name__ == "__main__":
    app = ImporterGUI()
    app.mainloop()