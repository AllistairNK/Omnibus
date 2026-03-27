import { Injectable, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Subject, Subscription, fromEvent } from 'rxjs';
import { filter } from 'rxjs/operators';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  description: string;
  action: () => void;
  preventDefault?: boolean;
  stopPropagation?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class KeyboardShortcutService implements OnDestroy {
  private shortcuts: KeyboardShortcut[] = [];
  private keydownSubject = new Subject<KeyboardEvent>();
  private subscriptions: Subscription[] = [];
  private isBrowser: boolean;

  constructor(@Inject(PLATFORM_ID) platformId: Object) {
    this.isBrowser = isPlatformBrowser(platformId);
    
    if (this.isBrowser) {
      this.setupGlobalListeners();
      this.registerDefaultShortcuts();
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
    this.keydownSubject.complete();
  }

  /**
   * Setup global keyboard event listeners
   */
  private setupGlobalListeners(): void {
    const keydown$ = fromEvent<KeyboardEvent>(document, 'keydown');
    
    const subscription = keydown$.subscribe(event => {
      this.handleKeydown(event);
    });
    
    this.subscriptions.push(subscription);
  }

  /**
   * Register a new keyboard shortcut
   */
  registerShortcut(shortcut: KeyboardShortcut): void {
    // Validate shortcut key
    if (typeof shortcut.key !== 'string') {
      console.warn('Keyboard shortcut key must be a string', shortcut);
      return;
    }
    this.shortcuts.push(shortcut);
  }

  /**
   * Unregister a keyboard shortcut
   */
  unregisterShortcut(key: string, ctrlKey = false, shiftKey = false, altKey = false, metaKey = false): void {
    this.shortcuts = this.shortcuts.filter(shortcut => 
      !(shortcut.key === key && 
        shortcut.ctrlKey === ctrlKey &&
        shortcut.shiftKey === shiftKey &&
        shortcut.altKey === altKey &&
        shortcut.metaKey === metaKey)
    );
  }

  /**
   * Handle keydown events
   */
  private handleKeydown(event: KeyboardEvent): void {
    // Guard against undefined/null key
    if (typeof event.key !== 'string') {
      return;
    }
    
    const key = event.key.toLowerCase();
    
    // Find matching shortcuts
    const matchingShortcuts = this.shortcuts.filter(shortcut => {
      // Guard against invalid shortcut key
      if (typeof shortcut.key !== 'string') {
        return false;
      }
      return shortcut.key.toLowerCase() === key &&
             (shortcut.ctrlKey === undefined || shortcut.ctrlKey === event.ctrlKey) &&
             (shortcut.shiftKey === undefined || shortcut.shiftKey === event.shiftKey) &&
             (shortcut.altKey === undefined || shortcut.altKey === event.altKey) &&
             (shortcut.metaKey === undefined || shortcut.metaKey === event.metaKey);
    });

    if (matchingShortcuts.length > 0) {
      // Execute all matching shortcuts
      matchingShortcuts.forEach(shortcut => {
        if (shortcut.preventDefault) {
          event.preventDefault();
        }
        if (shortcut.stopPropagation) {
          event.stopPropagation();
        }
        shortcut.action();
      });
    }
  }

  /**
   * Register default keyboard shortcuts
   */
  private registerDefaultShortcuts(): void {
    // Navigation shortcuts
    this.registerShortcut({
      key: '?',
      description: 'Show help dialog',
      action: () => this.showHelpDialog(),
      preventDefault: true
    });

    this.registerShortcut({
      key: 'k',
      ctrlKey: true,
      description: 'Focus chat input',
      action: () => this.focusChatInput(),
      preventDefault: true
    });

    this.registerShortcut({
      key: 'l',
      ctrlKey: true,
      description: 'Clear chat',
      action: () => this.clearChat(),
      preventDefault: true
    });

    this.registerShortcut({
      key: 'Enter',
      ctrlKey: true,
      description: 'Send message',
      action: () => this.sendMessage(),
      preventDefault: true
    });

    this.registerShortcut({
      key: 'Escape',
      description: 'Close dialogs/cancel',
      action: () => this.closeDialogs(),
      preventDefault: true
    });

    this.registerShortcut({
      key: 't',
      ctrlKey: true,
      shiftKey: true,
      description: 'Toggle theme',
      action: () => this.toggleTheme(),
      preventDefault: true
    });

    // Navigation shortcuts
    this.registerShortcut({
      key: '1',
      ctrlKey: true,
      description: 'Navigate to Chat',
      action: () => this.navigateTo('/chat'),
      preventDefault: true
    });

    this.registerShortcut({
      key: '2',
      ctrlKey: true,
      description: 'Navigate to Documents',
      action: () => this.navigateTo('/documents'),
      preventDefault: true
    });

    this.registerShortcut({
      key: '3',
      ctrlKey: true,
      description: 'Navigate to Settings',
      action: () => this.navigateTo('/settings'),
      preventDefault: true
    });

    // Command history navigation
    this.registerShortcut({
      key: 'ArrowUp',
      ctrlKey: true,
      description: 'Previous command in history',
      action: () => this.navigateCommandHistory(-1),
      preventDefault: true
    });

    this.registerShortcut({
      key: 'ArrowDown',
      ctrlKey: true,
      description: 'Next command in history',
      action: () => this.navigateCommandHistory(1),
      preventDefault: true
    });
  }

  /**
   * Get all registered shortcuts
   */
  getShortcuts(): KeyboardShortcut[] {
    return [...this.shortcuts];
  }

  /**
   * Get shortcuts grouped by category
   */
  getShortcutsByCategory(): { [category: string]: KeyboardShortcut[] } {
    const categories: { [category: string]: KeyboardShortcut[] } = {
      'Navigation': [],
      'Chat': [],
      'General': []
    };

    this.shortcuts.forEach(shortcut => {
      if (shortcut.key === '1' || shortcut.key === '2' || shortcut.key === '3') {
        categories['Navigation'].push(shortcut);
      } else if (shortcut.key === 'k' || shortcut.key === 'l' || shortcut.key === 'Enter' || 
                 shortcut.key === 'ArrowUp' || shortcut.key === 'ArrowDown') {
        categories['Chat'].push(shortcut);
      } else {
        categories['General'].push(shortcut);
      }
    });

    return categories;
  }

  // Default shortcut actions (these would be overridden by components)
  private showHelpDialog(): void {
    console.log('Help dialog would open');
    // This would be overridden by components
    const event = new CustomEvent('show-help-dialog');
    document.dispatchEvent(event);
  }

  private focusChatInput(): void {
    const event = new CustomEvent('focus-chat-input');
    document.dispatchEvent(event);
  }

  private clearChat(): void {
    const event = new CustomEvent('clear-chat');
    document.dispatchEvent(event);
  }

  private sendMessage(): void {
    const event = new CustomEvent('send-message');
    document.dispatchEvent(event);
  }

  private closeDialogs(): void {
    const event = new CustomEvent('close-dialogs');
    document.dispatchEvent(event);
  }

  private toggleTheme(): void {
    const event = new CustomEvent('toggle-theme');
    document.dispatchEvent(event);
  }

  private navigateTo(path: string): void {
    const event = new CustomEvent('navigate-to', { detail: { path } });
    document.dispatchEvent(event);
  }

  private navigateCommandHistory(direction: number): void {
    const event = new CustomEvent('navigate-command-history', { detail: { direction } });
    document.dispatchEvent(event);
  }
}