# LinkedIn Post Scheduler — Frontend

The frontend is a responsive Next.js dashboard for connecting a LinkedIn member, creating text or
single-image posts, publishing immediately, scheduling for later, and monitoring delivery status.

## Features

- LinkedIn OAuth entry point and local demo connection.
- Responsive login and dashboard layouts.
- Immediate and scheduled publishing modes.
- Current local date/time defaults with past-time validation.
- 3,000-character content limit and live character progress.
- JPEG, PNG, and GIF selection with client-side 5 MB validation.
- Configurable retry-attempt selection.
- Publishing activity with automatic five-second refreshes.
- Clickable activity cards and LinkedIn-style post preview modal.
- Attached-image preview using the backend image endpoint.
- Toast feedback for successful requests and API errors.

## Technology stack

| Purpose | Package |
|---|---|
| Framework | Next.js 15 App Router |
| UI runtime | React 19, TypeScript |
| Components | Material UI 7 and Material Icons |
| Styling | Emotion and `src/app/styles.css` |
| Server state | TanStack Query |
| HTTP client | Axios |
| Forms | React Hook Form |
| Validation | Zod |
| Notifications | React Hot Toast |
| Quality | ESLint, Prettier, TypeScript |

## Directory structure

```text
frontend/
├── src/
│   ├── @core/components/form-inputs/
│   │   ├── FormInputField.tsx      # React Hook Form text/date input wrapper
│   │   ├── FormSelect.tsx          # React Hook Form select wrapper
│   │   └── index.ts                # Component exports
│   ├── api/
│   │   ├── axiosInstance/index.ts  # Base URL, timeout, and error interceptor
│   │   ├── endpoints/index.ts      # API route definitions and URL helpers
│   │   ├── functions/linkedin/     # Typed Axios request functions
│   │   └── hooks/linkedin/         # TanStack Query queries and mutations
│   ├── app/
│   │   ├── layout.tsx              # Root HTML, font, metadata, and providers
│   │   ├── login/page.tsx          # Login route
│   │   ├── page.tsx                # Dashboard route
│   │   ├── providers.tsx           # Query, Material UI, and toast providers
│   │   └── styles.css              # Application-wide responsive styles
│   ├── module/
│   │   ├── auth/
│   │   │   ├── pages/LoginPage.tsx # OAuth and demo login experience
│   │   │   └── session.ts          # Browser local-storage navigation flag
│   │   └── dashboard/
│   │       ├── components/
│   │       │   ├── ConnectionCard.tsx
│   │       │   ├── PostActivity.tsx
│   │       │   └── SchedulePostForm.tsx
│   │       ├── pages/DashboardPage.tsx
│   │       └── validation/schedulePost.zod.ts
│   └── types/
│       ├── apps/linkedin/           # Request and status types
│       └── interface/linkedin/      # API response interfaces
├── .env.example
├── .prettierrc.json
├── eslint.config.mjs
├── next.config.ts
├── package.json
└── tsconfig.json
```

## Data flow

The API layer follows a small, predictable chain:

```text
Component
  -> TanStack Query hook
    -> typed Axios function
      -> endpoint definition
        -> FastAPI backend
```

- `endpoints/index.ts` owns path strings and absolute URL helpers.
- `functions/linkedin/index.api.ts` performs HTTP requests.
- `hooks/linkedin/hooks.ts` manages caching, polling, invalidation, and success notifications.
- Dashboard components render query state and invoke mutations.

The post list refreshes every five seconds. A successful post creation invalidates the post query so
the activity panel updates immediately instead of waiting for the next poll.

## Prerequisites

- Node.js 20 or newer.
- npm.
- The backend running and reachable from the browser.

## Environment configuration

Create a local environment file:

```bash
cp .env.example .env.local
```

| Variable | Required | Default/example | Description |
|---|---:|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `http://localhost:8000` | Public base URL of the FastAPI service. |

Because this variable is exposed to browser code, it must contain only a public URL—never a secret.
Restart the Next.js process after changing it.

## Installation and local development

```bash
npm install
npm run dev
```

Open `http://localhost:3000/login`.

Available commands:

| Command | Purpose |
|---|---|
| `npm run dev` | Start the Next.js development server. |
| `npm run build` | Create an optimized production build. |
| `npm run start` | Serve an existing production build. |
| `npm run typecheck` | Run TypeScript without emitting files. |
| `npm run lint` | Run ESLint across the frontend. |
| `npm run format:check` | Verify Prettier formatting. |
| `npm run format` | Format supported files with Prettier. |

