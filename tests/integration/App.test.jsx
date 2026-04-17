import React from 'react'
import { describe, expect, it } from 'vitest'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import App from '../../src/App'
import { AuthContext } from '../../src/utils/AuthContext'
import { CourseContext } from '../../src/utils/CourseContext'

describe('App shell', () => {
  it('renders the home page, navigates to major, and toggles theme', async () => {
    localStorage.clear()

    render(
      <AuthContext.Provider value={{ user: null, authLoading: false }}>
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
          <MemoryRouter initialEntries={['/']}>
            <App />
          </MemoryRouter>
        </CourseContext.Provider>
      </AuthContext.Provider>
    )

    expect(screen.getByText('Welcome to MajorMap')).toBeInTheDocument()

    await userEvent.click(screen.getByText('Get Started'))
    expect(screen.getByText('Select Completed Courses')).toBeInTheDocument()

    await userEvent.click(document.querySelector('.toggle-icon'))
    expect(localStorage.getItem('current_theme')).toBe('dark')
  })
})
