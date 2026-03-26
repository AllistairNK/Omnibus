import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NetworkService, NetworkStatus } from '../../services/network.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-network-status-indicator',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="showIndicator" 
         [class]="statusClass"
         [title]="tooltipText"
         (click)="toggleDetails()"
         class="network-status-indicator">
      
      <div class="status-icon">
        <span *ngIf="isOnline">✓</span>
        <span *ngIf="!isOnline">✗</span>
      </div>
      
      <div class="status-text" *ngIf="showText">
        {{ statusText }}
      </div>
      
      <div class="connection-details" *ngIf="showDetails">
        <div class="detail-item">
          <strong>Status:</strong> {{ isOnline ? 'Online' : 'Offline' }}
        </div>
        <div class="detail-item" *ngIf="networkStatus.connectionType">
          <strong>Connection:</strong> {{ networkStatus.connectionType }}
        </div>
        <div class="detail-item" *ngIf="networkStatus.effectiveType">
          <strong>Speed:</strong> {{ networkStatus.effectiveType }}
        </div>
        <div class="detail-item" *ngIf="networkStatus.downlink">
          <strong>Downlink:</strong> {{ networkStatus.downlink }} Mbps
        </div>
        <div class="detail-item" *ngIf="networkStatus.rtt">
          <strong>Latency:</strong> {{ networkStatus.rtt }} ms
        </div>
        <div class="detail-item" *ngIf="lastOnline">
          <strong>Last online:</strong> {{ lastOnline | date:'shortTime' }}
        </div>
        <div class="detail-item" *ngIf="lastOffline">
          <strong>Last offline:</strong> {{ lastOffline | date:'shortTime' }}
        </div>
      </div>
    </div>
  `,
  styles: [`
    .network-status-indicator {
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 8px 12px;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      z-index: 1000;
      cursor: pointer;
      transition: all 0.3s ease;
      max-width: 300px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
      border: 1px solid;
    }
    
    .network-status-indicator.online {
      background-color: rgba(0, 255, 0, 0.1);
      border-color: #00ff00;
      color: #00ff00;
    }
    
    .network-status-indicator.offline {
      background-color: rgba(255, 0, 0, 0.1);
      border-color: #ff0000;
      color: #ff0000;
      animation: pulse 2s infinite;
    }
    
    .network-status-indicator.slow {
      background-color: rgba(255, 165, 0, 0.1);
      border-color: #ffa500;
      color: #ffa500;
      animation: pulse 3s infinite;
    }
    
    .status-icon {
      display: inline-block;
      margin-right: 6px;
      font-weight: bold;
    }
    
    .status-text {
      display: inline-block;
    }
    
    .connection-details {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid currentColor;
      font-size: 11px;
    }
    
    .detail-item {
      margin-bottom: 4px;
    }
    
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.7; }
      100% { opacity: 1; }
    }
    
    @media (max-width: 768px) {
      .network-status-indicator {
        bottom: 10px;
        right: 10px;
        font-size: 10px;
        padding: 6px 8px;
      }
    }
  `]
})
export class NetworkStatusIndicatorComponent implements OnInit, OnDestroy {
  networkStatus: NetworkStatus = {
    online: true,
    lastOnline: null,
    lastOffline: null,
    connectionType: null,
    effectiveType: null,
    downlink: null,
    rtt: null
  };
  
  isOnline = true;
  showIndicator = false;
  showText = true;
  showDetails = false;
  
  private statusSubscription: Subscription | null = null;
  
  constructor(private networkService: NetworkService) {}
  
  ngOnInit(): void {
    this.statusSubscription = this.networkService.networkStatus$.subscribe(status => {
      this.networkStatus = status;
      this.isOnline = status.online;
      this.updateVisibility();
    });
  }
  
  ngOnDestroy(): void {
    if (this.statusSubscription) {
      this.statusSubscription.unsubscribe();
    }
  }
  
  get statusClass(): string {
    if (!this.isOnline) {
      return 'offline';
    }
    
    const speedCategory = this.networkService.getConnectionSpeedCategory();
    if (speedCategory === 'very-slow' || speedCategory === 'slow') {
      return 'slow';
    }
    
    return 'online';
  }
  
  get statusText(): string {
    if (!this.isOnline) {
      return 'OFFLINE';
    }
    
    const speedCategory = this.networkService.getConnectionSpeedCategory();
    switch (speedCategory) {
      case 'very-slow':
        return 'SLOW CONNECTION';
      case 'slow':
        return 'SLOW CONNECTION';
      case 'moderate':
        return 'ONLINE';
      case 'fast':
        return 'ONLINE';
      default:
        return 'ONLINE';
    }
  }
  
  get tooltipText(): string {
    if (!this.isOnline) {
      return 'You are offline. Some features may be unavailable.';
    }
    
    const speedCategory = this.networkService.getConnectionSpeedCategory();
    switch (speedCategory) {
      case 'very-slow':
        return 'Very slow connection. Some features may be limited.';
      case 'slow':
        return 'Slow connection. Some features may be limited.';
      default:
        return 'Connection is stable.';
    }
  }
  
  get lastOnline(): Date | null {
    return this.networkStatus.lastOnline;
  }
  
  get lastOffline(): Date | null {
    return this.networkStatus.lastOffline;
  }
  
  toggleDetails(): void {
    this.showDetails = !this.showDetails;
  }
  
  private updateVisibility(): void {
    // Always show when offline
    if (!this.isOnline) {
      this.showIndicator = true;
      this.showText = true;
      return;
    }
    
    // Show for slow connections for 10 seconds
    const isSlow = this.networkService.isSlowConnection();
    if (isSlow) {
      this.showIndicator = true;
      this.showText = true;
      
      // Hide after 10 seconds if still slow
      setTimeout(() => {
        if (this.isOnline && isSlow) {
          this.showText = false;
        }
      }, 10000);
    } else {
      // Hide for good connections after 3 seconds
      this.showIndicator = true;
      this.showText = true;
      
      setTimeout(() => {
        if (this.isOnline && !this.networkService.isSlowConnection()) {
          this.showIndicator = false;
        }
      }, 3000);
    }
  }
}