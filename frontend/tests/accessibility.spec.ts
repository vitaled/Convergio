/**
 * Accessibility Tests for Operational UX Components (M4)
 * Tests a11y compliance for Timeline and RunPanel components
 * Target: A11y ≥95%
 */

import { test, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { describe, it, beforeEach } from 'vitest';
import OperationalUX from '../src/routes/(app)/operational-ux/+page.svelte';

describe('Accessibility Tests - Operational UX', () => {
  beforeEach(() => {
    // Reset DOM before each test
    document.body.innerHTML = '';
  });

  describe('Overall Page Accessibility', () => {
    it('should have proper page title and heading structure', () => {
      render(OperationalUX);
      
      // Check main heading (h1)
      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toBeDefined();
      
      // Check heading hierarchy
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      expect(headings.length).toBeGreaterThan(3);
      
      // First heading should be h1
      const firstHeading = headings[0];
      expect(firstHeading.tagName.toLowerCase()).toBe('h1');
    });

    it('should have proper language declaration', () => {
      render(OperationalUX);
      
      // Check HTML lang attribute
      const htmlElement = document.querySelector('html');
      expect(htmlElement?.getAttribute('lang')).toBe('en');
    });

    it('should have proper viewport meta tag', () => {
      render(OperationalUX);
      
      // Check viewport meta tag for responsive design
      const viewportMeta = document.querySelector('meta[name="viewport"]');
      expect(viewportMeta).toBeDefined();
    });
  });

  describe('Timeline Component Accessibility', () => {
    it('should have proper form labels and associations', () => {
      render(OperationalUX);
      
      // Check conversation selector
      const conversationSelect = document.querySelector('#conversation-select');
      expect(conversationSelect).toBeDefined();
      
      // Check label association
      const label = document.querySelector('label[for="conversation-select"]');
      expect(label).toBeDefined();
      expect(label?.textContent).toContain('Test Conversation:');
    });

    it('should have proper button accessibility', () => {
      render(OperationalUX);
      
      // Check refresh buttons
      const refreshButtons = document.querySelectorAll('.btn-refresh');
      expect(refreshButtons.length).toBeGreaterThan(0);
      
      // Check aria-label
      const firstRefreshButton = refreshButtons[0];
      expect(firstRefreshButton?.getAttribute('aria-label')).toBe('Refresh timeline');
      
      // Check button type
      expect(firstRefreshButton?.getAttribute('type')).toBe('button');
    });

    it('should have proper list semantics', () => {
      render(OperationalUX);
      
      // Check that timeline content is present
      const timelineContent = document.querySelector('.timeline-content');
      expect(timelineContent).toBeDefined();
      
      // Check for proper list structure
      const timelineList = document.querySelector('.timeline-content ul, .timeline-content ol');
      if (timelineList) {
        expect(timelineList).toBeDefined();
      }
    });

    it('should support keyboard navigation', () => {
      render(OperationalUX);
      
      // Check that focusable elements are present
      const focusableElements = document.querySelectorAll('button, select, input, a, [tabindex]');
      expect(focusableElements.length).toBeGreaterThan(0);
      
      // Check that first focusable element can be focused
      const firstFocusable = focusableElements[0] as HTMLElement;
      firstFocusable.focus();
      expect(document.activeElement).toBe(firstFocusable);
    });
  });

  describe('RunPanel Component Accessibility', () => {
    it('should have proper card structure', () => {
      render(OperationalUX);
      
      // Check that metric cards are present
      const metricCards = document.querySelectorAll('.metric-card');
      expect(metricCards.length).toBeGreaterThan(0);
      
      // Each card should have a proper heading
      metricCards.forEach(card => {
        const cardTitle = card.querySelector('.card-title');
        expect(cardTitle).toBeDefined();
        
        // Check that card title is a proper heading
        const tagName = cardTitle?.tagName.toLowerCase();
        expect(['h2', 'h3', 'h4']).toContain(tagName);
      });
    });

    it('should have proper checkbox accessibility', () => {
      render(OperationalUX);
      
      // Check advanced metrics checkbox
      const advancedCheckbox = document.querySelector('input[type="checkbox"]');
      expect(advancedCheckbox).toBeDefined();
      
      // Check label association
      const checkboxLabel = document.querySelector('label');
      expect(checkboxLabel).toBeDefined();
      expect(checkboxLabel?.textContent).toContain('Show Advanced Metrics');
    });

    it('should have proper status indicators', () => {
      render(OperationalUX);
      
      // Check telemetry status section
      const telemetryStatus = document.querySelector('.telemetry-status');
      expect(telemetryStatus).toBeDefined();
      
      // Check status value
      const statusValue = document.querySelector('.status-value');
      expect(statusValue).toBeDefined();
    });
  });

  describe('Interactive Elements Accessibility', () => {
    it('should have proper button states', () => {
      render(OperationalUX);
      
      // Check refresh buttons
      const refreshButtons = document.querySelectorAll('.btn-refresh');
      expect(refreshButtons.length).toBeGreaterThan(0);
      
             refreshButtons.forEach(button => {
         // Check that button is not disabled by default
         expect(button?.getAttribute('disabled')).toBeNull();
         
         // Check aria-label
         expect(button?.getAttribute('aria-label')).toBeTruthy();
       });
    });

    it('should have proper focus indicators', () => {
      render(OperationalUX);
      
      // Check that focusable elements have visible focus indicators
      const focusableElements = document.querySelectorAll('button, select, input, a, [tabindex]');
      
             const elementsToTest = Array.from(focusableElements).slice(0, 5);
       elementsToTest.forEach(element => {
         const htmlElement = element as HTMLElement;
         htmlElement.focus();
         
         // Check for focus indicator (outline, border, or box-shadow)
         const computedStyle = window.getComputedStyle(htmlElement);
         const hasFocusIndicator = 
           computedStyle.outline !== 'none' ||
           computedStyle.border !== 'none' ||
           computedStyle.boxShadow !== 'none';
         
         // At least one focus indicator should be present
         expect(hasFocusIndicator).toBe(true);
       });
    });
  });

  describe('Screen Reader Support', () => {
    it('should have proper heading structure for screen readers', () => {
      render(OperationalUX);
      
      // Check heading hierarchy
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      
      if (headings.length > 0) {
        const headingLevels = [];
        
        for (let i = 0; i < headings.length; i++) {
          const heading = headings[i];
          const tagName = heading.tagName.toLowerCase();
          const level = parseInt(tagName.charAt(1));
          headingLevels.push(level);
        }
        
        // Check that headings don't skip levels (e.g., h1 -> h3)
        for (let i = 1; i < headingLevels.length; i++) {
          const currentLevel = headingLevels[i];
          const previousLevel = headingLevels[i - 1];
          expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
        }
      }
    });

    it('should have proper ARIA attributes', () => {
      render(OperationalUX);
      
             // Check for aria-label attributes on interactive elements
       const elementsWithAriaLabel = document.querySelectorAll('[aria-label]');
       expect(elementsWithAriaLabel.length).toBeGreaterThan(0);
       
       // Check for proper button roles
       const buttons = document.querySelectorAll('button, [role="button"]');
       buttons.forEach(button => {
         expect(button?.getAttribute('aria-label')).toBeTruthy();
       });
    });
  });

  describe('Mobile Accessibility', () => {
    it('should have proper touch target sizes', () => {
      render(OperationalUX);
      
      // Check touch target sizes (minimum 44x44px for accessibility)
      const interactiveElements = document.querySelectorAll('button, select, input, a, [tabindex]');
      
      for (let i = 0; i < Math.min(interactiveElements.length, 10); i++) {
        const element = interactiveElements[i] as HTMLElement;
        const boundingBox = element.getBoundingClientRect();
        
        // Check minimum touch target size
        expect(boundingBox.width).toBeGreaterThanOrEqual(44);
        expect(boundingBox.height).toBeGreaterThanOrEqual(44);
      }
    });
  });

  describe('Performance and Accessibility', () => {
    it('should load within accessibility time limits', () => {
      const startTime = performance.now();
      
      // Render component
      render(OperationalUX);
      
      const loadTime = performance.now() - startTime;
      
      // Component should render within 100ms for accessibility
      expect(loadTime).toBeLessThan(100);
    });

    it('should maintain accessibility during data loading', () => {
      render(OperationalUX);
      
      // Check loading states
      const loadingElements = document.querySelectorAll('.loading, [aria-busy="true"]');
      
             if (loadingElements.length > 0) {
         loadingElements.forEach(loadingElement => {
           // Check that loading is properly announced
           expect(loadingElement?.getAttribute('aria-busy')).toBe('true');
         });
       }
    });
  });
});
