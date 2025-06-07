from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid
from pathlib import Path

# Import 3D conversion algorithm
from algorithms.universal_converter import Universal3DConverter
from algorithms.model_analyzer import ModelAnalyzer



# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///depthify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MODELS_FOLDER'] = 'models'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db = SQLAlchemy(app)

# Create upload directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MODELS_FOLDER'], exist_ok=True)

# ===============================================================
#                    Database Models
# ===============================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with projects
    projects = db.relationship('Project', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    original_image_path = db.Column(db.String(255), nullable=False)
    result_model_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, completed, failed
    object_type = db.Column(db.String(50), default='auto')
    processing_time = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Model statistics
    vertices_count = db.Column(db.Integer)
    faces_count = db.Column(db.Integer)
    file_size = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'object_type': self.object_type,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
            'vertices_count': self.vertices_count,
            'faces_count': self.faces_count,
            'file_size': self.file_size
        }

# ===============================================================
#                    Helper Functions
# ===============================================================

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Generate unique filename to avoid conflicts"""
    unique_id = str(uuid.uuid4())
    extension = filename.rsplit('.', 1)[1].lower()
    return f"{unique_id}.{extension}"

# ===============================================================
#                    Authentication Routes
# ===============================================================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data['email'],
            password_hash=generate_password_hash(data['password'])
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================================================
#                    File Upload & Processing Routes
# ===============================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get additional form data
        user_id = request.form.get('user_id', 1)  # זמני - בהמשך יבוא מהauthentication
        object_type = request.form.get('object_type', 'auto')
        project_name = request.form.get('project_name', f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Create project record
        project = Project(
            user_id=user_id,
            name=project_name,
            original_image_path=file_path,
            object_type=object_type,
            status='uploaded'
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'project_id': project.id,
            'filename': unique_filename
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/<int:project_id>', methods=['POST'])

def process_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        if project.status != 'uploaded':
            return jsonify({'error': 'Project already processed or in progress'}), 400
        
        # Update status to processing
        project.status = 'processing'
        db.session.commit()
        
        # Here we'll integrate your 3D conversion algorithm
        try:
            import time
            start_time = time.time()
            
            # Use your actual 3D conversion algorithm
            print(f"🚀 Starting 3D conversion for project {project_id}")

            # Initialize your converter
            converter = Universal3DConverter(project.original_image_path, project.object_type)

            # Run the conversion
            converter.convert()

            # The PLY file should be created by the converter
            result_ply_path = converter.file_manager.ply_path
            
             # Calculate processing time
            processing_time = time.time() - start_time
            
            # Analyze the generated model
            analyzer = ModelAnalyzer(result_ply_path)
            mesh_quality = analyzer.check_mesh_quality()
            
            # Update project with real results
            project.status = 'completed'
            project.processing_time = round(processing_time, 2)
            project.vertices_count = mesh_quality.get('vertices', 0) if mesh_quality else 0
            project.faces_count = mesh_quality.get('faces', 0) if mesh_quality else 0
            project.result_model_path = result_ply_path
            
            db.session.commit()
            
            print(f"✅ 3D conversion completed in {processing_time:.2f}s")
            
            return jsonify({
                'message': 'Processing completed successfully',
                'project': project.to_dict()
            }), 200
            
        except Exception as processing_error:
            project.status = 'failed'
            db.session.commit()
            return jsonify({'error': f'Processing failed: {str(processing_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================================================
#                    Project Management Routes
# ===============================================================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        user_id = request.args.get('user_id', 1)  # זמני
        projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
        
        return jsonify({
            'projects': [project.to_dict() for project in projects]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        return jsonify({'project': project.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/download', methods=['GET'])
def download_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        if project.status != 'completed' or not project.result_model_path:
            return jsonify({'error': 'Project not ready for download'}), 400
        
        if os.path.exists(project.result_model_path):
            return send_file(project.result_model_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================================================
#                    Gallery Routes
# ===============================================================

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    try:
        # Get public projects (completed ones)
        projects = Project.query.filter_by(status='completed').order_by(Project.created_at.desc()).limit(20).all()
        
        gallery_items = []
        for project in projects:
            user = User.query.get(project.user_id)
            gallery_items.append({
                **project.to_dict(),
                'creator': f"{user.first_name} {user.last_name}" if user else "Unknown"
            })
        
        return jsonify({'gallery': gallery_items}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================================================
#                    Health Check & Info Routes
# ===============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_users = User.query.count()
        total_projects = Project.query.count()
        completed_projects = Project.query.filter_by(status='completed').count()
        
        return jsonify({
            'total_users': total_users,
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'success_rate': round((completed_projects / total_projects * 100) if total_projects > 0 else 0, 1)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================================================
#                    Database Initialization  
# ===============================================================

def create_tables():
    """Initialize database tables"""
    db.create_all()
    print("✅ Database tables created successfully!")

# ===============================================================
#                    Main Application
# ===============================================================

if __name__ == "__main__":
    # Create database tables
    with app.app_context():
        create_tables()  # ← שינוי כאן
        print("🚀 Depthify Backend Server Starting...")
        print("📊 Database initialized")
        print("🌐 CORS enabled for frontend")
        print("📁 Upload folders created")
    
    app.run(debug=True, host='0.0.0.0', port=5000)