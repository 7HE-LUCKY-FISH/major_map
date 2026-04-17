import React, { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Schedules from '../../src/components/Pages/Schedules'
import { CourseContext } from '../../src/utils/CourseContext'

vi.mock('../../src/api/api.js', async () => {
  const actual = await vi.importActual('../../src/api/api.js')
  return {
    ...actual,
    generateScheduleV2: vi.fn(),
  }
})

function renderSchedules(courseContextValue) {
  return render(
    <CourseContext.Provider value={courseContextValue}>
      <Schedules />
    </CourseContext.Provider>
  )
}

function StatefulScheduleHarness({ roadmap, initialScheduleState }) {
  const [scheduleState, setScheduleState] = useState(initialScheduleState)

  return (
    <CourseContext.Provider
      value={{
        roadmap,
        scheduleState,
        setScheduleState,
        plannerLoading: false,
      }}
    >
      <Schedules />
    </CourseContext.Provider>
  )
}

describe('Schedules page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows a warning when there is no roadmap', () => {
    renderSchedules({
      roadmap: [],
      scheduleState: {
        courseCodes: [],
        schedules: [],
        professorFreqs: {},
        selectedScheduleIndex: 0,
      },
      setScheduleState: vi.fn(),
      plannerLoading: false,
    })

    expect(
      screen.getByText(/Please select completed courses first/i)
    ).toBeInTheDocument()
  })

  it('renders the planner loading state', () => {
    renderSchedules({
      roadmap: [],
      scheduleState: {
        courseCodes: [],
        schedules: [],
        professorFreqs: {},
        selectedScheduleIndex: 0,
      },
      setScheduleState: vi.fn(),
      plannerLoading: true,
    })

    expect(screen.getByText('Loading your schedules...')).toBeInTheDocument()
  })

  it('renders generated schedules and professor frequencies', async () => {
    render(
      <StatefulScheduleHarness
        roadmap={[[{ course: 'CS146' }]]}
        initialScheduleState={{
          courseCodes: ['CS 146'],
          schedules: [
            {
              sections: [
                {
                  course_number: 'CS 146',
                  slot_label: 'MW 10:30AM-11:45AM',
                  instructor_name: 'Aamina Ahmad',
                },
              ],
            },
            {
              sections: [
                {
                  course_number: 'MATH 30',
                  slot_label: 'TR 1:30PM-2:45PM',
                  instructor_name: 'Another Professor',
                },
              ],
            },
          ],
          professorFreqs: {
            'CS 146': [
              {
                instructor_name: 'Aamina Ahmad',
                teach_count: 8,
                probability: 0.8,
              },
            ],
          },
          selectedScheduleIndex: 0,
        }}
      />
    )

    expect(await screen.findByText('Potential Predictive Schedules')).toBeInTheDocument()
    expect(await screen.findByText('Historical Professor Frequencies')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'CS 146' })).toBeInTheDocument()

    const scheduleSelect = screen.getByLabelText('Schedule option')
    await userEvent.selectOptions(scheduleSelect, '1')
    expect(scheduleSelect).toHaveValue('1')
  })

  it('shows the empty professor-frequency state when no historical data exists', async () => {
    render(
      <StatefulScheduleHarness
        roadmap={[[{ course: 'CS146' }]]}
        initialScheduleState={{
          courseCodes: ['CS 146'],
          schedules: [
            {
              sections: [
                {
                  course_number: 'CS 146',
                  slot_label: 'MW 10:30AM-11:45AM',
                  instructor_name: 'Aamina Ahmad',
                },
              ],
            },
          ],
          professorFreqs: {
            'CS 146': [],
          },
          selectedScheduleIndex: 0,
        }}
      />
    )

    expect(await screen.findByText('No historical data.')).toBeInTheDocument()
  })
})
