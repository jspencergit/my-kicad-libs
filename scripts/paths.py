from pathlib import Path

KICAD_VERSION = "9.0"

YOUR_LIBRARY_ROOT = Path(r"C:\KiCad\MyLibs")

# === KiCad Configure Paths variables (must match what you just added) ===
MY_3DMODEL_DIR = YOUR_LIBRARY_ROOT / "3dmodels"

# Our 5 clean libraries
SYMBOL_LIBS   = ["MyPassives", "MyConnectors", "MyPower", "MyAmplifiers", "MyICs"]
FOOTPRINT_LIBS = [f"{x}.pretty" for x in SYMBOL_LIBS]

print("paths.py loaded - MY_3DMODEL_DIR =", MY_3DMODEL_DIR)