import React, { useState, useEffect, useMemo } from 'react'
import './Search.css'
import { loadCSV } from '../../utils/CSVparser'
import ProfessorLinksRMP from '../../utils/ProfessorLinksRMP'

const MAX_RESULTS = 200

const Search = () => {
  const [data, setData] = useState([])
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('course')

  const [courseIndex, setCourseIndex] = useState(new Map())
  const [instructorIndex, setInstructorIndex] = useState(new Map())

  useEffect(() => {
    const loadData = async () => {
      const csvData = await loadCSV('/HistoricalCourseData.csv')

      const courseMap = new Map()
      const instructorMap = new Map()

      const enriched = csvData.map((row) => {
        const instructor = row.Instructor?.trim() || ''
        const section = row.Section || ''

        const instructorLower = instructor.toLowerCase()
        const sectionLower = section.toLowerCase()

        const newRow = {
          ...row,
          Instructor: instructor,
          Section: section,
          instructorLower,
          sectionLower,
          rmp_url: ProfessorLinksRMP[instructor] || null
        }

        const courseKey = sectionLower.slice(0, 3)
        const instructorKey = instructorLower.slice(0, 3)

        if (!courseMap.has(courseKey)) courseMap.set(courseKey, [])
        if (!instructorMap.has(instructorKey)) instructorMap.set(instructorKey, [])

        courseMap.get(courseKey).push(newRow)
        instructorMap.get(instructorKey).push(newRow)

        return newRow
      })

      setData(enriched)
      setCourseIndex(courseMap)
      setInstructorIndex(instructorMap)
    }

    loadData()
  }, [])

  const results = useMemo(() => {
    const q = query.toLowerCase().trim()
    if (!q || q.length < 2) return []

    const key = q.slice(0, 3)

    const index = mode === 'course' ? courseIndex : instructorIndex
    const pool = index.get(key) || data // fallback if no index hit

    const output = []

    for (let i = 0; i < pool.length; i++) {
      const item = pool[i]

      const match =
        mode === 'course'
          ? item.sectionLower.includes(q)
          : item.instructorLower.includes(q)

      if (match) {
        output.push(item)
        if (output.length >= MAX_RESULTS) break
      }
    }

    return output
  }, [query, mode, data, courseIndex, instructorIndex])

  return (
    <div className='search'>
      <h1>Historical Course Data</h1>
      <p>
        Search for courses or instructors to view historical data on course offerings, schedules, and professor reviews. Use the toggle to switch between searching by course or instructor name. 
        Results are limited to the first 200 matches, so try refining your search for more specific results.
      </p>
      <div className="search-controls">
        <div className="mode-toggle">
          <span className={mode === "course" ? "active-label" : ""}>
            Course
          </span>

          <label className="switch">
            <input
              type="checkbox"
              checked={mode === "instructor"}
              onChange={() =>
                setMode(mode === "course" ? "instructor" : "course")
              }
            />
            <span className="slider"></span>
          </label>

          <span className={mode === "instructor" ? "active-label" : ""}>
            Instructor
          </span>
        </div>

        <input
          type="text"
          placeholder={`Search ${
            mode === "course" ? "course" : "instructor"
          }...`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {results.length === MAX_RESULTS && (
        <div className="limit-warning">
          Showing first {MAX_RESULTS} results — refine your search
        </div>
      )}

      <div className='results-table'>
        <div className='table-header'>
          <div>Semester</div>
          <div>Course</div>
          <div>Day</div>
          <div>Time</div>
          <div>Unit</div>
          <div>Instructor</div>
          <div>Reviews (RMP)</div>
        </div>

        {results.map((row, index) => (
          <Row key={index} row={row} />
        ))}
      </div>
    </div>
  )
}

const Row = React.memo(({ row }) => {
  return (
    <div className='table-row'>
      <div>{row.Semester} {row.Year}</div>
      <div>{row.Section}</div>
      <div>{row.Days}</div>
      <div>{row.Times}</div>
      <div>{row.Unit}</div>
      <div>{row.Instructor}</div>

      <div>
        {row.rmp_url ? (
          <a
            href={row.rmp_url}
            target="_blank"
            rel="noopener noreferrer"
            className="review-button"
          >
            View Reviews
          </a>
        ) : (
          <span className="no-reviews">No Reviews</span>
        )}
      </div>
    </div>
  )
})

export default Search