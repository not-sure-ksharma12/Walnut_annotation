# Walnut Annotation

## Setup

### Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Sanity Check
Verify that all dependencies are installed correctly:
```bash
python -c "import cv2, numpy; print('opencv', cv2.__version__, 'numpy', numpy.__version__)"
```

### Crop Image Quadrants
```bash
python crop_image_quadrants.py --help
```

### Walnut Annotator
```bash
python walnut_annotator.py --help
```
