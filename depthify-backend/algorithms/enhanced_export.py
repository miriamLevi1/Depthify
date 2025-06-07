# Enhanced 3D Export System - Multiple Formats with Colors
# ========================================================
# Export 3D models in multiple formats for better compatibility
# ========================================================

import trimesh
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
import json

class Enhanced3DExporter:
    """Enhanced exporter supporting multiple 3D formats with colors"""
    
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.export_dir = self.file_manager.models_dir / "exports"
        self.export_dir.mkdir(exist_ok=True)
        
    def create_enhanced_mesh(self) -> Tuple[trimesh.Trimesh, pd.DataFrame]:
        """Create mesh with improved triangulation"""
        print("🏗️ Creating enhanced mesh with better triangulation...")
        
        df = pd.read_csv(self.file_manager.csv_path)
        
        # Enhanced outlier removal
        df = self._remove_outliers_advanced(df)
        
        # Sort points for better triangulation
        df = df.sort_values(['y', 'x']).reset_index(drop=True)
        
        # Vertices with enhanced colors
        vertices = df[['x', 'y', 'z']].values.astype(np.float32)
        colors = df[['r', 'g', 'b']].values.astype(np.uint8)
        
        # Scale Z dimension with the config
        vertices[:, 2] *= 60  # Using the scale_z from config
        
        # Enhanced triangulation with boundary detection
        faces = self._create_enhanced_triangulation(vertices[:, :2])
        
        if faces is None or len(faces) == 0:
            print("❌ Triangulation failed!")
            return None, df
        
        # Create mesh with colors
        mesh = trimesh.Trimesh(
            vertices=vertices,
            faces=faces,
            vertex_colors=colors,
            process=False  # Don't auto-process to preserve our data
        )
        
        # Apply gentle smoothing
        mesh = mesh.smoothed()
        
        print(f"✅ Enhanced mesh created: {len(vertices)} vertices, {len(faces)} faces")
        return mesh, df
    
    def _remove_outliers_advanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced outlier removal"""
        original_count = len(df)
        
        # Remove points with extreme Z values (top/bottom 1%)
        z_lower = df['z'].quantile(0.01)
        z_upper = df['z'].quantile(0.99)
        df = df[(df['z'] >= z_lower) & (df['z'] <= z_upper)]
        
        # Remove isolated points (points far from others)
        from scipy.spatial import cKDTree
        
        if len(df) > 1000:
            # Sample for distance calculation
            sample_df = df.sample(n=min(5000, len(df)), random_state=42)
            tree = cKDTree(sample_df[['x', 'y']].values)
            
            # Find distances to nearest neighbors
            distances, _ = tree.query(df[['x', 'y']].values, k=min(10, len(sample_df)))
            mean_distances = np.mean(distances, axis=1)
            
            # Remove points with very high mean distance to neighbors
            distance_threshold = np.percentile(mean_distances, 95)
            df = df[mean_distances <= distance_threshold]
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            print(f"🧹 Removed {removed_count} outlier points ({removed_count/original_count*100:.1f}%)")
        
        return df.reset_index(drop=True)
    
    def _create_enhanced_triangulation(self, points_2d: np.ndarray) -> Optional[np.ndarray]:
        """Enhanced triangulation with boundary detection"""
        try:
            from scipy.spatial import Delaunay
            from scipy.spatial.distance import cdist
            
            # Create Delaunay triangulation
            tri = Delaunay(points_2d)
            faces = tri.simplices
            
            # Filter out bad triangles
            good_faces = []
            
            for face in faces:
                # Get triangle vertices
                triangle_points = points_2d[face]
                
                # Calculate triangle area
                area = self._triangle_area(triangle_points)
                
                # Calculate edge lengths
                edge_lengths = [
                    np.linalg.norm(triangle_points[1] - triangle_points[0]),
                    np.linalg.norm(triangle_points[2] - triangle_points[1]),
                    np.linalg.norm(triangle_points[0] - triangle_points[2])
                ]
                
                # Filter criteria
                max_edge_length = np.max(edge_lengths)
                min_edge_length = np.min(edge_lengths)
                aspect_ratio = max_edge_length / min_edge_length if min_edge_length > 0 else float('inf')
                
                # Keep triangle if it meets quality criteria
                if (area > 1.0 and  # Minimum area
                    max_edge_length < 50 and  # Maximum edge length
                    aspect_ratio < 10):  # Aspect ratio limit
                    good_faces.append(face)
            
            if len(good_faces) == 0:
                print("⚠️ No good triangles found after filtering")
                return tri.simplices  # Return original if filtering removes everything
            
            filtered_faces = np.array(good_faces)
            print(f"🔧 Filtered triangles: {len(faces)} → {len(filtered_faces)} ({len(filtered_faces)/len(faces)*100:.1f}% kept)")
            
            return filtered_faces
            
        except Exception as e:
            print(f"❌ Triangulation error: {e}")
            return None
    
    def _triangle_area(self, points: np.ndarray) -> float:
        """Calculate triangle area using cross product"""
        if len(points) != 3:
            return 0
        
        v1 = points[1] - points[0]
        v2 = points[2] - points[0]
        
        # Cross product magnitude / 2 = triangle area
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        return abs(cross) / 2.0
    
    def export_obj_with_materials(self, mesh: trimesh.Trimesh) -> str:
        """Export OBJ with MTL material file for colors"""
        print("📁 Exporting OBJ with materials...")
        
        obj_path = self.export_dir / f"{self.file_manager.base_name}_colored.obj"
        mtl_path = self.export_dir / f"{self.file_manager.base_name}_colored.mtl"
        
        # Export OBJ
        with open(obj_path, 'w') as f:
            f.write(f"# OBJ file with colors\n")
            f.write(f"mtllib {mtl_path.name}\n")
            f.write(f"usemtl material_colored\n\n")
            
            # Write vertices with colors
            colors = mesh.visual.vertex_colors[:, :3] / 255.0  # Normalize to 0-1
            
            for i, (vertex, color) in enumerate(zip(mesh.vertices, colors)):
                f.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f} {color[0]:.6f} {color[1]:.6f} {color[2]:.6f}\n")
            
            f.write("\n")
            
            # Write faces
            for face in mesh.faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
        
        # Create MTL file
        with open(mtl_path, 'w') as f:
            f.write("# MTL file for colored object\n")
            f.write("newmtl material_colored\n")
            f.write("Ka 0.2 0.2 0.2\n")  # Ambient
            f.write("Kd 0.8 0.8 0.8\n")  # Diffuse
            f.write("Ks 0.1 0.1 0.1\n")  # Specular
            f.write("Ns 10.0\n")  # Shininess
        
        print(f"✅ OBJ exported: {obj_path}")
        return str(obj_path)
    
    def export_x3d_web_format(self, mesh: trimesh.Trimesh) -> str:
        """Export X3D format for web viewing"""
        print("🌐 Exporting X3D for web viewing...")
        
        x3d_path = self.export_dir / f"{self.file_manager.base_name}_web.x3d"
        
        with open(x3d_path, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<X3D profile="Immersive" version="3.3">\n')
            f.write('<Scene>\n')
            f.write('<Shape>\n')
            
            # Write geometry
            f.write('<IndexedFaceSet coordIndex="')
            for face in mesh.faces:
                f.write(f"{face[0]} {face[1]} {face[2]} -1 ")
            f.write('" colorPerVertex="true">\n')
            
            # Write coordinates
            f.write('<Coordinate point="')
            for vertex in mesh.vertices:
                f.write(f"{vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f} ")
            f.write('"/>\n')
            
            # Write colors
            f.write('<Color color="')
            colors = mesh.visual.vertex_colors[:, :3] / 255.0
            for color in colors:
                f.write(f"{color[0]:.6f} {color[1]:.6f} {color[2]:.6f} ")
            f.write('"/>\n')
            
            f.write('</IndexedFaceSet>\n')
            f.write('</Shape>\n')
            f.write('</Scene>\n')
            f.write('</X3D>\n')
        
        print(f"✅ X3D exported: {x3d_path}")
        return str(x3d_path)
    
    def export_glb_for_modern_viewers(self, mesh: trimesh.Trimesh) -> str:
        """Export GLB format for modern 3D viewers"""
        print("✨ Exporting GLB for modern viewers...")
        
        glb_path = self.export_dir / f"{self.file_manager.base_name}_modern.glb"
        
        try:
            # GLB export with colors
            mesh.export(str(glb_path))
            print(f"✅ GLB exported: {glb_path}")
            return str(glb_path)
        except Exception as e:
            print(f"⚠️ GLB export failed: {e}")
            return ""
    
    def create_html_viewer(self, glb_path: str = None) -> str:
        """Create HTML viewer with Three.js"""
        print("🌐 Creating HTML viewer...")
        
        html_path = self.export_dir / f"{self.file_manager.base_name}_viewer.html"
        
        glb_filename = Path(glb_path).name if glb_path else f"{self.file_manager.base_name}_modern.glb"
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Model Viewer - {self.file_manager.base_name}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: Arial, sans-serif;
            overflow: hidden;
        }}
        #container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 10px;
            z-index: 100;
        }}
        #controls {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 10px;
            z-index: 100;
        }}
        .control-button {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
        }}
        .control-button:hover {{
            background: #45a049;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="info">
            <h3>🎯 {self.file_manager.base_name.title()}</h3>
            <p>📱 Mouse: Rotate | Wheel: Zoom | Right: Pan</p>
            <p>📊 Model created with Depthify</p>
        </div>
        
        <div id="controls">
            <button class="control-button" onclick="resetView()">🔄 Reset View</button>
            <button class="control-button" onclick="toggleWireframe()">🔳 Wireframe</button>
            <button class="control-button" onclick="toggleAutoRotate()">🔄 Auto Rotate</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/controls/OrbitControls.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/loaders/GLTFLoader.js"></script>
    
    <script>
        let scene, camera, renderer, controls, model;
        let wireframeMode = false;
        let autoRotate = false;

        function init() {{
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf0f0f0);

            // Camera
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 0, 100);

            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('container').appendChild(renderer.domElement);

            // Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // Lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 10, 5);
            directionalLight.castShadow = true;
            scene.add(directionalLight);

            // Load model
            const loader = new THREE.GLTFLoader();
            loader.load('{glb_filename}', function(gltf) {{
                model = gltf.scene;
                
                // Center the model
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                model.position.sub(center);
                
                // Scale if needed
                const size = box.getSize(new THREE.Vector3());
                const maxSize = Math.max(size.x, size.y, size.z);
                if (maxSize > 50) {{
                    const scale = 50 / maxSize;
                    model.scale.setScalar(scale);
                }}
                
                scene.add(model);
                
                // Adjust camera
                controls.target.copy(center);
                controls.update();
            }}, undefined, function(error) {{
                console.error('Error loading model:', error);
                document.getElementById('info').innerHTML = '<h3>❌ Error loading model</h3><p>Make sure the GLB file is in the same folder</p>';
            }});

            animate();
        }}

        function animate() {{
            requestAnimationFrame(animate);
            
            if (autoRotate && model) {{
                model.rotation.y += 0.01;
            }}
            
            controls.update();
            renderer.render(scene, camera);
        }}

        function resetView() {{
            if (model) {{
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                
                const maxSize = Math.max(size.x, size.y, size.z);
                const distance = maxSize * 2;
                
                camera.position.set(distance, distance * 0.5, distance);
                controls.target.copy(center);
                controls.update();
            }}
        }}

        function toggleWireframe() {{
            if (model) {{
                wireframeMode = !wireframeMode;
                model.traverse(function(child) {{
                    if (child.isMesh) {{
                        child.material.wireframe = wireframeMode;
                    }}
                }});
            }}
        }}

        function toggleAutoRotate() {{
            autoRotate = !autoRotate;
        }}

        // Handle window resize
        window.addEventListener('resize', function() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        // Initialize
        init();
    </script>
</body>
</html>'''
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML viewer created: {html_path}")
        return str(html_path)
    
    def export_all_formats(self) -> dict:
        """Export model in all supported formats"""
        print("🚀 Exporting in multiple formats for maximum compatibility...")
        
        # Create enhanced mesh
        mesh, df = self.create_enhanced_mesh()
        if mesh is None:
            return {"error": "Failed to create mesh"}
        
        exported_files = {}
        
        # 1. Enhanced PLY (original)
        try:
            mesh.export(self.file_manager.ply_path)
            exported_files['ply'] = self.file_manager.ply_path
            print(f"✅ PLY (enhanced): {self.file_manager.ply_path}")
        except Exception as e:
            print(f"⚠️ PLY export failed: {e}")
        
        # 2. OBJ with materials
        try:
            obj_path = self.export_obj_with_materials(mesh)
            exported_files['obj'] = obj_path
        except Exception as e:
            print(f"⚠️ OBJ export failed: {e}")
        
        # 3. GLB for modern viewers
        try:
            glb_path = self.export_glb_for_modern_viewers(mesh)
            if glb_path:
                exported_files['glb'] = glb_path
        except Exception as e:
            print(f"⚠️ GLB export failed: {e}")
        
        # 4. X3D for web
        try:
            x3d_path = self.export_x3d_web_format(mesh)
            exported_files['x3d'] = x3d_path
        except Exception as e:
            print(f"⚠️ X3D export failed: {e}")
        
        # 5. STL for printing (no colors)
        try:
            stl_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False)
            stl_mesh.export(self.file_manager.stl_path)
            exported_files['stl'] = self.file_manager.stl_path
            print(f"✅ STL (printing): {self.file_manager.stl_path}")
        except Exception as e:
            print(f"⚠️ STL export failed: {e}")
        
        # 6. HTML Viewer
        try:
            if 'glb' in exported_files:
                html_path = self.create_html_viewer(exported_files['glb'])
                exported_files['html_viewer'] = html_path
        except Exception as e:
            print(f"⚠️ HTML viewer creation failed: {e}")
        
        # Create summary
        self._create_export_summary(exported_files)
        
        return exported_files
    
    def _create_export_summary(self, exported_files: dict) -> None:
        """Create summary of exported files"""
        summary_path = self.export_dir / f"{self.file_manager.base_name}_export_summary.txt"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"📁 3D Model Export Summary - {self.file_manager.base_name}\n")
            f.write("=" * 60 + "\n\n")
            
            if exported_files:
                f.write("✅ Successfully exported formats:\n\n")
                
                format_descriptions = {
                    'ply': '🎨 PLY - Best for Blender/MeshLab (with colors)',
                    'obj': '🎭 OBJ - Universal format (with materials)',
                    'glb': '✨ GLB - Modern web/AR viewers (best quality)',
                    'x3d': '🌐 X3D - Web browsers with plugin',
                    'stl': '🖨️ STL - 3D printing (no colors)',
                    'html_viewer': '👀 HTML - Interactive web viewer'
                }
                
                for fmt, path in exported_files.items():
                    if fmt in format_descriptions:
                        f.write(f"{format_descriptions[fmt]}\n")
                        f.write(f"   📂 {path}\n\n")
                
                f.write("\n🎯 Recommended viewers:\n")
                f.write("• Colors: Open HTML viewer or GLB in modern browsers\n")
                f.write("• Professional: PLY in Blender/MeshLab\n")
                f.write("• Quick view: OBJ in many applications\n")
                f.write("• 3D Printing: STL file\n")
            else:
                f.write("❌ No files exported successfully\n")
        
        print(f"📋 Export summary: {summary_path}")


# Integration function to add to the main converter
def integrate_enhanced_export(converter_class):
    """Add enhanced export to existing converter"""
    
    def create_enhanced_3d_mesh(self) -> None:
        """Enhanced version that exports multiple formats"""
        print("🏗️ Building enhanced 3D mesh with multiple formats...")
        
        # Create enhanced exporter
        exporter = Enhanced3DExporter(self.file_manager)
        
        # Export in all formats
        exported_files = exporter.export_all_formats()
        
        if exported_files and 'error' not in exported_files:
            print("\n🎉 Multi-format export completed!")
            print("💡 To see colors:")
            
            if 'html_viewer' in exported_files:
                print(f"   🌐 Open: {exported_files['html_viewer']}")
            if 'glb' in exported_files:
                print(f"   ✨ Or GLB in modern browser")
            if 'ply' in exported_files:
                print(f"   🎨 Or PLY in Blender/MeshLab")
                
            print(f"\n📁 All files in: {exporter.export_dir}")
        else:
            print("❌ Enhanced export failed - falling back to basic export")
            # Fall back to original method
            super(type(self), self).create_3d_mesh()
    
    # Replace the method
    converter_class.create_3d_mesh = create_enhanced_3d_mesh
    
    return converter_class

# Usage example - how to integrate this with your existing converter:
"""
# In your main converter file, add this line after the class definition:
Universal3DConverter = integrate_enhanced_export(Universal3DConverter)
"""