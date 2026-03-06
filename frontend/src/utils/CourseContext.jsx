import { createContext, useState, useEffect } from "react";
export const CourseContext = createContext();

export const CourseProvider = ({ children }) => {
    const [completedCourses, setCompletedCourses] = useState(
        JSON.parse(localStorage.getItem("completedCourses")) || []
    );

    const [selectedMajor, setSelectedMajor] = useState(
        localStorage.getItem("selectedMajor") || ""
    );

    const [submitted, setSubmitted] = useState(
        localStorage.getItem("submitted") === "true"
    );

    useEffect(()=>{
        localStorage.setItem("completedCourses", JSON.stringify(completedCourses))
    },[completedCourses])

    useEffect(()=>{
        localStorage.setItem("selectedMajor", selectedMajor)
    },[selectedMajor])

    useEffect(()=>{
        localStorage.setItem("submitted", submitted)
    },[submitted])

    return (
        <CourseContext.Provider
            value={{
                completedCourses,
                setCompletedCourses,
                selectedMajor,
                setSelectedMajor,
                submitted,
                setSubmitted
            }}
        >
        {children}
        </CourseContext.Provider>
    );
};