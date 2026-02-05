# Zettl UI

The frontend for Zettl - a personal knowledge management system powered by a knowledge graph.

## Features

### Capture (`/capture`)
Quickly capture notes with optional tags. Notes are automatically processed into the knowledge graph for intelligent retrieval later.

### Search (`/search`)
Search your notes using two modes:
- **Semantic** - AI-powered search using the knowledge graph to find conceptually related notes
- **Text** - Traditional chunk-based text matching

## Tech Stack

- **Framework**: Next.js 16 with React 19
- **Styling**: Tailwind CSS v4
- **Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React

## Getting Started

### Prerequisites

Ensure the backend API is running (default: `http://localhost:8000`). See the main project README for Docker setup.

### Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

## Project Structure

```
ui/
├── app/
│   ├── page.tsx          # Redirects to /capture
│   ├── capture/          # Note capture page
│   └── search/           # Note search page
├── components/
│   ├── capture-form.tsx  # Note input form
│   ├── search-form.tsx   # Search interface
│   └── ui/               # shadcn components
└── lib/
    ├── api.ts            # API client functions
    └── utils.ts          # Utility functions
```

## API Integration

The UI connects to the FastAPI backend:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notes` | POST | Create a new note |
| `/search` | POST | Search the knowledge graph |

## Building for Production

```bash
npm run build
npm start
```
