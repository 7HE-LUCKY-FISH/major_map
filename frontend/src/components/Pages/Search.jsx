import React, {useState, useEffect, useMemo} from 'react'
import './Search.css'
import { loadCSV } from '../../utils/CSVparser'

const Search = () => {
  const [data, setData] = useState([])
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('course')

  useEffect(() => {
    const loadData = async () => {
      const csvData = await loadCSV('/HistoricalCourseData.csv')
      console.log('Loaded CSV data:', csvData)
      setData(csvData)
    }
    loadData()
  }, [])

  const results = useMemo(() => {
    if (!query) {
      return []
    }
    return data.filter((item) => {
      if (mode === 'course') {
        return (item.Section || '').toLowerCase().includes(query.toLowerCase())
      } else if (mode === 'instructor') {
        return (item.Instructor || '').toLowerCase().includes(query.toLowerCase())
      }
      return false
    })
  }, [query, mode, data])

  return (
    <div className='search'>
      <h1>Historical Course Data</h1>
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
        <div className='results-table'>
          <div className='table-header'>
            <div>Semester</div>
            <div>Course</div>
            <div>Day</div>
            <div>Time</div>
            <div>Unit</div>
            <div>Instructor</div>
        </div>

          {results.map((row, index) => (
            <div key={index} className='table-row'>
              <div>{row.Semester} {row.Year}</div>
              <div>{row.Section}</div>
              <div>{row.Days}</div>
              <div>{row.Times}</div>
              <div>{row.Unit}</div>
              <div>{row.Instructor}</div>
            </div>
          ))}
        </div>  
      </div>
  )
}

export default Search