"""
Flask Web Application with File Upload
WARNING: Local storage is ephemeral in Azure App Service
Files may be lost during restarts, scaling, or deployments
"""

from flask import Flask, request, render_template, flash, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Secure the filename and add timestamp
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            filename = timestamp + filename
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            logger.info(f"File uploaded successfully: {filename}")
            flash(f'File {filename} uploaded successfully!')
            
            return redirect(url_for('list_files'))
        else:
            flash('File type not allowed')
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        flash('Upload failed. Please try again.')
        return redirect(request.url)

@app.route('/files')
def list_files():
    """List all uploaded files"""
    try:
        files = []
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    file_info = {
                        'name': filename,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath))
                    }
                    files.append(file_info)
        
        return render_template('files.html', files=files)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        flash('Error loading files')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download uploaded file"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        flash('File not found')
        return redirect(url_for('list_files'))

@app.route('/health')
def health_check():
    """Health check endpoint for Azure App Service"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

if __name__ == '__main__':
    # For development
    app.run(debug=True, host='0.0.0.0', port=5000)
