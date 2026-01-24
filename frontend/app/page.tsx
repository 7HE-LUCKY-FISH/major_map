import { Navigation } from "@/components/navigation"

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation Bar */}
      <Navigation />

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center bg-white">
        <h1 className="text-5xl font-normal text-black">Welcome to MajorMap</h1>
      </main>
    </div>
  )
}
