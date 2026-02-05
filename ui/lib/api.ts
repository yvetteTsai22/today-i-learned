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

export type SearchType = 'graph_completion' | 'chunks';

export interface SearchRequest {
  query: string;
  search_type?: SearchType;
}

export interface SearchResponse {
  results: string[];
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
