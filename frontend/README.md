# Frontend: React + TypeScript + Vite

```bash
npm install
npm run dev          # http://localhost:5173 (API expected at http://localhost:8000)
npm test             # Vitest + Testing Library
npm run test:coverage
npm run lint && npm run typecheck
npm run build
```

Set `VITE_API_URL` in `frontend/.env` if the API is not at `http://localhost:8000/api/v1`.

## Structure

```
src/
├── api/          # Typed fetch client (token, error normalization) + endpoint functions
├── auth/         # AuthContext, useAuth, protected/public routes
├── hooks/        # TanStack Query hooks, URL-synced filters, debounce
├── components/   # Presentational components (TaskCard, TaskForm, Modal, Pagination…)
├── pages/        # Route-level containers (Login, Register, Tasks)
├── utils/        # Date helpers
└── types.ts      # API types
```
