#!/usr/bin/env python3
"""
Interactive Walnut Annotation Tool
Click on walnuts to mark their centers and save annotations to text files.
"""

"""#### `walnut_annotator.py`
Purpose: Interactive tool for manually annotating walnut centers in images
Features:
- Click-to-annotate interface with visual feedback
- Zoom and pan functionality for precise annotation
- Saves annotations in text format (x y coordinates)
- Supports multiple images in a folder

Usage:
```bash
python walnut_annotator.py --input_folder /path/to/images --output_folder /path/to/annotations
```
"""

import os
import cv2
import numpy as np
import argparse
from pathlib import Path
import glob

class WalnutAnnotator:
    def __init__(self, image_folder, output_folder=None, circle_radius=8):
        self.image_folder = image_folder
        self.output_folder = output_folder or os.path.join(image_folder, "annotations")
        self.circle_radius = circle_radius
        
        # Create output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Get all image files
        self.image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        self.image_files = []
        for ext in self.image_extensions:
            self.image_files.extend(glob.glob(os.path.join(image_folder, ext)))
        
        self.image_files = sorted(self.image_files)
        self.current_image_idx = 0
        self.annotations = []  # List of (x, y) coordinates
        self.image = None
        self.display_image = None
        self.window_name = "Walnut Annotator"
        
        # Zoom functionality
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_pan_x = 0
        self.last_pan_y = 0
        
        if not self.image_files:
            raise ValueError(f"No images found in {image_folder}")
        
        print(f"Found {len(self.image_files)} images to annotate")
        print(f"Annotations will be saved to: {self.output_folder}")
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks to add/remove annotations and panning"""
        # Convert display coordinates to image coordinates
        img_x, img_y = self.display_to_image_coords(x, y)
        
        if event == cv2.EVENT_LBUTTONDOWN:
            if flags & cv2.EVENT_FLAG_CTRLKEY:
                # Ctrl + Left click: Start panning
                self.is_panning = True
                self.last_pan_x = x
                self.last_pan_y = y
            else:
                # Add annotation
                self.annotations.append((img_x, img_y))
                print(f"Added annotation at ({img_x}, {img_y}) - Total: {len(self.annotations)}")
                self.update_display()
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Remove nearest annotation
            if self.annotations:
                # Find closest annotation in image coordinates
                distances = [np.sqrt((img_x - ax)**2 + (img_y - ay)**2) for ax, ay in self.annotations]
                closest_idx = np.argmin(distances)
                if distances[closest_idx] < 30:  # Only remove if close enough
                    removed = self.annotations.pop(closest_idx)
                    print(f"Removed annotation at {removed} - Total: {len(self.annotations)}")
                    self.update_display()
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.is_panning:
                # Pan the image
                dx = x - self.last_pan_x
                dy = y - self.last_pan_y
                self.pan_x += dx
                self.pan_y += dy
                self.last_pan_x = x
                self.last_pan_y = y
                self.update_display()
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.is_panning = False
        
        elif event == cv2.EVENT_MOUSEWHEEL:
            # Zoom in/out
            if flags > 0:  # Scroll up - zoom out (OpenCV behavior)
                self.zoom_out()
            else:  # Scroll down - zoom in (OpenCV behavior)
                self.zoom_in()
    
    def zoom_in(self):
        """Zoom in"""
        self.zoom_factor = min(self.zoom_factor + self.zoom_step, self.max_zoom)
        self.update_display()
        print(f"Zoom: {self.zoom_factor:.1f}x")
    
    def zoom_out(self):
        """Zoom out"""
        self.zoom_factor = max(self.zoom_factor - self.zoom_step, self.min_zoom)
        self.update_display()
        print(f"Zoom: {self.zoom_factor:.1f}x")
    
    def reset_zoom(self):
        """Reset zoom and pan"""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_display()
        print("Zoom reset to 1.0x")
    
    def display_to_image_coords(self, x, y):
        """Convert display coordinates to image coordinates"""
        if self.image is None:
            return x, y
        
        # Account for zoom and pan
        img_x = (x - self.pan_x) / self.zoom_factor
        img_y = (y - self.pan_y) / self.zoom_factor
        
        # Clamp to image bounds
        img_x = max(0, min(img_x, self.image.shape[1] - 1))
        img_y = max(0, min(img_y, self.image.shape[0] - 1))
        
        return int(img_x), int(img_y)
    
    def image_to_display_coords(self, x, y):
        """Convert image coordinates to display coordinates"""
        if self.image is None:
            return x, y
        
        # Account for zoom and pan
        disp_x = x * self.zoom_factor + self.pan_x
        disp_y = y * self.zoom_factor + self.pan_y
        
        return int(disp_x), int(disp_y)
    
    def load_image(self, idx):
        """Load image at given index"""
        if 0 <= idx < len(self.image_files):
            image_path = self.image_files[idx]
            self.image = cv2.imread(image_path)
            if self.image is None:
                print(f"Error loading image: {image_path}")
                return False
            
            self.display_image = self.image.copy()
            self.current_image_idx = idx
            
            # Reset zoom and pan for new image
            self.reset_zoom()
            
            # Load existing annotations if they exist
            self.load_existing_annotations()
            
            # Update display
            self.update_display()
            
            print(f"\nImage {idx + 1}/{len(self.image_files)}: {os.path.basename(image_path)}")
            print(f"Image size: {self.image.shape[1]}x{self.image.shape[0]}")
            print(f"Current annotations: {len(self.annotations)}")
            
            return True
        return False
    
    def load_existing_annotations(self):
        """Load existing annotations for current image"""
        self.annotations = []
        image_name = Path(self.image_files[self.current_image_idx]).stem
        annotation_file = os.path.join(self.output_folder, f"{image_name}.txt")
        
        if os.path.exists(annotation_file):
            try:
                with open(annotation_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2:
                                x, y = float(parts[0]), float(parts[1])
                                self.annotations.append((int(x), int(y)))
                print(f"Loaded {len(self.annotations)} existing annotations")
            except Exception as e:
                print(f"Error loading annotations: {e}")
    
    def save_annotations(self):
        """Save current annotations to file"""
        if not self.annotations:
            return
        
        image_name = Path(self.image_files[self.current_image_idx]).stem
        annotation_file = os.path.join(self.output_folder, f"{image_name}.txt")
        
        try:
            with open(annotation_file, 'w') as f:
                f.write("# Walnut center annotations (x, y) coordinates\n")
                f.write(f"# Image: {os.path.basename(self.image_files[self.current_image_idx])}\n")
                f.write(f"# Image size: {self.image.shape[1]}x{self.image.shape[0]}\n")
                f.write(f"# Total walnuts: {len(self.annotations)}\n")
                f.write("# Format: x y\n")
                
                for x, y in self.annotations:
                    f.write(f"{x} {y}\n")
            
            print(f"Saved {len(self.annotations)} annotations to {annotation_file}")
        except Exception as e:
            print(f"Error saving annotations: {e}")
    
    def update_display(self):
        """Update the display with current annotations"""
        if self.image is None:
            return
        
        # Create a copy of the original image
        working_image = self.image.copy()
        
        # Draw annotations on the original image coordinates
        for i, (x, y) in enumerate(self.annotations):
            # Draw circle
            cv2.circle(working_image, (x, y), self.circle_radius, (0, 255, 0), 2)
            # Draw center dot
            cv2.circle(working_image, (x, y), 2, (0, 255, 0), -1)
            # Draw annotation number
            cv2.putText(working_image, str(i + 1), (x + self.circle_radius + 2, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Apply zoom and pan
        if self.zoom_factor != 1.0 or self.pan_x != 0 or self.pan_y != 0:
            # Resize image based on zoom
            new_width = int(working_image.shape[1] * self.zoom_factor)
            new_height = int(working_image.shape[0] * self.zoom_factor)
            
            if new_width > 0 and new_height > 0:
                zoomed_image = cv2.resize(working_image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
                
                # Create display canvas
                canvas_height = max(600, new_height + 100)  # Extra space for UI
                canvas_width = max(800, new_width + 100)
                self.display_image = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
                
                # Place zoomed image on canvas with pan offset
                y1 = max(0, self.pan_y)
                y2 = min(canvas_height, self.pan_y + new_height)
                x1 = max(0, self.pan_x)
                x2 = min(canvas_width, self.pan_x + new_width)
                
                src_y1 = max(0, -self.pan_y)
                src_y2 = src_y1 + (y2 - y1)
                src_x1 = max(0, -self.pan_x)
                src_x2 = src_x1 + (x2 - x1)
                
                if y2 > y1 and x2 > x1 and src_y2 <= new_height and src_x2 <= new_width:
                    self.display_image[y1:y2, x1:x2] = zoomed_image[src_y1:src_y2, src_x1:src_x2]
            else:
                self.display_image = working_image
        else:
            self.display_image = working_image
        
        # Add info text
        info_text = f"Image {self.current_image_idx + 1}/{len(self.image_files)} | Annotations: {len(self.annotations)} | Zoom: {self.zoom_factor:.1f}x"
        cv2.putText(self.display_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(self.display_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        
        # Add instructions
        instructions = "Left click: Add | Right click: Remove | Ctrl+Click: Pan | Mouse wheel: Zoom | 'r': Reset zoom | 's': Save | 'n': Next | 'p': Previous | 'q': Quit"
        cv2.putText(self.display_image, instructions, (10, self.display_image.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
        cv2.putText(self.display_image, instructions, (10, self.display_image.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        cv2.imshow(self.window_name, self.display_image)
    
    def run(self):
        """Main annotation loop"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        # Load first image
        if not self.load_image(0):
            print("Error loading first image")
            return
        
        print("\n" + "="*70)
        print("WALNUT ANNOTATION TOOL")
        print("="*70)
        print("Instructions:")
        print("- Left click: Add walnut annotation")
        print("- Right click: Remove nearest annotation")
        print("- Ctrl + Left click + drag: Pan around image")
        print("- Mouse wheel: Zoom in/out")
        print("- 's': Save current annotations")
        print("- 'n': Next image")
        print("- 'p': Previous image")
        print("- 'q': Quit and save all")
        print("- 'r': Reset zoom and pan")
        print("- 'z': Reset current image annotations")
        print("="*70)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                # Save and quit
                self.save_annotations()
                break
            
            elif key == ord('s'):
                # Save current annotations
                self.save_annotations()
            
            elif key == ord('n'):
                # Next image
                self.save_annotations()
                if self.current_image_idx < len(self.image_files) - 1:
                    self.load_image(self.current_image_idx + 1)
                else:
                    print("Already at last image")
            
            elif key == ord('p'):
                # Previous image
                self.save_annotations()
                if self.current_image_idx > 0:
                    self.load_image(self.current_image_idx - 1)
                else:
                    print("Already at first image")
            
            elif key == ord('r'):
                # Reset zoom and pan
                self.reset_zoom()
            
            elif key == ord('z'):
                # Reset current image annotations
                self.annotations = []
                self.update_display()
                print("Reset annotations for current image")
            
            elif key == 27:  # ESC key
                break
        
        cv2.destroyAllWindows()
        
        # Final save
        self.save_annotations()
        print(f"\nAnnotation complete! Files saved to: {self.output_folder}")
        
        # Print summary
        total_annotations = 0
        annotated_images = 0
        for image_file in self.image_files:
            image_name = Path(image_file).stem
            annotation_file = os.path.join(self.output_folder, f"{image_name}.txt")
            if os.path.exists(annotation_file):
                with open(annotation_file, 'r') as f:
                    count = sum(1 for line in f if line.strip() and not line.startswith('#'))
                total_annotations += count
                annotated_images += 1
        
        print(f"Summary: {annotated_images}/{len(self.image_files)} images annotated")
        print(f"Total walnut annotations: {total_annotations}")

def main():
    parser = argparse.ArgumentParser(description="Interactive Walnut Annotation Tool")
    parser.add_argument("image_folder", help="Folder containing images to annotate")
    parser.add_argument("-o", "--output", help="Output folder for annotations (default: image_folder/annotations)")
    parser.add_argument("-r", "--radius", type=int, default=8, help="Circle radius for annotations (default: 8)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_folder):
        print(f"Error: Image folder '{args.image_folder}' does not exist")
        return
    
    try:
        annotator = WalnutAnnotator(args.image_folder, args.output, args.radius)
        annotator.run()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
