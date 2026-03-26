import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataSyncService, SyncStatus } from '../../services/data-sync.service';
import { NetworkService } from '../../services/network.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-sync-status-indicator',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="showIndicator" 
         [class]="indicatorClass"
         class="sync-status-indicator"
         [title]="tooltipText">
      
      <div class="sync-icon">
        <span *ngIf="isSyncing">⟳</span>
        <span *ngIf="!isSyncing && pendingItems > 0">⏸</span>
        <span *ngIf="!isSyncing && pendingItems === 0">✓</span>
      </div>
      
      <div class="sync-text" *ngIf="showText">
        {{ statusText }}
      </div>
      
      <div class="sync-progress" *ngIf="isSyncing">
        <div class="progress-bar">
          <div class="progress-fill" [style.width.%]="syncProgress"></div>
        </div>
        <span class="progress-text">{{ syncProgress }}%</span>
      </div>
      
      <div class="sync-details" *ngIf="showDetails">
        <div class="detail-item">
          <strong>Pending:</strong> {{ pendingItems }}
        </div>
        <div class="detail-item">
          <strong>Completed:</strong> {{ completedItems }}
        </div>
        <div class="detail-item">
          <strong>Failed:</strong> {{ failedItems }}
        </div>
        <div class="detail-item" *ngIf="lastSync">
          <strong>Last sync:</strong> {{ lastSync | date:'shortTime' }}
        </div>
        <div class="detail-actions" *ngIf="pendingItems > 0 || failedItems > 0">
          <button class="sync-action" (click)="triggerSync()" *ngIf="!isSyncing && isOnline">
            Sync Now
          </button>
          <button class="sync-action" (click)="retryFailed()" *ngIf="failedItems > 0">
            Retry Failed
          </button>
          <button class="sync-action" (click)="clearCompleted()" *ngIf="completedItems > 0">
            Clear Completed
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .sync-status-indicator {
      position: fixed;
      bottom: 60px;
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
    
    .sync-status-indicator.syncing {
      background-color: rgba(0, 255, 255, 0.1);
      border-color: #00ffff;
      color: #00ffff;
      animation: pulse 2s infinite;
    }
    
    .sync-status-indicator.pending {
      background-color: rgba(255, 165, 0, 0.1);
      border-color: #ffa500;
      color: #ffa500;
    }
    
    .sync-status-indicator.idle {
      background-color: rgba(0, 255, 0, 0.1);
      border-color: #00ff00;
      color: #00ff00;
    }
    
    .sync-status-indicator.offline {
      background-color: rgba(128, 128, 128, 0.1);
      border-color: #808080;
      color: #808080;
    }
    
    .sync-icon {
      display: inline-block;
      margin-right: 6px;
      font-weight: bold;
      animation: spin 1s linear infinite;
    }
    
    .sync-status-indicator:not(.syncing) .sync-icon {
      animation: none;
    }
    
    .sync-text {
      display: inline-block;
    }
    
    .sync-progress {
      margin-top: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .progress-bar {
      flex-grow: 1;
      height: 4px;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 2px;
      overflow: hidden;
    }
    
    .progress-fill {
      height: 100%;
      background: currentColor;
      transition: width 0.3s ease;
    }
    
    .progress-text {
      font-size: 10px;
      min-width: 30px;
      text-align: right;
    }
    
    .sync-details {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid currentColor;
      font-size: 11px;
    }
    
    .detail-item {
      margin-bottom: 4px;
    }
    
    .detail-actions {
      margin-top: 8px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    
    .sync-action {
      padding: 3px 6px;
      border: 1px solid currentColor;
      background: none;
      color: currentColor;
      font-family: 'Courier New', monospace;
      font-size: 10px;
      cursor: pointer;
      border-radius: 2px;
      flex: 1;
      min-width: 80px;
    }
    
    .sync-action:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.7; }
      100% { opacity: 1; }
    }
    
    @media (max-width: 768px) {
      .sync-status-indicator {
        bottom: 50px;
        right: 10px;
        font-size: 10px;
        padding: 6px 8px;
      }
    }
  `]
})
export class SyncStatusIndicatorComponent implements OnInit, OnDestroy {
  syncStatus: SyncStatus = {
    isSyncing: false,
    pendingItems: 0,
    completedItems: 0,
    failedItems: 0,
    lastSync: null,
    syncProgress: 0
  };
  
  isOnline = true;
  isSyncing = false;
  pendingItems = 0;
  completedItems = 0;
  failedItems = 0;
  syncProgress = 0;
  lastSync: Date | null = null;
  
  showIndicator = false;
  showText = true;
  showDetails = false;
  
  private syncSubscription: Subscription | null = null;
  private networkSubscription: Subscription | null = null;
  
  constructor(
    private dataSyncService: DataSyncService,
    private networkService: NetworkService
  ) {}
  
  ngOnInit(): void {
    this.syncSubscription = this.dataSyncService.syncStatus$.subscribe(status => {
      this.syncStatus = status;
      this.isSyncing = status.isSyncing;
      this.pendingItems = status.pendingItems;
      this.completedItems = status.completedItems;
      this.failedItems = status.failedItems;
      this.syncProgress = status.syncProgress;
      this.lastSync = status.lastSync;
      this.updateVisibility();
    });
    
    this.networkSubscription = this.networkService.isOnline$.subscribe(online => {
      this.isOnline = online;
      this.updateVisibility();
    });
  }
  
  ngOnDestroy(): void {
    if (this.syncSubscription) {
      this.syncSubscription.unsubscribe();
    }
    if (this.networkSubscription) {
      this.networkSubscription.unsubscribe();
    }
  }
  
  get indicatorClass(): string {
    if (!this.isOnline) {
      return 'offline';
    }
    
    if (this.isSyncing) {
      return 'syncing';
    }
    
    if (this.pendingItems > 0) {
      return 'pending';
    }
    
    return 'idle';
  }
  
  get statusText(): string {
    if (!this.isOnline) {
      return 'OFFLINE';
    }
    
    if (this.isSyncing) {
      return 'SYNCING';
    }
    
    if (this.pendingItems > 0) {
      return `${this.pendingItems} PENDING`;
    }
    
    return 'SYNCED';
  }
  
  get tooltipText(): string {
    if (!this.isOnline) {
      return 'Offline - sync paused';
    }
    
    if (this.isSyncing) {
      return `Syncing... ${this.syncProgress}% complete`;
    }
    
    if (this.pendingItems > 0) {
      return `${this.pendingItems} items waiting to sync`;
    }
    
    if (this.failedItems > 0) {
      return `${this.failedItems} items failed to sync`;
    }
    
    return 'All data synced';
  }
  
  triggerSync(): void {
    this.dataSyncService.triggerSync();
  }
  
  retryFailed(): void {
    this.dataSyncService.retryFailed();
  }
  
  clearCompleted(): void {
    this.dataSyncService.clearCompleted();
  }
  
  private updateVisibility(): void {
    // Always show when syncing
    if (this.isSyncing) {
      this.showIndicator = true;
      this.showText = true;
      this.showDetails = true;
      return;
    }
    
    // Show when there are pending items
    if (this.pendingItems > 0 || this.failedItems > 0) {
      this.showIndicator = true;
      this.showText = true;
      this.showDetails = false;
      
      // Auto-hide details after 5 seconds if not interacting
      setTimeout(() => {
        if (!this.isSyncing && this.showDetails) {
          this.showDetails = false;
        }
      }, 5000);
      return;
    }
    
    // Show briefly after sync completes
    if (this.completedItems > 0 && this.lastSync) {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      if (this.lastSync > fiveMinutesAgo) {
        this.showIndicator = true;
        this.showText = true;
        this.showDetails = false;
        
        // Hide after 3 seconds
        setTimeout(() => {
          if (!this.isSyncing && this.pendingItems === 0) {
            this.showIndicator = false;
          }
        }, 3000);
        return;
      }
    }
    
    // Hide otherwise
    this.showIndicator = false;
  }
}