import React, { useContext, useEffect, useMemo, useState } from 'react'
import './Schedules.css'
import { generateScheduleV2 } from '../../api/api'
import { getCourseLink } from '../../utils/CourseLinks'
import { CourseContext } from '../../utils/CourseContext'

const DAYS = [
  { key: "M", label: "Monday" },
  { key: "T", label: "Tuesday" },
  { key: "W", label: "Wednesday" },
  { key: "R", label: "Thursday" },
  { key: "F", label: "Friday" }
]

const DEFAULT_START_MIN = 7 * 60 + 30
const DEFAULT_END_MIN = 21 * 60
const TIME_STEP_MIN = 15

const COURSE_COLORS = [
  { bg: "var(--course-bg-0)", border: "var(--course-border-0)" },
  { bg: "var(--course-bg-1)", border: "var(--course-border-1)" },
  { bg: "var(--course-bg-2)", border: "var(--course-border-2)" },
  { bg: "var(--course-bg-3)", border: "var(--course-border-3)" },
  { bg: "var(--course-bg-4)", border: "var(--course-border-4)" },
  { bg: "var(--course-bg-5)", border: "var(--course-border-5)" },
  { bg: "var(--course-bg-6)", border: "var(--course-border-6)" },
]

const parseTimeToMinutes = (timeStr) => {
  if (!timeStr) return null
  const cleaned = String(timeStr).trim().toUpperCase()
  if (cleaned === "TBA") return null
  const match = cleaned.match(/^(\d{1,2}):(\d{2})\s*([AP]M)$/)
  if (!match) return null
  let hours = Number(match[1])
  const minutes = Number(match[2])
  const meridiem = match[3]
  if (meridiem === "PM" && hours !== 12) hours += 12
  if (meridiem === "AM" && hours === 12) hours = 0
  return hours * 60 + minutes
}

const parseSlotLabel = (slotLabel) => {
  if (!slotLabel) return null
  const cleaned = String(slotLabel).trim()
  if (!cleaned || /TBA/i.test(cleaned) || /TBD/i.test(cleaned)) return null
  const parts = cleaned.split(/\s+/)
  if (parts.length < 2) return null
  const days = parts[0]
  const timeMatch = cleaned.match(/(\d{1,2}:\d{2}\s*[AP]M)-(\d{1,2}:\d{2}\s*[AP]M)/i)
  if (!timeMatch) return null
  const startMin = parseTimeToMinutes(timeMatch[1])
  const endMin = parseTimeToMinutes(timeMatch[2])
  if (startMin === null || endMin === null) return null
  return { days, startMin, endMin }
}

const formatTimeLabel = (minutes) => {
  const hours24 = Math.floor(minutes / 60)
  const mins = minutes % 60
  const meridiem = hours24 >= 12 ? "pm" : "am"
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12
  if (mins === 0) {
    return `${hours12}${meridiem}`
  }
  return `${hours12}:${mins.toString().padStart(2, "0")}${meridiem}`
}

const floorToStep = (minutes, step) => Math.floor(minutes / step) * step
const ceilToStep = (minutes, step) => Math.ceil(minutes / step) * step
const floorToStepMin = (minutes, step) => Math.floor(minutes / step) * step
const ceilToStepMin = (minutes, step) => Math.ceil(minutes / step) * step

const getCourseColor = (label) => {
  const safeLabel = label || "Unknown"
  let sum = 0
  for (let i = 0; i < safeLabel.length; i++) {
    sum += safeLabel.charCodeAt(i)
  }
  return COURSE_COLORS[sum % COURSE_COLORS.length]
}

const buildScheduleEvents = (sections) => {
  const events = []
  sections.forEach((section, index) => {
    const label = section.course_number || section.course || "Unknown Course"
    const slot = parseSlotLabel(section.slot_label)
    if (!slot) return
    const days = String(slot.days || "")
    days.split("").forEach((dayKey) => {
      if (!DAYS.find((d) => d.key === dayKey)) return
      events.push({
        id: `${label}-${index}-${dayKey}`,
        label,
        instructor: section.instructor_name || "Unknown Instructor",
        dayKey,
        startMin: slot.startMin,
        endMin: slot.endMin
      })
    })
  })
  return events
}

