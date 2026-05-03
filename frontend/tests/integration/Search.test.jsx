import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Search from '../../src/components/Pages/Search'

vi.mock('../../src/utils/CSVparser', () => ({
  loadCSV: vi.fn(),
}))

import { loadCSV } from '../../src/utils/CSVparser'

const baseRows = [
  {
    Semester: 'Fall',
    Year: '2025',
    Section: 'CS46A-01',
    Days: 'MW',
    Times: '10:30AM-11:45AM',
    Unit: '3',
    Instructor: 'Aamina Ahmad',
  },
  {
    Semester: 'Spring',
    Year: '2025',
    Section: 'CS146-02',
    Days: 'TR',
    Times: '9:00AM-10:15AM',
    Unit: '3',
    Instructor: 'Unknown Person',
  },
]

describe('Search page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads CSV data and searches by course', async () => {
    loadCSV.mockResolvedValue(baseRows)

    render(<Search />)

    await waitFor(() => expect(loadCSV).toHaveBeenCalled())

    await userEvent.type(screen.getByPlaceholderText('Search course...'), 'cs46')

    expect(await screen.findByText('CS46A-01')).toBeInTheDocument()
    expect(screen.getByText('View Reviews')).toHaveAttribute(
      'href',
      expect.stringContaining('ratemyprofessors.com')
    )
  })

  it('switches to instructor mode and shows the no-reviews fallback', async () => {
    loadCSV.mockResolvedValue(baseRows)

    render(<Search />)

    await waitFor(() => expect(loadCSV).toHaveBeenCalled())

    await userEvent.click(screen.getByRole('checkbox'))
    await userEvent.type(screen.getByPlaceholderText('Search instructor...'), 'unknown')

    expect(await screen.findByText('Unknown Person')).toBeInTheDocument()
    expect(screen.getByText('No Reviews')).toBeInTheDocument()
  })

  it('shows the result limit warning when more than 200 matches exist', async () => {
    loadCSV.mockResolvedValue(
      Array.from({ length: 210 }, (_, index) => ({
        ...baseRows[0],
        Section: `CS46A-${index}`,
        Instructor: `Aamina Ahmad ${index}`,
      }))
    )

    render(<Search />)

    await waitFor(() => expect(loadCSV).toHaveBeenCalled())
    await userEvent.type(screen.getByPlaceholderText('Search course...'), 'cs')

    expect(await screen.findByText(/Showing first 200 results/i)).toBeInTheDocument()
  })
})
