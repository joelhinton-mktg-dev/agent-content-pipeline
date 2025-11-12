/**
 * AI Content Pipeline Demo - Main JavaScript
 * Handles WebSocket communication, UI interactions, and real-time updates
 */

// Global variables
let isConnected = false;
let currentSession = null;
let progressInterval = null;

// Utility functions
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }, function(err) {
        console.error('Could not copy text: ', err);
        showToast('Failed to copy to clipboard', 'error');
    });
}

function showToast(message, type = 'info', duration = 3000) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
    toast.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease-out;
    `;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// Connection status management
function updateConnectionStatus(connected) {
    isConnected = connected;
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.innerHTML = connected 
            ? '<i class="fas fa-circle text-success me-1"></i>Connected'
            : '<i class="fas fa-circle text-danger me-1"></i>Disconnected';
    }
}

// Progress tracking
function updateProgressBar(percentage, stage, total, statusText) {
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-text');
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (progressText) {
        progressText.textContent = `Stage ${stage}/${total}: ${statusText}`;
    }
}

// Pipeline stage management
const pipelineStages = [
    { name: 'Outline Generation', icon: 'fas fa-list-alt', color: '#6f42c1' },
    { name: 'Research Collection', icon: 'fas fa-search', color: '#0d6efd' },
    { name: 'Content Creation', icon: 'fas fa-pen-nib', color: '#198754' },
    { name: 'Citation Processing', icon: 'fas fa-quote-left', color: '#fd7e14' },
    { name: 'Image Generation', icon: 'fas fa-image', color: '#e83e8c' },
    { name: 'Fact Checking', icon: 'fas fa-check-double', color: '#20c997' },
    { name: 'SEO Optimization', icon: 'fas fa-chart-line', color: '#ffc107' },
    { name: 'Publishing Preparation', icon: 'fas fa-upload', color: '#dc3545' }
];

function createStageIndicator(currentStage) {
    const container = document.createElement('div');
    container.className = 'stage-indicator mb-3';
    
    let html = '<div class="row text-center">';
    pipelineStages.forEach((stage, index) => {
        const isActive = index + 1 === currentStage;
        const isCompleted = index + 1 < currentStage;
        const statusClass = isCompleted ? 'completed' : isActive ? 'active' : 'pending';
        
        html += `
            <div class="col-3 col-md-1p5 mb-2">
                <div class="stage-step ${statusClass}" style="color: ${stage.color}">
                    <i class="${stage.icon} ${isActive ? 'fa-spin' : ''}"></i>
                    <div class="stage-number">${index + 1}</div>
                    <small class="stage-name">${stage.name}</small>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
    return container;
}

// Download management
function createDownloadButton(download) {
    return `
        <div class="download-item d-flex justify-content-between align-items-center p-2 mb-2 bg-light rounded">
            <div class="download-info">
                <strong class="d-block">${download.name}</strong>
                <small class="text-muted">${formatFileSize(download.size)}</small>
            </div>
            <div class="download-actions">
                <a href="${download.url}" class="btn btn-sm btn-primary me-1" target="_blank" title="Download">
                    <i class="fas fa-download"></i>
                </a>
                <button class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard('${download.url}')" title="Copy URL">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        </div>
    `;
}

// Content validation
function validateContentRequest(message) {
    const minLength = 10;
    const maxLength = 500;
    
    if (!message || message.trim().length < minLength) {
        return { valid: false, error: `Message must be at least ${minLength} characters long` };
    }
    
    if (message.length > maxLength) {
        return { valid: false, error: `Message must be less than ${maxLength} characters` };
    }
    
    return { valid: true };
}

// Topic extraction
function extractTopicFromMessage(message) {
    // Simple topic extraction logic
    const keywords = ['generate', 'create', 'write', 'article', 'about', 'content', 'on'];
    let topic = message.toLowerCase();
    
    // Remove common command words
    keywords.forEach(keyword => {
        topic = topic.replace(new RegExp(`\\b${keyword}\\b`, 'gi'), '');
    });
    
    // Clean up and return
    topic = topic.replace(/[^\w\s]/g, '').trim();
    
    // If topic is too short, use original message
    if (topic.length < 5) {
        topic = message;
    }
    
    return topic;
}

