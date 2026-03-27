import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export type Theme = 'dark' | 'light';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private currentTheme: Theme = 'dark';
  private readonly THEME_KEY = 'ai-chatbot-theme';

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    this.loadTheme();
  }

  /**
   * Load theme from localStorage or use default
   */
  private loadTheme(): void {
    if (isPlatformBrowser(this.platformId)) {
      const savedTheme = localStorage.getItem(this.THEME_KEY) as Theme;
      if (savedTheme && (savedTheme === 'dark' || savedTheme === 'light')) {
        this.currentTheme = savedTheme;
      } else {
        // Check system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.currentTheme = prefersDark ? 'dark' : 'light';
      }
      this.applyTheme(this.currentTheme);
    }
  }

  /**
   * Get current theme
   */
  getTheme(): Theme {
    return this.currentTheme;
  }

  /**
   * Check if dark theme is active
   */
  isDarkTheme(): boolean {
    return this.currentTheme === 'dark';
  }

  /**
   * Check if light theme is active
   */
  isLightTheme(): boolean {
    return this.currentTheme === 'light';
  }

  /**
   * Toggle between dark and light themes
   */
  toggleTheme(): void {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  }

  /**
   * Set specific theme
   */
  setTheme(theme: Theme): void {
    this.currentTheme = theme;
    this.applyTheme(theme);
    
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem(this.THEME_KEY, theme);
    }
  }

  /**
   * Apply theme to document
   */
  private applyTheme(theme: Theme): void {
    if (isPlatformBrowser(this.platformId)) {
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.classList.remove('dark-theme', 'light-theme');
      document.documentElement.classList.add(`${theme}-theme`);
      
      // Update meta theme-color for mobile browsers
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        const color = theme === 'dark' ? '#0a0a0a' : '#f5f5f5';
        metaThemeColor.setAttribute('content', color);
      }
    }
  }

  /**
   * Get theme color variables
   */
  getThemeColors(): { [key: string]: string } {
    return this.currentTheme === 'dark' ? darkThemeColors : lightThemeColors;
  }
}

// Dark theme colors (terminal theme)
const darkThemeColors = {
  '--background-primary': '#0a0a0a',
  '--background-secondary': '#111111',
  '--background-tertiary': '#1a1a1a',
  '--text-primary': '#00ff00',
  '--text-secondary': '#00cc00',
  '--text-accent': '#00ffcc',
  '--border-primary': '#00ff00',
  '--border-secondary': '#333333',
  '--accent-primary': '#00ff00',
  '--accent-secondary': '#00aaff',
  '--accent-warning': '#ffaa00',
  '--accent-error': '#ff5555',
  '--accent-success': '#00ffaa',
  '--scrollbar-track': '#1a1a1a',
  '--scrollbar-thumb': '#00ff00',
  '--scrollbar-thumb-hover': '#00cc00',
  '--button-background': '#003300',
  '--button-hover': '#005500',
  '--card-background': '#111111',
  '--card-shadow': 'rgba(0, 255, 0, 0.1)',
  '--input-background': '#000000',
  '--input-border': '#333333',
  '--input-focus': '#00ff00',
};

// Light theme colors
const lightThemeColors = {
  '--background-primary': '#f5f5f5',
  '--background-secondary': '#ffffff',
  '--background-tertiary': '#e0e0e0',
  '--text-primary': '#006400',
  '--text-secondary': '#008000',
  '--text-accent': '#008080',
  '--border-primary': '#006400',
  '--border-secondary': '#cccccc',
  '--accent-primary': '#006400',
  '--accent-secondary': '#0066cc',
  '--accent-warning': '#cc8800',
  '--accent-error': '#cc0000',
  '--accent-success': '#008055',
  '--scrollbar-track': '#e0e0e0',
  '--scrollbar-thumb': '#006400',
  '--scrollbar-thumb-hover': '#008000',
  '--button-background': '#d4edda',
  '--button-hover': '#c3e6cb',
  '--card-background': '#ffffff',
  '--card-shadow': 'rgba(0, 100, 0, 0.1)',
  '--input-background': '#ffffff',
  '--input-border': '#cccccc',
  '--input-focus': '#006400',
};