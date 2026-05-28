# Walnut Annotation

Tools for preparing walnut images and manually annotating walnut centers for training or evaluation.

## Overview

| Script | Purpose |
|--------|---------|
| `crop_image_quadrants.py` | Split one image into four equal quadrants (useful for tiling large photos). |
| `walnut_annotator.py` | Interactive GUI to click walnut centers and save coordinates to text files. |

**Typical workflow**

1. (Optional) Crop large images into quadrants with `crop_image_quadrants.py`.
2. Annotate walnut centers with `walnut_annotator.py`.
3. Use the generated `.txt` annotation files downstream (training, validation, etc.).

## Documentation in the scripts

Both scripts are documented in two places:

1. **Module docstrings** (top of each file) — usage, options, and behavior at a glance.
2. **Inline comments** — explain non-obvious logic (coordinate transforms, zoom/pan, save format, quadrant naming).

Read the file headers before running; they mirror what `--help` shows and add context (e.g. quadrant naming `q00`–`q11`, annotation file format).

## Requirements

- Python 3.9+
- Dependencies: `opencv-python`, `numpy` (see `requirements.txt`)

OpenCV needs a display for `walnut_annotator.py` (not ideal over headless SSH). Use `opencv-python` (not `opencv-python-headless`) if the GUI window does not open.

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
```

On Windows (Command Prompt):

```cmd
python -m venv .venv
```

### 2. Activate the virtual environment

**macOS / Linux (bash/zsh):**

```bash
source .venv/bin/activate
```

**Windows — PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows — Command Prompt:**

```cmd
.venv\Scripts\activate.bat
```

#### Windows: “running scripts is disabled on this system”

If PowerShell refuses to run `Activate.ps1` with an execution-policy error, allow scripts for your user (one-time):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

- `RemoteSigned` lets local scripts run; downloaded scripts still need signing.
- You can revert later with `Set-ExecutionPolicy -ExecutionPolicy Restricted -Scope CurrentUser` if you prefer.
- Alternative: use **Command Prompt** and `activate.bat` above (no PowerShell script policy).

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Sanity check

```bash
python -c "import cv2, numpy; print('opencv', cv2.__version__, 'numpy', numpy.__version__)"
python crop_image_quadrants.py --help
python walnut_annotator.py --help
```

## Usage

### `crop_image_quadrants.py`

Split an image into four equal tiles.

```bash
python crop_image_quadrants.py /path/to/image.jpg -o /path/to/output
```

| Option | Description |
|--------|-------------|
| `-o`, `--output` | Output directory (default: same folder as the input image) |
| `--pad` | If width/height is odd, pad to even size before splitting |
| `--pad-color R G B` | Padding color when using `--pad` (default: `0 0 0`) |

**Output names:** `<stem>_q00`, `_q01`, `_q10`, `_q11` + original extension

| Suffix | Region |
|--------|--------|
| `q00` | top-left |
| `q01` | top-right |
| `q10` | bottom-left |
| `q11` | bottom-right |

**Example:**

```bash
python crop_image_quadrants.py image/photo.jpg -o image/quadrants --pad
```

### `walnut_annotator.py`

Interactive annotation over all images in a folder.

```bash
python walnut_annotator.py /path/to/images -o /path/to/annotations
```

| Option | Description |
|--------|-------------|
| `image_folder` | Folder of `.jpg` / `.jpeg` / `.png` images |
| `-o`, `--output` | Where `.txt` annotations are saved (default: `image_folder/annotations`) |
| `-r`, `--radius` | Circle radius for markers (default: `8`) |

**Controls**

| Action | Effect |
|--------|--------|
| Left click | Add walnut center |
| Right click | Remove nearest annotation |
| Ctrl + left click + drag | Pan |
| Mouse wheel | Zoom in/out |
| `s` | Save current image |
| `n` / `p` | Next / previous image (saves first) |
| `r` | Reset zoom and pan |
| `z` | Clear annotations on current image |
| `q` or Esc | Quit (saves before exit) |

**Annotation files:** one `<image_stem>.txt` per image in the output folder. Header lines start with `#`; data lines are `x y` in image pixel coordinates.

## Project layout

```
Walnut_annotation/
├── crop_image_quadrants.py
├── walnut_annotator.py
├── requirements.txt
├── Readme.md
└── image/                 # example images (optional)
```

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| PowerShell won’t activate venv | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`, or use `activate.bat` in cmd |
| `import cv2` fails | Activate venv, run `pip install -r requirements.txt` |
| Annotator window doesn’t appear | Use `opencv-python`, run locally with a display |
| Crop fails on odd dimensions | Add `--pad` (and optional `--pad-color`) |
