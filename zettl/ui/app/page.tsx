import { Dashboard } from "@/components/dashboard";

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-background py-8 px-4 md:px-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-foreground mb-1">Dashboard</h1>
        <p className="text-muted-foreground mb-8">
          Your knowledge at a glance
        </p>
        <Dashboard />
      </div>
    </div>
  );
}
