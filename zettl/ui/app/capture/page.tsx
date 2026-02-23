import { CaptureForm } from '@/components/capture-form';

export default function CapturePage() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-background py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-foreground mb-2">Capture</h1>
        <p className="text-muted-foreground mb-8">
          Capture your knowledge. Let the connections emerge.
        </p>
        <CaptureForm />
      </div>
    </div>
  );
}