// Audience detection
function detectAudience(message) {
    const audienceMap = {
        'healthcare professionals': /healthcare|medical|doctor|nurse|physician|clinic/i,
        'business leaders': /business|executive|ceo|manager|leadership|corporate/i,
        'IT professionals': /it|technology|tech|developer|programmer|software|cyber/i,
        'marketing professionals': /marketing|advertis|brand|campaign|social media/i,
        'educators': /education|teacher|student|academic|university|school/i,
        'researchers': /research|study|academic|scientist|analysis/i
    };
    
    for (const [audience, pattern] of Object.entries(audienceMap)) {
        if (pattern.test(message)) {
            return audience;
        }
    }
    
    return 'General audience';
}

// Length estimation
function estimateLength(message) {
    // Simple length estimation based on keywords
    if (/comprehensive|detailed|in-depth|extensive/.test(message.toLowerCase())) {
        return 2500;
    } else if (/brief|short|quick|summary/.test(message.toLowerCase())) {
        return 1000;
    } else if (/long|thorough|complete/.test(message.toLowerCase())) {
        return 3000;
    }
    
    return 1500; // Default length
}

// Export utility functions for use in templates
window.aiPipelineUtils = {
    formatTimestamp,
    formatFileSize,
    copyToClipboard,
    showToast,
    updateConnectionStatus,
    updateProgressBar,
    createStageIndicator,
    createDownloadButton,
    validateContentRequest,
    extractTopicFromMessage,
    detectAudience,
    estimateLength,
    pipelineStages
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Content Pipeline Demo initialized');
    
    // Add connection status indicator if not present
    if (!document.getElementById('connectionStatus')) {
        const statusHtml = `
            <div id="connectionStatus" class="position-fixed" style="bottom: 20px; left: 20px; z-index: 1000;">
                <small class="badge bg-secondary">
                    <i class="fas fa-circle text-warning me-1"></i>Connecting...
                </small>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', statusHtml);
    }
    
    // Add CSS animations
    const animationCSS = `
        <style>
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            .stage-step {
                transition: all 0.3s ease;
                padding: 10px 5px;
                border-radius: 8px;
                background: rgba(255,255,255,0.1);
            }
            .stage-step.active {
                background: rgba(255,255,255,0.2);
                transform: scale(1.05);
            }
            .stage-step.completed {
                opacity: 0.7;
            }
            .stage-number {
                font-size: 0.7rem;
                font-weight: bold;
                margin-top: 5px;
            }
            .stage-name {
                font-size: 0.65rem;
                display: block;
                margin-top: 2px;
                line-height: 1.1;
            }
            .download-item {
                transition: all 0.2s ease;
            }
            .download-item:hover {
                background-color: #e9ecef !important;
                transform: translateY(-1px);
            }
            @media (max-width: 768px) {
                .stage-name { display: none; }
                .stage-step { padding: 5px 3px; }
            }
        </style>
    `;
    document.head.insertAdjacentHTML('beforeend', animationCSS);
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl+Enter to send message
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const sendButton = document.getElementById('sendButton');
        if (sendButton) {
            sendButton.click();
        }
    }
    
    // Escape to clear input
    if (event.key === 'Escape') {
        const messageInput = document.getElementById('messageInput');
        if (messageInput && messageInput.value) {
            messageInput.value = '';
            messageInput.focus();
        }
    }
});

// Handle visibility change (tab switching)
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Tab became visible - could refresh connection status
        console.log('Tab became visible');
    }
});

// Add error boundary for JavaScript errors
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    showToast('An unexpected error occurred. Please refresh the page.', 'error', 5000);
});

// Add unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('A connection error occurred. Please check your network.', 'error', 5000);
});