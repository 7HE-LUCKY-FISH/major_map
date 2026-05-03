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

  it('respects the preferredUnits limit and splits semesters accordingly', () => {
    const courses = [
      { course: 'MATH1', prerequisites: [], units: 4 },
      { course: 'MATH2', prerequisites: [], units: 4 },
      { course: 'MATH3', prerequisites: [], units: 4 },
      { course: 'MATH4', prerequisites: [], units: 4 },
    ]

    // With a limit of 15, and 4-unit classes, we can only fit 3 classes (12 units) per semester.
    // The 4th class must be pushed to semester 2.
    expect(RoadmapGenerator(courses, [], 15)).toEqual([
      [
        { course: 'MATH1', prerequisites: [], units: 4 },
        { course: 'MATH2', prerequisites: [], units: 4 },
        { course: 'MATH3', prerequisites: [], units: 4 },
      ],
      [
        { course: 'MATH4', prerequisites: [], units: 4 },
      ]
    ])
  })
})
