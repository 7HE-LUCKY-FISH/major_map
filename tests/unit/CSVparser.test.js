import { describe, expect, it, vi } from 'vitest'
import { loadCSV } from '../../src/utils/CSVparser'

describe('loadCSV', () => {
  it('fetches and parses CSV rows', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        text: vi.fn().mockResolvedValue('Section,Instructor\nCS46A,Aamina Ahmad\n'),
      })
    )

    const rows = await loadCSV('/HistoricalCourseData.csv')

    expect(fetch).toHaveBeenCalledWith('/HistoricalCourseData.csv')
    expect(rows).toEqual([
      { Section: 'CS46A', Instructor: 'Aamina Ahmad' },
    ])
  })
})
