# LinkedIn Post Scheduler — Frontend

Next.js dashboard for connecting one LinkedIn account, scheduling text or single-image posts, and
monitoring publishing status.

```bash
cp .env.example .env.local
npm install
npm run dev
```

The app runs at `http://localhost:3000` and uses the FastAPI backend at `http://localhost:8000`.
API code follows `endpoints -> functions -> hooks -> components`; forms use React Hook Form and Zod.
