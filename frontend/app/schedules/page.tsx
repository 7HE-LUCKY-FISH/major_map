import { Navigation } from "@/components/navigation"

export default function SchedulesPage() {
  const schedules = [
    {
      course: "BIOL 10",
      courseNo: "44801",
      professor: "Mary Poffenroth",
      day: "TBA",
      time: "TBA (Online)",
    },
    {
      course: "CHEM 1A",
      courseNo: "40801",
      professor: "Niloofar Salehi",
      day: "MWF",
      time: "01:30PM-02:45PM",
    },
    {
      course: "CMPE 30",
      courseNo: "44001",
      professor: "Faramarz Mortezaie",
      day: "MW",
      time: "03:00PM-04:15PM",
    },
    {
      course: "CMPE 102",
      courseNo: "44800",
      professor: "Michael Lam",
      day: "TR",
      time: "07:30AM-08:45AM",
    },
    {
      course: "CMPE 120",
      courseNo: "40000",
      professor: "Bhawandeep Singh Harsh",
      day: "TR",
      time: "06:30PM-08:45PM",
    },
  ]

  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      <main className="max-w-6xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-semibold text-center mb-12">Potential Predictive Schedules for Spring 2026</h1>

        <div className="mb-8">
          <h2 className="text-xl font-medium mb-4">Option 1:</h2>

          <div className="border-2 border-black">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Course</th>
                  <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Course No.</th>
                  <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Professor</th>
                  <th className="border-r-2 border-b-2 border-black px-4 py-3 text-left font-semibold">Day</th>
                  <th className="border-b-2 border-black px-4 py-3 text-left font-semibold">Time</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map((schedule, index) => (
                  <tr key={index} className={index !== schedules.length - 1 ? "border-b-2 border-black" : ""}>
                    <td className="border-r-2 border-black px-4 py-3">{schedule.course}</td>
                    <td className="border-r-2 border-black px-4 py-3">{schedule.courseNo}</td>
                    <td className="border-r-2 border-black px-4 py-3">{schedule.professor}</td>
                    <td className="border-r-2 border-black px-4 py-3">{schedule.day}</td>
                    <td className="px-4 py-3">{schedule.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}
