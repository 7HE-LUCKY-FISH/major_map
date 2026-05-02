export const RoadmapGenerator = (courses, completed, preferredUnits = 15) => {
  const remaining = courses.filter(
    c => !completed.includes(c.course)
  )

  const roadmap = []
  const done = [...completed]

  while (remaining.length > 0) {
    const semester = []
    let currentSemesterUnits = 0;
    
    for (let i = 0; i < remaining.length; i++) {
      const course = remaining[i]
      if (semester.find(c => c.course === course.course)) continue

      const prereqsMet = course.prerequisites.every(pr => {
        if (Array.isArray(pr)) {
          return pr.some(p => done.includes(p))
        }
        return done.includes(pr)
      })

      if (!prereqsMet) continue
      let group = [course]

      if (course.corequisites && course.corequisites.length > 0) {
        const coreqs = course.corequisites
          .map(code => courses.find(c => c.course === code))
          .filter(c => c && !done.includes(c.course))
        group = [course, ...coreqs]
      }

      const groupUnits = group.reduce((sum, g) => sum + (g.units || 3), 0);

      if (semester.length > 0 && currentSemesterUnits + groupUnits > preferredUnits) continue

      group.forEach(g => {
        if (!semester.find(c => c.course === g.course)) {
          semester.push(g)
          currentSemesterUnits += (g.units || 3)
        }
      })
    }

    semester.forEach(c => {
      done.push(c.course)
      const index = remaining.findIndex(r => r.course === c.course)
      if (index !== -1) remaining.splice(index, 1)
    })
    
    if (semester.length === 0) break
    roadmap.push(semester)
  }
  return roadmap
}