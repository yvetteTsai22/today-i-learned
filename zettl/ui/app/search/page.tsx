import { SearchForm } from '@/components/search-form';

export default function SearchPage() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-background py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-foreground mb-2">Search</h1>
        <p className="text-muted-foreground mb-8">
          Search your knowledge graph
        </p>
        <SearchForm />
      </div>
    </div>
  );
}
