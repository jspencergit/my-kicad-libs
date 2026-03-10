header = '(kicad_symbol_lib (version 20240915) (generator "kicad_symbol_editor"))\n'

files = [
    "MyPassives.kicad_sym",
    "MyConnectors.kicad_sym",
    "MyPower.kicad_sym",
    "MyAmplifiers.kicad_sym",
    "MyICs.kicad_sym"
]

for f in files:
    with open(f, "w", encoding="utf-8") as file:
        file.write(header)
    print("Fixed:", f)

print("\nAll 5 symbol libraries are now valid and ready for KiCad.")