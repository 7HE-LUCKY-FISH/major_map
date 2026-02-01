"use client"

import { Navigation } from "@/components/navigation"
import { useEffect, useState } from "react"

interface Semester {
  season: string
  year: number
  courses: string[]
}

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState<Semester[]>([])
  const [totalUnits, setTotalUnits] = useState(16)

  useEffect(() => {
    // Get the completed courses from sessionStorage
    const completedCoursesStr = sessionStorage.getItem("completedCourses")
    const completedCourses = completedCoursesStr ? JSON.parse(completedCoursesStr) : []

    // For demo purposes, generate a sample roadmap based on completed courses
    // In a real app, this would come from an API
    const allCourses = [
      "Biol 10",
      "Chem 1A",
      "CMPE 30",
      "CMPE 50",
      "CMPE 102",
      "CMPE 110",
      "CMPE 120",
      "CMPE 124",
      "CMPE 133",
    ]
    const remainingCourses = allCourses.filter((course) => !completedCourses.includes(course))

    // Generate roadmap
    const generatedRoadmap: Semester[] = [
      {
        season: "Spring",
        year: 2026,
        courses: remainingCourses.slice(0, 5),
      },
      {
        season: "Fall",
        year: 2026,
        courses: remainingCourses.slice(5),
      },
    ]

    setRoadmap(generatedRoadmap.filter((sem) => sem.courses.length > 0))
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />

      <main className="flex-1 bg-white py-12 px-6">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-2xl text-black leading-relaxed">
              Based on your completed courses, here
              <br />
              is a personalized roadmap for you
              <br />
              <span className="text-lg">({totalUnits} units recommended)</span>
            </h1>
          </div>

          {/* Roadmap Semesters */}
          <div className="space-y-10">
            {roadmap.map((semester, idx) => (
              <div key={idx}>
                <h2 className="text-2xl font-semibold text-black mb-4">
                  {semester.season} {semester.year}
                </h2>
                <div className="border-b-2 border-gray-300 pb-4">
                  <ul className="space-y-2 ml-6">
                    {semester.courses.map((course, courseIdx) => (
                      <li key={courseIdx} className="text-black text-lg list-disc">
                        {course}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
