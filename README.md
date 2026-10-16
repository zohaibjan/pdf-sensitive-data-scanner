# PDF Sensitive-Data Scanner

Sample a large document repository, scan the sampled PDFs for **checksum-valid Australian
Tax File Number (TFN) candidates** — and optionally other PII / government identifiers —
and copy any flagged files into an output directory. Built to be **scalable,
multi-threaded and configuration-driven**.

It catches sensitive data in three forms:

1. **Plain text PDFs** — normal extractable text layer.
2. **Redacted-but-readable PDFs** — a black box is drawn over the value but the
   underlying text is still present; we extract it *and* mark it as redacted.
3. **Scanned / image-only PDFs** — no text layer at all; pages are rendered and
   run through Tesseract **OCR**.

A number is only flagged as a TFN if it passes the official ATO weighted
**modulus-11 checksum**, which reduces accidental matches. A passing checksum does not establish that a number was issued, and false positives and false negatives remain possible.

---

## How it works

```
repository/  ──►  stratified sampler  ──►  thread pool  ──►  detectors  ──►  report + flagged/
 (folders &       (% of files from        (N workers)      (tfn/pii/gri)     output dir
  subfolders)      each folder)
```

* **Stratified sampling** — files are grouped by folder and a percentage is
  sampled from *each* folder, so one huge folder can't dominate the sample.
* **Pluggable detectors** — enabled/disabled purely from YAML (`tfn`, `pii`,
  `gri`). Adding a new detector is a single registry entry.
* **Multi-threaded** — a `ThreadPoolExecutor` scans many PDFs concurrently;
  PyMuPDF and the OCR subprocess release the GIL, so threads scale well for this
  I/O- and native-bound workload.

---

## Install

```bash
python -m pip install -e '.[dev]'
```

OCR (for scanned PDFs) additionally needs the Tesseract binary:

```bash
# Debian/Ubuntu
sudo apt-get install -y tesseract-ocr
# macOS
brew install tesseract
```

If Tesseract is absent, scanned pages are skipped with a warning; everything
else still works.

### Offline / air-gapped install

A pre-downloaded wheel bundle for **Windows 64-bit + Python 3.11** lives in
[`offline/`](offline/). Copy that folder to the target machine and run
`install.bat` — no internet required. See [`offline/README.md`](offline/README.md)
for details (and how to rebuild for another OS/Python version).

---

## Quick start

```bash
# 1. (optional) generate a sample repository to test against
python tools/generate_sample_pdfs.py ./sample_repo --folders 5 --per-folder 8

# 2. scan 10% of it (per the YAML), copying flagged files to ./output/flagged
python -m file_flag ./sample_repo -c config/scan_config.yaml

# preview what WOULD be sampled, without scanning
python -m file_flag ./sample_repo -c config/scan_config.yaml --dry-run
```

Install the package with `pip install -e .` (or the development install above) before using the module or the `file_flag` command.

### Useful CLI flags

| Flag | Effect |
|------|--------|
| `--percent N` | override sampling percentage |
| `--threads N` | override worker thread count |
| `--flagged-dir DIR` | where flagged files are copied/moved |
| `--report PATH` | JSON report location |
| `--dry-run` | print the sampling plan only |
| `--no-mask` | write raw (unmasked) values into the report |

---

## Configuration (`config/scan_config.yaml`)

```yaml
detectors:
  tfn:
    enabled: true
    require_valid: true      # only flag numbers passing the ATO checksum
  pii:
    enabled: false
    types: [email, phone_au, credit_card]
  gri:                       # Government Related Identifiers
    enabled: false
    types: [medicare, abn]

sampling:
  percent: 10                # sample 10% of files...
  strategy: proportional     # ...from EACH folder (proportional | equal)
  seed: 42                   # reproducible sampling; null = random
  min_per_folder: 1

ocr:
  enabled: true              # only used for pages with no text layer
  dpi: 300
  language: eng

processing:
  threads: 8

output:
  flagged_dir: ./output/flagged
  copy_mode: copy            # copy | move | none
  preserve_tree: true        # mirror source folder structure
  report: ./output/report.json
  mask_values: true          # mask sensitive values in the report
```

### Sampling strategies

* **`proportional`** (default) — take `percent`% of the files in each folder.
  Folders keep their relative weight; large folders contribute more files.
* **`equal`** — compute a global budget of `percent`% of all files, then draw the
  **same number of files from every folder** (capped by folder size). This is the
  literal "equal number of files from each folder" behaviour.

### Detectors

| Flag | Detects | Validation |
|------|---------|------------|
| `tfn` | Australian Tax File Numbers | ATO modulus-11 checksum |
| `pii` | email, AU phone, credit card | Luhn check for cards |
| `gri` | Medicare number, ABN | Medicare & ABN checksums |

A file is **flagged** if *any* enabled detector produces a finding.

---

## Output

* Flagged PDFs are copied (or moved) into `flagged_dir`, optionally mirroring the
  original folder tree.
* A JSON report (`output/report.json`) records, per flagged file: the detector,
  masked value, page number, surrounding context, and whether the value was
  `redacted` or recovered `via_ocr`.

```json
{
  "summary": { "scanned": 24, "flagged": 16, "findings_by_kind": { "tfn": 16 } },
  "results": [
    { "path": ".../doc_redacted.pdf",
      "flagged": true,
      "findings": [
        { "kind": "tfn", "value": "89*******96", "page": 1,
          "redacted": true, "via_ocr": false }
      ] }
  ]
}
```

Values are masked by default; use `--no-mask` only in a secure environment.

---

## Project layout

```
src/file_flag/
  cli.py            # argparse entry point  (python -m file_flag)
  config.py         # YAML load + defaults + validation
  sampler.py        # stratified per-folder sampling
  extraction.py     # text extraction, OCR fallback, redaction detection
  scanner.py        # scan one PDF -> ScanResult
  pipeline.py       # thread pool + flagged-file routing
  reporting.py      # summary + JSON report
  detectors/        # tfn, pii, gri  (+ pluggable registry)
tools/
  generate_sample_pdfs.py   # build a test repository
tests/                      # pytest suite
config/scan_config.yaml
```

---

## Tests

```bash
python -m pytest -q
```

Covers the TFN/ABN/Medicare checksums, stratified sampling strategies, the
detector registry, and an end-to-end pipeline run (text, redacted and clean
PDFs; scanned PDFs exercise OCR when Tesseract is installed).

---

## Notes & extension points

* **Scaling further** — for very large repositories the work is embarrassingly
  parallel; swap `ThreadPoolExecutor` for `ProcessPoolExecutor` (or shard the
  sampled list across machines) if you become CPU-bound on OCR.
* **New detector** — implement `Detector.detect()` in `detectors/`, add it to the
  `REGISTRY`, and switch it on in the YAML. No other code changes needed.
* **Security** — reports mask values by default; treat `flagged_dir` and any
  `--no-mask` report as sensitive.
