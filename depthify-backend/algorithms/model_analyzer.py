# 3D Model Analysis and Viewer Tool - Enhanced
# ===============================================
# Analyzes, visualizes and optimizes 3D models with color support
# ===============================================

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import trimesh
from pathlib import Path
import cv2
from PIL import Image
import json
from typing import Dict, List, Optional, Tuple

class ModelAnalyzer:
    """Comprehensive 3D model analysis"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.base_name = self.model_path.stem.replace('_model', '').replace('_depth', '')
        self.model_dir = self.model_path.parent
        self.csv_path = self.model_dir / f"{self.base_name}_depth.csv"
        self.debug_dir = self.model_dir.parent / "debug"
        self.analysis_dir = self.model_dir.parent / "analysis"
        
        # Create analysis directory
        self.analysis_dir.mkdir(exist_ok=True)
    
    def load_data(self) -> Optional[pd.DataFrame]:
        """Load CSV data if available"""
        if self.csv_path.exists():
            return pd.read_csv(self.csv_path)
        else:
            print(f"⚠️ CSV file not found: {self.csv_path}")
            return None
    
    def analyze_depth_quality(self) -> Optional[Dict]:
        """Analyze depth map quality"""
        print("🔍 Analyzing depth quality...")
        
        df = self.load_data()
        if df is None:
            return None
        
        # Basic statistics
        z_stats = {
            'count': len(df),
            'min': df['z'].min(),
            'max': df['z'].max(),
            'mean': df['z'].mean(),
            'std': df['z'].std(),
            'range': df['z'].max() - df['z'].min(),
            'median': df['z'].median(),
            'q25': df['z'].quantile(0.25),
            'q75': df['z'].quantile(0.75)
        }
        
        # Advanced metrics
        z_stats['coefficient_of_variation'] = z_stats['std'] / z_stats['mean'] if z_stats['mean'] > 0 else 0
        z_stats['depth_distribution_score'] = self._calculate_distribution_score(df['z'].values)
        
        print(f"📊 Depth Statistics:")
        for key, value in z_stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.4f}")
            else:
                print(f"   {key}: {value}")
        
        return z_stats
    
    def _calculate_distribution_score(self, values: np.ndarray) -> float:
        """Calculate how well distributed the depth values are"""
        hist, _ = np.histogram(values, bins=20)
        # Better distribution = more uniform histogram
        return 1.0 - (np.std(hist) / np.mean(hist)) if np.mean(hist) > 0 else 0
    
    def analyze_color_quality(self) -> Optional[Dict]:
        """Analyze color preservation and quality"""
        print("🎨 Analyzing color quality...")
        
        df = self.load_data()
        if df is None or not all(col in df.columns for col in ['r', 'g', 'b']):
            print("⚠️ Color data not available")
            return None
        
        colors_rgb = df[['r', 'g', 'b']].values
        
        color_stats = {
            'total_colors': len(np.unique(colors_rgb.view(np.void), axis=0)),
            'brightness_mean': np.mean(colors_rgb.sum(axis=1) / 3),
            'brightness_std': np.std(colors_rgb.sum(axis=1) / 3),
            'color_range_r': colors_rgb[:, 0].max() - colors_rgb[:, 0].min(),
            'color_range_g': colors_rgb[:, 1].max() - colors_rgb[:, 1].min(),
            'color_range_b': colors_rgb[:, 2].max() - colors_rgb[:, 2].min(),
            'color_variance': np.var(colors_rgb, axis=0).mean(),
            'dominant_color': tuple(np.median(colors_rgb, axis=0).astype(int))
        }
        
        print(f"🎨 Color Statistics:")
        for key, value in color_stats.items():
            print(f"   {key}: {value}")
        
        return color_stats
    
    def visualize_depth_analysis(self) -> None:
        """Create comprehensive depth visualization"""
        print("📊 Creating depth analysis visualization...")
        
        df = self.load_data()
        if df is None:
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # 1. Depth histogram
        axes[0, 0].hist(df['z'], bins=50, alpha=0.7, color='blue', edgecolor='black')
        axes[0, 0].set_title('Depth Distribution')
        axes[0, 0].set_xlabel('Z Value')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Top-down depth map
        scatter = axes[0, 1].scatter(df['x'], df['y'], c=df['z'], cmap='hot', s=0.5, alpha=0.8)
        axes[0, 1].set_title('Depth Map - Top View')
        axes[0, 1].set_aspect('equal')
        plt.colorbar(scatter, ax=axes[0, 1], label='Depth')
        
        # 3. Depth profile (center slice)
        center_y = df['y'].mean()
        center_slice = df[abs(df['y'] - center_y) < 10].copy()
        center_slice = center_slice.sort_values('x')
        if len(center_slice) > 0:
            axes[0, 2].plot(center_slice['x'], center_slice['z'], 'b-', linewidth=2)
            axes[0, 2].fill_between(center_slice['x'], center_slice['z'], alpha=0.3)
        axes[0, 2].set_title('Depth Profile (Center Slice)')
        axes[0, 2].set_xlabel('X Position')
        axes[0, 2].set_ylabel('Z Depth')
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. Depth gradient magnitude
        if len(df) > 100:
            # Create gradient map
            x_unique = sorted(df['x'].unique())
            y_unique = sorted(df['y'].unique())
            
            if len(x_unique) > 10 and len(y_unique) > 10:
                # Sample for gradient calculation
                sample_df = df.sample(n=min(5000, len(df)))
                gradient_mag = np.sqrt(
                    np.gradient(sample_df['z'])**2
                )
                axes[1, 0].scatter(sample_df['x'], sample_df['y'], c=gradient_mag, 
                                 cmap='plasma', s=0.5, alpha=0.8)
                axes[1, 0].set_title('Depth Gradient Magnitude')
                axes[1, 0].set_aspect('equal')
        
        # 5. 3D wireframe sample
        if len(df) > 1000:
            sample_3d = df.sample(n=1000, random_state=42)
        else:
            sample_3d = df
        
        ax_3d = axes[1, 1]
        ax_3d.remove()
        ax_3d = fig.add_subplot(2, 3, 5, projection='3d')
        
        ax_3d.scatter(sample_3d['x'], sample_3d['y'], sample_3d['z'] * 60, 
                     c=sample_3d['z'], cmap='viridis', s=1, alpha=0.6)
        ax_3d.set_title('3D Sample View')
        ax_3d.set_xlabel('X')
        ax_3d.set_ylabel('Y')
        ax_3d.set_zlabel('Z')
        
        # 6. Quality metrics
        z_stats = self.analyze_depth_quality()
        if z_stats:
            axes[1, 2].axis('off')
            metrics_text = f"""Quality Metrics:
            
