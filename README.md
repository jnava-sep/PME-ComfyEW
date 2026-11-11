# PME-ComfyEW: Engineering Workbench

**PME-ComfyEW** (Pratt Miller Engineering — ComfyUI Engineering Workbench) is a specialized fork of ComfyUI adapted for **engineering data pipelines, vehicle dynamics analysis, telemetry processing, batch simulations, and modular Python calculations**.

Instead of generative image/video diffusion models, PME-ComfyEW repurposes ComfyUI's visual node-graph execution engine into a high-throughput, interactive visual workbench tailored for motorsport, automotive, robotics, and defense engineering workflows.

---

## Key Highlights & Architectural Changes

### 1. Pruned Core Engine
* **Stripped Generative AI Dependencies**: Over 2,700 lines of generative diffusion models, samplers, VAEs, and latent pipelines were pruned from `nodes.py` and default blueprints.
* **Lean Execution Core**: Focuses on high-speed data flow, string manipulation, file routing, image preview/reporting, and custom engineering node evaluation.

### 2. Time-Series & Telemetry Suite (`custom_nodes/timeseries-nodes`)
A purpose-built suite for ingesting, transforming, and visualizing high-frequency telemetry and sensor data:
* **`LoadTimeseries`**: Ingests CSV and Parquet files, automatically detects time/timestamp channels, infers sampling frequency, and outputs standardized `TIMESERIES` structures.
* **`ChannelMapper`**: An interactive in-canvas table widget built directly into the ComfyUI canvas / Vue Node 2.0 interface. Supports:
  * Per-channel transforms: $\text{result} = \text{polarity} \times \text{gain} \times \text{raw} + \text{offset}$.
  * In-place unit remapping and signal renaming.
  * Dynamic output slot generation linked to reactive Pinia/Vue state.
* **`ChannelBundle` & `TimeseriesListBundle`**: Bus/Mux creators to package separate channels into unified time-series objects or aggregate multiple test runs into batch lists.
* **`AttachMetadata`**: Attaches key-value metadata tags (e.g., test run IDs, vehicle setup, tire compounds, ambient conditions) directly to telemetry payloads.
* **`SaveHDF5` / `SaveHDF5List` / `LoadHDF5List`**: High-performance binary archival and retrieval of single or batch telemetry runs using standard HDF5 structures.
* **`ChannelXYPlot` ("XY-Plotter-Simple") & `XYPlotOverlay` ("XY-Plotter-Overlay")**: Matplotlib-backed plotting nodes rendering publication-quality line charts and multi-run overlays directly as visual node outputs.

### 3. Dynamic Python Scripting Engine (`custom_nodes/python-calcs`)
Execute arbitrary engineering scripts without building boilerplate ComfyUI nodes:
* **`PythonCalcNode`**: Drop `.py` calculation scripts into `scripts/`. The node inspects the file, rebuilds its input/output connection slots dynamically, and runs the script's `run()` function.
* **Declarative Contract (`__comfy_meta__`)**: Scripts declare typed inputs, outputs, default ranges, and error policies (`raise` vs. `default`).
* **Zero-Overhead AST Validation**: Inspects script interfaces via Python AST parsing without importing heavy libraries (`numpy`, `scipy`, `torch`) at load time.
* **Live Hot-Reloading**: Automatically detects file modifications based on `mtime`, reloading scripts on execution without restarting the server.
* **Dual-Mode Scalar Widgets**: Scalar parameters (FLOAT, INT, STRING, BOOLEAN) render as interactive widgets that simultaneously support native hover-to-connect cable wiring.

### 4. Graph Flow Control & Iterative Execution
Overcomes the traditional DAG (Directed Acyclic Graph) limitation of ComfyUI:
* **`For-Loop-Enumerate (Open / Close)`**: Implements true loop iterations over file lists or channel bundles using dynamic graph expansion via `GraphBuilder` and `DYNPROMPT`.
* **`ExternalProcessBatNode`**: Orchestrates external engineering executables, solvers, and batch scripts (`.bat`, `.cmd`, CLI tools) with live output streaming over WebSockets, configurable timeouts, and clean Windows process tree termination.
* **`FileListBuilderNode`**: In-graph file selection list manager with interactive Add/Remove/Clear controls.
* **Boolean & Logic Utilities**: Conditionals, threshold comparisons, and string scanners for branching and validation.

### 5. Engineering Template Library
* **Custom Template System**: Replaces default AI art blueprints with engineering categories configured via `user/default/template_library.json`.
* **Configured Categories**: *Vehicle Dynamics*, *Load Analysis*, *Utility*, *LLM*, *Popular*, *Get Started*.
* **Prebuilt Demo Workflows**: Includes end-to-end demonstrations such as `Lunch_And_Learn_Demo.json` and `Lunch_And_Learn_Loads.json`, showcasing batch run processing, external solver calls, telemetry remapping, and overlay plotting.

