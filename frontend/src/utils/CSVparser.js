import Papa from "papaparse"

export const loadCSV = async (path) => {
  const response = await fetch(path)
  const text = await response.text()

  return new Promise((resolve) => {
    Papa.parse(text, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        resolve(results.data)
      }
    })
  })
}