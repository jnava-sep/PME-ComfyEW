# Project Charter: PME-ComfyEW

> **Pratt Miller Engineering — Comfy Engineering Workbench**  
> *Transforming Visual Node Graphs into a High-Performance Physical Engineering & Telemetry Platform.*

---

## 1. Preamble & Executive Summary

**PME-ComfyEW** repurposes the open-source ComfyUI visual Directed Acyclic Graph (DAG) runtime into an interactive, deterministic engineering workbench for motorsport telemetry, vehicle dynamics simulation, sensor signal processing, and automated test reporting.

While the broader open-source community associates ComfyUI with generative image and video diffusion, **PME-ComfyEW is strictly an engineering and scientific dataflow environment.** This charter defines the philosophical identity, core mission, and immutable ground rules governing every line of code, node definition, and workflow created within this platform.

---

## 2. The Soul & Philosophy of the Workbench

### Why Visual Dataflow for Engineering?
Traditional motorsport and simulation analysis often suffers from two extremes:
1. **Monolithic, brittle scripts:** Hard to read, difficult to audit track-side, and prone to breaking when sensor channel names change.
2. **Opaque black-box GUI tools:** Rigid, vendor-locked, and difficult to extend with custom algorithms or automated machine learning.

**PME-ComfyEW bridges this gap:**
* **Visual Transparency:** Complex signal transformations—from raw accelerometer voltages to filtered yaw rates, aerodynamic balance, and tire slip angles—are laid out as an intuitive, auditable pipeline.
* **Instant Reactivity:** Tweaking a filter cutoff or calibration parameter recalculates and updates plots instantaneously across the entire dependency graph.
* **Traceable Lineage:** Every metric, calculation, and plot can be traced back to its raw source file, channel, and mathematical formulation.

---

## 3. The Non-Negotiable Ground Rules

All contributors, maintainers, and integrated AI assistants must adhere to the following five fundamental rules:

### Rule 1: The Generative Media Boundary (Absolute Prohibition)
> **Under no circumstances are generative AI diffusion models, checkpoint weights, UNETs, VAE decoders, latent samplers, LoRAs, or image/video synthesis workflows permitted in this repository.**

* Any attempt to introduce diffusion dependencies, image generative pipelines, or external HuggingFace model downloads without prior written authorization from PME branch leadership is strictly forbidden.
* AI within PME-ComfyEW is focused exclusively on **analytical intelligence**: telemetry summarization, anomaly detection, automated mathematical script generation, structured report synthesis, and workflow co-pilot guidance.

### Rule 2: Dependency & Environment Integrity (Zero Bloat)
> **The workbench must remain deployable, deterministic, and lean.**

* **Standard Library First:** All core nodes and utility bridges must maximize the use of Python’s standard library (`subprocess`, `ast`, `urllib`, `json`, `math`).
* **Approved Science Packages Only:** External packages are strictly limited to the pre-approved workspace stack: `numpy`, `scipy`, `pandas`, `h5py`, and `matplotlib`.
* **No Unapproved `pip install`:** Rogue package installations, heavy PyPI frameworks, or unvetted third-party node suites are disallowed. If an external library is required, it must go through an architectural review.

### Rule 3: Vendor-Agnostic, Open-Ended AI Architecture
> **No artificial intelligence capability may be locked into a single vendor or proprietary cloud silo.**

* All assistant systems (including the telemetry nodes and **Comfy Concierge**) must implement a pluggable, provider-agnostic adapter interface (`BaseAgentProvider`).
* The system must seamlessly support:
  1. **Local CLI Subprocesses:** (e.g., local `agentapi` / Gemini CLI bridge).
  2. **Local Offline Inference Servers:** (e.g., **Ollama**, **vLLM**, **LM Studio**, **LocalAI**) via universal standard library `/v1/chat/completions` HTTP calls.
  3. **Commercial Cloud APIs:** (e.g., Anthropic Claude, OpenAI) via standard HTTP requests with user-configured API keys.
