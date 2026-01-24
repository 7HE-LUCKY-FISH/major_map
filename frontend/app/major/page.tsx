"use client"

import { Navigation } from "@/components/navigation"
import { useState } from "react"
import { useRouter } from "next/navigation"

export default function MajorPage() {
  const router = useRouter()
  const [selectedMajor, setSelectedMajor] = useState("Software Engineering")
  const [completedCourses, setCompletedCourses] = useState<string[]>(["CMPE 50", "CMPE 110"])

  const majors = ["Software Engineering", "Electrical Engineering", "Computer Science", "Computer Engineering"]

  const leftColumnCourses = ["Biol 10", "Chem 1A", "CMPE 30", "CMPE 50"]
  const rightColumnCourses = ["CMPE 102", "CMPE 110", "CMPE 120", "CMPE 124"]

  const toggleCourse = (course: string) => {
    setCompletedCourses((prev) => (prev.includes(course) ? prev.filter((c) => c !== course) : [...prev, course]))
  }

  const handleSubmit = () => {
    // Store the selected data for the roadmap page
    sessionStorage.setItem("selectedMajor", selectedMajor)
    sessionStorage.setItem("completedCourses", JSON.stringify(completedCourses))
    router.push("/roadmap")
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />

      <main className="flex-1 bg-white py-12 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Page Title */}
          <h1 className="text-5xl font-normal text-black text-center mb-8">Major</h1>

          {/* Major Dropdown */}
          <div className="flex justify-center mb-12">
            <select
              value={selectedMajor}
              onChange={(e) => setSelectedMajor(e.target.value)}
              className="w-64 px-4 py-2 border-2 border-black bg-white text-black text-lg appearance-none cursor-pointer"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 20 20'%3E%3Cpath fill='none' stroke='%23000' strokeWidth='2' d='M5 7l5 5 5-5'/%3E%3C/svg%3E")`,
                backgroundRepeat: "no-repeat",
                backgroundPosition: "right 12px center",
              }}
            >
              {majors.map((major) => (
                <option key={major} value={major}>
                  {major}
                </option>
              ))}
            </select>
          </div>

          {/* Course Selection Section */}
          <div className="mb-8">
            <h2 className="text-xl text-black text-center mb-6">
              Required Major Courses
              <br />
              (Select your completed courses)
            </h2>

            {/* Two Column Course Layout */}
            <div className="grid grid-cols-2 gap-x-32 gap-y-4 max-w-2xl mx-auto">
              {/* Left Column */}
              <div className="space-y-4">
                {leftColumnCourses.map((course) => (
                  <label key={course} className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={completedCourses.includes(course)}
                      onChange={() => toggleCourse(course)}
                      className="w-5 h-5 border-2 border-black cursor-pointer"
                    />
                    <span className="text-black text-lg">{course}</span>
                  </label>
                ))}
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                {rightColumnCourses.map((course) => (
                  <label key={course} className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={completedCourses.includes(course)}
                      onChange={() => toggleCourse(course)}
                      className="w-5 h-5 border-2 border-black cursor-pointer"
                    />
                    <span className="text-black text-lg">{course}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center mt-12">
            <button
              onClick={handleSubmit}
              className="px-8 py-3 bg-[#5B9BD5] text-black font-semibold text-lg hover:opacity-90 transition-opacity"
            >
              Submit
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
