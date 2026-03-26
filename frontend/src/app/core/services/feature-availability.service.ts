import { Injectable } from '@angular/core';
import { NetworkService } from './network.service';
import { BehaviorSubject, Observable, combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

export interface FeatureAvailability {
  // Core features
  chat: boolean;
  streaming: boolean;
  rag: boolean;
  documentUpload: boolean;
  documentProcessing: boolean;
  
  // Advanced features
  modelSwitching: boolean;
  costEstimation: boolean;
  sourceCitations: boolean;
  slashCommands: boolean;
  
  // UI features
  animations: boolean;
  realTimeUpdates: boolean;
  filePreviews: boolean;
  
  // Overall status
  overallStatus: 'full' | 'degraded' | 'limited' | 'offline';
  message: string;
}

export interface DegradationRule {
  feature: keyof FeatureAvailability;
  condition: () => boolean;
  fallback: any;
  message: string;
}

/**
 * Service for managing graceful degradation when features are unavailable.
 * Monitors network conditions, browser capabilities, and backend availability
 * to determine which features should be enabled or disabled.
 */
@Injectable({
  providedIn: 'root'
})
export class FeatureAvailabilityService {
  private availabilitySubject = new BehaviorSubject<FeatureAvailability>(this.getInitialAvailability());
  
  /**
   * Observable that emits the current feature availability status.
   */
  public availability$: Observable<FeatureAvailability> = this.availabilitySubject.asObservable();
  
  private degradationRules: DegradationRule[] = [
    // Network-dependent features
    {
      feature: 'streaming',
      condition: () => this.networkService.isVerySlowConnection(),
      fallback: false,
      message: 'Streaming disabled due to slow connection'
    },
    {
      feature: 'streaming',
      condition: () => !this.networkService.isOnline(),
      fallback: false,
      message: 'Streaming disabled while offline'
    },
    {
      feature: 'realTimeUpdates',
      condition: () => !this.networkService.isOnline(),
      fallback: false,
      message: 'Real-time updates disabled while offline'
    },
    
    // Browser capability checks
    {
      feature: 'animations',
      condition: () => this.isReducedMotionPreferred(),
      fallback: false,
      message: 'Animations reduced due to user preference'
    },
    {
      feature: 'filePreviews',
      condition: () => !this.supportsFileAPI(),
      fallback: false,
      message: 'File previews not supported in this browser'
    },
    
    // Backend-dependent features (simulated checks)
    {
      feature: 'rag',
      condition: () => this.isBackendServiceUnavailable('rag'),
      fallback: false,
      message: 'RAG features temporarily unavailable'
    },
    {
      feature: 'documentProcessing',
      condition: () => this.isBackendServiceUnavailable('document-processing'),
      fallback: false,
      message: 'Document processing temporarily unavailable'
    }
  ];
  
  constructor(private networkService: NetworkService) {
    // Update availability when network status changes
    combineLatest([
      this.networkService.networkStatus$
    ]).subscribe(() => {
      this.updateAvailability();
    });
    
    // Initial update
    this.updateAvailability();
  }
  
  /**
   * Get the current feature availability status
   */
  getCurrentAvailability(): FeatureAvailability {
    return this.availabilitySubject.value;
  }
  
  /**
   * Check if a specific feature is available
   */
  isFeatureAvailable(feature: keyof FeatureAvailability): boolean {
    const availability = this.getCurrentAvailability();
    return availability[feature] as boolean;
  }
  
  /**
   * Get a fallback value for a feature if it's unavailable
   */
  getFeatureFallback<T>(feature: keyof FeatureAvailability, defaultValue: T): T {
    const rule = this.degradationRules.find(r => r.feature === feature);
    if (rule && rule.condition()) {
      return rule.fallback as T;
    }
    return defaultValue;
  }
  
  /**
   * Get degradation message for a feature if it's unavailable
   */
  getFeatureMessage(feature: keyof FeatureAvailability): string | null {
    const rule = this.degradationRules.find(r => r.feature === feature);
    if (rule && rule.condition()) {
      return rule.message;
    }
    return null;
  }
  
  /**
   * Register a custom degradation rule
   */
  registerDegradationRule(rule: DegradationRule): void {
    this.degradationRules.push(rule);
    this.updateAvailability();
  }
  
  /**
   * Simulate backend service being unavailable (for testing)
   */
  simulateServiceUnavailable(service: string, unavailable: boolean = true): void {
    // In a real implementation, this would update a service status cache
    localStorage.setItem(`service-${service}-unavailable`, unavailable.toString());
    this.updateAvailability();
  }
  
  private getInitialAvailability(): FeatureAvailability {
    return {
      // Core features - assume available by default
      chat: true,
      streaming: true,
      rag: true,
      documentUpload: true,
      documentProcessing: true,
      
      // Advanced features
      modelSwitching: true,
      costEstimation: true,
      sourceCitations: true,
      slashCommands: true,
      
      // UI features
      animations: true,
      realTimeUpdates: true,
      filePreviews: true,
      
      // Overall status
      overallStatus: 'full',
      message: 'All features available'
    };
  }
  
  private updateAvailability(): void {
    const current = this.getCurrentAvailability();
    const updated = { ...current };
    
    // Apply degradation rules
    let anyDegradation = false;
    let degradationMessages: string[] = [];
    
    for (const rule of this.degradationRules) {
      if (rule.condition()) {
        (updated as any)[rule.feature] = rule.fallback;
        anyDegradation = true;
        degradationMessages.push(rule.message);
      }
    }
    
    // Update overall status based on network
    if (!this.networkService.isOnline()) {
      updated.overallStatus = 'offline';
      updated.message = 'Offline mode - limited functionality';
    } else if (this.networkService.isVerySlowConnection()) {
      updated.overallStatus = 'limited';
      updated.message = 'Slow connection - some features disabled';
    } else if (anyDegradation) {
      updated.overallStatus = 'degraded';
      updated.message = degradationMessages.join('; ');
    } else {
      updated.overallStatus = 'full';
      updated.message = 'All features available';
    }
    
    this.availabilitySubject.next(updated);
  }
  
  private isReducedMotionPreferred(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
  
  private supportsFileAPI(): boolean {
    return 'File' in window && 'FileReader' in window && 'FileList' in window && 'Blob' in window;
  }
  
  private isBackendServiceUnavailable(service: string): boolean {
    // In a real implementation, this would check health endpoints
    // For now, we'll check localStorage for simulated outages
    return localStorage.getItem(`service-${service}-unavailable`) === 'true';
  }
}