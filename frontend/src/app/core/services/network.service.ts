import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent, merge, of } from 'rxjs';
import { map, startWith } from 'rxjs/operators';

export interface NetworkStatus {
  online: boolean;
  lastOnline: Date | null;
  lastOffline: Date | null;
  connectionType: string | null;
  effectiveType: string | null;
  downlink: number | null;
  rtt: number | null;
}

/**
 * Network service for monitoring online/offline status and connection quality.
 * Provides real-time updates when network status changes.
 */
@Injectable({
  providedIn: 'root'
})
export class NetworkService implements OnDestroy {
  private networkStatusSubject = new BehaviorSubject<NetworkStatus>(this.getInitialStatus());
  
  /**
   * Observable that emits the current network status.
   * Subscribe to this to get real-time updates.
   */
  public networkStatus$: Observable<NetworkStatus> = this.networkStatusSubject.asObservable();
  
  /**
   * Observable that emits a simple boolean indicating if online.
   */
  public isOnline$: Observable<boolean> = this.networkStatus$.pipe(
    map(status => status.online)
  );
  
  private onlineListener: any;
  private offlineListener: any;
  private connectionChangeListener: any;
  
  constructor() {
    this.setupNetworkMonitoring();
  }
  
  ngOnDestroy(): void {
    this.cleanupListeners();
  }
  
  /**
   * Get the current network status synchronously
   */
  getCurrentStatus(): NetworkStatus {
    return this.networkStatusSubject.value;
  }
  
  /**
   * Check if currently online
   */
  isOnline(): boolean {
    return this.getCurrentStatus().online;
  }
  
  /**
   * Check if connection is slow (effectiveType is 'slow-2g', '2g', or '3g')
   */
  isSlowConnection(): boolean {
    const status = this.getCurrentStatus();
    if (!status.effectiveType) return false;
    
    const slowTypes = ['slow-2g', '2g', '3g'];
    return slowTypes.includes(status.effectiveType);
  }
  
  /**
   * Check if connection is very slow (effectiveType is 'slow-2g' or '2g')
   */
  isVerySlowConnection(): boolean {
    const status = this.getCurrentStatus();
    if (!status.effectiveType) return false;
    
    const verySlowTypes = ['slow-2g', '2g'];
    return verySlowTypes.includes(status.effectiveType);
  }
  
  /**
   * Get connection speed category for UI display
   */
  getConnectionSpeedCategory(): string {
    const status = this.getCurrentStatus();
    
    if (!status.online) return 'offline';
    if (!status.effectiveType) return 'unknown';
    
    switch (status.effectiveType) {
      case 'slow-2g':
        return 'very-slow';
      case '2g':
        return 'slow';
      case '3g':
        return 'moderate';
      case '4g':
        return 'fast';
      default:
        return 'unknown';
    }
  }
  
  /**
   * Simulate offline mode for testing
   */
  simulateOffline(): void {
    const currentStatus = this.getCurrentStatus();
    const newStatus: NetworkStatus = {
      ...currentStatus,
      online: false,
      lastOffline: new Date()
    };
    this.networkStatusSubject.next(newStatus);
  }
  
  /**
   * Simulate online mode for testing
   */
  simulateOnline(): void {
    const currentStatus = this.getCurrentStatus();
    const newStatus: NetworkStatus = {
      ...currentStatus,
      online: true,
      lastOnline: new Date()
    };
    this.networkStatusSubject.next(newStatus);
  }
  
  private getInitialStatus(): NetworkStatus {
    const online = navigator.onLine;
    const now = new Date();
    
    // Try to get connection info if available
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    
    return {
      online,
      lastOnline: online ? now : null,
      lastOffline: online ? null : now,
      connectionType: connection?.type || null,
      effectiveType: connection?.effectiveType || null,
      downlink: connection?.downlink || null,
      rtt: connection?.rtt || null
    };
  }
  
  private setupNetworkMonitoring(): void {
    // Listen to basic online/offline events
    this.onlineListener = () => this.handleOnline();
    this.offlineListener = () => this.handleOffline();
    
    window.addEventListener('online', this.onlineListener);
    window.addEventListener('offline', this.offlineListener);
    
    // Listen to connection changes if supported
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    if (connection) {
      this.connectionChangeListener = () => this.handleConnectionChange();
      connection.addEventListener('change', this.connectionChangeListener);
    }
    
    // Initial update
    this.updateNetworkStatus();
  }
  
  private cleanupListeners(): void {
    if (this.onlineListener) {
      window.removeEventListener('online', this.onlineListener);
    }
    if (this.offlineListener) {
      window.removeEventListener('offline', this.offlineListener);
    }
    
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    if (connection && this.connectionChangeListener) {
      connection.removeEventListener('change', this.connectionChangeListener);
    }
  }
  
  private handleOnline(): void {
    console.log('NetworkService: Device came online');
    this.updateNetworkStatus();
  }
  
  private handleOffline(): void {
    console.warn('NetworkService: Device went offline');
    this.updateNetworkStatus();
  }
  
  private handleConnectionChange(): void {
    console.log('NetworkService: Connection changed');
    this.updateNetworkStatus();
  }
  
  private updateNetworkStatus(): void {
    const currentStatus = this.getCurrentStatus();
    const newStatus = this.getInitialStatus();
    
    // Update timestamps
    if (newStatus.online && !currentStatus.online) {
      newStatus.lastOnline = new Date();
      newStatus.lastOffline = currentStatus.lastOffline;
    } else if (!newStatus.online && currentStatus.online) {
      newStatus.lastOnline = currentStatus.lastOnline;
      newStatus.lastOffline = new Date();
    } else {
      newStatus.lastOnline = currentStatus.lastOnline;
      newStatus.lastOffline = currentStatus.lastOffline;
    }
    
    this.networkStatusSubject.next(newStatus);
  }
}