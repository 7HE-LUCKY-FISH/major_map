import React from 'react'
import './Navbar.css'
import logoWhite from '../../assets/logoWhite.png'
import logoBlack from '../../assets/logoBlack.png'
import logoDarkMode from '../../assets/day.png'
import logoLightMode from '../../assets/night.png'
import {Link} from 'react-router-dom'
import {NavLink} from 'react-router-dom'

const Navbar = ({theme, setTheme}) => {
  
    const toggle_mode = () => {
        theme == 'light' ? setTheme('dark') : setTheme('light');
    }
  
    return ( 
    <div className='navbar'>
        <Link to="/">
        <img src={theme == 'light' ? logoWhite : logoBlack} alt="" className='logo'/>
        </Link>

        <ul>
            <li><NavLink to="/">Home</NavLink></li>
            <li><NavLink to="/major">Major</NavLink></li>
            <li><NavLink to="/roadmap">Roadmap</NavLink></li>
            <li><NavLink to="/schedules">Schedules</NavLink></li>
            <li><NavLink to="/courses">Courses</NavLink></li>
        </ul>

        <img onClick={()=>{toggle_mode()}} src={theme == 'light' ? logoLightMode : logoDarkMode} alt="" className='toggle-icon'/>

    </div>
  )
}

export default Navbar