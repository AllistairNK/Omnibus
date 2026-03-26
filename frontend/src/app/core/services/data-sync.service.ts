import { Injectable, OnDestroy } from '@angular/core';
import { NetworkService } from './network.service';
import { BehaviorSubject, Observable, Subscription, from, of } from 'rxjs';
import { catchError, switchMap, tap, delay, retryWhen, take, map } from 'rxjs/operators';

export interface SyncItem {
  id: string;
  type: 'chat_message' | 'document_upload' | 'api_key' | 'settings';
  data: any;
  timestamp: Date;
  retryCount: number;
  maxRetries: number;
  status: 'pending' | 'syncing' | 'completed' | 'failed';
  error?: string;
}

export interface SyncStatus {
  isSyncing: boolean;
  pendingItems: number;
  completedItems: number;
  failedItems: number;
  lastSync: Date | null;
  syncProgress: number; // 0-100
}

/**
 * Service for managing data synchronization when reconnecting after being offline.
 * Stores pending operations locally and syncs them when network is restored.
 */
@Injectable({
  providedIn: 'root'
})
export class DataSyncService implements OnDestroy {
  private syncQueue: SyncItem[] = [];
  private syncStatusSubject = new BehaviorSubject<SyncStatus>(this.getInitialStatus());
  private networkSubscription: Subscription | null = null;
  
  /**
   * Observable that emits the current sync status
   */
  public syncStatus$: Observable<SyncStatus> = this.syncStatusSubject.asObservable();
  
  /**
   * Observable that emits when sync starts or stops
   */
  public isSyncing$: Observable<boolean> = this.syncStatus$.pipe(
    map((status: SyncStatus) => status.isSyncing)
  );
  
  constructor(private networkService: NetworkService) {
    this.loadQueueFromStorage();
    this.setupNetworkMonitoring();
  }
  
  ngOnDestroy(): void {
    if (this.networkSubscription) {
      this.networkSubscription.unsubscribe();
    }
  }
  
  /**
   * Get current sync status
   */
  getSyncStatus(): SyncStatus {
    return this.syncStatusSubject.value;
  }
  
  /**
   * Add an item to the sync queue
   */
  addToQueue(type: SyncItem['type'], data: any, maxRetries: number = 3): string {
    const id = this.generateId();
    const item: SyncItem = {
      id,
      type,
      data,
      timestamp: new Date(),
      retryCount: 0,
      maxRetries,
      status: 'pending'
    };
    
    this.syncQueue.push(item);
    this.saveQueueToStorage();
    this.updateSyncStatus();
    
    // If online, try to sync immediately
    if (this.networkService.isOnline()) {
      this.processQueue();
    }
    
    return id;
  }
  
  /**
   * Remove an item from the sync queue
   */
  removeFromQueue(id: string): boolean {
    const index = this.syncQueue.findIndex(item => item.id === id);
    if (index !== -1) {
      this.syncQueue.splice(index, 1);
      this.saveQueueToStorage();
      this.updateSyncStatus();
      return true;
    }
    return false;
  }
  
  /**
   * Get all items in the sync queue
   */
  getQueueItems(): SyncItem[] {
    return [...this.syncQueue];
  }
  
  /**
   * Get pending items count
   */
  getPendingCount(): number {
    return this.syncQueue.filter(item => item.status === 'pending').length;
  }
  
  /**
   * Manually trigger sync process
   */
  triggerSync(): void {
    if (this.networkService.isOnline()) {
      this.processQueue();
    }
  }
  
  /**
   * Clear all completed items from queue
   */
  clearCompleted(): void {
    this.syncQueue = this.syncQueue.filter(item => item.status !== 'completed');
    this.saveQueueToStorage();
    this.updateSyncStatus();
  }
  
  /**
   * Clear all items from queue
   */
  clearAll(): void {
    this.syncQueue = [];
    this.saveQueueToStorage();
    this.updateSyncStatus();
  }
  
  /**
   * Retry all failed items
   */
  retryFailed(): void {
    this.syncQueue.forEach(item => {
      if (item.status === 'failed' && item.retryCount < item.maxRetries) {
        item.status = 'pending';
        item.retryCount++;
        item.error = undefined;
      }
    });
    
    this.saveQueueToStorage();
    this.updateSyncStatus();
    
    if (this.networkService.isOnline()) {
      this.processQueue();
    }
  }
  
