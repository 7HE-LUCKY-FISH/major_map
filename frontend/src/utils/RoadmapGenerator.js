export const RoadmapGenerator = (courses, completed) => {
  const remaining = courses.filter(
    c => !completed.includes(c.course)
  )

  const roadmap = []
  const done = [...completed]

  while (remaining.length > 0) {
    const semester = []
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
          .filter(c => c && !completed.includes(c.course))
        group = [course, ...coreqs]
      }

      if (semester.length + group.length > 5) continue

      group.forEach(g => {
        if (!semester.find(c => c.course === g.course)) {
          semester.push(g)
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