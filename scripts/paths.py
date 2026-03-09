from pathlib import Path

KICAD_VERSION = "9.0"

OFFICIAL_FOOTPRINT_DIR = Path(r"C:\Program Files\KiCad") / KICAD_VERSION / r"share\kicad\footprints\Package_SO.pretty"
OFFICIAL_SYMBOL_DIR    = Path(r"C:\Program Files\KiCad") / KICAD_VERSION / r"share\kicad\symbols"

YOUR_LIBRARY_ROOT = Path(r"C:\KiCad\MyLibs")

# Our final 5 libraries
SYMBOL_LIBS   = ["MyPassives", "MyConnectors", "MyPower", "MyAmplifiers", "MyICs"]
FOOTPRINT_LIBS = [f"{x}.pretty" for x in SYMBOL_LIBS]
