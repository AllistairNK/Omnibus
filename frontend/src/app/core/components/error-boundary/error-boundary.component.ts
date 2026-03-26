import { Component, ErrorHandler, Input, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GlobalErrorHandlerService } from '../../error-handling/global-error-handler.service';

export interface ErrorBoundaryState {
  hasError: boolean;
  error: any;
  errorInfo: any;
}

/**
 * Error Boundary component that catches errors in its child components.
 * Similar to React's Error Boundary pattern, but implemented for Angular.
 * 
 * Usage:
 * <app-error-boundary [fallback]="fallbackTemplate" [componentName]="'MyComponent'">
 *   <!-- Child components that might throw errors -->
 * </app-error-boundary>
 * 
 * <ng-template #fallbackTemplate let-error>
 *   <div class="error-fallback">
 *     <h3>Something went wrong</h3>
 *     <p>{{ error.message }}</p>
 *     <button (click)="reload()">Try Again</button>
 *   </div>
 * </ng-template>
 */
@Component({
  selector: 'app-error-boundary',
  standalone: true,
  imports: [CommonModule],
  template: `
    <ng-container *ngIf="!state.hasError; else errorTemplate">
      <ng-content />
    </ng-container>
    
    <ng-template #errorTemplate>
      <ng-container *ngIf="fallback; else defaultFallback">
        <ng-container *ngTemplateOutlet="fallback; context: { $implicit: state.error }" />
      </ng-container>
      
      <ng-template #defaultFallback>
        <div class="error-boundary-fallback">
          <div class="error-header">
            <span class="error-icon">⚠</span>
            <span class="error-title">Component Error</span>
          </div>
          <div class="error-body">
            <p><strong>Something went wrong in {{ componentName || 'this component' }}</strong></p>
            <p class="error-message">{{ getErrorMessage(state.error) }}</p>
            <div class="error-actions">
              <button class="error-action" (click)="resetError()">Try Again</button>
              <button class="error-action" (click)="reportError()">Report Error</button>
              <button class="error-action" (click)="reloadPage()">Reload Page</button>
            </div>
            <div class="error-details" *ngIf="showDetails">
              <pre class="error-stack">{{ getErrorStack(state.error) }}</pre>
              <button class="toggle-details" (click)="showDetails = false">Hide Details</button>
            </div>
            <button class="toggle-details" *ngIf="!showDetails" (click)="showDetails = true">
              Show Technical Details
            </button>
          </div>
        </div>
      </ng-template>
    </ng-template>
  `,
  styles: [`
    .error-boundary-fallback {
      padding: 20px;
      border: 1px solid #ff0000;
      background: rgba(255, 0, 0, 0.05);
      color: #ff0000;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      border-radius: 4px;
      margin: 10px 0;
    }
    
    .error-header {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid currentColor;
    }
    
    .error-icon {
      font-size: 16px;
      margin-right: 8px;
    }
    
    .error-title {
      font-weight: bold;
      font-size: 14px;
    }
    
    .error-body {
      line-height: 1.5;
    }
    
    .error-body p {
      margin: 0 0 12px 0;
    }
    
    .error-message {
      font-size: 11px;
      opacity: 0.9;
      word-break: break-word;
      margin-bottom: 16px;
    }
    
    .error-actions {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }
    
    .error-action {
      padding: 6px 12px;
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
    
    .error-details {
      margin-top: 16px;
      padding: 12px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 2px;
      overflow: auto;
      max-height: 200px;
    }
    
    .error-stack {
      font-size: 10px;
      white-space: pre-wrap;
      word-break: break-all;
      margin: 0 0 8px 0;
    }
    
    .toggle-details {
      background: none;
      border: none;
      color: currentColor;
      font-size: 10px;
      text-decoration: underline;
      cursor: pointer;
      padding: 4px 0;
    }
    
    .toggle-details:hover {
      opacity: 0.8;
    }
  `]
})
export class ErrorBoundaryComponent implements OnDestroy {
  @Input() fallback: any;
  @Input() componentName?: string;
  
  state: ErrorBoundaryState = {
    hasError: false,
    error: null,
    errorInfo: null
  };
  
  showDetails = false;
  
  private originalErrorHandler: any;
  
  constructor(
    private errorHandler: ErrorHandler,
    private globalErrorHandler: GlobalErrorHandlerService
  ) {
    // Override the error handler for this component's subtree
    this.overrideErrorHandler();
  }
  
  ngOnDestroy(): void {
    // Restore original error handler
    this.restoreErrorHandler();
  }
  
  /**
   * Reset the error state and try again
   */
  resetError(): void {
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
    this.showDetails = false;
  }
  
  /**
   * Report the error to the global error handler
   */
  reportError(): void {
    if (this.state.error) {
      this.globalErrorHandler.reportError(
        this.state.error,
        'medium',
        this.componentName
      );
      alert('Error has been reported. Thank you!');
    }
  }
  
  /**
   * Reload the entire page
   */
  reloadPage(): void {
    window.location.reload();
  }
  
  /**
   * Get a user-friendly error message
   */
  getErrorMessage(error: any): string {
    if (!error) return 'Unknown error';
    
    if (typeof error === 'string') {
      return error;
    }
    
    if (error.message) {
      return error.message;
    }
    
    return 'An unexpected error occurred';
  }
  
  /**
   * Get error stack trace
   */
  getErrorStack(error: any): string {
    if (!error) return 'No stack trace available';
    
    if (error.stack) {
      return error.stack;
    }
    
    return 'Stack trace not available';
  }
  
  private overrideErrorHandler(): void {
    // Store the original error handler
    this.originalErrorHandler = (this.errorHandler as any).handleError;
    
    // Override with our custom handler
    (this.errorHandler as any).handleError = (error: any) => {
      this.state = {
        hasError: true,
        error,
        errorInfo: this.getErrorInfo(error)
      };
      
      // Also call the original handler to maintain global error handling
      if (this.originalErrorHandler) {
        this.originalErrorHandler.call(this.errorHandler, error);
      }
    };
  }
  
  private restoreErrorHandler(): void {
    if (this.originalErrorHandler) {
      (this.errorHandler as any).handleError = this.originalErrorHandler;
    }
  }
  
  private getErrorInfo(error: any): any {
    // Capture additional error information
    return {
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      component: this.componentName
    };
  }
}