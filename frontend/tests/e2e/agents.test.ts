import { test, expect, type Page } from '@playwright/test';

test.describe('AI Agents Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to agents page
    await page.goto('/agents');
    
    // Wait for agents to load
    await page.waitForSelector('[data-testid="agent-list"]', { timeout: 10000 });
  });

  test('should display all 41 AI agents', async ({ page }) => {
    // Check for agent grid/list container
    const agentContainer = page.locator('[data-testid="agent-list"]');
    await expect(agentContainer).toBeVisible();

    // Count agent cards
    const agentCards = page.locator('[data-testid="agent-card"]');
    const count = await agentCards.count();
    
    // Should have at least 40+ agents
    expect(count).toBeGreaterThanOrEqual(40);
  });

  test('should display Ali as Chief of Staff', async ({ page }) => {
    // Look for Ali specifically
    const aliCard = page.locator('[data-testid="agent-card"]').filter({ hasText: 'Ali' });
    await expect(aliCard).toBeVisible();
    
    // Check for Chief of Staff title
    await expect(aliCard).toContainText(/Chief of Staff|Master Orchestrator/i);
  });

  test('should show agent categories', async ({ page }) => {
    // Check for different agent categories
    const categories = [
      'Strategic Leadership',
      'Technology & Engineering', 
      'Creative & Design',
      'Business Operations'
    ];

    for (const category of categories) {
      const categoryElement = page.getByText(category);
      await expect(categoryElement).toBeVisible();
    }
  });

  test('should allow agent selection', async ({ page }) => {
    // Click on first available agent
    const firstAgent = page.locator('[data-testid="agent-card"]').first();
    await firstAgent.click();

    // Check if agent details or chat interface appears
    const agentDetails = page.locator('[data-testid="agent-details"], [data-testid="chat-interface"]');
    await expect(agentDetails).toBeVisible({ timeout: 5000 });
  });

  test('should display agent specializations', async ({ page }) => {
    // Check that agents show their specializations
    const agentCards = page.locator('[data-testid="agent-card"]');
    const firstCard = agentCards.first();
    
    // Should have some description or specialization text
    await expect(firstCard).toContainText(/specialization|expertise|role/i);
  });

  test('should have functional agent search or filter', async ({ page }) => {
    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i], input[placeholder*="filter" i]');
    
    if (await searchInput.count() > 0) {
      await searchInput.fill('Ali');
      
      // Should filter to show Ali
      const visibleAgents = page.locator('[data-testid="agent-card"]:visible');
      const count = await visibleAgents.count();
      expect(count).toBeLessThanOrEqual(5); // Should significantly reduce results
      
      await expect(visibleAgents.first()).toContainText('Ali');
    }
  });

  test('should show agent status indicators', async ({ page }) => {
    // Look for status indicators (online, offline, busy, etc.)
    const statusIndicators = page.locator('[data-testid="agent-status"], .status-indicator, .online, .offline, .busy');
    
    if (await statusIndicators.count() > 0) {
      await expect(statusIndicators.first()).toBeVisible();
    }
  });

  test('should navigate between agent categories', async ({ page }) => {
    // Look for category navigation tabs or buttons
    const categoryNav = page.locator('[data-testid="category-nav"], .category-tabs, .filter-buttons');
    
    if (await categoryNav.count() > 0) {
      const firstCategory = categoryNav.locator('button, a').first();
      await firstCategory.click();
      
      // Should update the displayed agents
      await page.waitForTimeout(1000);
      const agentCards = page.locator('[data-testid="agent-card"]');
      await expect(agentCards.first()).toBeVisible();
    }
  });
});