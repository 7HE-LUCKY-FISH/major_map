import React, { useState } from 'react'
import './Navbar.css'
import logoWhite from '../../assets/logoWhite.png'
import logoBlack from '../../assets/logoBlack.png'
import logoDarkMode from '../../assets/day.png'
import logoLightMode from '../../assets/night.png'
import {Link} from 'react-router-dom'
import {NavLink} from 'react-router-dom'

const Navbar = ({theme, setTheme}) => {
    const [menuOpen, setMenuOpen] = useState(false)
  
    const toggle_mode = () => {
        theme === 'light' ? setTheme('dark') : setTheme('light');
    }

    const closeMenu = () => {
        setMenuOpen(false)
    }
  
    return ( 
    <div className='navbar'>
        <Link to="/" onClick={closeMenu}>
        <img src={theme == 'light' ? logoWhite : logoBlack} alt="" className='logo'/>
        </Link>

        <button
            className="menu-toggle"
            aria-label="Toggle navigation menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
        >
            ☰
        </button>

        <ul className={menuOpen ? 'open' : ''}>
            <li><NavLink to="/" onClick={closeMenu}>Home</NavLink></li>
            <li><NavLink to="/major" onClick={closeMenu}>Major</NavLink></li>
            <li><NavLink to="/roadmap" onClick={closeMenu}>Roadmap</NavLink></li>
            <li><NavLink to="/schedules" onClick={closeMenu}>Schedules</NavLink></li>
            <li><NavLink to="/search" onClick={closeMenu}>Search</NavLink></li>
            {/* <li><NavLink to={user ? "/account" : "/login"}>{user ? "Account" : "Login"}</NavLink></li> */}
        </ul>

        <img onClick={()=>{toggle_mode()}} src={theme == 'light' ? logoLightMode : logoDarkMode} alt="" className='toggle-icon'/>

    </div>
  )
}

export default Navbar
