import React, { useContext } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CourseProvider } from '../../src/utils/CourseContext.jsx'
import { CourseContext } from '../../src/utils/CourseContext'
import { AuthContext } from '../../src/utils/AuthContext'

vi.mock('../../src/api/api.js', () => ({
  getPlannerState: vi.fn(),
  updatePlannerState: vi.fn(),
}))

import { getPlannerState, updatePlannerState } from '../../src/api/api.js'

function Consumer() {
  const planner = useContext(CourseContext)

  return (
    <div>
      <div data-testid="major">{planner.selectedMajor || 'none'}</div>
      <div data-testid="submitted">{String(planner.submitted)}</div>
      <button onClick={() => planner.setSelectedMajor('CS')}>set major</button>
      <button onClick={() => planner.setSubmitted(true)}>submit</button>
      <button onClick={() => planner.setRoadmap([[{ course: 'CS46A' }]])}>roadmap</button>
    </div>
  )
}

function renderWithAuth(authValue) {
  return render(
    <AuthContext.Provider value={authValue}>
      <CourseProvider>
        <Consumer />
      </CourseProvider>
    </AuthContext.Provider>
  )
}

describe('CourseProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('loads and saves guest planner state in localStorage', async () => {
    localStorage.setItem(
      'guestPlannerState',
      JSON.stringify({
        major: {
          completedCourses: [],
          selectedMajor: 'SE',
          submitted: false,
        },
        roadmap: [],
        schedule: {
          courseCodes: [],
          schedules: [],
          professorFreqs: {},
          selectedScheduleIndex: 0,
        },
      })
    )

    renderWithAuth({
      user: null,
      authLoading: false,
    })

    await waitFor(() =>
      expect(screen.getByTestId('major')).toHaveTextContent('SE')
    )

    await userEvent.click(screen.getByText('set major'))

    await waitFor(() =>
      expect(JSON.parse(localStorage.getItem('guestPlannerState')).major.selectedMajor).toBe('CS')
    )
  })

  it('loads authenticated planner state and debounces remote saves', async () => {
    getPlannerState.mockResolvedValue({
      major: {
        completedCourses: [],
        selectedMajor: 'EE',
        submitted: false,
      },
      roadmap: [],
      schedule: {
        courseCodes: [],
        schedules: [],
        professorFreqs: {},
        selectedScheduleIndex: 0,
      },
    })
    updatePlannerState.mockResolvedValue({ ok: true })

    renderWithAuth({
      user: { user_id: 7, username: 'sam' },
      authLoading: false,
    })

    await waitFor(() =>
      expect(screen.getByTestId('major')).toHaveTextContent('EE')
    )

    await userEvent.click(screen.getByText('submit'))
    await userEvent.click(screen.getByText('roadmap'))

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 350))
    })

    await waitFor(() => expect(updatePlannerState).toHaveBeenCalled())
    expect(getPlannerState).toHaveBeenCalled()
  })
})
