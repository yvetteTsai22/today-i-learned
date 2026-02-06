import { SearchForm } from '@/components/search-form';
import Link from 'next/link';
import { PenLine, Sparkles } from 'lucide-react';

export default function SearchPage() {
  return (
    <main className="min-h-screen bg-teal-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-teal-900 text-center mb-2">
          Zettl
        </h1>
        <p className="text-teal-700 text-center mb-8">
          Search your knowledge graph
        </p>

        <SearchForm />

        <div className="mt-8 flex justify-center gap-6">
          <Link
            href="/capture"
            className="inline-flex items-center gap-2 text-teal-600 hover:text-teal-700 transition-colors"
          >
            <PenLine className="h-4 w-4" />
            Capture notes
          </Link>
          <Link
            href="/digest"
            className="inline-flex items-center gap-2 text-teal-600 hover:text-teal-700 transition-colors"
          >
            <Sparkles className="h-4 w-4" />
            Weekly digest
          </Link>
        </div>
      </div>
    </main>
  );
}
