import React from 'react'
import { useNavigate } from 'react-router-dom'
import './Home.css'


const Home = () => {
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
    </div>
  )
}

export default Home
