import React, { useEffect, useMemo, useRef, useState } from 'react'
import './Schedules.css'
import { getHealth, generateScheduleV2 } from '../../api/api'

const Schedules = () => {
  const roadmap = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('roadmap') || '[]')
    } catch {
      return []
    }
  }, [])
  const firstSemester = useMemo(() => roadmap[0] || [], [roadmap])
  const courseCodes = useMemo(() => {
    return firstSemester
      .map(c => c.course)
      .filter(Boolean)
      .map(code => code.replace(/^([A-Za-z]+)(\d.*)$/, "$1 $2"));
  }, [firstSemester])

  const [apiStatus, setApiStatus] = useState("checking...");
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const lastCoursesKey = useRef("");

  useEffect(() => {
    // use helper from api module
    getHealth()
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus("failed"));
  }, []);

  useEffect(() => {
    console.log("[Schedules] courseCodes:", courseCodes);
    if (courseCodes.length === 0) {
      setSchedules([]);
      return;
    }

    const nextKey = courseCodes.join("|");
    if (lastCoursesKey.current === nextKey) return;
    lastCoursesKey.current = nextKey;

    setLoading(true);
    setError("");

    generateScheduleV2({ courses: courseCodes })
      .then((data) => {
        const allSchedules = data.schedules || [];
        setSchedules(allSchedules.slice(0, 6));
      })
      .catch((err) => {
        setError(err.message || "Failed to generate schedules.");
        setSchedules([]);
      })
      .finally(() => setLoading(false));
  }, [courseCodes]);


  if(courseCodes.length === 0){
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
      {loading && <p>Generating schedules...</p>}
      {error && <p className="schedule-error">{error}</p>}
      <div className="schedule-container">
        {schedules.map((schedule, index) => (
          <div key={index} className="schedule-box">
            <h2>Option {index + 1}</h2>
            <div className="schedule-courses">
              {(schedule.sections || []).map((section, sectionIndex) => (
                <div key={`${section.course_number || section.course || "course"}-${sectionIndex}`} className="schedule-course">
                  <div>{section.course_number || section.course || "Unknown Course"}</div>
                  <div className="schedule-meta">
                    {section.instructor_name || "Unknown Instructor"} - {section.slot_label || "TBD"}
                  </div>
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
