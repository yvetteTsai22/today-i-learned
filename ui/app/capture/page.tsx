import { CaptureForm } from '@/components/capture-form';

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
      </div>
    </main>
  );
}