Points: {z_stats['count']:,}
Range: {z_stats['range']:.3f}
Mean: {z_stats['mean']:.3f}
Std: {z_stats['std']:.3f}
CV: {z_stats['coefficient_of_variation']:.3f}
Distribution Score: {z_stats['depth_distribution_score']:.3f}
            """
            axes[1, 2].text(0.1, 0.9, metrics_text, transform=axes[1, 2].transAxes, 
                           verticalalignment='top', fontfamily='monospace', fontsize=10,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        
        plt.tight_layout()
        
        # Save visualization
        save_path = self.analysis_dir / f"{self.base_name}_depth_analysis.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ Depth analysis saved: {save_path}")
    
    def visualize_3d_model_enhanced(self, show_colors: bool = True, view_angles: List[Tuple] = None) -> None:
        """Enhanced 3D model visualization with multiple views"""
        print("🎨 Creating enhanced 3D visualization...")
        
        df = self.load_data()
        if df is None:
            return
        
        # Default view angles
        if view_angles is None:
            view_angles = [(30, 45), (0, 0), (90, 0), (30, 135)]
        
        # Sample data for performance
        if len(df) > 15000:
            df_sample = df.sample(n=15000, random_state=42)
            print(f"💡 Displaying sample of {len(df_sample)} points from {len(df)} total")
        else:
            df_sample = df
        
        fig = plt.figure(figsize=(20, 15))
        
        # Check if colors are available
        has_colors = all(col in df_sample.columns for col in ['r', 'g', 'b'])
        
        for i, (elev, azim) in enumerate(view_angles):
            ax = fig.add_subplot(2, 2, i+1, projection='3d')
            
            if show_colors and has_colors:
                colors = df_sample[['r', 'g', 'b']].values / 255.0
                ax.scatter(df_sample['x'], df_sample['y'], df_sample['z'] * 60, 
                          c=colors, s=0.8, alpha=0.7, edgecolors='none')
                title_suffix = " (Original Colors)"
            else:
                scatter = ax.scatter(df_sample['x'], df_sample['y'], df_sample['z'] * 60,
                                   c=df_sample['z'], cmap='viridis', s=0.8, alpha=0.8, edgecolors='none')
                if i == 0:  # Add colorbar only to first plot
                    plt.colorbar(scatter, ax=ax, label='Depth', shrink=0.8)
                title_suffix = " (Depth Colors)"
            
            ax.view_init(elev=elev, azim=azim)
            
            # Set titles based on view
            view_names = ["Perspective View", "Side View", "Top View", "Rear View"]
            ax.set_title(f'{view_names[i]}{title_suffix}')
            
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            
            # Set equal aspect ratio
            ax.set_box_aspect([1,1,0.5])
        
        plt.tight_layout()
        
        # Save visualization
        color_suffix = "_colored" if (show_colors and has_colors) else "_depth"
        save_path = self.analysis_dir / f"{self.base_name}_3d_views{color_suffix}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ 3D visualization saved: {save_path}")
    
    def visualize_color_analysis(self) -> None:
        """Analyze and visualize color distribution"""
        print("🌈 Creating color analysis...")
        
        df = self.load_data()
        if df is None or not all(col in df.columns for col in ['r', 'g', 'b']):
            print("⚠️ Color data not available for analysis")
            return
        
        colors_rgb = df[['r', 'g', 'b']].values
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # 1. RGB histograms
        colors = ['red', 'green', 'blue']
        channels = ['r', 'g', 'b']
        
        for i, (channel, color) in enumerate(zip(channels, colors)):
            axes[0, i].hist(df[channel], bins=50, alpha=0.7, color=color, edgecolor='black')
            axes[0, i].set_title(f'{channel.upper()} Channel Distribution')
            axes[0, i].set_xlabel('Value')
            axes[0, i].set_ylabel('Frequency')
            axes[0, i].grid(True, alpha=0.3)
        
        # 2. Color space visualization
        axes[1, 0].scatter(df['r'], df['g'], c=df['b'], cmap='cool', s=0.5, alpha=0.6)
        axes[1, 0].set_title('R-G Color Space (B as color)')
        axes[1, 0].set_xlabel('Red')
        axes[1, 0].set_ylabel('Green')
        
        # 3. Brightness distribution
        brightness = (df['r'] + df['g'] + df['b']) / 3
        axes[1, 1].hist(brightness, bins=50, alpha=0.7, color='gray', edgecolor='black')
        axes[1, 1].set_title('Brightness Distribution')
        axes[1, 1].set_xlabel('Brightness')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 4. Color statistics
        color_stats = self.analyze_color_quality()
        if color_stats:
            axes[1, 2].axis('off')
            stats_text = f"""Color Statistics:
            
