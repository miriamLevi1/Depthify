# Universal 2D to 3D Object Converter - Enhanced
# ===================================================
# Converts any 2D object image to a 3D model with original colors
# Optimized for all object types, not just apples
# ===================================================

from __future__ import annotations
import os, cv2, numpy as np, pandas as pd, trimesh
from PIL import Image, ImageFilter, ImageEnhance
from rembg import remove
from scipy.spatial import Delaunay
from scipy.ndimage import gaussian_filter, binary_erosion, binary_dilation
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from pathlib import Path
import json
from typing import Dict, Tuple, Optional

# =============================================================
#                    Configuration System
# =============================================================

class Config:
    """Configuration for different object types"""
    
    # Default settings for universal objects
    DEFAULT_SETTINGS = {
        "scale_z": 60,           # Moderate depth scaling
        "smooth_sigma": 1.5,     # Smoothing amount
        "depth_boost": 1.3,      # Depth enhancement
        "gradient_strength": 0.6, # Gradient intensity
        "weights": {
            "shape_contour": 0.35,
            "radial_gradient": 0.25,
            "edge_enhanced": 0.25,
            "texture_depth": 0.15,
        }
    }
    
    # Specific settings for different object types
    OBJECT_PRESETS = {
        "fruit": {
            "scale_z": 80,
            "smooth_sigma": 2.0,
            "depth_boost": 1.5,
            "gradient_strength": 0.7,
            "weights": {
                "shape_contour": 0.4,
                "radial_gradient": 0.3,
                "edge_enhanced": 0.2,
                "texture_depth": 0.1,
            }
        },
        "geometric": {
            "scale_z": 40,
            "smooth_sigma": 0.8,
            "depth_boost": 1.1,
            "gradient_strength": 0.4,
            "weights": {
                "shape_contour": 0.5,
                "radial_gradient": 0.2,
                "edge_enhanced": 0.2,
                "texture_depth": 0.1,
            }
        },
        "organic": {
            "scale_z": 70,
            "smooth_sigma": 2.2,
            "depth_boost": 1.4,
            "gradient_strength": 0.65,
            "weights": {
                "shape_contour": 0.3,
                "radial_gradient": 0.3,
                "edge_enhanced": 0.25,
                "texture_depth": 0.15,
            }
        },
        "flat": {
            "scale_z": 25,
            "smooth_sigma": 1.0,
            "depth_boost": 1.0,
            "gradient_strength": 0.3,
            "weights": {
                "shape_contour": 0.6,
                "radial_gradient": 0.15,
                "edge_enhanced": 0.15,
                "texture_depth": 0.1,
            }
        }
    }

# =============================================================
#                    Enhanced File Management
# =============================================================

class FileManager:
    """Manages file paths and directory creation"""
    
    def __init__(self, input_image: str, object_type: str = "default"):
        self.input_path = Path(input_image)
        self.object_type = object_type
        
        # Create base name from input file
        self.base_name = self.input_path.stem
        
        # Setup directory structure
        self.setup_directories()
        
    def setup_directories(self):
        """Creates necessary directories"""
        self.base_dir = Path(r"C:\Users\Student6\Desktop\Depthify\depthify-backend")
        self.images_dir = self.base_dir / "uploads"
        self.models_dir = self.base_dir / "models"
        self.debug_dir = self.base_dir / "debug"
        
        for directory in [self.images_dir, self.models_dir, self.debug_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def png_path(self) -> str:
        return str(self.images_dir / f"{self.base_name}_no_bg.png")
    
    @property
    def csv_path(self) -> str:
        return str(self.models_dir / f"{self.base_name}_depth.csv")
    
    @property
    def ply_path(self) -> str:
        return str(self.models_dir / f"{self.base_name}_model.ply")
    
    @property
    def stl_path(self) -> str:
        return str(self.models_dir / f"{self.base_name}_printable.stl")

# =============================================================
#                    Smart Object Analysis
# =============================================================

class ObjectAnalyzer:
    """Analyzes object characteristics to optimize depth generation"""
    
    @staticmethod
    def analyze_object_type(rgb: np.ndarray, mask: np.ndarray) -> str:
        """Automatically detects object type from image characteristics"""
        
        # Calculate various metrics
        masked_rgb = rgb[mask]
        
        if len(masked_rgb) == 0:
            return "default"
        
        # Color variance (high = colorful, low = monochrome)
        color_variance = np.var(masked_rgb, axis=0).mean()
        
        # Edge density
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges[mask]) / np.sum(mask)
        
        # Shape complexity (perimeter to area ratio)
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(largest_contour, True)
            area = cv2.contourArea(largest_contour)
            complexity = perimeter / np.sqrt(area) if area > 0 else 0
        else:
            complexity = 0
        
        # Decision logic
        if color_variance > 1000 and complexity > 15:
            return "organic"
        elif edge_density > 0.1 and complexity < 12:
            return "geometric"
        elif color_variance > 500 and edge_density < 0.05:
            return "fruit"
        elif edge_density < 0.02:
            return "flat"
        else:
            return "default"

