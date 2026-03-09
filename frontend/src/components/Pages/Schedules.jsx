import React, { useEffect, useState } from 'react'
import './Schedules.css'
import {ScheduleGenerator} from '../../utils/ScheduleGenerator'
import { getHealth } from '../../api/api'

const Schedules = () => {
  const roadmap = JSON.parse(localStorage.getItem('roadmap')) || []
  const firstSemester = roadmap[0] || []
  const schedules = ScheduleGenerator(firstSemester)

  const [apiStatus, setApiStatus] = useState("checking...");

  useEffect(() => {
    // use helper from api module
    getHealth()
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus("failed"));
  }, []);



  if(firstSemester.length === 0){
    return(
      <div className="schedules">
        <p>API status: {apiStatus}</p>
        <div className="warning">
          <h2>Please select completed courses first on the Major page and submit your selection.</h2>
        </div>
      </div>
    )
  }

  return (
    <div className="schedules">
      <p>API status: {apiStatus}</p>
      <h1>Potential Predictive Schedules</h1>
      <div className="schedule-container">
        {schedules.map((schedule, index) => (
          <div key={index} className="schedule-box">
            <h2>Option {index + 1}</h2>
            <div className="schedule-courses">
              {schedule.map(course => (
                <div key={course.course} className="schedule-course">
                  {course.course}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Schedules