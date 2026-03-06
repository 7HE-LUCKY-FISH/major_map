export const ScheduleGenerator = (courses) => {
  if (!courses || courses.length === 0) return []
  const schedules = []
  for(let i=0;i<3;i++){
    const shuffled = [...courses].sort(()=>Math.random()-0.5)
    schedules.push(shuffled)
  }
  return schedules
}