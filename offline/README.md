# Offline install bundle (Windows x86_64, Python 3.11)

This folder lets you install **file_flag 0.1.1** on a machine with **no internet**.
Everything needed — the app and all its Python dependencies — is pre-downloaded
as `.whl` files in `wheels/`.

## Contents

```
offline/
  wheels/                     all .whl files (file_flag + dependencies + pip tooling)
  install.bat                 one-click offline installer (Windows)
  install.sh                  offline installer (Linux/macOS)
  pip.ini                     optional: make ALL pip commands use wheels/ offline
  requirements-offline.txt    pinned dependency versions
  build_bundle.sh             rebuild this bundle for another OS / Python version
```

The bundled binary wheels are built for **Windows 64-bit + CPython 3.11**.
For a different OS or Python version, see *"Rebuilding"* below.

## Install (on the offline client)

1. Copy this whole `offline/` folder to the client machine.
2. Make sure **Python 3.11 (64-bit)** is installed and on `PATH`
   (`python --version` should print 3.11.x).
3. Double-click **`install.bat`** (or run it in a terminal).

That runs, fully offline:

```bat
python -m pip install --no-index --find-links wheels --upgrade pip setuptools wheel
python -m pip install --no-index --find-links wheels file_flag==0.1.1
```

Verify:

```bat
python -m file_flag --help
```

### Manual one-liner (equivalent)

```bat
pip install --no-index --find-links "C:\path\to\offline\wheels" file_flag==0.1.1
```

`--no-index` tells pip not to contact PyPI; `--find-links` points it at the
local folder.

## Making pip use the folder by default (optional)

If you want every `pip install` on the client to work offline without flags,
edit `pip.ini` (set the real `find-links` path) and copy it to
`%APPDATA%\pip\pip.ini`. After that, `pip install file_flag` just works.

## ⚠️ OCR / Tesseract is NOT included

OCR for *scanned image-only* PDFs relies on the **Tesseract** program, which is
a native Windows executable — **not** a Python wheel, so it cannot live in this
folder. Two options on the client:

* **Don't need OCR** (your PDFs have a text layer, including redacted-but-readable
  ones): set `ocr.enabled: false` in `config/scan_config.yaml`. Everything works
  with no extra install.
* **Need OCR** for genuine scans: download the Tesseract installer
  (`tesseract-ocr-w64-setup-*.exe` from the UB-Mannheim build) on an
  internet-connected machine, copy it over, and install it on the client.

## Rebuilding for a different OS / Python version

On an internet-connected machine:

```bash
# examples
PLATFORM=win_amd64            PYVER=311 ./build_bundle.sh   # Windows, 3.11 (default)
PLATFORM=manylinux2014_x86_64 PYVER=312 ./build_bundle.sh   # Linux,   3.12
PLATFORM=macosx_11_0_arm64    PYVER=311 ./build_bundle.sh   # macOS Apple Silicon
```

Then copy the refreshed `offline/` folder to the client.

The bundled application wheel is rebuilt from source version 0.1.1. The wheel contents are checked in CI. Installation on a real offline Windows machine and native OCR remain separate acceptance checks.
