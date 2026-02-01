"use client"

import { Navigation } from "@/components/navigation"
import { Search } from "lucide-react"
import { useState } from "react"

export default function CoursesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [searchType, setSearchType] = useState<"course" | "professor">("course")

  // Sample data for course search
  const allCourseData = [
    {
      semester: "Spring 2022",
      section: "Section 1",
      course: "BIOL 10",
      professor: "Sonia Cuellar-Ortiz",
      day: "MW",
      time: "01:30PM-02:45PM",
    },
    {
      semester: "Spring 2022",
      section: "Section 2",
      course: "BIOL 10",
      professor: "Brandon White",
      day: "TBA",
      time: "TBA (Online)",
    },
  ]

  // Sample data for professor search
  const allProfessorData = [
    {
      semester: "Spring 2022",
      course: "CMPE102",
      section: "1",
      professor: "Bhawandeep Singh Harsh",
      day: "MW",
      time: "01:30PM-02:45PM",
    },
    {
      semester: "Spring 2022",
      course: "CMPE 102",
      section: "2",
      professor: "Bhawandeep Singh Harsh",
      day: "MW",
      time: "03:00PM-04:15PM (Online)",
    },
  ]

  const courseResults = allCourseData.filter((item) =>
    item.course.toLowerCase().replace(/\s+/g, "").includes(searchQuery.toLowerCase().replace(/\s+/g, "")),
  )

  const professorResults = allProfessorData.filter((item) =>
    item.professor.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const showResults = searchQuery.trim().length > 0

  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      <main className="max-w-6xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-semibold mb-8">Course</h1>

        {/* Search Bar */}
        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-600" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={searchType === "course" ? "Search by course (e.g., BIOL 10)" : "Search by professor name"}
            className="w-full border-2 border-black px-12 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-[#5B9BD5]"
          />
        </div>

        {/* Radio Buttons */}
        <div className="flex items-center gap-6 mb-8">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="searchType"
              checked={searchType === "course"}
              onChange={() => setSearchType("course")}
              className="w-5 h-5 accent-gray-700"
            />
            <span className="text-lg font-medium">By Course</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="searchType"
              checked={searchType === "professor"}
              onChange={() => setSearchType("professor")}
              className="w-5 h-5 accent-gray-700"
            />
            <span className="text-lg font-medium">By Professor</span>
          </label>
        </div>

        {showResults && (
          <>
            {/* Results Table - By Course */}
            {searchType === "course" && (
              <div className="border-2 border-black">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Semester</th>
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Section</th>
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">
                        Professor
                      </th>
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Day</th>
                      <th className="border-b-2 border-black px-4 py-3 text-left font-semibold">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {courseResults.length > 0 ? (
                      courseResults.map((result, index) => (
                        <tr key={index} className={index !== courseResults.length - 1 ? "border-b-2 border-black" : ""}>
                          <td className="border-r-2 border-black px-4 py-3">{result.semester}</td>
                          <td className="border-r-2 border-black px-4 py-3">{result.section}</td>
                          <td className="border-r-2 border-black px-4 py-3">{result.professor}</td>
                          <td className="border-r-2 border-black px-4 py-3">{result.day}</td>
                          <td className="px-4 py-3">{result.time}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                          No courses found matching "{searchQuery}"
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Results Table - By Professor */}
            {searchType === "professor" && (
              <div className="border-2 border-black">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Semester</th>
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Course</th>
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Section</th>
                      <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Day</th>
                      <th className="border-b-2 border-black px-4 py-3 text-left font-semibold">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {professorResults.length > 0 ? (
                      professorResults.map((result, index) => (
                        <tr
                          key={index}
                          className={index !== professorResults.length - 1 ? "border-b-2 border-black" : ""}
                        >
                          <td className="border-r-2 border-black px-4 py-3">{result.semester}</td>
                          <td className="border-r-2 border-black px-4 py-3">{result.course}</td>
                          <td className="border-r-2 border-black px-4 py-3">{result.section}</td>
                          <td className="border-r-2 border-black px-4 py-3">{result.day}</td>
                          <td className="px-4 py-3">{result.time}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                          No professors found matching "{searchQuery}"
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
