import React, {useEffect, useState} from 'react'
import Navbar from './components/Navbar/Navbar'
import { Route, Routes } from 'react-router-dom';
import {Home, Major, Roadmap, Schedules, Search, Account, Login, Register} from './components/Pages/index'



const App = () => {

  const current_theme = localStorage.getItem('current_theme');
  const [theme, setTheme] = useState(current_theme ? current_theme : 'light');
  
  useEffect(()=>{
    localStorage.setItem('current_theme', theme);
  }, [theme])

  return (
    <div className={`container ${theme}`}>
      <Navbar theme={theme} setTheme={setTheme}/>
      <Routes>
        <Route path='/' element={<Home/>}/>
        <Route path='/major' element={<Major/>}/>
        <Route path='/roadmap' element={<Roadmap/>}/>
        <Route path='/schedules' element={<Schedules/>}/>
        <Route path='/search' element={<Search/>}/>
        <Route path='/login' element={<Login/>}/>
        <Route path='/register' element={<Register/>}/>
        <Route path='/account' element={<Account/>}/>
      </Routes>
    </div>
  )
}

export default App
