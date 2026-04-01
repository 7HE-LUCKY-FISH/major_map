import React, { useEffect, useMemo, useState } from 'react'
import './Schedules.css'
import { getHealth, generateScheduleV2 } from '../../api/api'
import { getCourseLink } from '../../utils/CourseLinks'

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
  const [professorFreqs, setProfessorFreqs] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [prevCourseCodes, setPrevCourseCodes] = useState(courseCodes);

  if (courseCodes !== prevCourseCodes){
    setPrevCourseCodes(courseCodes);
    setSchedules([]);
    setError("");
    if(courseCodes.length > 0){
      setLoading(true);
    }else{
      setLoading(false);
    }
  }

  useEffect(() => {
    // use helper from api module
    getHealth()
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus("failed"));
  }, []);

  useEffect(() => {
    console.log("[Schedules] courseCodes:", courseCodes);
    if (courseCodes.length === 0) return;

    generateScheduleV2({ courses: courseCodes })
      .then((data) => {
        console.log("[Schedules] generateScheduleV2 response data:", data);
        const allSchedules = data.schedules || [];
        setSchedules(allSchedules.slice(0, 6));
        setProfessorFreqs(data.professor_frequencies || {});
      })
      .catch((err) => {
        setError(err.message || "Failed to generate schedules.");
        setSchedules([]);
        setProfessorFreqs({});
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

      {!loading && Object.keys(professorFreqs).length > 0 && (
        <div className="freq-container">
          <h2>Historical Professor Frequencies</h2>
          <div className="freq-grid">
            {Object.entries(professorFreqs).map(([course, profs]) => (
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

      <div className="schedule-container">
        {schedules.map((schedule, index) => (
          <div key={index} className="schedule-box">
            <h2>Option {index + 1}</h2>
            <div className="schedule-courses">
              {(schedule.sections || []).map((section, sectionIndex) => (
                <div key={`${section.course_number || section.course || "course"}-${sectionIndex}`} className="schedule-course">
                  {(() => {
                    const courseLabel = section.course_number || section.course || "Unknown Course"
                    const courseLink = courseLabel === "Unknown Course" ? "" : getCourseLink(courseLabel)
                    if (!courseLink) {
                      return <div>{courseLabel}</div>
                    }
                    return (
                      <a
                        className="schedule-course-link"
                        href={courseLink}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {courseLabel}
                      </a>
                    )
                  })()}
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
