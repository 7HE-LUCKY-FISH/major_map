import React, { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Major from '../../src/components/Pages/Major'
import { CourseContext } from '../../src/utils/CourseContext'

function MajorHarness({
  initialCompletedCourses = [],
  initialSelectedMajor = '',
  initialPreferredUnits = 15,
  plannerLoading = false,
  initialRoadmap = ['stale roadmap'],
  initialScheduleState = {
    courseCodes: ['OLD 101'],
    schedules: [{ sections: [] }],
    professorFreqs: { old: [] },
    selectedScheduleIndex: 2,
  },
}) {
  const [completedCourses, setCompletedCourses] = useState(initialCompletedCourses)
  const [selectedMajor, setSelectedMajor] = useState(initialSelectedMajor)
  const [submitted, setSubmitted] = useState(true)
  const [roadmap, setRoadmap] = useState(initialRoadmap)
  const [scheduleState, setScheduleState] = useState(initialScheduleState)
  const [preferredUnits, setPreferredUnits] = useState(initialPreferredUnits) 

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
        plannerLoading,
        setPreferredUnits,
        preferredUnits,
      }}
    >
      <Routes>
        <Route path="/" element={<Major />} />
        <Route path="/roadmap" element={<div>Your Personalized Roadmap</div>} />
      </Routes>
      <div data-testid="completed-courses">{completedCourses.join(',')}</div>
      <div data-testid="selected-major">{selectedMajor}</div>
      <div data-testid="submitted">{String(submitted)}</div>
      <div data-testid="roadmap">{JSON.stringify(roadmap)}</div>
      <div data-testid="schedule-state">{JSON.stringify(scheduleState)}</div>
      <div data-testid="preferred-units">{preferredUnits}</div>
    </CourseContext.Provider>
  )
}

describe('Major page', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('renders the planner loading state', () => {
    render(
      <MemoryRouter>
        <MajorHarness plannerLoading />
      </MemoryRouter>
    )

    expect(screen.getByText('Loading your planner...')).toBeInTheDocument()
  })

  it('loads saved courses for a selected major, filters invalid selections, and submits the roadmap', async () => {
    localStorage.setItem('completed_CMPE', JSON.stringify(['PHYS50', 'EE98', 'CMPE30']))

    render(
      <MemoryRouter>
        <MajorHarness />
      </MemoryRouter>
    )

    const majorSelect = screen.getByRole('combobox')
    await userEvent.selectOptions(majorSelect, 'CMPE')

    await waitFor(() =>
      expect(screen.getByTestId('selected-major')).toHaveTextContent('CMPE')
    )

    await waitFor(() =>
      expect(screen.getByTestId('completed-courses')).toHaveTextContent('PHYS50,CMPE30')
    )
    expect(screen.getByLabelText(/^EE98$/i)).toBeDisabled()
    expect(screen.getByLabelText(/^CMPE50$/i)).not.toBeDisabled()

    await userEvent.click(screen.getByLabelText(/^CMPE50$/i))
    expect(screen.getByTestId('completed-courses')).toHaveTextContent('PHYS50,CMPE30,CMPE50')

    await userEvent.click(screen.getByText('Generate Roadmap'))
    expect(await screen.findByText('Your Personalized Roadmap')).toBeInTheDocument()
  })

  it('clears selections only after confirmation and resets planner state when the major is cleared', async () => {
    const confirmSpy = vi
      .spyOn(window, 'confirm')
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
    localStorage.setItem('completed_CS', JSON.stringify(['CS46A', 'MATH30']))

    render(
      <MemoryRouter>
        <MajorHarness initialSelectedMajor="CS" initialCompletedCourses={['CS46A', 'MATH30']} />
      </MemoryRouter>
    )

    await waitFor(() =>
      expect(screen.getByTestId('completed-courses')).toHaveTextContent('CS46A,MATH30')
    )

    await userEvent.click(screen.getByText('Clear Selections'))
    expect(confirmSpy).toHaveBeenCalledWith(
      'Are you sure you want to clear all selections for Computer Science?'
    )
    expect(screen.getByTestId('completed-courses')).toHaveTextContent('CS46A,MATH30')

    await userEvent.click(screen.getByText('Clear Selections'))
    await waitFor(() =>
      expect(screen.getByTestId('completed-courses')).toHaveTextContent('')
    )

    await userEvent.selectOptions(screen.getByRole('combobox'), '')

    await waitFor(() => {
      expect(screen.getByTestId('selected-major')).toHaveTextContent('')
      expect(screen.getByTestId('submitted')).toHaveTextContent('false')
      expect(screen.getByTestId('roadmap')).toHaveTextContent('[]')
      expect(screen.getByTestId('schedule-state')).toHaveTextContent(
        JSON.stringify({
          courseCodes: [],
          schedules: [],
          professorFreqs: {},
          selectedScheduleIndex: 0,
        })
      )
    })
  })
  it('allows users to update their target unit cap', async () => {
    render(
      <MemoryRouter>
        <MajorHarness />
      </MemoryRouter>
    )

    // Select major first so the unit input appears
    await userEvent.selectOptions(screen.getByRole('combobox'), 'CS')

    // Find the input, clear it, and type 18
    const unitInput = screen.getByLabelText(/Target Units per Semester/i)
    await userEvent.clear(unitInput)
    await userEvent.type(unitInput, '18')

    // Verify context updated and form reset
    expect(screen.getByTestId('preferred-units')).toHaveTextContent('18')
    expect(screen.getByTestId('submitted')).toHaveTextContent('false')
  })
})
