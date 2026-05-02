import { test, expect } from '@playwright/test'

test('guest user can build a roadmap and use search', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByText('Welcome to MajorMap')).toBeVisible()
  await page.getByRole('button', { name: 'Get Started' }).click()

  await expect(page).toHaveURL(/\/major$/)
  await page.getByRole('combobox').selectOption('CS')
  await expect(page.locator('.course-card .course-code', { hasText: 'CS46A' })).toBeVisible()

  const generateRoadmapButton = page.getByRole('button', { name: 'Generate Roadmap' })
  await generateRoadmapButton.evaluate((button) => button.click())
  await expect(page).toHaveURL(/\/roadmap$/)
  await expect(page.getByText('Your Personalized Roadmap')).toBeVisible()

  await page.goto('/search')
  await page.getByPlaceholder('Search course...').fill('cs')
  await expect(page.locator('.table-row').first()).toBeVisible()
})
