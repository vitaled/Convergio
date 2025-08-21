/**
 * 🎨 Theme Store - Sistema di gestione temi dinamico
 * Gestisce light/dark mode con persistenza localStorage
 */

import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'system';

// Store per il tema corrente
export const theme = writable<Theme>('system');

// Store per il tema effettivo applicato (resolved da 'system')
export const resolvedTheme = writable<'light' | 'dark'>('light');

/**
 * Inizializza il sistema temi
 */
export function initializeTheme() {
  if (!browser) return;

  // Carica tema salvato o default a 'system'
  const savedTheme = localStorage.getItem('theme') as Theme || 'system';
  theme.set(savedTheme);
  
  // Applica tema iniziale
  applyTheme(savedTheme);
  
  // Ascolta cambiamenti preferenze sistema
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', handleSystemThemeChange);
  
  // Ascolta cambiamenti store tema
  theme.subscribe(handleThemeChange);
}

/**
 * Applica il tema al DOM
 */
function applyTheme(newTheme: Theme) {
  if (!browser) return;
  
  const isDark = resolveTheme(newTheme);
  const root = document.documentElement;
  
  if (isDark) {
    root.classList.add('dark');
    resolvedTheme.set('dark');
  } else {
    root.classList.remove('dark');
    resolvedTheme.set('light');
  }
  
  // Aggiorna meta theme-color per mobile
  updateMetaThemeColor(isDark);
}

/**
 * Risolve il tema effettivo da applicare
 */
function resolveTheme(themeValue: Theme): boolean {
  if (themeValue === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return themeValue === 'dark';
}

/**
 * Gestisce cambiamenti nelle preferenze di sistema
 */
function handleSystemThemeChange() {
  theme.subscribe(currentTheme => {
    if (currentTheme === 'system') {
      applyTheme('system');
    }
  })();
}

/**
 * Gestisce cambiamenti nel store tema
 */
function handleThemeChange(newTheme: Theme) {
  if (!browser) return;
  
  localStorage.setItem('theme', newTheme);
  applyTheme(newTheme);
}

/**
 * Aggiorna meta theme-color per dispositivi mobili
 */
function updateMetaThemeColor(isDark: boolean) {
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  const color = isDark ? '#0f172a' : '#ffffff';
  
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', color);
  } else {
    const meta = document.createElement('meta');
    meta.name = 'theme-color';
    meta.content = color;
    document.head.appendChild(meta);
  }
}

/**
 * Utility functions per l'uso nei componenti
 */
export const themeUtils = {
  /**
   * Cambia tema
   */
  setTheme(newTheme: Theme) {
    theme.set(newTheme);
  },
  
  /**
   * Toggle tra light e dark
   */
  toggleTheme() {
    theme.subscribe(current => {
      if (current === 'system') {
        const systemIsDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        theme.set(systemIsDark ? 'light' : 'dark');
      } else {
        theme.set(current === 'light' ? 'dark' : 'light');
      }
    })();
  },
  
  /**
   * Cicla tra tutti i temi
   */
  cycleTheme() {
    // Get current value without subscribing
    const currentTheme = get(theme);
    const themes: Theme[] = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    this.setTheme(themes[nextIndex]);
  },
  
  /**
   * Controlla se il tema corrente è dark
   */
  isDark(): boolean {
    let isDark = false;
    resolvedTheme.subscribe(resolved => {
      isDark = resolved === 'dark';
    })();
    return isDark;
  }
};

// Auto-inizializzazione se in browser
if (browser) {
  initializeTheme();
}