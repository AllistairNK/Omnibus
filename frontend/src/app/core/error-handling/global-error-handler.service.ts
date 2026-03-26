import { ErrorHandler, Injectable, Injector } from '@angular/core';
import { Router } from '@angular/router';
import { LocationStrategy, PathLocationStrategy } from '@angular/common';

export interface ErrorLog {
  id: string;
  timestamp: Date;
  message: string;
  stack: string;
  url: string;
  userAgent: string;
  userId?: string;
  component?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

/**
 * Global error handler service that catches unhandled errors across the application.
 * This service should be registered as the ErrorHandler in the app module.
 */
@Injectable({
  providedIn: 'root'
})
export class GlobalErrorHandlerService implements ErrorHandler {
  private errorLogs: ErrorLog[] = [];
  private maxLogs = 100;
  
  constructor(private injector: Injector) {}
  
  handleError(error: any): void {
    try {
      // Extract error information
      const errorLog = this.createErrorLog(error);
      
      // Add to logs
      this.errorLogs.unshift(errorLog);
      if (this.errorLogs.length > this.maxLogs) {
        this.errorLogs.pop();
      }
      
      // Log to console (in development)
      console.error('GlobalErrorHandler caught error:', error);
      console.error('Error details:', errorLog);
      
      // Send to error tracking service (in production)
      this.sendToErrorTracking(errorLog);
      
      // Show user-friendly error message
      this.showUserNotification(errorLog);
      
      // Navigate to error page for critical errors
      if (this.isCriticalError(error)) {
        this.navigateToErrorPage(errorLog);
      }
    } catch (handlerError) {
      // Fallback if error handler itself fails
      console.error('Error handler failed:', handlerError);
      console.error('Original error:', error);
    }
  }
  
  /**
   * Get recent error logs
   */
  getErrorLogs(): ErrorLog[] {
    return [...this.errorLogs];
  }
  
  /**
   * Clear error logs
   */
  clearErrorLogs(): void {
    this.errorLogs = [];
  }
  
  /**
   * Report a manual error (for caught exceptions that should still be logged)
   */
  reportError(error: any, severity: ErrorLog['severity'] = 'medium', component?: string): void {
    const errorLog = this.createErrorLog(error, severity, component);
    this.errorLogs.unshift(errorLog);
    
    if (this.errorLogs.length > this.maxLogs) {
      this.errorLogs.pop();
    }
    
    console.error('Manual error report:', errorLog);
    this.sendToErrorTracking(errorLog);
  }
  
  private createErrorLog(error: any, severity: ErrorLog['severity'] = 'medium', component?: string): ErrorLog {
    const router = this.injector.get(Router);
    const location = this.injector.get(LocationStrategy);
    
    // Get current URL
    const url = location instanceof PathLocationStrategy 
      ? location.path() 
      : window.location.href;
    
    // Extract error message and stack
    let message = 'Unknown error';
    let stack = '';
    
    if (error instanceof Error) {
      message = error.message;
      stack = error.stack || '';
    } else if (typeof error === 'string') {
      message = error;
    } else if (error && error.message) {
      message = error.message;
      stack = error.stack || '';
    }
    
    // Determine severity
    let finalSeverity = severity;
    if (this.isCriticalError(error)) {
      finalSeverity = 'critical';
    } else if (error.status === 404 || error.status === 403) {
      finalSeverity = 'low';
    } else if (error.status >= 500) {
      finalSeverity = 'high';
    }
    
    return {
      id: this.generateId(),
      timestamp: new Date(),
      message,
      stack,
      url,
      userAgent: navigator.userAgent,
      component,
      severity: finalSeverity
    };
  }
  
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
  
  private sendToErrorTracking(errorLog: ErrorLog): void {
    // In a real application, this would send to Sentry, LogRocket, etc.
    // For now, we'll just log to localStorage for debugging
    try {
      const trackingLogs = JSON.parse(localStorage.getItem('error-tracking-logs') || '[]');
      trackingLogs.push({
        ...errorLog,
        timestamp: errorLog.timestamp.toISOString()
      });
      
      // Keep only last 50 logs in localStorage
      if (trackingLogs.length > 50) {
        trackingLogs.shift();
      }
      
      localStorage.setItem('error-tracking-logs', JSON.stringify(trackingLogs));
    } catch (e) {
      console.error('Failed to save error to localStorage:', e);
    }
  }
  
