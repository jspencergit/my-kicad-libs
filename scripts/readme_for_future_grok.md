# KiCad 9 Personal Library System - Primer for Grok (March 2026)

I am an EE using KiCad 9.0.7. I want a fast, reliable way to import real manufacturer parts (mostly from SamacSys) into my own clean personal libraries.

### Current Folder Structure (never change this)
C:\KiCad\MyLibs\
├── symbols\
│   ├── MyPassives.kicad_sym
│   ├── MyConnectors.kicad_sym
│   ├── MyPower.kicad_sym          ← LTC7890 and ADP123 live here
│   ├── MyAmplifiers.kicad_sym
│   └── MyICs.kicad_sym
├── footprints\
│   ├── MyPassives.pretty\
│   ├── MyConnectors.pretty\
│   ├── MyPower.pretty\            ← contains QFN50P600X600X80-41N-D.kicad_mod etc.
│   ├── MyAmplifiers.pretty\
│   └── MyICs.pretty\
├── 3dmodels\
│   ├── MyPassives\
│   ├── MyConnectors\
│   ├── MyPower\                   ← .step files live here
│   ├── MyAmplifiers\
│   └── MyICs\
├── scripts\
│   ├── paths.py
│   ├── import_samacsys.py          ← CLI version (working)
│   └── import_samacsys_gui.py      ← GUI version (working, uses Browse button)
├── projects\
│   └── Test-Library-Workflow\      ← test project with all 5 libraries added
└── Downloads\                      ← SamacSys ZIPs land here (not in Git)

### paths.py content (important)
YOUR_LIBRARY_ROOT = Path('C:/KiCad/MyLibs')
MY_3DMODEL_DIR is set to C:\KiCad\MyLibs\3dmodels

### Key Requirements for any future script/GUI update
1. Always produce valid KiCad 9 .kicad_sym format:
   - Header must be exactly:
     (kicad_symbol_lib
       (version 20241209)
       (generator "kicad_symbol_editor")
       (generator_version "9.0")
     ... symbols ... )

2. When appending a new symbol to an existing library, do NOT close the library early.
   - Extract only the (symbol "NAME" ...) block from the imported file.
   - Keep the library wrapper open and only close it once at the very end of the file.

3. Duplicate handling (critical):
   - If symbol name already exists, ask user: [R]eplace / [K]eep / [S]kip
   - Same prompt for footprint and 3D model.

4. Automatically fix two things on every import:
   - Change Footprint property to "MyXXX:PartName" (e.g. "MyPower:QFN50P600X600X80-41N-D")
   - Inject correct 3D model line into the .kicad_mod:
     (model "C:/KiCad/MyLibs/3dmodels/MyPower/PartName.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))

5. Support both CLI and GUI versions:
   - GUI should have Browse button + status log + dropdown for the 5 libraries.
   - GUI should call the same robust import logic (no code duplication).

6. Ultra Librarian / other sources are nice-to-have later. For now focus only on SamacSys ZIPs.

### Current working scripts
- import_samacsys.py (CLI)
- import_samacsys_gui.py (GUI)

When I return in the future, I will say:
"Here is the current state. Update the importer/GUI to also handle [new requirement]."

Use this file as the single source of truth.

GitHub repo (manual push only): https://github.com/jspencergit/my-kicad-libs
Test project: C:\KiCad\Projects\Test-Library-Workflow

Saved on: March 10, 2026