import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  resolve: {
    preserveSymlinks: true,
  },
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup/vitest.setup.js'],
    css: true,
    coverage: {
      enabled: true,
      provider: 'v8',
      reporter: ['text', 'html', 'lcov', 'json-summary'],
      reportsDirectory: '../docs/evaluation/coverage',
      include: [
        'src/App.jsx',
        'src/components/Navbar/Navbar.jsx',
        'src/components/Pages/Home.jsx',
        'src/components/Pages/Search.jsx',
        'src/components/Pages/Major.jsx',
        'src/components/Pages/Roadmap.jsx',
        'src/components/Pages/Schedules.jsx',
        'src/utils/CSVparser.js',
        'src/utils/CourseLinks.js',
        'src/utils/RoadmapGenerator.js'
      ],
      exclude: [
        'src/main.jsx',
        'src/components/Pages/index.js',
        'src/components/Pages/Account.jsx',
        'src/components/Pages/Login.jsx',
        'src/components/Pages/Register.jsx',
        'src/utils/AuthContext.js',
        'src/utils/AuthContext.jsx',
        'src/utils/CourseContext.js',
        'src/utils/CourseContext.jsx',
        'src/utils/ProfessorLinksRMP.js',
        'src/data/**'
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 75,
        statements: 90
      }
    }
  }
})
