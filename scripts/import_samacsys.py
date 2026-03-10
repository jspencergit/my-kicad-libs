import sys
import zipfile
import shutil
import re
from pathlib import Path
import importlib.util

# ====================== LOAD PATHS ======================
spec = importlib.util.spec_from_file_location("paths", "paths.py")
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)

if len(sys.argv) < 2:
    print("Usage: python import_samacsys.py \"path\\to\\ZIP\"")
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
step_file = next((f for f in temp_dir.rglob("*") if f.suffix.lower() in (".step", ".stp")), None)

if not fp_file or not sym_file:
    print("❌ Could not find symbol or footprint")
    shutil.rmtree(temp_dir, ignore_errors=True)
    sys.exit(1)

footprint_name = fp_file.stem

# Extract real symbol name
with open(sym_file, "r", encoding="utf-8") as f:
    samacsys_data = f.read()

m = re.search(r'\(symbol "([^"]+)"', samacsys_data)
symbol_name = m.group(1) if m else footprint_name

print(f"Detected → Symbol: {symbol_name}   |   Footprint package: {footprint_name}")

print("\nWhere should this part go?")
print("1=MyPassives  2=MyConnectors  3=MyPower  4=MyAmplifiers  5=MyICs")
choice = input("Enter 1-5: ").strip()

lib_map = {"1":"MyPassives","2":"MyConnectors","3":"MyPower","4":"MyAmplifiers","5":"MyICs"}
sym_lib = lib_map.get(choice, "MyPower")

target_sym = paths.YOUR_LIBRARY_ROOT / "symbols" / f"{sym_lib}.kicad_sym"
target_fp  = paths.YOUR_LIBRARY_ROOT / "footprints" / f"{sym_lib}.pretty" / f"{footprint_name}.kicad_mod"
target_3d  = paths.YOUR_LIBRARY_ROOT / "3dmodels" / sym_lib / f"{footprint_name}.step"

# ====================== ROBUST PAREN COUNTING ======================
def extract_top_level_symbols(content: str):
    symbols = []
    i = 0
    while True:
        start = content.find('(symbol "', i)
        if start == -1:
            break
        depth = 0
        in_string = False
        for j in range(start, len(content)):
            c = content[j]
            if c == '"' and (j == 0 or content[j-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        symbols.append(content[start:j+1].strip())
                        i = j + 1
                        break
        else:
            break
    return symbols

# ====================== SYMBOL LIBRARY (blank or populated) ======================
print("\n=== Symbol ===")
if target_sym.exists() and target_sym.stat().st_size > 10:
    with open(target_sym, "r", encoding="utf-8") as f:
        lib_content = f.read()
    existing_blocks = extract_top_level_symbols(lib_content)
    symbol_exists = any(symbol_name in block[:300] for block in existing_blocks)
else:
    existing_blocks = []
    symbol_exists = False

if symbol_exists:
    action = input(f"Symbol '{symbol_name}' already exists. [R]eplace / [K]eep / [S]kip? ").strip().upper()
    if action == "R":
        existing_blocks = [b for b in existing_blocks if symbol_name not in b[:300]]
        print("✅ Old symbol removed")
        replace_symbol = True
    elif action == "S":
        print("✅ Skipped symbol")
        replace_symbol = False
    else:
        print("✅ Kept existing symbol")
        replace_symbol = False
else:
    replace_symbol = True

if replace_symbol:
    incoming_blocks = extract_top_level_symbols(samacsys_data)
    if incoming_blocks:
        new_block = incoming_blocks[0]
        full_fp = f"{sym_lib}:{footprint_name}"
        new_block = re.sub(r'(\(property "Footprint" )"[^"]*"', rf'\1"{full_fp}"', new_block)
        existing_blocks.append(new_block)
        print(f"✅ Symbol '{symbol_name}' added (Footprint field → {full_fp})")
    else:
        print("⚠️ Could not extract symbol block")

# === BUILD CLEAN LIBRARY ===
header = '''(kicad_symbol_lib
  (version 20241209)
  (generator "kicad_symbol_editor")
  (generator_version "9.0")
'''
final_content = header + "\n".join(existing_blocks) + "\n)"

target_sym.parent.mkdir(parents=True, exist_ok=True)
target_sym.write_text(final_content, encoding="utf-8")
print(f"   Library rebuilt cleanly ({len(existing_blocks)} symbols total)")

# ====================== FOOTPRINT ======================
print("\n=== Footprint ===")
target_fp.parent.mkdir(parents=True, exist_ok=True)
if target_fp.exists():
    action = input(f"Footprint exists. [R]eplace / [K]eep / [S]kip? ").strip().upper()
    if action == "R":
        shutil.copy2(fp_file, target_fp)
        print("✅ Footprint replaced")
    elif action == "S":
        print("✅ Skipped footprint")
        fp_file = None
    else:
        print("✅ Kept existing footprint")
        fp_file = None
else:
    shutil.copy2(fp_file, target_fp)
    print("✅ Footprint copied")

# ====================== 3D MODEL ======================
if step_file:
    print("\n=== 3D Model ===")
    target_3d.parent.mkdir(parents=True, exist_ok=True)
    if target_3d.exists():
        action = input(f"3D model exists. [R]eplace / [K]eep? ").strip().upper()
        if action == "R":
            shutil.copy2(step_file, target_3d)
            print("✅ 3D model replaced")
        else:
            print("✅ Kept existing 3D model")
    else:
        shutil.copy2(step_file, target_3d)
        print("✅ 3D model copied")

# ====================== FINAL FOOTPRINT 3D PATH FIX ======================
if fp_file is not None and target_fp.exists():
    with open(target_fp, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'\(module ', '(footprint ', content)
    content = re.sub(r'\(version \d+\)', '(version 20241229)', content)
    full_3d_path = f"C:/KiCad/MyLibs/3dmodels/{sym_lib}/{footprint_name}.step"
    model_block = f'  (model "{full_3d_path}"\n    (offset (xyz 0 0 0))\n    (scale (xyz 1 1 1))\n    (rotate (xyz 0 0 0))\n  )'
    content = re.sub(r'\(model .*?\)', model_block, content, flags=re.DOTALL)
    with open(target_fp, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 3D model path fixed in footprint: {full_3d_path}")

print(f"\n🎉 SUCCESS: {symbol_name} imported into {sym_lib}")
print(f"   Symbol:     {target_sym}")
print(f"   Footprint:  {target_fp}")
print(f"   3D model:   {target_3d if step_file else 'None'}")
shutil.rmtree(temp_dir, ignore_errors=True)