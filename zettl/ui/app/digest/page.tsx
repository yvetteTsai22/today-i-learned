import { DigestPanel } from '@/components/digest-panel';
import { ThemeSwitcher } from '@/components/theme-switcher';
import Link from 'next/link';
import { PenLine, Search } from 'lucide-react';

export default function DigestPage() {
  return (
    <main className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header with Theme Switcher */}
        <div className="flex justify-end mb-4">
          <ThemeSwitcher />
        </div>

        <h1 className="text-3xl font-bold text-foreground text-center mb-2">
          Zettl
        </h1>
        <p className="text-muted-foreground text-center mb-8">
          Your weekly knowledge digest
        </p>

        <DigestPanel />

        <div className="mt-8 flex justify-center gap-6">
          <Link
            href="/capture"
            className="inline-flex items-center gap-2 text-primary hover:text-primary/80 transition-colors"
          >
            <PenLine className="h-4 w-4" />
            Capture notes
          </Link>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 text-primary hover:text-primary/80 transition-colors"
          >
            <Search className="h-4 w-4" />
            Search notes
          </Link>
        </div>
      </div>
    </main>
  );
}