* The workbench must function completely offline when required.

### Rule 4: Engineering Rigor, Safety & Determinism
> **Calculations must be mathematically transparent, safe, and reproducible.**

* **No Unchecked `eval()`:** User math expressions must be safely parsed and sandboxed (e.g., via AST verification in `ComfyMathExpression`) to prevent arbitrary code execution, filesystem escapes, or security vulnerabilities.
* **Explicit Channel Contracts:** Signal pipelines must respect `TIMESERIES` and `CHANNEL` data contracts, preserving channel names, physical units (e.g., `km/h`, `deg/s`, `bar`), and sampling frequencies ($f_s$).
* **Reproducibility:** A saved workflow JSON must produce identical numerical outputs when loaded on any authorized PME workstation.

### Rule 5: Sub-Repository Modularity
> **Custom capabilities must be modular and independently version-controlled.**

* Domain-specific toolkits reside in dedicated sub-repositories under `custom_nodes/` (e.g., `timeseries-nodes`, `python-calcs`, `pme-gemini-nodes`).
* Root repository boundaries and `.gitignore` rules must be strictly maintained to ensure sub-repositories can be updated, branched, or tested independently without polluting the main codebase.

---

## 4. Platform Domains & Capabilities

PME-ComfyEW is organized into four core functional pillars:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PME-ComfyEW Platform                            │
├────────────────────┬────────────────────┬──────────────────────────────┤
│ 1. Telemetry &     │ 2. Calculation &   │ 3. Engineering AI &          │
│    Signal I/O      │    Math Engine     │    Reporting                 │
├────────────────────┼────────────────────┼──────────────────────────────┤
│ • MAT / MDF4 / CSV │ • PythonCalcNode   │ • Data Insights Node         │
│ • Channel Slicing  │ • ComfyMathExpr    │ • Py/Math Gen Node           │
│ • XY Plotting      │ • Vectorized NumPy │ • Report Gen Node            │
│ • Signal Filtering │ • Custom Scripts   │ • Comfy Concierge (GUI)      │
└────────────────────┴────────────────────┴──────────────────────────────┘
```

1. **Telemetry & Signal Processing (`timeseries-nodes`):**
   High-rate ingestion, channel mapping, multi-rate resampling, and synchronized interactive visual plotting.
2. **Calculation & Dynamic Math (`python-calcs` & `ComfyMathExpression`):**
   Execution of user-defined formulas, vectorized array mathematics, and verified vehicle dynamics libraries.
3. **Engineering Intelligence (`pme-gemini-nodes`):**
   Telemetry anomaly audits, natural language formula synthesis, and automated Markdown/HTML test report compilation.
4. **Interactive Co-Pilot (**Comfy Concierge**):**
   Overarching, graph-aware GUI assistant embedded in the ComfyUI interface to inspect workflows, diagnose errors, and guide node selection.

---

## 5. Architectural Quality Standards

* **Scale & Performance:** Visual rendering and calculation pipelines must handle multi-megabyte telemetry files (>1,000,000 samples per channel) without freezing the canvas or consuming excessive memory.
* **Canvas Cleanliness:** Front-end JavaScript extensions must maintain DOM cleanliness (using `overflow: clip`, proper scale compensation, and adhering to ComfyUI's Vue 3 / YJS reactivity model).
* **Automated Verification:** Every custom node suite must maintain an automated test suite (e.g., `test_gemini_nodes.py`) achieving fast, reliable validation without network dependencies.

---

## 6. Governance & Amendments

* **Custodian:** This charter is governed by the Pratt Miller Engineering development team and branch leadership.
* **Amendments:** Modifications to this charter—particularly any change affecting the ground rules or dependency policies—require explicit review and consensus from PME branch developers.
* **Onboarding & AI Directives:** Any automated coding agent, pair-programming LLM, or external developer working within this codebase must be directed to read this charter before contributing code.

---

*Adopted by Pratt Miller Engineering — 2026.*
