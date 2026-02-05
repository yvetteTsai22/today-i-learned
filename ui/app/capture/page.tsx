import { CaptureForm } from '@/components/capture-form';
import Link from 'next/link';
import { Search } from 'lucide-react';

export default function CapturePage() {
  return (
    <main className="min-h-screen bg-teal-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-teal-900 text-center mb-8">
          Zettl
        </h1>
        <p className="text-teal-700 text-center mb-8">
          Capture your knowledge. Let the connections emerge.
        </p>
        <CaptureForm />

        <div className="mt-8 text-center">
          <Link
            href="/search"
            className="inline-flex items-center gap-2 text-teal-600 hover:text-teal-700 transition-colors"
          >
            <Search className="h-4 w-4" />
            Search your notes
          </Link>
        </div>
      </div>
    </main>
  );
}