  private setupNetworkMonitoring(): void {
    this.networkSubscription = this.networkService.networkStatus$.subscribe(status => {
      if (status.online && !this.getSyncStatus().isSyncing) {
        // Network restored - start syncing
        console.log('Network restored, starting sync...');
        this.processQueue();
      } else if (!status.online && this.getSyncStatus().isSyncing) {
        // Network lost while syncing
        console.warn('Network lost during sync');
        this.updateSyncStatus({ isSyncing: false });
      }
    });
  }
  
  private processQueue(): void {
    if (this.getSyncStatus().isSyncing) {
      return; // Already syncing
    }
    
    const pendingItems = this.syncQueue.filter(item => item.status === 'pending');
    if (pendingItems.length === 0) {
      return; // Nothing to sync
    }
    
    this.updateSyncStatus({ isSyncing: true });
    
    // Process items sequentially
    this.processItemsSequentially(pendingItems)
      .then(() => {
        this.updateSyncStatus({ 
          isSyncing: false,
          lastSync: new Date()
        });
        console.log('Sync completed successfully');
      })
      .catch(error => {
        console.error('Sync failed:', error);
        this.updateSyncStatus({ isSyncing: false });
      });
  }
  
  private async processItemsSequentially(items: SyncItem[]): Promise<void> {
    const totalItems = items.length;
    let processed = 0;
    
    for (const item of items) {
      try {
        // Update item status
        item.status = 'syncing';
        this.saveQueueToStorage();
        
        // Process based on type
        await this.processItem(item);
        
        // Mark as completed
        item.status = 'completed';
        processed++;
        
        // Update progress
        this.updateSyncStatus({
          syncProgress: Math.round((processed / totalItems) * 100)
        });
        
      } catch (error) {
        // Mark as failed
        item.status = 'failed';
        item.error = error instanceof Error ? error.message : String(error);
        item.retryCount++;
        
        console.error(`Failed to sync item ${item.id}:`, error);
      }
      
      this.saveQueueToStorage();
    }
    
    // Reset progress
    this.updateSyncStatus({ syncProgress: 0 });
  }
  
  private async processItem(item: SyncItem): Promise<void> {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // In a real implementation, this would make actual API calls
    // For now, we'll simulate successful sync with occasional failures
    const shouldFail = Math.random() < 0.2 && item.retryCount < 2; // 20% chance to fail
    
    if (shouldFail) {
      throw new Error(`Simulated sync failure for ${item.type}`);
    }
    
    console.log(`Successfully synced ${item.type} item:`, item.id);
    
    // Here you would implement actual API calls:
    // switch (item.type) {
    //   case 'chat_message':
    //     await this.chatService.sendMessage(item.data);
    //     break;
    //   case 'document_upload':
    //     await this.documentService.uploadDocument(item.data);
    //     break;
    //   // etc.
    // }
  }
  
  private loadQueueFromStorage(): void {
    try {
      const saved = localStorage.getItem('sync-queue');
      if (saved) {
        const parsed = JSON.parse(saved);
        // Convert timestamp strings back to Date objects
        this.syncQueue = parsed.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }));
      }
    } catch (error) {
      console.error('Failed to load sync queue from storage:', error);
      this.syncQueue = [];
    }
    
    this.updateSyncStatus();
  }
  
  private saveQueueToStorage(): void {
    try {
      localStorage.setItem('sync-queue', JSON.stringify(this.syncQueue));
    } catch (error) {
      console.error('Failed to save sync queue to storage:', error);
    }
  }
  
  private updateSyncStatus(updates: Partial<SyncStatus> = {}): void {
    const current = this.syncStatusSubject.value;
    const pendingItems = this.syncQueue.filter(item => item.status === 'pending').length;
    const completedItems = this.syncQueue.filter(item => item.status === 'completed').length;
    const failedItems = this.syncQueue.filter(item => item.status === 'failed').length;
    
    const newStatus: SyncStatus = {
      ...current,
      ...updates,
      pendingItems,
      completedItems,
      failedItems
    };
    
    this.syncStatusSubject.next(newStatus);
  }
  
  private getInitialStatus(): SyncStatus {
    return {
      isSyncing: false,
      pendingItems: 0,
      completedItems: 0,
      failedItems: 0,
      lastSync: null,
      syncProgress: 0
    };
  }
  
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}