Unique Colors: {color_stats['total_colors']:,}
Brightness Mean: {color_stats['brightness_mean']:.1f}
Brightness Std: {color_stats['brightness_std']:.1f}
R Range: {color_stats['color_range_r']}
G Range: {color_stats['color_range_g']}
B Range: {color_stats['color_range_b']}
Color Variance: {color_stats['color_variance']:.1f}
Dominant Color: {color_stats['dominant_color']}
            """
            axes[1, 2].text(0.1, 0.9, stats_text, transform=axes[1, 2].transAxes,
                           verticalalignment='top', fontfamily='monospace', fontsize=10,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        
        plt.tight_layout()
        
        # Save visualization
        save_path = self.analysis_dir / f"{self.base_name}_color_analysis.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ Color analysis saved: {save_path}")
    
    def check_mesh_quality(self) -> Optional[Dict]:
        """Comprehensive mesh quality check"""
        print("🔧 Checking mesh quality...")
        
        if not self.model_path.exists():
            print(f"❌ Model file not found: {self.model_path}")
            return None
        
        try:
            mesh = trimesh.load(self.model_path)
            
            quality_report = {
                'file_format': self.model_path.suffix,
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'edges': len(mesh.edges_unique),
                'is_watertight': mesh.is_watertight,
                'is_winding_consistent': mesh.is_winding_consistent,
                'is_valid': mesh.is_valid,
                'volume': mesh.volume if mesh.is_watertight else None,
                'surface_area': mesh.area,
                'bounds_x': mesh.bounds[1, 0] - mesh.bounds[0, 0],
                'bounds_y': mesh.bounds[1, 1] - mesh.bounds[0, 1],
                'bounds_z': mesh.bounds[1, 2] - mesh.bounds[0, 2],
                'center': tuple(mesh.center_mass),
                'has_vertex_colors': hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None
            }
            
            # Additional quality metrics
            if len(mesh.faces) > 0:
                # Face area statistics
                face_areas = mesh.area_faces
                quality_report.update({
                    'face_area_mean': np.mean(face_areas),
                    'face_area_std': np.std(face_areas),
                    'face_area_min': np.min(face_areas),
                    'face_area_max': np.max(face_areas),
                    'degenerate_faces': np.sum(face_areas < 1e-10)
                })
            
            print("📋 Mesh Quality Report:")
            for key, value in quality_report.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.4f}")
                elif isinstance(value, tuple):
                    formatted_tuple = tuple(f"{v:.2f}" if isinstance(v, float) else v for v in value)
                    print(f"   {key}: {formatted_tuple}")
                else:
                    print(f"   {key}: {value}")
            
            return quality_report
            
        except Exception as e:
            print(f"❌ Error loading mesh: {e}")
            return None
    
    def suggest_improvements(self) -> List[str]:
        """Analyze model and suggest improvements"""
        print("💡 Analyzing model and suggesting improvements...")
        
        suggestions = []
        
        # Analyze depth quality
        z_stats = self.analyze_depth_quality()
        if z_stats:
            if z_stats['range'] < 0.2:
                suggestions.append("🔧 Depth range is low - consider increasing SCALE_Z or DEPTH_BOOST")
            
            if z_stats['std'] < 0.08:
                suggestions.append("🔧 Depth variation is low - adjust depth function weights for more variation")
            
            if z_stats['coefficient_of_variation'] < 0.3:
                suggestions.append("🔧 Depth distribution is too uniform - try different object type settings")
            
            if z_stats['depth_distribution_score'] < 0.5:
                suggestions.append("🔧 Depth distribution is uneven - consider smoothing parameters")
        
        # Analyze color quality
        color_stats = self.analyze_color_quality()
        if color_stats:
            if color_stats['color_variance'] < 500:
                suggestions.append("🎨 Color variation is low - original image might benefit from enhancement")
            
            if color_stats['total_colors'] < 1000:
                suggestions.append("🎨 Limited color palette - consider higher resolution input")
        
        # Analyze mesh quality
        mesh_quality = self.check_mesh_quality()
        if mesh_quality:
            if not mesh_quality['is_watertight']:
                suggestions.append("🔧 Mesh is not watertight - may cause 3D printing issues")
            
            if mesh_quality['faces'] > 100000:
                suggestions.append("📉 Mesh is very dense - consider decimation for better performance")
            
            if mesh_quality['faces'] < 500:
                suggestions.append("📈 Mesh is too sparse - increase resolution or reduce filtering")
            
            if mesh_quality.get('degenerate_faces', 0) > 0:
                suggestions.append("🔧 Mesh has degenerate faces - consider mesh repair")
        
        if suggestions:
            print("\n🎯 Improvement Suggestions:")
            for suggestion in suggestions:
                print(f"   {suggestion}")
        else:
            print("✅ Model looks good! No major improvements needed.")
        
        return suggestions
    
    def export_analysis_report(self) -> None:
        """Export comprehensive analysis report"""
        print("📄 Generating comprehensive analysis report...")
        
        report = {
            'model_info': {
                'name': self.base_name,
                'model_path': str(self.model_path),
                'csv_path': str(self.csv_path) if self.csv_path.exists() else None
            },
            'depth_analysis': self.analyze_depth_quality(),
            'color_analysis': self.analyze_color_quality(),
            'mesh_quality': self.check_mesh_quality(),
            'suggestions': self.suggest_improvements()
        }
        
        # Save JSON report
        report_path = self.analysis_dir / f"{self.base_name}_analysis_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Create markdown report
        md_path = self.analysis_dir / f"{self.base_name}_analysis_report.md"
        self._create_markdown_report(report, md_path)
        
        print(f"✅ Analysis report saved:")
        print(f"   📄 JSON: {report_path}")
        print(f"   📝 Markdown: {md_path}")
    
    def _create_markdown_report(self, report: Dict, md_path: Path) -> None:
        """Create readable markdown report"""
        with open(md_path, 'w') as f:
            f.write(f"# 3D Model Analysis Report\n\n")
            f.write(f"**Model:** {report['model_info']['name']}\n\n")
            
            # Depth Analysis
            if report['depth_analysis']:
                f.write("## Depth Analysis\n\n")
                depth = report['depth_analysis']
                f.write(f"- **Points:** {depth['count']:,}\n")
                f.write(f"- **Depth Range:** {depth['range']:.4f}\n")
                f.write(f"- **Mean Depth:** {depth['mean']:.4f}\n")
                f.write(f"- **Standard Deviation:** {depth['std']:.4f}\n")
                f.write(f"- **Distribution Score:** {depth['depth_distribution_score']:.4f}\n\n")
            
            # Color Analysis
            if report['color_analysis']:
                f.write("## Color Analysis\n\n")
                color = report['color_analysis']
                f.write(f"- **Unique Colors:** {color['total_colors']:,}\n")
                f.write(f"- **Average Brightness:** {color['brightness_mean']:.1f}\n")
                f.write(f"- **Color Variance:** {color['color_variance']:.1f}\n")
                f.write(f"- **Dominant Color:** RGB{color['dominant_color']}\n\n")
            
            # Mesh Quality
            if report['mesh_quality']:
                f.write("## Mesh Quality\n\n")
                mesh = report['mesh_quality']
                f.write(f"- **Vertices:** {mesh['vertices']:,}\n")
                f.write(f"- **Faces:** {mesh['faces']:,}\n")
                f.write(f"- **Watertight:** {'✅' if mesh['is_watertight'] else '❌'}\n")
                f.write(f"- **Valid:** {'✅' if mesh['is_valid'] else '❌'}\n")
                f.write(f"- **Has Colors:** {'✅' if mesh['has_vertex_colors'] else '❌'}\n\n")
            
            # Suggestions
            if report['suggestions']:
                f.write("## Improvement Suggestions\n\n")
                for suggestion in report['suggestions']:
                    f.write(f"- {suggestion}\n")
                f.write("\n")

# =============================================================
#                    Easy Usage Functions
# =============================================================

def analyze_model(model_path: str, full_analysis: bool = True) -> ModelAnalyzer:
    """Quick analysis of a 3D model"""
    analyzer = ModelAnalyzer(model_path)
    
    if full_analysis:
        analyzer.visualize_depth_analysis()
        analyzer.visualize_3d_model_enhanced(show_colors=True)
        analyzer.visualize_color_analysis()
        analyzer.suggest_improvements()
        analyzer.export_analysis_report()
    else:
        analyzer.check_mesh_quality()
        analyzer.suggest_improvements()
    
    return analyzer

def batch_analyze_models(models_directory: str) -> None:
    """Analyze multiple models in a directory"""
    models_dir = Path(models_directory)
    
    if not models_dir.exists():
        print(f"❌ Directory not found: {models_directory}")
        return
    
    # Find model files
    model_files = []
    for ext in ['.ply', '.stl', '.obj']:
        model_files.extend(models_dir.glob(f"*{ext}"))
    
    if not model_files:
        print(f"❌ No 3D model files found in: {models_directory}")
        return
    
    print(f"🔄 Found {len(model_files)} models to analyze")
    
    for i, model_path in enumerate(model_files, 1):
        print(f"\n📊 Analyzing {i}/{len(model_files)}: {model_path.name}")
        try:
            analyze_model(str(model_path), full_analysis=False)
        except Exception as e:
            print(f"❌ Error analyzing {model_path.name}: {e}")
    
    print(f"\n🎉 Batch analysis completed!")

def create_model_comparison(model_paths: List[str]) -> None:
    """Compare multiple models side by side"""
    print("🔄 Creating model comparison...")
    
    analyzers = []
    for path in model_paths:
        try:
            analyzer = ModelAnalyzer(path)
            analyzers.append(analyzer)
        except Exception as e:
            print(f"❌ Error loading {path}: {e}")
    
    if len(analyzers) < 2:
        print("❌ Need at least 2 valid models for comparison")
        return
    
    # Create comparison visualization
    fig, axes = plt.subplots(2, len(analyzers), figsize=(6*len(analyzers), 12))
    if len(analyzers) == 1:
        axes = axes.reshape(-1, 1)
    
    for i, analyzer in enumerate(analyzers):
        df = analyzer.load_data()
        if df is None:
            continue
        
        # Sample for visualization
        if len(df) > 5000:
            df_sample = df.sample(n=5000, random_state=42)
        else:
            df_sample = df
        
        # Top view
        axes[0, i].scatter(df_sample['x'], df_sample['y'], c=df_sample['z'], 
                          cmap='hot', s=0.5, alpha=0.8)
        axes[0, i].set_title(f'{analyzer.base_name} - Top View')
        axes[0, i].set_aspect('equal')
        
        # 3D view
        axes[1, i].remove()
        ax_3d = fig.add_subplot(2, len(analyzers), len(analyzers) + i + 1, projection='3d')
        
        has_colors = all(col in df_sample.columns for col in ['r', 'g', 'b'])
        if has_colors:
            colors = df_sample[['r', 'g', 'b']].values / 255.0
            ax_3d.scatter(df_sample['x'], df_sample['y'], df_sample['z'] * 60,
                         c=colors, s=0.8, alpha=0.7)
        else:
            ax_3d.scatter(df_sample['x'], df_sample['y'], df_sample['z'] * 60,
                         c=df_sample['z'], cmap='viridis', s=0.8, alpha=0.8)
        
        ax_3d.set_title(f'{analyzer.base_name} - 3D View')
        ax_3d.set_xlabel('X')
        ax_3d.set_ylabel('Y')
        ax_3d.set_zlabel('Z')
    
    plt.tight_layout()
    
    # Save comparison
    comparison_path = Path("output/analysis/model_comparison.png")
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(comparison_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✅ Model comparison saved: {comparison_path}")

# =============================================================
#                    Main Execution
# =============================================================

if __name__ == "__main__":
    # Example usage
    model_path = r"C:\Users\Student6\Desktop\Depthify\picture\after\models\nani_model.ply"
    
    # Analyze single model
    analyzer = analyze_model(model_path, full_analysis=True)
    
    # Batch analyze all models in directory
    # batch_analyze_models("output/models/")
    
    # Compare multiple models
    # model_list = ["output/models/apple_model.ply", "output/models/orange_model.ply"]
    # create_model_comparison(model_list)