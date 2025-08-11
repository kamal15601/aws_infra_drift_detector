"""
Flask Web Application with Azure Blob Storage File Upload
RECOMMENDED: Production-ready solution with persistent storage
"""

from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import tempfile

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Azure Blob Storage configuration
# These should be set as environment variables in Azure App Service
STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME', 'your-storage-account')
CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'uploads')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_blob_service_client():
    """Get Azure Blob Service Client using Managed Identity"""
    try:
        # Use Managed Identity for authentication (recommended for Azure App Service)
        credential = DefaultAzureCredential()
        account_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
        return BlobServiceClient(account_url=account_url, credential=credential)
    except Exception as e:
        logger.error(f"Failed to create blob service client: {str(e)}")
        return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index_blob.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload to Azure Blob Storage"""
    try:
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Get blob service client
            blob_service_client = get_blob_service_client()
            if not blob_service_client:
                flash('Storage service unavailable. Please try again later.')
                return redirect(request.url)
            
            # Secure the filename and add timestamp
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            blob_name = timestamp + filename
            
            # Upload to Azure Blob Storage
            blob_client = blob_service_client.get_blob_client(
                container=CONTAINER_NAME, 
                blob=blob_name
            )
            
            # Upload file data
            file_data = file.read()
            blob_client.upload_blob(
                file_data, 
                overwrite=True,
                metadata={
                    'original_filename': file.filename,
                    'upload_date': datetime.now().isoformat(),
                    'file_size': str(len(file_data))
                }
            )
            
            logger.info(f"File uploaded to blob storage: {blob_name}")
            flash(f'File {filename} uploaded successfully to Azure Blob Storage!')
            
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
    """List all uploaded files from Azure Blob Storage"""
    try:
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            flash('Storage service unavailable')
            return redirect(url_for('index'))
        
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        
        files = []
        for blob in container_client.list_blobs(include=['metadata']):
            file_info = {
                'name': blob.name,
                'size': blob.size,
                'modified': blob.last_modified,
                'original_filename': blob.metadata.get('original_filename', blob.name) if blob.metadata else blob.name
            }
            files.append(file_info)
        
        # Sort by upload date (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return render_template('files_blob.html', files=files)
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        flash('Error loading files from storage')
        return redirect(url_for('index'))

@app.route('/download/<blob_name>')
def download_file(blob_name):
    """Download file from Azure Blob Storage"""
    try:
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            flash('Storage service unavailable')
            return redirect(url_for('list_files'))
        
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, 
            blob=blob_name
        )
        
        # Download blob data
        blob_data = blob_client.download_blob().readall()
        
        # Get blob properties for filename
        blob_properties = blob_client.get_blob_properties()
        original_filename = blob_properties.metadata.get('original_filename', blob_name) if blob_properties.metadata else blob_name
        
        # Create response with file data
        from flask import Response
        return Response(
            blob_data,
            headers={
                'Content-Disposition': f'attachment; filename={original_filename}',
                'Content-Type': 'application/octet-stream'
            }
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        flash('File not found or download failed')
        return redirect(url_for('list_files'))

@app.route('/health')
def health_check():
    """Health check endpoint for Azure App Service"""
    try:
        # Test blob storage connection
        blob_service_client = get_blob_service_client()
        storage_status = "connected" if blob_service_client else "disconnected"
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'storage_status': storage_status,
            'storage_account': STORAGE_ACCOUNT_NAME,
            'container': CONTAINER_NAME
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # For development
    app.run(debug=True, host='0.0.0.0', port=5000)