# =============================================================
#                    Enhanced Color Preservation
# =============================================================

class ColorPreserver:
    """Preserves and enhances original colors"""
    
    @staticmethod
    def enhance_colors(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Enhances colors while preserving original appearance"""
        enhanced = rgb.copy()
        
        # Apply enhancement only to masked area
        if np.any(mask):
            masked_rgb = rgb[mask]
            
            # Convert to PIL for enhancement
            temp_img = Image.fromarray(rgb)
            
            # Slight saturation boost
            enhancer = ImageEnhance.Color(temp_img)
            temp_img = enhancer.enhance(1.1)
            
            # Slight contrast boost
            enhancer = ImageEnhance.Contrast(temp_img)
            temp_img = enhancer.enhance(1.05)
            
            enhanced = np.array(temp_img)
        
        return enhanced
    
    @staticmethod
    def create_color_mapping(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Creates optimized color mapping for 3D display"""
        colors = rgb.copy().astype(np.float32)
        
        # Normalize colors for better 3D visualization
        colors = colors / 255.0
        
        # Apply gamma correction for better appearance in 3D viewers
        colors = np.power(colors, 0.9)
        
        # Ensure colors stay in valid range
        colors = np.clip(colors, 0, 1)
        
        return (colors * 255).astype(np.uint8)

# =============================================================
#                    Universal Depth Map Functions
# =============================================================

def depth_shape_contour_universal(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Universal shape-based depth mapping"""
    mask_uint8 = (mask * 255).astype(np.uint8)
    
    # Advanced morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    clean_mask = cv2.morphologyEx(mask_uint8, cv2.MORPH_CLOSE, kernel)
    clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
    
    # Distance transform with better parameters
    dist = cv2.distanceTransform(clean_mask, cv2.DIST_L2, 5)
    
    if dist[mask].max() > 0:
        normalized = dist / dist[mask].max()
        # Adaptive power function based on object size
        power = 0.6 + 0.3 * (1.0 - np.sum(mask) / (mask.shape[0] * mask.shape[1]))
        depth = np.power(normalized, power)
    else:
        depth = np.zeros_like(dist)
    
    depth[~mask] = 0
    return depth.astype(np.float32)

def depth_radial_gradient_universal(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Universal radial gradient depth"""
    h, w = mask.shape
    
    # Find center of mass with better weighting
    coords = np.where(mask)
    if len(coords[0]) == 0:
        return np.zeros_like(mask, dtype=np.float32)
    
    # Weight center calculation by intensity
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    weights = gray[coords] + 1  # Avoid zero weights
    center_y = np.average(coords[0], weights=weights)
    center_x = np.average(coords[1], weights=weights)
    
    # Create distance grid
    y_grid, x_grid = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    distances = np.sqrt((x_grid - center_x)**2 + (y_grid - center_y)**2)
    
    # Adaptive maximum distance
    max_dist = np.percentile(distances[mask], 95) if distances[mask].size > 0 else 1
    
    # Create gradient with adaptive falloff
    depth = 1.0 - (distances / max_dist)
    depth = np.clip(depth, 0, 1)
    
    # Apply adaptive power function
    depth = np.power(depth, 0.8)
    
    depth[~mask] = 0
    return depth.astype(np.float32)

def depth_edge_enhanced_universal(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Universal edge-based depth"""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    
    # Multi-scale edge detection
    edges1 = cv2.Canny(gray, 30, 100)
    edges2 = cv2.Canny(gray, 80, 200)
    
    # Combine edges
    edges_combined = cv2.bitwise_or(edges1, edges2)
    
    # Distance from edges
    edges_smooth = gaussian_filter(edges_combined.astype(np.float32), sigma=1.5)
    
    # Invert to create depth
    depth = 1.0 - (edges_smooth / 255.0)
    depth[~mask] = 0
    
    return depth.astype(np.float32)

def depth_texture_universal(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Universal texture-based depth"""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    
    # Multi-scale texture analysis
    texture_maps = []
    
    for kernel_size in [3, 7, 11]:
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        variance = np.abs(gray.astype(np.float32) - mean_filtered)
        texture_maps.append(variance)
    
    # Combine texture maps
    combined_texture = np.mean(texture_maps, axis=0)
    
    # Normalize
    if combined_texture[mask].max() > 0:
        depth = combined_texture / combined_texture[mask].max()
    else:
        depth = np.zeros_like(gray, dtype=np.float32)
    
    depth[~mask] = 0
    return depth.astype(np.float32)

# Enhanced depth functions dictionary
UNIVERSAL_DEPTH_FUNCS = {
    "shape_contour": depth_shape_contour_universal,
    "radial_gradient": depth_radial_gradient_universal,
    "edge_enhanced": depth_edge_enhanced_universal,
    "texture_depth": depth_texture_universal,
}

# =============================================================
#                    Main Converter Class
# =============================================================

class Universal3DConverter:
    """Main converter class"""
    
    def __init__(self, input_image: str, object_type: str = "auto"):
        self.file_manager = FileManager(input_image, object_type)
        self.object_type = object_type
        self.config = None
        
    def load_image_with_alpha(self, path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Load image with alpha channel"""
        img = Image.open(path).convert("RGBA")
        rgba = np.array(img)
        rgb = rgba[:, :, :3]
        alpha = rgba[:, :, 3]
        mask = alpha > 128
        return rgb, mask, alpha
    
    def remove_background(self) -> None:
        """Remove background with optimization"""
        print(f"🎯 Removing background from {self.file_manager.input_path}...")
        
        with open(self.file_manager.input_path, "rb") as f:
            input_data = f.read()
        
        output_data = remove(input_data)
        
        with open(self.file_manager.png_path, "wb") as f:
            f.write(output_data)
        
        print(f"✅ Background removed → {self.file_manager.png_path}")
    
    def analyze_and_configure(self) -> None:
        """Analyze object and set optimal configuration"""
        rgb, mask, alpha = self.load_image_with_alpha(self.file_manager.png_path)
        
        if self.object_type == "auto":
            detected_type = ObjectAnalyzer.analyze_object_type(rgb, mask)
            print(f"🔍 Detected object type: {detected_type}")
            self.object_type = detected_type
        
        # Load configuration
        if self.object_type in Config.OBJECT_PRESETS:
            self.config = Config.OBJECT_PRESETS[self.object_type]
        else:
            self.config = Config.DEFAULT_SETTINGS
        
        print(f"⚙️ Using configuration for: {self.object_type}")
    
    def create_enhanced_depth_map(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Create enhanced depth map with color preservation"""
        print("🧮 Creating enhanced depth maps...")
        
        rgb, mask, alpha = self.load_image_with_alpha(self.file_manager.png_path)
        
        # Enhance colors
        rgb_enhanced = ColorPreserver.enhance_colors(rgb, mask)
        
        # Create depth maps
        depth_maps = {}
        for name, func in UNIVERSAL_DEPTH_FUNCS.items():
            print(f"  📊 Processing {name} depth map...")
            depth_maps[name] = func(rgb_enhanced, mask)
        
        # Combine maps with weights
        combined = np.zeros_like(next(iter(depth_maps.values())))
        weights = self.config["weights"]
        
        for name, weight in weights.items():
            if name in depth_maps:
                combined += depth_maps[name] * weight
        
        # Apply smoothing
        combined = gaussian_filter(combined, sigma=self.config["smooth_sigma"])
        
        # Apply depth boost
        combined = np.power(combined, 1.0 / self.config["depth_boost"])
        combined = np.clip(combined, 0, 1)
        
        # Apply mask
        combined[~mask] = 0
        
        # Save debug visualization
        self.save_debug_visualization(depth_maps, combined)
        
        print("✅ Enhanced depth map completed")
        return combined, rgb_enhanced, mask
    
    def save_debug_visualization(self, depth_maps: Dict, combined: np.ndarray) -> None:
        """Save debug visualization"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, (name, depth_map) in enumerate(depth_maps.items()):
            if i < len(axes) - 1:
                axes[i].imshow(depth_map, cmap='hot')
                axes[i].set_title(f'{name}')
                axes[i].axis('off')
        
        axes[-1].imshow(combined, cmap='hot')
        axes[-1].set_title('Combined Depth')
        axes[-1].axis('off')
        
        plt.tight_layout()
        debug_path = self.file_manager.debug_dir / f"{self.file_manager.base_name}_depth_analysis.png"
        plt.savefig(debug_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"🔍 Debug visualization saved: {debug_path}")
    
    def create_colored_csv(self) -> None:
        """Create CSV with enhanced colors"""
        combined_depth, rgb, mask = self.create_enhanced_depth_map()
        
        h, w = combined_depth.shape
        y_coords, x_coords = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
        
        # Only points within the object
        valid_mask = combined_depth > 0.01
        
        # Create color mapping
        colors_mapped = ColorPreserver.create_color_mapping(rgb, mask)
        
        points_data = {
            'x': x_coords[valid_mask],
            'y': y_coords[valid_mask],
            'z': combined_depth[valid_mask],
            'r': colors_mapped[valid_mask, 0],
            'g': colors_mapped[valid_mask, 1],
            'b': colors_mapped[valid_mask, 2]
        }
        
        df = pd.DataFrame(points_data)
        
        # Filter outliers
        z_mean = df['z'].mean()
        z_std = df['z'].std()
        df = df[np.abs(df['z'] - z_mean) < 3 * z_std]
        
        df.to_csv(self.file_manager.csv_path, index=False)
        print(f"✅ Colored CSV saved → {self.file_manager.csv_path} | {len(df)} points")
    
    def create_3d_mesh(self) -> None:
        """Create 3D mesh with colors"""
        print("🏗️ Building 3D mesh...")
        
        df = pd.read_csv(self.file_manager.csv_path)
        
        # Vertices with enhanced colors
        vertices = df[['x', 'y', 'z']].values.astype(np.float32)
        colors = df[['r', 'g', 'b']].values.astype(np.uint8)
        
        # Scale Z dimension
        vertices[:, 2] *= self.config["scale_z"]
        
        # Triangulation
        try:
            tri = Delaunay(vertices[:, :2])
            
            # Create mesh with colors
            mesh = trimesh.Trimesh(
                vertices=vertices,
                faces=tri.simplices,
                vertex_colors=colors,
                process=False
            )
            
            # Smooth mesh
            mesh = mesh.smoothed()
            
            # Validation
            print(f"📊 Mesh statistics:")
            print(f"   Vertices: {len(vertices)}")
            print(f"   Faces: {len(tri.simplices)}")
            print(f"   Watertight: {mesh.is_watertight}")
            
            # Save PLY with colors
            mesh.export(self.file_manager.ply_path)
            print(f"✅ PLY saved (with colors): {self.file_manager.ply_path}")
            
            # Save STL for printing
            try:
                # Create a clean STL version (no colors)
                stl_mesh = trimesh.Trimesh(
                    vertices=mesh.vertices,
                    faces=mesh.faces,
                    process=False
                )
                stl_mesh.export(self.file_manager.stl_path)
                            
                # Verify STL file was created
                if Path(self.file_manager.stl_path).exists():
                    print(f"✅ STL saved (for printing): {self.file_manager.stl_path}")
                else:
                    print(f"⚠️ STL file creation failed")
                    
            except Exception as stl_error:
                print(f"⚠️ STL export warning: {stl_error}")
            
        except Exception as e:
            print(f"❌ Error creating mesh: {e}")
    
    def convert(self) -> None:
        """Main conversion process"""
        print("🔄 Universal 2D to 3D Converter")
        print("=" * 50)
        
        # Check input
        if not self.file_manager.input_path.exists():
            print(f"❌ Input file not found: {self.file_manager.input_path}")
            return
        
        # Step 1: Remove background
        if not Path(self.file_manager.png_path).exists():
            self.remove_background()
        else:
            print(f"✅ PNG exists: {self.file_manager.png_path}")
        
        # Step 2: Analyze and configure
        self.analyze_and_configure()
        
        # Step 3: Create colored CSV
        self.create_colored_csv()
        
        # Step 4: Create 3D mesh
        self.create_3d_mesh()
        
        print("\n🎉 Conversion completed successfully!")
        print("💡 Tips:")
        print(f"   • Open PLY file in Blender/MeshLab for viewing with colors")
        print(f"   • Use STL file for 3D printing")
        print(f"   • Check debug images in: {self.file_manager.debug_dir}")

# =============================================================
#                    Easy Usage Functions
# =============================================================

def convert_image_to_3d(input_path: str, object_type: str = "auto") -> str:
    """Easy function to convert any image to 3D model"""
    converter = Universal3DConverter(input_path, object_type)
    converter.convert()
    return converter.file_manager.ply_path

def batch_convert(input_directory: str, object_type: str = "auto") -> None:
    """Convert multiple images in a directory"""
    input_dir = Path(input_directory)
    
    if not input_dir.exists():
        print(f"❌ Directory not found: {input_directory}")
        return
    
    # Supported image formats
    formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    images = []
    
    for fmt in formats:
        images.extend(input_dir.glob(f"*{fmt}"))
        images.extend(input_dir.glob(f"*{fmt.upper()}"))
    
    if not images:
        print(f"❌ No images found in: {input_directory}")
        return
    
    print(f"🔄 Found {len(images)} images to convert")
    
    for i, image_path in enumerate(images, 1):
        print(f"\n📸 Processing {i}/{len(images)}: {image_path.name}")
        try:
            convert_image_to_3d(str(image_path), object_type)
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")
    
    print(f"\n🎉 Batch conversion completed!")

# =============================================================
#                    Main Execution
# =============================================================

if __name__ == "__main__":
    # Example usage
    input_image = r"C:\Users\Student6\Desktop\Depthify\picture\before\buba.jpg"  # Change this to your image path
    
    # Convert single image (auto-detect object type)
    convert_image_to_3d(input_image, "auto")
    
    # Or specify object type for better results:
    # convert_image_to_3d(input_image, "fruit")     # For fruits
    # convert_image_to_3d(input_image, "geometric") # For geometric objects
    # convert_image_to_3d(input_image, "organic")   # For organic shapes
    # convert_image_to_3d(input_image, "flat")      # For flat objects
    
    # Batch convert directory:
    # batch_convert("input_images/", "auto")