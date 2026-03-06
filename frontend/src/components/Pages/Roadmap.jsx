import React, {useContext} from 'react'
import './Roadmap.css'
import { CourseContext } from '../../utils/CourseContext'
import coursesData from '../../data/courses.json'
import {RoadmapGenerator} from '../../utils/RoadmapGenerator'

const generateSemesters = (count) => {
  let year = 2026
  let term = "Fall"
  const semesters = []

  for (let i = 0; i < count; i++) {
    semesters.push(`${term} ${year}`)

    if (term === "Fall") {
      term = "Spring"
      year++
    } else {
      term = "Fall"
    }
  }

  return semesters
}

const Roadmap = () => {
    const {completedCourses,selectedMajor,submitted} =
  useContext(CourseContext)

  if(!submitted){
    return(
      <div className="roadmap">
        <div className="warning">
          <h2>Please select completed courses first on the Major page and submit your selection.</h2>
        </div>
      </div>
    )
  }

  const allCourses = coursesData[selectedMajor] || [];
  const roadmap = RoadmapGenerator(allCourses, completedCourses)
  localStorage.setItem('roadmap', JSON.stringify(roadmap))
  const semesterLabels = generateSemesters(roadmap.length)

  return (
    <div className="roadmap">
      <h1>Your Personalized Roadmap</h1>

      <div className="roadmap-container">
        {semesterLabels.map((semester, i) => {
        const semesterCourses = roadmap[i] || []

        return (
          <div key={i} className="semester">
            <h2>{semester}</h2>
            <div className="semester-courses">
              {semesterCourses.map((course) => (
                <div key={course.course} className="roadmap-course">
                  {course.course}
                </div>
              ))}
            </div>
          </div>
        );
      })}
      </div>
    </div>
  )
}

export default Roadmap