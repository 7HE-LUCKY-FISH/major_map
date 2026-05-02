import React, { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Schedules from '../../src/components/Pages/Schedules'
import { CourseContext } from '../../src/utils/CourseContext'
import { generateScheduleV2 } from '../../src/api/api'

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

function StatefulScheduleHarness({ roadmap, initialScheduleState, onSetScheduleState = () => {} }) {
  const [scheduleState, setScheduleState] = useState(initialScheduleState)
  const trackedSetScheduleState = (value) => {
    onSetScheduleState(value)
    setScheduleState((prev) => (typeof value === 'function' ? value(prev) : value))
  }

  return (
    <CourseContext.Provider
      value={{
        roadmap,
        scheduleState,
        setScheduleState: trackedSetScheduleState,
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
      screen.getByText(/In order to generate a predictive schedule/i)
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

  it('fetches schedules when cached data is missing and renders schedule events', async () => {
    vi.mocked(generateScheduleV2).mockResolvedValue({
      schedules: [
        {
          sections: [
            {
              course_number: 'CS 146',
              slot_label: 'MW 10:30AM-11:45AM',
              instructor_name: 'Aamina Ahmad',
            },
            {
              course: 'MATH 30',
              slot_label: 'TR 1:30PM-2:45PM',
              instructor_name: '',
            },
            {
              course_number: 'ENGR 10',
              slot_label: 'TBA',
              instructor_name: 'Ignored Instructor',
            },
          ],
        },
      ],
      professor_frequencies: {
        'CS 146': [
          {
            instructor_name: 'Aamina Ahmad',
            teach_count: 8,
            probability: 0.8,
          },
        ],
      },
    })

    const setScheduleState = vi.fn()

    render(
      <StatefulScheduleHarness
        roadmap={[[{ course: 'CS146' }, { course: 'MATH30' }]]}
        initialScheduleState={{
          courseCodes: [],
          schedules: [],
          professorFreqs: {},
          selectedScheduleIndex: 3,
        }}
        onSetScheduleState={setScheduleState}
      />
    )

    expect(await screen.findByText('Historical Professor Frequencies')).toBeInTheDocument()
    expect(generateScheduleV2).toHaveBeenCalledWith({ courses: ['CS 146', 'MATH 30'] })
    expect(setScheduleState).toHaveBeenCalledWith({
      courseCodes: ['CS 146', 'MATH 30'],
      schedules: [
        {
          sections: [
            {
              course_number: 'CS 146',
              slot_label: 'MW 10:30AM-11:45AM',
              instructor_name: 'Aamina Ahmad',
            },
            {
              course: 'MATH 30',
              slot_label: 'TR 1:30PM-2:45PM',
              instructor_name: '',
            },
            {
              course_number: 'ENGR 10',
              slot_label: 'TBA',
              instructor_name: 'Ignored Instructor',
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
    })

    screen.getAllByRole('link', { name: 'CS 146' }).forEach((link) => {
      expect(link).toHaveAttribute('href', expect.stringContaining('CS+146'))
    })
    expect(screen.getAllByText('Unknown Instructor')[0]).toBeInTheDocument()
    expect(screen.queryByText('Ignored Instructor')).not.toBeInTheDocument()
    expect(screen.getAllByText('10:30am - 11:45am')).toHaveLength(2)
    expect(screen.getAllByText('1:30pm - 2:45pm')).toHaveLength(2)
  })

  it('shows an API error and clears cached state when generation fails', async () => {
    vi.mocked(generateScheduleV2).mockRejectedValue(new Error('Backend unavailable'))

    const setScheduleState = vi.fn()

    renderSchedules({
      roadmap: [[{ course: 'CS146' }]],
      scheduleState: {
        courseCodes: [],
        schedules: [],
        professorFreqs: {},
        selectedScheduleIndex: 0,
      },
      setScheduleState,
      plannerLoading: false,
    })

    expect(await screen.findByText('Backend unavailable')).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.queryByText('Generating schedules...')).not.toBeInTheDocument()
    )
    expect(setScheduleState).toHaveBeenCalledWith({
      courseCodes: ['CS 146'],
      schedules: [],
      professorFreqs: {},
      selectedScheduleIndex: 0,
    })
  })

  it('shows the empty schedule state when generation succeeds with no valid options', async () => {
    vi.mocked(generateScheduleV2).mockResolvedValue({
      schedules: [],
      professor_frequencies: {},
    })

    renderSchedules({
      roadmap: [[{ course: 'CS146' }]],
      scheduleState: {
        courseCodes: [],
        schedules: [],
        professorFreqs: {},
        selectedScheduleIndex: 0,
      },
      setScheduleState: vi.fn(),
      plannerLoading: false,
    })

    expect(await screen.findByText('No Valid Schedules')).toBeInTheDocument()
  })

  it('persists schedule selection changes back into cached planner state', async () => {
    const setScheduleState = vi.fn()

    renderSchedules({
      roadmap: [[{ course: 'CS146' }]],
      scheduleState: {
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
                course_number: 'CS 146',
                slot_label: 'TR 2:00PM-3:15PM',
                instructor_name: 'Second Instructor',
              },
            ],
          },
        ],
        professorFreqs: {},
        selectedScheduleIndex: 0,
      },
      setScheduleState,
      plannerLoading: false,
    })

    const scheduleSelect = screen.getByLabelText('Schedule option')
    await userEvent.selectOptions(scheduleSelect, '1')

    await waitFor(() =>
      expect(setScheduleState).toHaveBeenLastCalledWith(expect.any(Function))
    )

    const updater = setScheduleState.mock.calls.at(-1)[0]
    expect(
      updater({
        courseCodes: ['CS 146'],
        schedules: [],
        professorFreqs: {},
        selectedScheduleIndex: 0,
      })
    ).toEqual({
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
              course_number: 'CS 146',
              slot_label: 'TR 2:00PM-3:15PM',
              instructor_name: 'Second Instructor',
            },
          ],
        },
      ],
      professorFreqs: {},
      selectedScheduleIndex: 1,
    })
  })
})
