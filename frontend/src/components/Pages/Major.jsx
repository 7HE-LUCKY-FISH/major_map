import React,{useContext, useEffect, useMemo} from 'react'
import './Major.css'
import {CourseContext} from '../../utils/CourseContext'
import coursesData from '../../data/courses.json'
import { useNavigate } from 'react-router-dom'

const Major = () => {
  const {
    completedCourses,
    setCompletedCourses,
    selectedMajor,
    setSelectedMajor,
    setSubmitted
  } = useContext(CourseContext)

  const navigate = useNavigate()
  const majors = Object.keys(coursesData)

  const majorNames = {
    CS: "Computer Science",
    SE: "Software Engineering",
    CMPE: "Computer Engineering",
    EE: "Electrical Engineering"
  }

  const toggleCourse = (course) => {
    setCompletedCourses(prev =>
      prev.includes(course)
        ? prev.filter(c => c !== course)
        : [...prev, course]
      )
  }

  const isUnlocked = (course) => {
    return course.prerequisites.every(pr =>{
      if (Array.isArray(pr)) {
        return pr.some(p=>completedCourses.includes(p))
      }
      return completedCourses.includes(pr)
    })
  }

  const submit = () => {
    setSubmitted(true)
    navigate('/roadmap')
  }

  const courses = useMemo(() => {
    return selectedMajor ? coursesData[selectedMajor] || [] : []
  }, [selectedMajor])

  useEffect(() => {
  const validCourses = completedCourses.filter(courseCode => {
    const courseObj = courses.find(c => c.course === courseCode)
    if (!courseObj) return false
    return courseObj.prerequisites.every(pr =>{
      if (Array.isArray(pr)) {
        return pr.some(p=>completedCourses.includes(p))
      }
      return completedCourses.includes(pr)
    }) 
  })
    if (validCourses.length !== completedCourses.length) {
      setCompletedCourses(validCourses)
    }
  }, [completedCourses, courses, setCompletedCourses])

  return (
    <div className="major">
      <h1>Select Completed Courses</h1>
      <div className="major-select">
        <select
          value={selectedMajor}
          onChange={(e)=>setSelectedMajor(e.target.value)}
        >
          <option value="">Select Major</option>

          {majors.map(m=>(
            <option key={m} value={m}>
              {majorNames[m] || m}
            </option>
          ))}

        </select>
      </div>

      {selectedMajor && (
      <div className="courses-container">
          <div className="courses-grid">
          {courses.map(course=>{
          const unlocked = isUnlocked(course)
          return(
            <label
              key={course.course}
              className={`course-card ${!unlocked ? "locked" : ""}`}
            >
              <input
                type="checkbox"
                disabled={!unlocked}
                checked={completedCourses.includes(course.course)}
                onChange={()=>toggleCourse(course.course)}
              />
              <span>{course.course}</span>
            </label>
          )
        })}
        </div>
      </div>
      )}

      {selectedMajor &&
      <div className="submit-container">
        <button
          className="submit-btn"
          onClick={submit}
        >
          Generate Roadmap
        </button>
      </div>
      }
    </div>
  )
}

export default Major