  private showUserNotification(errorLog: ErrorLog): void {
    // Only show notifications for medium+ severity errors
    if (errorLog.severity === 'low') {
      return;
    }
    
    // Create a temporary notification element
    const notification = document.createElement('div');
    notification.className = 'global-error-notification';
    notification.innerHTML = `
      <div class="error-notification-content">
        <div class="error-header">
          <span class="error-icon">⚠</span>
          <span class="error-title">Application Error</span>
          <button class="error-close">×</button>
        </div>
        <div class="error-body">
          <p>Something went wrong. The error has been logged.</p>
          <p class="error-message">${this.truncateMessage(errorLog.message, 100)}</p>
        </div>
        <div class="error-footer">
          <button class="error-action" data-action="dismiss">Dismiss</button>
          <button class="error-action" data-action="details">Details</button>
          <button class="error-action" data-action="refresh">Refresh Page</button>
        </div>
      </div>
    `;
    
    // Add styles
    const styles = document.createElement('style');
    styles.textContent = `
      .global-error-notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 350px;
        background: rgba(255, 0, 0, 0.1);
        border: 1px solid #ff0000;
        color: #ff0000;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        z-index: 9999;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        border-radius: 4px;
        animation: slideIn 0.3s ease-out;
      }
      
      .error-notification-content {
        padding: 12px;
      }
      
      .error-header {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid currentColor;
      }
      
      .error-icon {
        font-size: 16px;
        margin-right: 8px;
      }
      
      .error-title {
        font-weight: bold;
        flex-grow: 1;
      }
      
      .error-close {
        background: none;
        border: none;
        color: currentColor;
        font-size: 18px;
        cursor: pointer;
        line-height: 1;
        padding: 0 4px;
      }
      
      .error-body {
        margin-bottom: 12px;
      }
      
      .error-body p {
        margin: 0 0 8px 0;
      }
      
      .error-message {
        font-size: 11px;
        opacity: 0.8;
        word-break: break-word;
      }
      
      .error-footer {
        display: flex;
        justify-content: space-between;
        gap: 8px;
      }
      
      .error-action {
        padding: 4px 8px;
        border: 1px solid currentColor;
        background: none;
        color: currentColor;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        cursor: pointer;
        border-radius: 2px;
        flex: 1;
      }
      
      .error-action:hover {
        background: rgba(255, 255, 255, 0.1);
      }
      
      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateX(100%);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
    `;
    
    document.head.appendChild(styles);
    document.body.appendChild(notification);
    
    // Add event listeners
    notification.querySelector('.error-close')?.addEventListener('click', () => {
      notification.remove();
      styles.remove();
    });
    
    notification.querySelector('[data-action="dismiss"]')?.addEventListener('click', () => {
      notification.remove();
      styles.remove();
    });
    
    notification.querySelector('[data-action="details"]')?.addEventListener('click', () => {
      // Show error details in console
      console.error('Error details:', errorLog);
      alert(`Error details:\n\nMessage: ${errorLog.message}\n\nSee console for full stack trace.`);
    });
    
    notification.querySelector('[data-action="refresh"]')?.addEventListener('click', () => {
      window.location.reload();
    });
    
    // Auto-remove after 30 seconds for non-critical errors
    if (errorLog.severity !== 'critical') {
      setTimeout(() => {
        if (document.body.contains(notification)) {
          notification.remove();
          styles.remove();
        }
      }, 30000);
    }
  }
  
  private navigateToErrorPage(errorLog: ErrorLog): void {
    try {
      const router = this.injector.get(Router);
      router.navigate(['/error'], {
        state: { error: errorLog }
      });
    } catch (e) {
      console.error('Failed to navigate to error page:', e);
    }
  }
  
  private isCriticalError(error: any): boolean {
    // Define what constitutes a critical error
    if (error instanceof Error) {
      const criticalMessages = [
        'cannot read property',
        'cannot call method',
        'undefined is not a function',
        'maximum call stack',
        'out of memory',
        'failed to fetch',
        'network error'
      ];
      
      const errorMessage = error.message.toLowerCase();
      return criticalMessages.some(msg => errorMessage.includes(msg));
    }
    
    return false;
  }
  
  private truncateMessage(message: string, maxLength: number): string {
    if (message.length <= maxLength) {
      return message;
    }
    return message.substring(0, maxLength) + '...';
  }
}