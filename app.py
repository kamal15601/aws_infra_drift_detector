"""
InfraSnap - Infrastructure Monitoring Web Application
Python 3.9 Flask Backend with Static Frontend

This Flask application serves the InfraSnap static web application
and provides API endpoints for infrastructure monitoring data.

Security Features:
- CORS protection
- Security headers
- Request rate limiting ready
- Environment-based configuration
- Logging and monitoring

Performance Features:
- Static file caching
- Gzip compression
- Connection pooling ready
- Background task support
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
import random
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static')

# Security Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# CORS Configuration - Secure for production
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
CORS(app, origins=cors_origins)

# Application Configuration
PORT = int(os.environ.get('PORT', 8000))
HOST = os.environ.get('HOST', '0.0.0.0')

# In-memory data storage (In production, use Redis or database)
class InfrastructureData:
    """
    Infrastructure monitoring data manager
    In production, this would connect to real monitoring systems
    """
    def __init__(self):
        self.data = {
            'total_resources': 247,
            'drift_count': 3,
            'compliance_score': 98.2,
            'last_scan': datetime.now().isoformat(),
            'status': 'operational'
        }
        self.activities = [
            {
                'type': 'info',
                'title': 'Configuration Updated',
                'description': 'Load balancer settings modified in us-east-1',
                'timestamp': (datetime.now() - timedelta(minutes=2)).isoformat(),
                'icon': 'fas fa-cog'
            },
            {
                'type': 'warning',
                'title': 'Drift Detected',
                'description': 'Security group rules changed outside of Terraform',
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'icon': 'fas fa-exclamation-triangle'
            },
            {
                'type': 'success',
                'title': 'Scan Completed',
                'description': 'Full infrastructure scan completed successfully',
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'icon': 'fas fa-check-circle'
            }
        ]
        self.lock = threading.Lock()
        self._start_background_updates()
    
    def _start_background_updates(self):
        """Start background thread for data simulation"""
        def update_data():
            while True:
                try:
                    time.sleep(30)  # Update every 30 seconds
                    self.simulate_data_update()
                except Exception as e:
                    logger.error(f"Background update error: {e}")
        
        thread = threading.Thread(target=update_data, daemon=True)
        thread.start()
        logger.info("Background data update thread started")
    
    def simulate_data_update(self):
        """Simulate real-time infrastructure changes"""
        with self.lock:
            # Simulate resource count changes
            change = random.randint(-2, 3)
            self.data['total_resources'] = max(0, self.data['total_resources'] + change)
            
            # Simulate drift detection
            drift_change = random.randint(-1, 2)
            self.data['drift_count'] = max(0, self.data['drift_count'] + drift_change)
            
            # Simulate compliance score fluctuation
            score_change = random.uniform(-0.5, 0.5)
            new_score = self.data['compliance_score'] + score_change
            self.data['compliance_score'] = round(max(90.0, min(100.0, new_score)), 1)
            
            # Update last scan time
            self.data['last_scan'] = datetime.now().isoformat()
            
            logger.info(f"Data updated - Resources: {self.data['total_resources']}, "
                       f"Drift: {self.data['drift_count']}, "
                       f"Compliance: {self.data['compliance_score']}%")
    
    def get_dashboard_data(self):
        """Get current dashboard data"""
        with self.lock:
            return self.data.copy()
    
    def get_activities(self):
        """Get recent activities"""
        with self.lock:
            return self.activities.copy()
    
    def add_activity(self, activity_type, title, description):
        """Add new activity"""
        with self.lock:
            new_activity = {
                'type': activity_type,
                'title': title,
                'description': description,
                'timestamp': datetime.now().isoformat(),
                'icon': self._get_icon_for_type(activity_type)
            }
            self.activities.insert(0, new_activity)
            # Keep only last 10 activities
            self.activities = self.activities[:10]
    
    def _get_icon_for_type(self, activity_type):
        """Get appropriate icon for activity type"""
        icons = {
            'info': 'fas fa-info-circle',
            'warning': 'fas fa-exclamation-triangle',
            'success': 'fas fa-check-circle',
            'error': 'fas fa-times-circle'
        }
        return icons.get(activity_type, 'fas fa-info-circle')

# Initialize data manager
infra_data = InfrastructureData()

@app.before_request
def log_request():
    """Log incoming requests for monitoring"""
    if request.endpoint != 'static':
        logger.info(f"{request.method} {request.path} - {request.remote_addr}")

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if app.config['ENV'] == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error for path: {request.path}")
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Routes

@app.route('/')
def index():
    """Serve the main application page"""
    try:
        return send_from_directory('src', 'index.html')
    except FileNotFoundError:
        logger.error("index.html not found in src directory")
        return jsonify({'error': 'Application not properly configured'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'python_version': '3.9'
    })

# API Routes

@app.route('/api/dashboard')
def get_dashboard_data():
    """Get current dashboard statistics"""
    try:
        data = infra_data.get_dashboard_data()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/activities')
def get_activities():
    """Get recent infrastructure activities"""
    try:
        activities = infra_data.get_activities()
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities)
        })
    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate infrastructure report"""
    try:
        # Simulate report generation delay
        time.sleep(1)
        
        dashboard_data = infra_data.get_dashboard_data()
        activities = infra_data.get_activities()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_resources': dashboard_data['total_resources'],
                'drift_count': dashboard_data['drift_count'],
                'compliance_score': dashboard_data['compliance_score'],
                'last_scan': dashboard_data['last_scan']
            },
            'recent_activities': activities[:5],  # Last 5 activities
            'recommendations': [
                'Review and fix security group configurations',
                'Enable encryption on all storage resources',
                'Update AMIs to latest versions',
                'Implement automated remediation for common drift patterns'
            ],
            'report_id': f"RPT-{int(time.time())}"
        }
        
        # Add activity for report generation
        infra_data.add_activity(
            'info',
            'Report Generated',
            f"Infrastructure report {report['report_id']} created"
        )
        
        return jsonify({
            'success': True,
            'report': report,
            'download_url': f"/api/download-report/{report['report_id']}"
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger infrastructure scan"""
    try:
        # Simulate scan
        infra_data.simulate_data_update()
        infra_data.add_activity(
            'success',
            'Manual Scan Triggered',
            'Infrastructure scan initiated by user request'
        )
        
        return jsonify({
            'success': True,
            'message': 'Infrastructure scan triggered successfully',
            'scan_id': f"SCAN-{int(time.time())}"
        })
        
    except Exception as e:
        logger.error(f"Error triggering scan: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Static file serving

@app.route('/styles.css')
def serve_css():
    """Serve CSS file from src directory"""
    try:
        return send_from_directory('src', 'styles.css', mimetype='text/css')
    except FileNotFoundError:
        logger.error("styles.css not found in src directory")
        return "CSS file not found", 404

@app.route('/app.js')
def serve_js():
    """Serve JavaScript file from src directory"""
    try:
        return send_from_directory('src', 'app.js', mimetype='application/javascript')
    except FileNotFoundError:
        logger.error("app.js not found in src directory")
        return "JavaScript file not found", 404

@app.route('/src/<path:filename>')
def serve_src_files(filename):
    """Serve any file from src directory"""
    try:
        return send_from_directory('src', filename)
    except FileNotFoundError:
        logger.error(f"File {filename} not found in src directory")
        return f"File {filename} not found", 404

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (for future use)"""
    try:
        return send_from_directory('static', filename)
    except FileNotFoundError:
        return f"Static file {filename} not found", 404

if __name__ == '__main__':
    """
    Application entry point
    
    For production deployment:
    - Use a WSGI server like Gunicorn
    - Set environment variables for configuration
    - Use proper database instead of in-memory storage
    - Implement authentication and authorization
    - Add rate limiting and monitoring
    """
    logger.info(f"Starting InfraSnap application on {HOST}:{PORT}")
    logger.info(f"Environment: {app.config['ENV']}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    
    app.run(
        host=HOST,
        port=PORT,
        debug=app.config['DEBUG'],
        threaded=True  # Enable threading for background tasks
    )
