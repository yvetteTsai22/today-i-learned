const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface NoteCreate {
  content: string;
  source?: 'manual' | 'notion' | 'agent' | 'ui';
  tags?: string[];
  source_reference?: string;
}

export interface NoteResponse {
  id: string;
  content: string;
  source: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export async function createNote(note: NoteCreate): Promise<NoteResponse> {
  const response = await fetch(`${API_URL}/notes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...note,
      source: note.source || 'ui',
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create note: ${response.statusText}`);
  }

  return response.json();
}

// Note management

export interface NoteUpdate {
  content: string;
  tags?: string[];
}

export async function updateNote(id: string, update: NoteUpdate): Promise<NoteResponse> {
  const response = await fetch(`${API_URL}/notes/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error(`Failed to update note: ${response.statusText}`);
  }

  return response.json();
}

export async function deleteNote(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/notes/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete note: ${response.statusText}`);
  }
}

export type SearchType = 'graph_completion' | 'chunks';

export interface SearchRequest {
  query: string;
  search_type?: SearchType;
}

export interface SearchResultItem {
  id: string;
  content: string;
  source: 'manual' | 'notion' | 'agent' | 'ui';
  tags: string[];
  created_at: string;
}

export interface SearchResponse {
  results: SearchResultItem[];
  query: string;
}

export async function searchNotes(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_URL}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: request.query,
      search_type: request.search_type || 'graph_completion',
    }),
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  return response.json();
}

// Digest types and API functions

export interface TopicSuggestion {
  title: string;
  reasoning: string;
  relevant_chunks: string[];
}

export interface DigestResponse {
  id: string;
  summary: string;
  suggested_topics: TopicSuggestion[];
  week_start: string;
  week_end: string;
  created_at: string;
}

export type ContentFormat = 'blog' | 'linkedin' | 'x_thread' | 'video_script';

export interface ContentGenerationRequest {
  topic: string;
  source_chunks: string[];
  formats: ContentFormat[];
}

export interface ContentGenerationResponse {
  topic: string;
  blog: string | null;
  linkedin: string | null;
  x_thread: string | null;
  video_script: string | null;
}

export async function generateDigest(
  forceRefresh: boolean = false
): Promise<DigestResponse> {
  const params = forceRefresh ? '?force_refresh=true' : '';
  const response = await fetch(`${API_URL}/digest${params}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to generate digest: ${response.statusText}`);
  }

  return response.json();
}

export async function generateContent(
  request: ContentGenerationRequest
): Promise<ContentGenerationResponse> {
  const response = await fetch(`${API_URL}/digest/content`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate content: ${response.statusText}`);
  }

  return response.json();
}

// Stats

export interface StatsResponse {
  notes: number;
  topics: number;
  connections: number;
  this_week: number;
}

export async function fetchStats(): Promise<StatsResponse> {
  const response = await fetch(`${API_URL}/stats`);

  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }

  return response.json();
}

// Graph

export interface GraphNode {
  id: string;
  label: string;
  content: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function fetchGraph(): Promise<GraphResponse> {
  const response = await fetch(`${API_URL}/graph`);

  if (!response.ok) {
    throw new Error(`Failed to fetch graph: ${response.statusText}`);
  }

  return response.json();
}
