import React, {useContext, useEffect, useMemo} from 'react'
import './Roadmap.css'
import { CourseContext } from '../../utils/CourseContext'
import coursesData from '../../data/courses.json'
import {RoadmapGenerator} from '../../utils/RoadmapGenerator'
import { getCourseLink } from '../../utils/CourseLinks'

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
    const {
      completedCourses,
      selectedMajor,
      submitted,
      roadmap,
      setRoadmap,
      plannerLoading
    } =
  useContext(CourseContext)

  const allCourses = useMemo(() => coursesData[selectedMajor] || [], [selectedMajor])
  const generatedRoadmap = useMemo(() => {
    if (!submitted || !selectedMajor) {
      return []
    }
    return RoadmapGenerator(allCourses, completedCourses)
  }, [allCourses, completedCourses, selectedMajor, submitted])

  useEffect(() => {
    if (!submitted) {
      if (roadmap.length > 0) {
        setRoadmap([])
      }
      return
    }

    const roadmapChanged =
      JSON.stringify(roadmap) !== JSON.stringify(generatedRoadmap)

    if (roadmapChanged) {
      setRoadmap(generatedRoadmap)
    }
  }, [generatedRoadmap, roadmap, setRoadmap, submitted])

  if (plannerLoading) {
    return (
      <div className="roadmap">
        <div className="warning">
          <h2>Loading your roadmap...</h2>
        </div>
      </div>
    )
  }

  if(!submitted){
    return(
      <div className="roadmap">
        <div className="warning">
          <h2>Please select completed courses first on the Major page and submit your selection.</h2>
        </div>
      </div>
    )
  }

  const roadmapToRender = roadmap.length > 0 ? roadmap : generatedRoadmap
  const semesterLabels = generateSemesters(roadmapToRender.length)

  return (
    <div className="roadmap">
      <h1>Your Personalized Roadmap</h1>
      <p>
        Below is your personalized roadmap based on the courses you've completed. Each semester contains maximum of 5 courses and you can click on any course to view more details about it.
      </p>
      <p>
        Select "Schedules" from the naigation menu to view potential predictive schedules for the courses listed in the upcoming semester.
      </p>
      <div className="roadmap-container">
        {semesterLabels.map((semester, i) => {
        const semesterCourses = roadmapToRender[i] || []

        return (
          <div key={i} className="semester">
            <h2>{semester}</h2>
            <div className="semester-courses">
              {semesterCourses.map((course) => {
                const courseLink = getCourseLink(course.course)
                if (!courseLink) {
                  return (
                    <div key={course.course} className="roadmap-course">
                      {course.course}
                    </div>
                  )
                }
                return (
                  <a
                    key={course.course}
                    className="roadmap-course roadmap-course-link"
                    href={courseLink}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {course.course}
                  </a>
                )
              })}
            </div>
          </div>
        );
      })}
      </div>
    </div>
  )
}

export default Roadmap
