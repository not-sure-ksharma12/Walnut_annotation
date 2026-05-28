#create virtual env
python3 -m venv .venv
source .venv/bin/activate

#install dependencies
pip install -r requirements.txt

#sanity check
python -c "import cv2, numpy; print('opencv', cv2.__version__, 'numpy', numpy.__version__)"
python crop_image_quadrants.py --help
python walnut_annotator.py --help