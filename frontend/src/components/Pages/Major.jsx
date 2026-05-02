import React,{useContext, useEffect, useMemo, useState} from 'react'
import './Major.css'
import {CourseContext} from '../../utils/CourseContext'
import coursesData from '../../data/courses.json'
import { useNavigate } from 'react-router-dom'
import { getCourseLink } from '../../utils/CourseLinks'

const Major = () => {
  const {
    completedCourses,
    setCompletedCourses,
    selectedMajor,
    setSelectedMajor,
    setSubmitted,
    setRoadmap,
    setScheduleState,
    plannerLoading,
    preferredUnits,
    setPreferredUnits
  } = useContext(CourseContext)

  const navigate = useNavigate()
  const [isGenerating, setIsGenerating] = useState(false)
  const majors = Object.keys(coursesData)



  const majorNames = {
    CS: "Computer Science",
    SE: "Software Engineering",
    CMPE: "Computer Engineering",
    EE: "Electrical Engineering"
  }

useEffect(() => {
    if (selectedMajor) {
      const savedForMajor = localStorage.getItem(`completed_${selectedMajor}`);
      if (savedForMajor) {
        setCompletedCourses(JSON.parse(savedForMajor));
      } else {
        setCompletedCourses([]);
      }
    }
  }, [selectedMajor, setCompletedCourses]);

 
  useEffect(() => {
    if (selectedMajor) {
      localStorage.setItem(`completed_${selectedMajor}`, JSON.stringify(completedCourses));
    }
  }, [completedCourses, selectedMajor]);


  const toggleCourse = (course) => {
    setCompletedCourses(prev =>
      prev.includes(course)
        ? prev.filter(c => c !== course)
        : [...prev, course]
      )
  }

  const clearMajorCourses = () => {
    const majorName = majorNames[selectedMajor] || selectedMajor;
    if (window.confirm(`Are you sure you want to clear all selections for ${majorName}?`)) {
      setCompletedCourses([]);
    }
  }

  const isUnlocked = (course) => {
    return course.prerequisites.every(pr =>{
      if (Array.isArray(pr)) {
        return pr.some(p=>completedCourses.includes(p))
      }
      return completedCourses.includes(pr)
    })
  }

  const getMissingPrereqs = (course) => {
    return (course.prerequisites || []).flatMap((pr) => {
      if (Array.isArray(pr)) {
        const hasAnyOption = pr.some((option) => completedCourses.includes(option))
        return hasAnyOption ? [] : [`(${pr.join(' or ')})`]
      }
      return completedCourses.includes(pr) ? [] : [pr]
    })
  }

  const handleGenerate = () => {
    setIsGenerating(true)
    setTimeout(() => {
      setSubmitted(true)
      setIsGenerating(false)
      navigate('/roadmap')
    }, 800)
  }

  const courses = useMemo(() => {
    return selectedMajor ? coursesData[selectedMajor] || [] : []
  }, [selectedMajor])

  const sortedCourses = useMemo(() => {
    return [...courses].sort((a, b) =>
      (a.course || '').localeCompare((b.course || ''), undefined, {
        numeric: true,
        sensitivity: 'base'
      })
    )
  }, [courses])

  useEffect(() => {
    if (!selectedMajor) {
      setCompletedCourses([])
      setSubmitted(false)
      setRoadmap([])
      setScheduleState({
        courseCodes: [],
        schedules: [],
        professorFreqs: {},
        selectedScheduleIndex: 0
      })
    }
  }, [selectedMajor, setCompletedCourses, setRoadmap, setScheduleState, setSubmitted])

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
  }, [completedCourses, courses, selectedMajor, setCompletedCourses])

  if (plannerLoading) {
    return (
      <div className="major">
        <h1>Loading your planner...</h1>
      </div>
    )
  }

  return (
    <div className="major">
      <h1>Select Completed Courses</h1>
      <p>Select Your Major → Select Completed Courses → Scroll Down & Select "Generate Roadmap" Button</p>
      <p>
        For more details on any course, click the "Details" link next to the course code. 
      </p>
      <p>Locked (faded) courses require their prerequisite course(s) to be selected first. Hover over them to check their prerequisite(s)</p>
      <div className="major-select">
        <select
          value={selectedMajor}
          onChange={(e)=>{
            setSelectedMajor(e.target.value)
            setSubmitted(false)
            setRoadmap([])
            setScheduleState({
              courseCodes: [],
              schedules: [],
              professorFreqs: {},
              selectedScheduleIndex: 0
            })
          }}
        >
          <option value="">Select Major</option>

          {majors.map(m=>(
            <option key={m} value={m}>
              {majorNames[m] || m}
            </option>
          ))}

        </select>

        {selectedMajor && (
          <div className="unit-preference-container">
            <label htmlFor="unit-input" className="unit-preference-label">
              Target Units per Semester:
            </label>
            <input 
              id="unit-input"
              type="number" 
              min="1" 
              max="25"
              value={preferredUnits} 
              onChange={(e) => {
                setPreferredUnits(e.target.value === '' ? '' : Number(e.target.value));
                setSubmitted(false);
              }}
              onBlur={() => {
                if (!preferredUnits || preferredUnits < 1) {
                  setPreferredUnits(15);
                  setSubmitted(false);
                }
              }}
              className="unit-input-box"
            />
          </div>
        )}
      </div>

      {selectedMajor && (
      <div className="courses-container">
          <div className="courses-grid">
          {sortedCourses.map((course, index)=>{
          const unlocked = isUnlocked(course)
          const missingPrereqs = getMissingPrereqs(course)
          const lockedHint = missingPrereqs.length
            ? `Select prerequisite(s): ${missingPrereqs.join(', ')}`
            : ''
          const courseLink = getCourseLink(course.course)
          return(
            <div
              key={course.course}
              className={`course-card-wrapper ${!unlocked ? "locked" : ""} ${index < 5 ? "first-row-card" : ""}`}
            >
              <label className={`course-card ${!unlocked ? "locked" : ""}`}>
                <input
                  type="checkbox"
                  aria-label={course.course}
                  disabled={!unlocked}
                  checked={completedCourses.includes(course.course)}
                  onChange={()=>toggleCourse(course.course)}
                />
                <span className="course-code">{course.course}</span>
                {courseLink && (
                  <a
                    className="course-link"
                    href={courseLink}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Details
                  </a>
                )}
              </label>
              {!unlocked && (
                <span className="locked-tooltip" aria-hidden="true">{lockedHint}</span>
              )}
            </div>
          )
        })}
        </div>
      </div>
      )}

  {selectedMajor && (
        <div className="sticky-action-bar">
          <button className="clear-btn" onClick={clearMajorCourses}>
            Clear Selections
          </button>
          <button 
            className="submit-btn" 
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? "Generating..." : "Generate Roadmap"}
          </button>
        </div>
      )}
    </div>
  )
}

export default Major
