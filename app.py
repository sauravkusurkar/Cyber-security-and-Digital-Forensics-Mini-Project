import io
import json
import tempfile
from pathlib import Path
import shutil

import cv2
import numpy as np
import streamlit as st

from forensic.file_utils import compute_file_hash, save_uploaded_file
from forensic.metadata import extract_metadata
from forensic.frames import sample_frames, frame_to_jpeg_bytes, build_frame_hash_manifest
from forensic.reporter import create_evidence_package
from forensic.comparator import compare_media


st.set_page_config(
    page_title="Digital Image Forensics Analysis Tool",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background: #0e1117; }
    .block-container { padding-top: 1.2rem; max-width: 1400px; }
    .hero {
        padding: 1.2rem 1.4rem;
        border: 1px solid #2d3748;
        border-radius: 14px;
        background: linear-gradient(135deg, #111827, #172033);
        margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { color: #aab4c3; margin: .35rem 0 0; }
    .metric-card {
        padding: .8rem 1rem;
        border: 1px solid #303846;
        border-radius: 12px;
        background: #151a23;
    }
    .small-muted { color: #98a2b3; font-size: .85rem; }
    div[data-testid="stMetric"] {
        border: 1px solid #303846;
        padding: .7rem;
        border-radius: 10px;
        background: #151a23;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🔎 Digital Image Forensics Analysis Tool</h1>
  <p>SHA-256 integrity verification • metadata extraction • frame sampling • per-frame hashing • comparison • evidence packaging</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Forensic Controls")
    sample_interval = st.number_input(
        "Frame sampling interval (seconds)",
        min_value=0.1, max_value=60.0, value=1.0, step=0.1,
        help="The report recommends 1 frame per second as a practical default."
    )
    jpeg_quality = st.slider("Frame JPEG quality", 50, 100, 85)
    max_frames = st.number_input(
        "Maximum sampled frames", min_value=1, max_value=5000, value=300, step=1
    )
    st.divider()
    st.caption("Supported video containers in the report: MP4, MOV, AVI, MKV.")
    st.caption("Best results come from local execution in VS Code.")

tab_analyze, tab_compare, tab_about = st.tabs(
    ["📁 Forensic Analysis", "🆚 Compare Evidence", "ℹ️ About Project"]
)

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

with tab_analyze:
    uploaded = st.file_uploader(
        "Upload an evidence video",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        help="The original file is not modified by the analysis workflow."
    )

    if uploaded is not None:
        with tempfile.TemporaryDirectory(prefix="forensic_") as tmp:
            source_path = Path(tmp) / uploaded.name
            save_uploaded_file(uploaded, source_path)

            file_hash = compute_file_hash(source_path)
            metadata = extract_metadata(source_path)
            frames = sample_frames(
                source_path,
                interval_seconds=float(sample_interval),
                max_frames=int(max_frames)
            )
            frame_manifest = build_frame_hash_manifest(
                frames, jpeg_quality=int(jpeg_quality)
            )

            st.session_state.analysis_result = {
                "name": uploaded.name,
                "hash": file_hash,
                "metadata": metadata,
                "frames": frames,
                "frame_manifest": frame_manifest,
                "source_path": str(source_path),
            }

            st.subheader("Evidence Overview")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("SHA-256", file_hash[:12] + "…")
            c2.metric("Frames sampled", len(frames))
            c3.metric("Sampling", f"{sample_interval:g} sec")
            c4.metric("Metadata source", metadata.get("_source", "fallback"))

            st.success("Analysis completed successfully.")

            st.subheader("File Integrity")
            st.code(file_hash, language="text")

            st.subheader("Metadata Extraction")
            clean_metadata = {k: v for k, v in metadata.items() if not k.startswith("_")}
            st.json(clean_metadata)

            st.subheader("Frame Sampling & Inspection")
            if not frames:
                st.warning("No frames could be sampled. Check the video codec or install a compatible FFmpeg/OpenCV backend.")
            else:
                cols = st.columns(5)
                for i, frame in enumerate(frames):
                    with cols[i % 5]:
                        st.image(
                            cv2.cvtColor(frame["frame"], cv2.COLOR_BGR2RGB),
                            caption=f"Frame {frame['index']} • {frame['timestamp']:.2f}s",
                            use_container_width=True
                        )

                manifest_text = json.dumps(frame_manifest, indent=2)
                st.download_button(
                    "Download Frame Hash Manifest",
                    manifest_text,
                    file_name="frame_hash_manifest.json",
                    mime="application/json",
                )

            st.subheader("Export Forensic Evidence")
            if st.button("Generate Evidence ZIP", type="primary", use_container_width=True):
                with tempfile.TemporaryDirectory(prefix="evidence_") as evidence_tmp:
                    evidence_dir = Path(evidence_tmp)
                    original_copy = evidence_dir / uploaded.name
                    shutil.copy2(source_path, original_copy)

                    package = create_evidence_package(
                        original_file=original_copy,
                        file_hash=file_hash,
                        metadata=metadata,
                        frames=frames,
                        frame_manifest=frame_manifest,
                        output_dir=evidence_dir / "package",
                        sampling_interval=float(sample_interval),
                        jpeg_quality=int(jpeg_quality),
                    )
                    data = package.read_bytes()
                    st.download_button(
                        "Download Tamper-Evident Evidence Package",
                        data,
                        file_name=package.name,
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("Evidence package generated with original file, metadata, sampled frames, hashes, logs, and manifest.")

with tab_compare:
    st.subheader("Compare Two Evidence Files")
    left, right = st.columns(2)
    with left:
        file_a = st.file_uploader("Original / Evidence A", type=["mp4", "mov", "avi", "mkv", "webm"], key="compare_a")
    with right:
        file_b = st.file_uploader("Evidence B", type=["mp4", "mov", "avi", "mkv", "webm"], key="compare_b")

    if file_a and file_b and st.button("Run Forensic Comparison", type="primary"):
        with tempfile.TemporaryDirectory(prefix="compare_") as tmp:
            p1 = Path(tmp) / ("A_" + file_a.name)
            p2 = Path(tmp) / ("B_" + file_b.name)
            save_uploaded_file(file_a, p1)
            save_uploaded_file(file_b, p2)

            with st.spinner("Computing hashes, metadata and frame-level differences..."):
                result = compare_media(
                    p1, p2,
                    interval_seconds=float(sample_interval),
                    max_frames=int(max_frames),
                    jpeg_quality=int(jpeg_quality),
                )

            st.subheader("File Hash Comparison")
            if result["file_hash_a"] == result["file_hash_b"]:
                st.success("SHA-256 MATCH — the two files are byte-for-byte identical.")
            else:
                st.warning("SHA-256 DIFFERENCE — the two files are not byte-for-byte identical.")
            h1, h2 = st.columns(2)
            h1.code(result["file_hash_a"])
            h2.code(result["file_hash_b"])

            st.subheader("Metadata Differences")
            if result["metadata_diff"]:
                st.json(result["metadata_diff"])
            else:
                st.success("No reported metadata differences in the comparable fields.")

            st.subheader("Frame-Level Comparison")
            st.write(
                f"Compared {result['frames_compared']} sampled frame pairs. "
                f"Average pixel difference: **{result['average_frame_difference']:.4f}** "
                f"(0 means identical sampled pixels)."
            )
            if result["frame_rows"]:
                st.dataframe(result["frame_rows"], use_container_width=True, hide_index=True)

with tab_about:
    st.subheader("Project Alignment")
    st.markdown("""
This implementation follows the project report's stated architecture:

- **File Operations:** SHA-256 file hashing and evidence file handling.
- **Metadata Extraction:** FFprobe/FFmpeg where available, with OpenCV fallback.
- **Frame Processing:** configurable sampling with a default of 1 frame/second and JPEG-based frame hashing.
- **Evidence Reporting:** structured ZIP package containing the original evidence, extracted frames, metadata JSON, frame hashes, processing log and manifest.
- **User Interface:** Streamlit dashboard for analysis, inspection, comparison and export.

The report describes the project as a Python-based Streamlit/OpenCV/FFmpeg forensic workflow and lists MP4, MOV, AVI and MKV test formats.
""")
    st.info("Important: this is an academic forensic-analysis prototype. A matching SHA-256 hash proves byte equality, but a different hash alone does not prove malicious tampering.")
