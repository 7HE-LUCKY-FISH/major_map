import React, { useState } from 'react'
import { describe, expect, it } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Major from '../../src/components/Pages/Major'
import Roadmap from '../../src/components/Pages/Roadmap'
import { CourseContext } from '../../src/utils/CourseContext'

function PlannerHarness() {
  const [completedCourses, setCompletedCourses] = useState([])
  const [selectedMajor, setSelectedMajor] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [roadmap, setRoadmap] = useState([])
  const [scheduleState, setScheduleState] = useState({
    courseCodes: [],
    schedules: [],
    professorFreqs: {},
    selectedScheduleIndex: 0,
  })

  return (
    <CourseContext.Provider
      value={{
        completedCourses,
        setCompletedCourses,
        selectedMajor,
        setSelectedMajor,
        submitted,
        setSubmitted,
        roadmap,
        setRoadmap,
        scheduleState,
        setScheduleState,
        plannerLoading: false,
      }}
    >
      <Routes>
        <Route path="/major" element={<Major />} />
        <Route path="/roadmap" element={<Roadmap />} />
      </Routes>
    </CourseContext.Provider>
  )
}

describe('planner pages', () => {
  it('lets the user choose a major and generate a roadmap', async () => {
    render(
      <MemoryRouter initialEntries={['/major']}>
        <PlannerHarness />
      </MemoryRouter>
    )

    await userEvent.selectOptions(screen.getByRole('combobox'), 'CS')
    expect(await screen.findByText('CS46A')).toBeInTheDocument()

    const courseCheckbox = screen.getAllByRole('checkbox')[0]
    await userEvent.click(courseCheckbox)
    expect(courseCheckbox).toBeChecked()

    await userEvent.click(screen.getByText('Generate Roadmap'))

    await waitFor(() =>
      expect(screen.getByText('Your Personalized Roadmap')).toBeInTheDocument()
    )
    expect(screen.getByText('CS46B')).toBeInTheDocument()
  })

  it('shows a warning when roadmap is opened without a submitted plan', () => {
    render(
      <MemoryRouter initialEntries={['/roadmap']}>
        <CourseContext.Provider
          value={{
            completedCourses: [],
            setCompletedCourses: vi.fn(),
            selectedMajor: '',
            setSelectedMajor: vi.fn(),
            submitted: false,
            setSubmitted: vi.fn(),
            roadmap: [],
            setRoadmap: vi.fn(),
            scheduleState: {
              courseCodes: [],
              schedules: [],
              professorFreqs: {},
              selectedScheduleIndex: 0,
            },
            setScheduleState: vi.fn(),
            plannerLoading: false,
          }}
        >
          <Routes>
            <Route path="/roadmap" element={<Roadmap />} />
          </Routes>
        </CourseContext.Provider>
      </MemoryRouter>
    )

    expect(
      screen.getByText(/Please select completed courses first/i)
    ).toBeInTheDocument()
  })
})