Recommended validation before pushing:

```bash
npm run typecheck
npm run lint
npm run format:check
npm run build
```

## Routes

| Route | Component | Purpose |
|---|---|---|
| `/login` | `LoginPage` | Start real LinkedIn OAuth or create a demo connection. |
| `/` | `DashboardPage` | View the connection, compose posts, and monitor activity. |

After OAuth, the backend redirects to `/?linkedin=connected&connection_id=...`. The dashboard records
a browser session flag, removes the query string, reloads connection data, and displays the app.

## Authentication behavior

`module/auth/session.ts` stores `postpilot-session=active` in local storage. It controls frontend
navigation and logout behavior only. It is not a secure session, cookie, or access-control system.
The backend currently exposes its routes without user authentication.

Before a public production deployment, replace this mechanism with authenticated server-managed
sessions or tokens, and enforce connection ownership in the backend.

## Post composer behavior

`SchedulePostForm.tsx` supports two publishing modes:

- **Post now** sends the browser's current timestamp. The backend stores it as due immediately.
- **Schedule post** reveals a `datetime-local` field, initially five minutes in the future.

The native input receives a minimum equal to the current local time, while the Zod schema performs an
independent future-time check. The selected local datetime is converted to an ISO timestamp before it
is submitted.

Content validation:

- Whitespace-only content is rejected.
- Content must be between 1 and 3,000 characters after trimming.
- Retry attempts must be between 1 and 10.

Image validation:

- Allowed MIME types: `image/jpeg`, `image/png`, and `image/gif`.
- Maximum size: 5 MB.
- The browser displays an object-URL preview before submission.
- On submission, the file is converted to base64 and sent with its MIME type and filename.

## Publishing activity and preview

`PostActivity.tsx` presents the newest backend records as clickable activity cards. Each card includes
the effective date, content excerpt, media indicator, attempt information, and current status.

Selecting a card opens a LinkedIn-style modal with:

- Member identity and visibility metadata.
- Full post content.
- The stored image at `GET /api/v1/posts/{id}/image`.
- A feed-style reaction and action preview.
- Private delivery details such as status, scheduled/published time, attempts, and errors.

The media frame uses intrinsic image sizing with `max-width` and `max-height`, so the full image is
shown without stretching or cropping.

## API endpoints used

| Method | Path | Frontend usage |
|---|---|---|
| GET | `/api/v1/auth/linkedin/authorize` | Redirect browser into LinkedIn OAuth. |
| GET | `/api/v1/connections` | Load the connected member. |
| POST | `/api/v1/connections/mock` | Create a demo connection in mock mode. |
| GET | `/api/v1/posts?limit=50` | Load publishing activity. |
| POST | `/api/v1/posts` | Create an immediate or scheduled post. |
| GET | `/api/v1/posts/{id}/image` | Render attached media in the post preview. |

Every post creation generates a fresh UUID using `crypto.randomUUID()` and sends it in the
`Idempotency-Key` header.

## Styling and responsiveness

The Material UI theme is defined in `src/app/providers.tsx`; the detailed application styles are in
`src/app/styles.css`. The layout uses a two-column dashboard on larger screens, collapses the
navigation at tablet widths, and becomes a single-column interface on small screens. The preview
modal also collapses its publishing-detail grid on mobile.

## Production deployment

1. Set `NEXT_PUBLIC_API_BASE_URL` to the public HTTPS backend origin.
2. Run `npm ci` and `npm run build`.
3. Start with `npm run start`, or deploy using a platform that supports Next.js 15.
4. Add the frontend origin to the backend's `CORS_ORIGINS` and `FRONTEND_URL`.
5. Ensure the backend OAuth callback redirects to the production frontend.

Do not deploy the current local-storage navigation flag as the only authentication mechanism for a
multi-user or public application.

## Troubleshooting

- **Unable to reach the API:** confirm the backend is running and `NEXT_PUBLIC_API_BASE_URL` is
  correct from the browser's perspective.
- **Demo connection returns 404:** set `LINKEDIN_MOCK_MODE=true` in the backend and restart it.
- **OAuth returns to the wrong page:** check the backend `FRONTEND_URL`.
- **Image preview is unavailable:** confirm the post has media and the backend image endpoint is
  reachable.
- **Scheduled date is rejected:** select a time later than the browser's current local time.
- **Old query data remains visible:** use Refresh or confirm the five-second query polling is active.
