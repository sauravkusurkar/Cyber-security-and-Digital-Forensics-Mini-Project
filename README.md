# Digital Image Forensics Analysis Tool

A ready-to-run academic mini-project implementation based on the supplied **CSDF mini-project report: "Digital Image Forensics Analysis Tool"**.

The report describes a Python + Streamlit + OpenCV + FFmpeg workflow with:

- SHA-256 file-level hashing
- FFprobe/PyMediaInfo-style metadata extraction
- configurable frame sampling, defaulting to 1 frame/second
- JPEG-based per-frame SHA-256 hashes
- thumbnail timeline inspection
- comparison of two evidence files
- structured ZIP evidence packaging
- manifest and processing logs

## 1. Requirements

- Windows 10/11, Linux, or macOS
- Python 3.10 or newer
- VS Code recommended

FFmpeg/FFprobe is **optional**. If `ffprobe` is available on PATH, it is used for rich metadata. If not, the application automatically falls back to OpenCV metadata so the project can still run.

## 2. Open in VS Code

Extract this ZIP and open the extracted folder in VS Code.

Open the VS Code terminal:

```powershell
python --version
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can avoid activation entirely:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Or use Command Prompt:

```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

## 3. One-click Windows setup

Double-click `setup.bat`.

Then double-click `run.bat`.

## 4. How to use

1. Open the Streamlit page shown in the terminal.
2. Upload an MP4, MOV, AVI, MKV, or WEBM evidence video.
3. Review the SHA-256 hash.
4. Review extracted metadata.
5. Inspect sampled frames.
6. Download the frame hash manifest.
7. Generate the forensic evidence ZIP.
8. Use **Compare Evidence** to compare two files.

## 5. Evidence package structure

The generated ZIP contains:

```text
forensic_evidence/
├── original/
│   └── original_video.ext
├── frames/
│   ├── frame_000000_000000.00s.jpg
│   └── ...
├── metadata/
│   ├── metadata.json
│   ├── file_sha256.txt
│   └── frame_hash_manifest.json
├── logs/
│   └── processing_log.json
└── manifest.json
```

## 6. Project architecture

```text
Streamlit UI
    |
    +-- File Operations
    |      +-- SHA-256 hashing
    |      +-- evidence file handling
    |
    +-- Metadata Extraction
    |      +-- FFprobe when available
    |      +-- OpenCV fallback
    |
    +-- Frame Processing
    |      +-- configurable sampling
    |      +-- JPEG encoding
    |      +-- per-frame SHA-256
    |
    +-- Comparison
    |      +-- file hashes
    |      +-- metadata differences
    |      +-- sampled frame differences
    |
    +-- Evidence Reporting
           +-- original file
           +-- frames
           +-- metadata
           +-- manifests
           +-- logs
           +-- ZIP package
```

## 7. Notes for the project viva

A matching SHA-256 hash means the files are byte-for-byte identical. A different hash means the bytes differ; it does **not**, by itself, prove malicious tampering.

The project is an academic forensic-analysis prototype and should not be described as a certified legal forensic product.

## 8. Report alignment

The supplied report's system architecture names File Operations, Frame Processing, Evidence Reporting, User Interface, and Dependency Management. This implementation keeps those same conceptual modules and the report's default 1 FPS sampling approach.

The report also shows screenshots for the dashboard, hash/metadata analysis, frame sampling, comparison results, and evidence export. The current application implements those corresponding workflows in Streamlit.