---

## Project Structure

```text
PME-ComfyEW/
├── app/                        # ComfyUI core server and frontend management
│   ├── custom_node_manager.py  # Local template discovery and routing
│   └── frontend_management.py  # Template asset mapping and UI overrides
├── blueprints/                 # Pruned engineering blueprints and workflows
├── custom_nodes/
│   ├── python-calcs/           # Dynamic Python scripting, loops & external process runner
│   │   ├── js/                 # Dynamic slot rendering and live UI updates
│   │   ├── scripts/            # User-authored calculation scripts
│   │   ├── loop_enumerate_nodes.py # Dynamic graph expansion loops
│   │   ├── external_process_node.py # Subprocess runner with live terminal feedback
│   │   └── node.py             # PythonCalcNode engine
│   ├── timeseries-nodes/       # Telemetry ingestion, ChannelMapper & plotting
│   │   ├── js/                 # DOM / Vue table widget and XY plot extensions
│   │   ├── channel_mapper.py   # In-canvas signal transformer and dynamic outputs
│   │   ├── load_timeseries.py  # CSV/Parquet loader
│   │   ├── save_hdf5.py        # HDF5 single and batch archival
│   │   └── DEVELOPER_NOTES.md  # Deep technical reference on LiteGraph/Vue 2.0 quirks
│   └── ComfyUI-Data-Analysis/  # Dataframe manipulation and statistical operations
├── user/
│   └── default/
│       ├── template_library/   # Categorized engineering workflow templates
│       │   ├── Vehicle Dynamics/
│       │   └── Load Analysis/
│       └── template_library.json # Template configuration & menu pruning flags
├── main.py                     # Application entry point
├── nodes.py                    # Lean core node definitions
└── server.py                   # AsyncIO / aiohttp webserver
```

---

## Getting Started

### 1. Prerequisites
* Python 3.10+ (Recommended: Python 3.12 or 3.13)
* Windows 10/11 or Linux
* Virtual environment (`.venv` or `.comfy-venv`)

### 2. Environment Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install base requirements
pip install -r requirements.txt

# Install engineering telemetry & plotting packages
pip install h5py matplotlib pandas
```

### 3. Launching the Workbench
```powershell
python main.py
```
Open your browser to `http://127.0.0.1:8188`.

---

## Authoring Custom Calculations (`python-calcs`)

To add an engineering calculation, create a Python file in `custom_nodes/python-calcs/scripts/` (e.g., `filter_signal.py`):

```python
__comfy_meta__ = {
    "name": "Butterworth Lowpass Filter",
    "description": "Applies a lowpass Butterworth filter to a telemetry channel",
    "on_error": "raise",  # or "default"
    "inputs": [
        {"name": "channel", "type": "CHANNEL"},
        {"name": "cutoff_hz", "type": "FLOAT", "default": 10.0, "min": 0.1, "max": 1000.0, "step": 0.5},
        {"name": "order", "type": "INT", "default": 2, "min": 1, "max": 10},
    ],
    "outputs": [
        {"name": "filtered_channel", "type": "CHANNEL", "default": None},
    ],
}

def run(channel, cutoff_hz, order):
    import numpy as np
    from scipy.signal import butter, filtfilt

    data = np.array(channel["data"], dtype=float)
    fs = channel.get("sample_rate", 100.0)

    nyq = 0.5 * fs
    normal_cutoff = cutoff_hz / nyq
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    filtered = filtfilt(b, a, data)

    out = dict(channel)
    out["data"] = filtered.tolist()
    return (out,)
```
The node automatically surfaces in ComfyUI under **`Python Script`** and re-draws its slots immediately upon selecting the script.

---

## Development Notes & Frontend Integration

For developers extending custom nodes or working with ComfyUI's canvas:
* **DOM Table Rendering**: Refer to `custom_nodes/timeseries-nodes/DEVELOPER_NOTES.md` for detailed rules on DOM element clipping (`overflow: clip`), scale compensation, and preventing ghost compositor artifacts.
* **ComfyUI Node 2.0 (Vue 3)**: Mutations must propagate through `app.canvas.initLayoutMutations().resizeNode()` and `app.graph.onNodeAdded(node)` to ensure synchronization with the YJS layout store and Vue reactivity.
* **Custom Endpoints**: Always register HTTP routes via `@PromptServer.instance.routes.get()` decorators rather than mutating `server.app.router` directly.

---

## License & Attribution
Based on the open-source [ComfyUI](https://github.com/Comfy-Org/ComfyUI) engine. Customized for engineering workflows by Pratt Miller Engineering.
