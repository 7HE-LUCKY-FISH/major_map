import React from 'react'
import { useNavigate } from 'react-router-dom'
import './Home.css'
import semesterPlanningLogoLight from '../../assets/SemesterPlanningLogoLight.png'
import semesterPlanningLogoDark from '../../assets/SemesterPlanningLogoDark.png'
import roadmapLogoLight from '../../assets/RoadmapLogoLight.png'
import roadmapLogoDark from '../../assets/RoadmapLogoDark.png'
import graduationLogoLight from '../../assets/GraduationLogoLight.png'
import graduationLogoDark from '../../assets/GraduationLogoDark.png'


const Home = ({ theme }) => {
  const navigate = useNavigate()

  const navigateToMajorPage = () => {
    navigate('/major')
  }
  
  return (
    <div className='home'>
      <h1>Welcome to MajorMap</h1>
      <p>
        Select "Major" from the navigation menu or click the button below to get started.
        If you would only like to look at historical course data, select "Search" from the navigation menu.
      </p>
      <button className='get-started-btn' onClick={navigateToMajorPage}>
        Get Started
      </button>
      <div className="home-logos" aria-label="Planner feature logos">
        <img
          className="home-logo-item home-logo-semester"
          src={theme === 'dark' ? semesterPlanningLogoDark : semesterPlanningLogoLight}
          alt="Semester planning logo"
        />
        <img
          className="home-logo-item home-logo-roadmap"
          src={theme === 'dark' ? roadmapLogoDark : roadmapLogoLight}
          alt="Roadmap logo"
        />
        <img
          className="home-logo-item home-logo-graduation"
          src={theme === 'dark' ? graduationLogoDark : graduationLogoLight}
          alt="Graduation logo"
        />
      </div>
    </div>
  )
}

export default Home
