import Link from "next/link"
import { GraduationCap } from "lucide-react"

export function Navigation() {
  return (
    <nav className="bg-[#5B9BD5] px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <GraduationCap className="w-10 h-10 text-black" />
          <span className="text-2xl font-bold text-black">MajorMap</span>
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-8">
          <Link href="/" className="text-black font-medium hover:opacity-80 transition-opacity">
            Home
          </Link>
          <Link href="/major" className="text-black font-medium hover:opacity-80 transition-opacity">
            Major
          </Link>
          <Link href="/roadmap" className="text-black font-medium hover:opacity-80 transition-opacity">
            Roadmap
          </Link>
          <Link href="/schedules" className="text-black font-medium hover:opacity-80 transition-opacity">
            Schedules
          </Link>
          <Link href="/courses" className="text-black font-medium hover:opacity-80 transition-opacity">
            Courses
          </Link>
        </div>
      </div>
    </nav>
  )
}