const Schedules = () => {
  const { roadmap, scheduleState, setScheduleState, plannerLoading } = useContext(CourseContext)
  const firstSemester = useMemo(() => roadmap[0] || [], [roadmap])
  const courseCodes = useMemo(() => {
    return firstSemester
      .map(c => c.course)
      .filter(Boolean)
      .map(code => code.replace(/^([A-Za-z]+)(\d.*)$/, "$1 $2"));
  }, [firstSemester])
  const courseCodesKey = useMemo(() => JSON.stringify(courseCodes), [courseCodes])
  const savedCourseCodesKey = useMemo(
    () => JSON.stringify(scheduleState.courseCodes || []),
    [scheduleState.courseCodes]
  )

  const [schedules, setSchedules] = useState(scheduleState.schedules || [])
  const [professorFreqs, setProfessorFreqs] = useState(scheduleState.professorFreqs || {});
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [selectedScheduleIndex, setSelectedScheduleIndex] = useState(
    scheduleState.selectedScheduleIndex || 0
  )

  const isUsingCache = savedCourseCodesKey === courseCodesKey
  const effectiveSchedules = isUsingCache
    ? (scheduleState.schedules || [])
    : schedules
  const effectiveProfessorFreqs = isUsingCache
    ? (scheduleState.professorFreqs || {})
    : professorFreqs
  const effectiveSelectedIndex = isUsingCache
    ? (scheduleState.selectedScheduleIndex || 0)
    : selectedScheduleIndex
  const shouldFetch =
    !plannerLoading &&
    courseCodes.length > 0 &&
    !(savedCourseCodesKey === courseCodesKey && schedules.length > 0)

  useEffect(() => {
    if (shouldFetch) {
      const id = setTimeout(() => setLoading(true), 0)
      return () => clearTimeout(id)
    }
  }, [shouldFetch])
    
  useEffect(() => {
    if (!shouldFetch) return

    let cancelled = false

    generateScheduleV2({ courses: courseCodes })
      .then((data) => {
        if (cancelled) return

        const nextSchedules = (data.schedules || []).slice(0, 6)
        const nextProfessorFreqs = data.professor_frequencies || {}

        setSchedules(nextSchedules)
        setSelectedScheduleIndex(0)
        setProfessorFreqs(nextProfessorFreqs)

        setScheduleState({
          courseCodes,
          schedules: nextSchedules,
          professorFreqs: nextProfessorFreqs,
          selectedScheduleIndex: 0
        })
      })
      .catch((err) => {
        if (cancelled) return

        setError(err.message || "Failed to generate schedules.")
        setSchedules([])
        setProfessorFreqs({})

        setScheduleState({
          courseCodes,
          schedules: [],
          professorFreqs: {},
          selectedScheduleIndex: 0
        })
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [shouldFetch, courseCodesKey])

  useEffect(() => {
    if (plannerLoading || !isUsingCache) return

    setScheduleState(prev => ({
      ...prev,
      courseCodes,
      schedules,
      professorFreqs,
      selectedScheduleIndex
    }))
  }, [
    schedules, 
    professorFreqs, 
    selectedScheduleIndex, 
    isUsingCache, 
    plannerLoading
  ])

  if (plannerLoading) {
    return (
      <div className="schedules">
        <div className="warning">
          <h2>Loading your schedules...</h2>
        </div>
      </div>
    )
  }


  if(courseCodes.length === 0){
    return(
      <div className="schedules">
        <div className="warning">
          <h2>Please select completed courses first on the Major page and submit your selection.</h2>
        </div>
      </div>
    )
  }

  const selectedSchedule = effectiveSchedules[effectiveSelectedIndex] || { sections: [] }
  const scheduleEvents = buildScheduleEvents(selectedSchedule.sections || [])
  const eventTimes = scheduleEvents.flatMap(event => [event.startMin, event.endMin])
  const minStart = eventTimes.length ? Math.min(...eventTimes) : DEFAULT_START_MIN
  const maxEnd = eventTimes.length ? Math.max(...eventTimes) : DEFAULT_END_MIN
  const gridStartMin = Math.min(DEFAULT_START_MIN, floorToStep(minStart, TIME_STEP_MIN))
  const gridEndMin = Math.max(DEFAULT_END_MIN, ceilToStep(maxEnd, TIME_STEP_MIN))
  const timeSlots = []
  for (let minutes = gridStartMin; minutes <= gridEndMin; minutes += TIME_STEP_MIN) {
    timeSlots.push(minutes)
  }

  return (
    <div className="schedules">
      <h1>Potential Predictive Schedules</h1>
      <p>
        Below are potential schedules for the upcoming semester based on the courses in your roadmap and historical scheduling data. Select different schedule options to view various conflict-free combinations of sections. You can also view historical professor frequencies for each course to help inform your schedule selection.
      </p>
      {loading && (
        <div className="spinner-container">
          <div className="loading-spinner"></div>
          <p>Generating schedules...</p>
        </div>
      )}
      {error && <p className="schedule-error">{error}</p>}

      {!loading && Object.keys(effectiveProfessorFreqs).length > 0 && (
        <div className="freq-container">
          <h2>Historical Professor Frequencies</h2>
          <div className="freq-grid">
            {Object.entries(effectiveProfessorFreqs).map(([course, profs]) => (
              <div key={course} className="freq-course-box">
                <h3>{course}</h3>
                {profs && profs.length > 0 ? (
                  <ul>
                    {profs.map((p, i) => (
                      <li key={i}>
                        <strong>{p.instructor_name}</strong>
                        <div>{p.teach_count} sections ({(p.probability * 100).toFixed(1)}%)</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No historical data.</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {effectiveSchedules.length > 0 ? (
        <>
          <div className="schedule-controls">
            <label className="schedule-select-label" htmlFor="schedule-option">
              Schedule option
            </label>
            <select
              id="schedule-option"
              className="schedule-select"
              value={effectiveSelectedIndex}
              onChange={(event) => setSelectedScheduleIndex(Number(event.target.value))}
            >
              {effectiveSchedules.map((_, index) => (
                <option key={`option-${index}`} value={index}>
                  Option {index + 1}
                </option>
              ))}
            </select>
          </div>

          <div className="schedule-weekly">
            <div className="schedule-grid">
              <div className="schedule-corner" />
              {DAYS.map((day) => (
                <div key={day.key} className="schedule-day-header">
                  {day.label}
                </div>
              ))}
              {timeSlots.map((minutes, rowIndex) => (
                <React.Fragment key={`row-${minutes}`}>
                  <div
                    className={`schedule-time-label ${minutes % 60 === 0 ? "schedule-time-label-hour" : ""}`}
                    style={{ gridRow: rowIndex + 2, gridColumn: "1 / 2" }}
                  >
                    <span
                      className={`schedule-time-label-text ${rowIndex === 0 ? "schedule-time-label-text-first" : ""}`}
                    >
                      {formatTimeLabel(minutes)}
                    </span>
                  </div>
                  {DAYS.map((day, dayIndex) => (
                    <div
                      key={`${day.key}-${minutes}`}
                      className={`schedule-cell ${minutes % 60 === 0 ? "schedule-cell-hour" : ""}`}
                      style={{ gridRow: rowIndex + 2, gridColumn: dayIndex + 2 }}
                    />
                  ))}
                </React.Fragment>
              ))}
              {scheduleEvents.map((event) => {
                const dayIndex = DAYS.findIndex((day) => day.key === event.dayKey)
                if (dayIndex === -1) return null
                const snappedStart = floorToStepMin(event.startMin, TIME_STEP_MIN)
                const snappedEnd = ceilToStepMin(event.endMin, TIME_STEP_MIN)
                const rowStart = Math.floor((snappedStart - gridStartMin) / TIME_STEP_MIN) + 2
                const rowEnd = Math.max(
                  rowStart + 1,
                  Math.ceil((snappedEnd - gridStartMin) / TIME_STEP_MIN) + 2
                )
                const columnStart = dayIndex + 2
                const color = getCourseColor(event.label)
                return (
                  <div
                    key={event.id}
                    className="schedule-event"
                    style={{
                      gridColumn: `${columnStart} / ${columnStart + 1}`,
                      gridRow: `${rowStart} / ${rowEnd}`,
                      backgroundColor: color.bg,
                      borderColor: color.border
                    }}
                  >
                    <div className="schedule-event-title">
                      {(() => {
                        const courseLink = getCourseLink(event.label)
                        if (!courseLink) return event.label
                        return (
                          <a
                            className="schedule-event-link"
                            href={courseLink}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {event.label}
                          </a>
                        )
                      })()}
                    </div>
                    <div className="schedule-event-meta">
                      {event.instructor}
                    </div>
                    <div className="schedule-event-meta">
                      {formatTimeLabel(event.startMin)} - {formatTimeLabel(event.endMin)}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      ) : (
        !loading && !error && <div className="empty-schedule-state">
          <h3>No Valid Schedules</h3>
          <p>We couldn't predict a conflict-free schedule for these courses based on historical data.</p>
        </div>
      )}
    </div>
  )
}

export default Schedules
