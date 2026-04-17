import { describe, expect, it } from 'vitest'
import { getCourseLink } from '../../src/utils/CourseLinks'

describe('getCourseLink', () => {
  it('returns an empty string for blank input', () => {
    expect(getCourseLink('')).toBe('')
    expect(getCourseLink(null)).toBe('')
  })

  it('normalizes compact course codes into a searchable catalog URL', () => {
    const link = getCourseLink('CS46A')

    expect(link).toContain('catalog.sjsu.edu')
    expect(link).toContain('filter%5Bkeyword%5D=CS+46A')
  })

  it('preserves spaced course codes with trimmed whitespace', () => {
    const link = getCourseLink('  MATH 30 ')

    expect(link).toContain('filter%5Bkeyword%5D=MATH+30')
  })
})
