import { Component, OnInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { filter } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import { RouterModule } from '@angular/router';
import { NetworkStatusIndicatorComponent } from './core/components/network-status-indicator/network-status-indicator.component';
import { FeatureDegradationWarningComponent } from './core/components/feature-degradation-warning/feature-degradation-warning.component';
import { SyncStatusIndicatorComponent } from './core/components/sync-status-indicator/sync-status-indicator.component';
import { ThemeToggleComponent } from './core/components/theme-toggle/theme-toggle.component';
import { KeyboardShortcutHelpComponent } from './core/components/keyboard-shortcut-help/keyboard-shortcut-help.component';
import { KeyboardShortcutService } from './core/services/keyboard-shortcut.service';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, MatButtonModule, MatIconModule, MatDialogModule, CommonModule, RouterModule, NetworkStatusIndicatorComponent, FeatureDegradationWarningComponent, SyncStatusIndicatorComponent, ThemeToggleComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'AI Chatbot with RAG';
  currentRoute = '';
  currentTime = new Date();
  private subscriptions: Subscription[] = [];
  private isBrowser: boolean;

  constructor(
    private router: Router,
    private dialog: MatDialog,
    private keyboardShortcutService: KeyboardShortcutService,
    private themeService: ThemeService,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngOnInit() {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.currentRoute = event.urlAfterRedirects.substring(1) || 'home';
    });

    // Update time every second
    setInterval(() => {
      this.currentTime = new Date();
    }, 1000);

    // Setup keyboard shortcut listeners
    if (this.isBrowser) {
      this.setupKeyboardShortcuts();
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  /**
   * Setup keyboard shortcut event listeners
   */
  private setupKeyboardShortcuts(): void {
    // Show help dialog on ? key
    document.addEventListener('show-help-dialog', () => {
      this.showKeyboardShortcutHelp();
    });

    // Toggle theme on Ctrl+Shift+T
    document.addEventListener('toggle-theme', () => {
      this.themeService.toggleTheme();
    });

    // Navigation shortcuts
    document.addEventListener('navigate-to', (event: any) => {
      const path = event.detail?.path;
      if (path) {
        this.router.navigate([path]);
      }
    });

    // Register custom shortcuts
    this.keyboardShortcutService.registerShortcut({
      key: '/',
      description: 'Focus chat input and show command suggestions',
      action: () => this.focusChatInputWithSlash(),
      preventDefault: true
    });
  }

  /**
   * Show keyboard shortcut help dialog
   */
  showKeyboardShortcutHelp(): void {
    this.dialog.open(KeyboardShortcutHelpComponent, {
      width: '600px',
      maxWidth: '90vw',
      panelClass: 'keyboard-shortcut-dialog'
    });
  }

  /**
   * Focus chat input with slash command
   */
  private focusChatInputWithSlash(): void {
    // Dispatch event to chat component
    const event = new CustomEvent('focus-chat-input-with-slash');
    document.dispatchEvent(event);
  }
}
