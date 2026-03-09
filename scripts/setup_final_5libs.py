from pathlib import Path

base = Path(r"C:\KiCad\MyLibs")

print("Creating clean 5-library structure...\n")

# 1. Symbol libraries
symbol_names = ["MyPassives", "MyConnectors", "MyPower", "MyAmplifiers", "MyICs"]
for name in symbol_names:
    (base / "symbols" / f"{name}.kicad_sym").touch()
    print(f"   Created symbol library: {name}.kicad_sym")

# 2. Footprint libraries + matching 3D folders
fp_names = ["MyPassives", "MyConnectors", "MyPower", "MyAmplifiers", "MyICs"]
for name in fp_names:
    pretty = f"{name}.pretty"
    (base / "footprints" / pretty).mkdir(exist_ok=True)
    (base / "3dmodels" / name).mkdir(exist_ok=True)
    (base / "footprints" / pretty / ".gitkeep").touch()
    (base / "3dmodels" / name / ".gitkeep").touch()
    print(f"   Created footprint library: {pretty}  +  3dmodels/{name}/")

# 3. Create updated paths.py
paths_content = '''from pathlib import Path

KICAD_VERSION = "9.0"

OFFICIAL_FOOTPRINT_DIR = Path(r"C:\\Program Files\\KiCad") / KICAD_VERSION / r"share\\kicad\\footprints\\Package_SO.pretty"
OFFICIAL_SYMBOL_DIR    = Path(r"C:\\Program Files\\KiCad") / KICAD_VERSION / r"share\\kicad\\symbols"

YOUR_LIBRARY_ROOT = Path(r"C:\\KiCad\\MyLibs")

# Our final 5 libraries
SYMBOL_LIBS   = ["MyPassives", "MyConnectors", "MyPower", "MyAmplifiers", "MyICs"]
FOOTPRINT_LIBS = [f"{x}.pretty" for x in SYMBOL_LIBS]
'''

(base / "scripts" / "paths.py").write_text(paths_content, encoding="utf-8")
print("\n✅ paths.py created")

print("\n🎉 Done! Your library is now clean and organized with exactly 5 libraries.")
print("   Next: I'll give you the new add_kicad_part.py + the ADA4610-2ARZ part file.")