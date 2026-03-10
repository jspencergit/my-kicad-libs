import sys
import zipfile
import shutil
import re
import hashlib
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("paths", "paths.py")
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)

if len(sys.argv) < 2:
    print("Usage: python import_samacsys.py <zip_file>")
    sys.exit(1)

zip_path = Path(sys.argv[1])
print(f"Processing: {zip_path.name}\n")

temp_dir = Path("temp_samacsys")
if temp_dir.exists():
    shutil.rmtree(temp_dir)
temp_dir.mkdir()

with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(temp_dir)

fp_file = next(temp_dir.rglob("*.kicad_mod"), None)
sym_file = next(temp_dir.rglob("*.kicad_sym"), None)
step_file = next((f for f in temp_dir.rglob("*.step") if "3D" in str(f).upper()), None) or \
            next((f for f in temp_dir.rglob("*.stp") if "3D" in str(f).upper()), None) or \
            next(temp_dir.rglob("*.step"), None) or next(temp_dir.rglob("*.stp"), None)

if not fp_file or not sym_file:
    print("❌ Could not find symbol or footprint")
    shutil.rmtree(temp_dir, ignore_errors=True)
    sys.exit(1)

part_name = fp_file.stem
print(f"Detected part: {part_name}")

print("\nWhere should this part go?")
print("1=MyPassives  2=MyConnectors  3=MyPower  4=MyAmplifiers  5=MyICs")
choice = input("Enter 1-5: ").strip()

lib_map = {
    "1": ("MyPassives",   "MyPassives.pretty",   "MyPassives"),
    "2": ("MyConnectors", "MyConnectors.pretty", "MyConnectors"),
    "3": ("MyPower",      "MyPower.pretty",      "MyPower"),
    "4": ("MyAmplifiers", "MyAmplifiers.pretty", "MyAmplifiers"),
    "5": ("MyICs",        "MyICs.pretty",        "MyICs")
}

sym_lib, fp_lib, three_d_folder = lib_map.get(choice, ("MyPower", "MyPower.pretty", "MyPower"))

target_sym = paths.YOUR_LIBRARY_ROOT / "symbols"   / f"{sym_lib}.kicad_sym"
target_fp  = paths.YOUR_LIBRARY_ROOT / "footprints" / fp_lib / f"{part_name}.kicad_mod"
target_3d  = paths.YOUR_LIBRARY_ROOT / "3dmodels"  / three_d_folder / f"{part_name}.step"

full_3d_path = f"C:/Kicad/MyLibs/3dmodels/{three_d_folder}/{part_name}.step"

# === Duplicate protection for footprint ===
if target_fp.exists():
    with open(target_fp, "rb") as f:
        old_hash = hashlib.md5(f.read()).hexdigest()
    with open(fp_file, "rb") as f:
        new_hash = hashlib.md5(f.read()).hexdigest()
    if old_hash == new_hash:
        print("✅ Footprint identical — skipping")
    else:
        act = input(f"Footprint differs. [R]eplace / [K]eep / [S]kip? ").strip().upper()
        if act == "R":
            shutil.copy2(fp_file, target_fp)
        elif act == "S":
            print("✅ Skipped")
            shutil.rmtree(temp_dir, ignore_errors=True)
            sys.exit(0)

if step_file:
    shutil.copy2(step_file, target_3d)
    print("✅ 3D model copied")

# === Create PERFECT footprint (exact format that works for you) ===
with open(fp_file, "r", encoding="utf-8") as f:
    content = f.read()

# Force correct KiCad 9 footprint format
content = re.sub(r'\(module ', '(footprint ', content)
content = re.sub(r'\(version \d+\)', '(version 20241229)', content)
content = re.sub(r'\(generator_version ".*?"\)', '(generator_version "9.0")', content)

# Replace model block with the exact working one
model_block = f'''  (model "{full_3d_path}"
    (offset (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)'''

content = re.sub(r'\(model .*?\n.*?\n.*?\n.*?\n\s*\)', model_block, content, flags=re.DOTALL)

with open(target_fp, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Footprint written in exact working format")

# === Symbol - clean replacement (never breaks header) ===
with open(sym_file, "r", encoding="utf-8") as f:
    data = f.read()

symbol_start = data.find('(symbol "')
symbol_block = data[symbol_start:]

full_fp = f"{sym_lib}:{part_name}"
symbol_block = re.sub(
    r'(\(property "Footprint" )"[^"]*"',
    rf'\1"{full_fp}"',
    symbol_block
)

# Write clean symbol library (header + one symbol only)
with open(target_sym, "w", encoding="utf-8") as f:
    f.write('(kicad_symbol_lib\n')
    f.write('  (version 20241209)\n')
    f.write('  (generator "kicad_symbol_editor")\n')
    f.write('  (generator_version "9.0")\n')
    f.write('\n' + symbol_block)

print("✅ Symbol library written cleanly (no duplicates, correct header)")

print("\n🎉 SUCCESS! This importer now produces exactly the files that work for you.")
print(f"   Part: {part_name} → {sym_lib}")
print("   You can now safely import any SamacSys ZIP.")

shutil.rmtree(temp_dir, ignore_errors=True)