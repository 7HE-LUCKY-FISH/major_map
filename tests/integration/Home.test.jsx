import React from 'react'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import Home from '../../src/components/Pages/Home'

const getLogoSources = () => [
  screen.getByAltText('Semester planning logo').getAttribute('src'),
  screen.getByAltText('Roadmap logo').getAttribute('src'),
  screen.getByAltText('Graduation logo').getAttribute('src'),
]

describe('Home page', () => {
  it('renders light theme logos by default and dark theme logos when theme is dark', () => {
    const { rerender } = render(
      <MemoryRouter>
        <Home theme="light" />
      </MemoryRouter>
    )

    const lightSources = getLogoSources()
    lightSources.forEach((src) => {
      expect(src).toMatch(/Light/i)
    })

    rerender(
      <MemoryRouter>
        <Home theme="dark" />
      </MemoryRouter>
    )

    const darkSources = getLogoSources()
    darkSources.forEach((src) => {
      expect(src).toMatch(/Dark/i)
    })
  })
})
