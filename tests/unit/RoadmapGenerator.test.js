import { describe, expect, it } from 'vitest'
import { RoadmapGenerator } from '../../src/utils/RoadmapGenerator'

describe('RoadmapGenerator', () => {
  it('builds a roadmap in prerequisite order', () => {
    const courses = [
      { course: 'CS46A', prerequisites: [] },
      { course: 'CS46B', prerequisites: ['CS46A'] },
      { course: 'CS146', prerequisites: ['CS46B'] },
    ]

    expect(RoadmapGenerator(courses, [])).toEqual([
      [{ course: 'CS46A', prerequisites: [] }],
      [{ course: 'CS46B', prerequisites: ['CS46A'] }],
      [{ course: 'CS146', prerequisites: ['CS46B'] }],
    ])
  })

  it('keeps corequisites together when capacity allows', () => {
    const courses = [
      { course: 'PHYS50', prerequisites: [], corequisites: ['PHYS50L'] },
      { course: 'PHYS50L', prerequisites: [], corequisites: [] },
      { course: 'MATH31', prerequisites: [], corequisites: [] },
    ]

    expect(RoadmapGenerator(courses, [])).toEqual([
      [
        { course: 'PHYS50', prerequisites: [], corequisites: ['PHYS50L'] },
        { course: 'PHYS50L', prerequisites: [], corequisites: [] },
        { course: 'MATH31', prerequisites: [], corequisites: [] },
      ],
    ])
  })

  it('stops when remaining courses are impossible to unlock', () => {
    const courses = [
      { course: 'CS146', prerequisites: ['CS46B'] },
    ]

    expect(RoadmapGenerator(courses, [])).toEqual([])
  })
})
