import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FeatureAvailabilityService, FeatureAvailability } from '../../services/feature-availability.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-feature-degradation-warning',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="showWarning" 
         [class]="warningClass"
         class="feature-degradation-warning">
      
      <div class="warning-header">
        <span class="warning-icon">⚠</span>
        <span class="warning-title">{{ warningTitle }}</span>
        <button class="close-button" (click)="dismissWarning()" *ngIf="dismissible">×</button>
      </div>
      
      <div class="warning-body">
        <p>{{ availability.message }}</p>
        
        <div class="affected-features" *ngIf="affectedFeatures.length > 0">
          <strong>Affected features:</strong>
          <ul>
            <li *ngFor="let feature of affectedFeatures">
              {{ getFeatureDisplayName(feature) }}
            </li>
          </ul>
        </div>
        
        <div class="suggestions" *ngIf="suggestions.length > 0">
          <strong>Suggestions:</strong>
          <ul>
            <li *ngFor="let suggestion of suggestions">{{ suggestion }}</li>
          </ul>
        </div>
      </div>
      
      <div class="warning-footer" *ngIf="showActions">
        <button class="action-button primary" (click)="refreshPage()">
          Refresh
        </button>
        <button class="action-button secondary" (click)="continueAnyway()">
          Continue Anyway
        </button>
      </div>
    </div>
  `,
  styles: [`
    .feature-degradation-warning {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      width: 90%;
      max-width: 600px;
      padding: 16px;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      z-index: 1001;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
      border: 1px solid;
      animation: slideDown 0.3s ease-out;
    }
    
    .feature-degradation-warning.full {
      display: none;
    }
    
    .feature-degradation-warning.degraded {
      background-color: rgba(255, 165, 0, 0.1);
      border-color: #ffa500;
      color: #ffa500;
    }
    
    .feature-degradation-warning.limited {
      background-color: rgba(255, 69, 0, 0.1);
      border-color: #ff4500;
      color: #ff4500;
    }
    
    .feature-degradation-warning.offline {
      background-color: rgba(255, 0, 0, 0.1);
      border-color: #ff0000;
      color: #ff0000;
      animation: pulse 2s infinite;
    }
    
    .warning-header {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid currentColor;
    }
    
    .warning-icon {
      font-size: 16px;
      margin-right: 8px;
    }
    
    .warning-title {
      font-weight: bold;
      font-size: 14px;
      flex-grow: 1;
    }
    
    .close-button {
      background: none;
      border: none;
      color: currentColor;
      font-size: 18px;
      cursor: pointer;
      padding: 0 4px;
      line-height: 1;
    }
    
    .close-button:hover {
      opacity: 0.8;
    }
    
    .warning-body {
      margin-bottom: 16px;
    }
    
    .warning-body p {
      margin: 0 0 12px 0;
    }
    
    .affected-features, .suggestions {
      margin-top: 12px;
    }
    
    .affected-features ul, .suggestions ul {
      margin: 4px 0;
      padding-left: 20px;
    }
    
    .affected-features li, .suggestions li {
      margin-bottom: 4px;
    }
    
    .warning-footer {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding-top: 12px;
      border-top: 1px solid currentColor;
    }
    
    .action-button {
      padding: 6px 12px;
      border: 1px solid currentColor;
      background: none;
      color: currentColor;
      font-family: 'Courier New', monospace;
      font-size: 11px;
      cursor: pointer;
      border-radius: 2px;
      transition: all 0.2s ease;
    }
    
    .action-button:hover {
      background-color: rgba(255, 255, 255, 0.1);
    }
    
    .action-button.primary {
      background-color: currentColor;
      color: #000;
    }
    
    .action-button.primary:hover {
      opacity: 0.9;
    }
    
    @keyframes slideDown {
      from {
        opacity: 0;
        transform: translate(-50%, -20px);
      }
      to {
        opacity: 1;
        transform: translate(-50%, 0);
      }
    }
    
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.8; }
      100% { opacity: 1; }
    }
    
    @media (max-width: 768px) {
      .feature-degradation-warning {
        width: 95%;
        top: 10px;
        font-size: 11px;
      }
      
      .warning-footer {
        flex-direction: column;
      }
      
      .action-button {
        width: 100%;
      }
    }
  `]
})
export class FeatureDegradationWarningComponent implements OnInit, OnDestroy {
  availability: FeatureAvailability = {
    chat: true,
    streaming: true,
    rag: true,
    documentUpload: true,
    documentProcessing: true,
    modelSwitching: true,
    costEstimation: true,
    sourceCitations: true,
    slashCommands: true,
    animations: true,
    realTimeUpdates: true,
    filePreviews: true,
    overallStatus: 'full',
    message: 'All features available'
  };
  
  showWarning = false;
  dismissible = true;
  showActions = false;
  
  private availabilitySubscription: Subscription | null = null;
  private dismissedWarnings: Set<string> = new Set();
  
  constructor(private featureService: FeatureAvailabilityService) {}
  
  ngOnInit(): void {
    this.availabilitySubscription = this.featureService.availability$.subscribe(availability => {
      this.availability = availability;
      this.updateVisibility();
    });
    
    // Load dismissed warnings from localStorage
    const saved = localStorage.getItem('dismissed-feature-warnings');
    if (saved) {
      this.dismissedWarnings = new Set(JSON.parse(saved));
    }
  }
  
  ngOnDestroy(): void {
    if (this.availabilitySubscription) {
      this.availabilitySubscription.unsubscribe();
    }
  }
  
  get warningClass(): string {
    return this.availability.overallStatus;
  }
  
  get warningTitle(): string {
    switch (this.availability.overallStatus) {
      case 'degraded':
        return 'SYSTEM DEGRADED';
      case 'limited':
        return 'LIMITED FUNCTIONALITY';
      case 'offline':
        return 'OFFLINE MODE';
      default:
        return 'SYSTEM STATUS';
    }
  }
  
  get affectedFeatures(): string[] {
    const features: string[] = [];
    const availability = this.availability as any;
    
    // Check each feature that might be disabled
    const featureKeys: (keyof FeatureAvailability)[] = [
      'streaming', 'rag', 'documentProcessing', 'modelSwitching',
      'costEstimation', 'sourceCitations', 'animations', 'realTimeUpdates',
      'filePreviews'
    ];
    
    for (const key of featureKeys) {
      if (availability[key] === false) {
        features.push(key);
      }
    }
    
    return features;
  }
  
  get suggestions(): string[] {
    const suggestions: string[] = [];
    
    if (this.availability.overallStatus === 'offline') {
      suggestions.push('Check your internet connection');
      suggestions.push('Try refreshing the page when back online');
      suggestions.push('Use cached data where available');
    } else if (this.availability.overallStatus === 'limited') {
      suggestions.push('Consider using a faster internet connection');
      suggestions.push('Disable streaming for faster responses');
      suggestions.push('Upload smaller documents for processing');
    } else if (this.affectedFeatures.includes('rag')) {
      suggestions.push('Try again in a few minutes');
      suggestions.push('Use basic chat mode instead');
    }
    
    return suggestions;
  }
  
  dismissWarning(): void {
    // Store dismissal for this specific status
    this.dismissedWarnings.add(this.availability.overallStatus);
    localStorage.setItem('dismissed-feature-warnings', JSON.stringify(Array.from(this.dismissedWarnings)));
    this.showWarning = false;
  }
  
  refreshPage(): void {
    window.location.reload();
  }
  
  continueAnyway(): void {
    this.dismissWarning();
  }
  
  getFeatureDisplayName(feature: string): string {
    const displayNames: Record<string, string> = {
      'streaming': 'Real-time streaming',
      'rag': 'RAG (document search)',
      'documentProcessing': 'Document processing',
      'modelSwitching': 'Model switching',
      'costEstimation': 'Cost estimation',
      'sourceCitations': 'Source citations',
      'animations': 'Animations',
      'realTimeUpdates': 'Real-time updates',
      'filePreviews': 'File previews'
    };
    
    return displayNames[feature] || feature;
  }
  
  private updateVisibility(): void {
    // Don't show for full availability
    if (this.availability.overallStatus === 'full') {
      this.showWarning = false;
      return;
    }
    
    // Check if user has dismissed this warning
    if (this.dismissedWarnings.has(this.availability.overallStatus)) {
      this.showWarning = false;
      return;
    }
    
    // Show warning for degraded, limited, or offline status
    this.showWarning = true;
    
    // Configure based on status
    switch (this.availability.overallStatus) {
      case 'offline':
        this.dismissible = false; // Can't dismiss offline warning
        this.showActions = true;
        break;
      case 'limited':
        this.dismissible = true;
        this.showActions = true;
        break;
      case 'degraded':
        this.dismissible = true;
        this.showActions = false;
        break;
    }
  }
}