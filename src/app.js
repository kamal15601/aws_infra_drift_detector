// InfraSnap Web App JavaScript - Python Backend Integration
class InfraSnapApp {
    constructor() {
        this.apiBase = window.location.origin;
        this.initializeApp();
        this.setupEventListeners();
        this.loadInitialData();
    }

    initializeApp() {
        console.log('InfraSnap Web App Initialized - Python 3.9 Backend');
        this.loadDashboardData();
        this.loadActivities();
    }

    setupEventListeners() {
        // Smooth scrolling for navigation links
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Add scroll effect to navbar
        window.addEventListener('scroll', () => {
            const header = document.querySelector('.header');
            if (window.scrollY > 100) {
                header.style.background = 'rgba(255, 255, 255, 0.98)';
            } else {
                header.style.background = 'rgba(255, 255, 255, 0.95)';
            }
        });
    }

    loadInitialData() {
        // Load data from Python backend
        this.loadDashboardData();
        this.loadActivities();
        
        // Update data every 30 seconds from backend
        setInterval(() => {
            this.loadDashboardData();
            this.updateLastScanTime();
        }, 30000);
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBase}/api/dashboard`);
            const result = await response.json();
            
            if (result.success) {
                this.updateDashboardUI(result.data);
            } else {
                console.error('Failed to load dashboard data:', result.error);
                this.showNotification('Failed to load dashboard data', 'error');
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showNotification('Connection error - using cached data', 'warning');
        }
    }

    updateDashboardUI(data) {
        // Update dashboard elements with real data from Python backend
        const totalResources = document.getElementById('totalResources');
        const driftCount = document.getElementById('driftCount');
        const complianceScore = document.getElementById('complianceScore');
        const lastScan = document.getElementById('lastScan');

        if (totalResources) {
            totalResources.textContent = data.total_resources;
        }

        if (driftCount) {
            driftCount.textContent = data.drift_count;
            
            // Update color based on drift count
            if (data.drift_count > 5) {
                driftCount.className = 'stat-number error';
            } else if (data.drift_count > 2) {
                driftCount.className = 'stat-number warning';
            } else {
                driftCount.className = 'stat-number';
            }
        }

        if (complianceScore) {
            complianceScore.textContent = data.compliance_score + '%';
        }

        if (lastScan) {
            const scanTime = new Date(data.last_scan);
            const now = new Date();
            const diffMinutes = Math.floor((now - scanTime) / 60000);
            
            if (diffMinutes < 1) {
                lastScan.textContent = 'Just now';
            } else if (diffMinutes === 1) {
                lastScan.textContent = '1 min ago';
            } else {
                lastScan.textContent = `${diffMinutes} min ago`;
            }
        }
    }

    async loadActivities() {
        try {
            const response = await fetch(`${this.apiBase}/api/activities`);
            const result = await response.json();
            
            if (result.success) {
                this.populateActivityList(result.activities);
            } else {
                console.error('Failed to load activities:', result.error);
            }
        } catch (error) {
            console.error('Error loading activities:', error);
        }
    }

    updateLastScanTime() {
        // This method is now handled by loadDashboardData() from backend
        // Keep for compatibility but data comes from Python backend
    }

    populateActivityList(activities = null) {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;

        // Use activities from backend if provided, otherwise load from API
        if (!activities) {
            this.loadActivities();
            return;
        }

        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    <i class="${activity.icon}"></i>
                </div>
                <div class="activity-content">
                    <h4>${activity.title}</h4>
                    <p>${activity.description}</p>
                </div>
                <div class="activity-time">${this.formatTimeAgo(activity.timestamp)}</div>
            </div>
        `).join('');
    }

    formatTimeAgo(timestamp) {
        const activityTime = new Date(timestamp);
        const now = new Date();
        const diffMinutes = Math.floor((now - activityTime) / 60000);
        
        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes === 1) return '1 minute ago';
        if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
        
        const diffHours = Math.floor(diffMinutes / 60);
    formatTimeAgo(timestamp) {
        const activityTime = new Date(timestamp);
        const now = new Date();
        const diffMinutes = Math.floor((now - activityTime) / 60000);
        
        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes === 1) return '1 minute ago';
        if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
        
        const diffHours = Math.floor(diffMinutes / 60);
        if (diffHours === 1) return '1 hour ago';
        if (diffHours < 24) return `${diffHours} hours ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays === 1) return '1 day ago';
        return `${diffDays} days ago`;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
            <span>${message}</span>
        `;

        // Add to body
        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    async generateReport() {
        const button = event.target;
        const originalText = button.innerHTML;
        
        // Show loading state
        button.innerHTML = '<i class="loading"></i> Generating...';
        button.disabled = true;

        try {
            // Call Python backend to generate report
            const response = await fetch(`${this.apiBase}/api/generate-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Create and download report
                this.downloadReportData(result.report);
                this.showNotification('Infrastructure report generated successfully!', 'success');
                
                // Refresh activities to show the new report generation activity
                this.loadActivities();
            } else {
                this.showNotification('Failed to generate report: ' + result.error, 'error');
            }
            
        } catch (error) {
            console.error('Error generating report:', error);
            this.showNotification('Failed to generate report. Please try again.', 'error');
        } finally {
            // Restore button
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    downloadReportData(reportData) {
        const reportContent = `
# Infrastructure Drift Report

**Generated:** ${new Date(reportData.timestamp).toLocaleString()}
**Report ID:** ${reportData.report_id}

## Summary
- **Total Resources:** ${reportData.summary.total_resources}
- **Drift Detected:** ${reportData.summary.drift_count} resources
- **Compliance Score:** ${reportData.summary.compliance_score}%
- **Last Scan:** ${new Date(reportData.summary.last_scan).toLocaleString()}

## Recent Activities
${reportData.recent_activities.map(activity => `- **${activity.title}**: ${activity.description} (${this.formatTimeAgo(activity.timestamp)})`).join('\n')}

## Recommendations
${reportData.recommendations.map(rec => `- ${rec}`).join('\n')}

---
Generated by InfraSnap v1.0 (Python 3.9 Backend)
        `;

        const blob = new Blob([reportContent], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `infrastructure-report-${new Date().toISOString().split('T')[0]}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
        const originalText = button.innerHTML;
        
        // Show loading state
        button.innerHTML = '<i class="loading"></i> Generating...';
        button.disabled = true;

        try {
            // Simulate report generation
            await this.delay(2000);
            
            // Create mock report data
            const reportData = {
                timestamp: new Date().toISOString(),
                totalResources: document.getElementById('totalResources')?.textContent || '247',
                driftCount: document.getElementById('driftCount')?.textContent || '3',
                complianceScore: document.getElementById('complianceScore')?.textContent || '98.2%',
                issues: [
                    'Security group sg-12345 has unrestricted SSH access',
                    'S3 bucket my-app-logs is not encrypted',
                    'EC2 instance i-67890 has outdated AMI'
                ]
            };

            // Generate and download report
            this.downloadReport(reportData);
            this.showNotification('Infrastructure report generated successfully!', 'success');
            
        } catch (error) {
            this.showNotification('Failed to generate report. Please try again.', 'error');
        } finally {
            // Restore button
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    downloadReport(data) {
        const reportContent = `
# Infrastructure Drift Report

**Generated:** ${new Date(data.timestamp).toLocaleString()}

## Summary
- **Total Resources:** ${data.totalResources}
- **Drift Detected:** ${data.driftCount} resources
- **Compliance Score:** ${data.complianceScore}

## Issues Found
${data.issues.map(issue => `- ${issue}`).join('\n')}

## Recommendations
1. Review and fix security group configurations
2. Enable encryption on all storage resources
3. Update AMIs to latest versions
4. Implement automated remediation for common drift patterns

---
Generated by InfraSnap v1.0
        `;

        const blob = new Blob([reportContent], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `infrastructure-report-${new Date().toISOString().split('T')[0]}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async loadDashboard() {
        // Smooth scroll to dashboard
        const dashboardSection = document.getElementById('dashboard');
        if (dashboardSection) {
            dashboardSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            
            // Add highlight effect
            dashboardSection.style.background = 'linear-gradient(135deg, #f0f9ff, #e0f2fe)';
            
            setTimeout(() => {
                dashboardSection.style.background = 'linear-gradient(135deg, #f8fafc, #e2e8f0)';
            }, 2000);
            
            this.showNotification('Dashboard loaded successfully!', 'success');
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Global functions for button clicks
function loadDashboard() {
    app.loadDashboard();
}

function generateReport() {
    app.generateReport();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new InfraSnapApp();
});

// Add notification styles dynamically
const notificationStyles = `
    .notification {
        position: fixed;
        top: 100px;
        right: 20px;
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        min-width: 300px;
        transform: translateX(100%);
        animation: slideIn 0.3s ease forwards;
    }

    .notification.success {
        border-left: 4px solid #10b981;
        color: #065f46;
    }

    .notification.error {
        border-left: 4px solid #ef4444;
        color: #991b1b;
    }

    .notification.info {
        border-left: 4px solid #3b82f6;
        color: #1e40af;
    }

    @keyframes slideIn {
        to {
            transform: translateX(0);
        }
    }

    .stat-number.error {
        color: #ef4444 !important;
    }
`;

// Add styles to head
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
