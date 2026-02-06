'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { searchNotes, SearchType } from '@/lib/api';
import { Search, Sparkles, FileText, Loader2 } from 'lucide-react';

interface SearchResult {
  content: string;
  index: number;
}

export function SearchForm() {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<SearchType>('graph_completion');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);

    try {
      const response = await searchNotes({
        query: query.trim(),
        search_type: searchType,
      });

      setResults(
        response.results.map((content, index) => ({
          content,
          index,
        }))
      );

      if (response.results.length === 0) {
        toast.info('No results found', {
          description: 'Try different keywords or search type.',
        });
      }
    } catch (error) {
      toast.error('Search failed', {
        description: 'Unable to search notes. Please try again.',
      });
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-foreground">Search Notes</CardTitle>
        </CardHeader>
        <form onSubmit={handleSearch}>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search your knowledge..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-input bg-background rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                disabled={isSearching}
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Search type:</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setSearchType('graph_completion')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors cursor-pointer ${
                    searchType === 'graph_completion'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Semantic
                </button>
                <button
                  type="button"
                  onClick={() => setSearchType('chunks')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors cursor-pointer ${
                    searchType === 'chunks'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                >
                  <FileText className="h-3.5 w-3.5" />
                  Text
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={!query.trim() || isSearching}
              className="w-full cursor-pointer"
            >
              {isSearching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </CardContent>
        </form>
      </Card>

      {hasSearched && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-foreground">
              Results {results.length > 0 && `(${results.length})`}
            </h2>
            {results.length > 0 && (
              <Badge variant="secondary">
                {searchType === 'graph_completion' ? 'Semantic' : 'Text'} search
              </Badge>
            )}
          </div>

          {results.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="py-8 text-center text-muted-foreground">
                <Search className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p>No notes found matching your query.</p>
                <p className="text-sm mt-1">Try different keywords or switch search type.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {results.map((result) => (
                <Card key={result.index} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="py-4">
                    <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">
                      {result.content}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
