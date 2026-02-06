'use client';

import { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  generateDigest,
  generateContent,
  DigestResponse,
  TopicSuggestion,
  ContentGenerationResponse,
  ContentFormat,
} from '@/lib/api';
import {
  Sparkles,
  Calendar,
  ChevronDown,
  ChevronUp,
  FileText,
  Linkedin,
  Twitter,
  Video,
  Loader2,
  Copy,
  Check,
} from 'lucide-react';

const FORMAT_CONFIG: Record<
  ContentFormat,
  { label: string; icon: React.ReactNode; description: string }
> = {
  blog: {
    label: 'Blog Post',
    icon: <FileText className="h-4 w-4" />,
    description: 'Long-form article',
  },
  linkedin: {
    label: 'LinkedIn',
    icon: <Linkedin className="h-4 w-4" />,
    description: 'Professional post',
  },
  x_thread: {
    label: 'X Thread',
    icon: <Twitter className="h-4 w-4" />,
    description: 'Thread format',
  },
  video_script: {
    label: 'Video Script',
    icon: <Video className="h-4 w-4" />,
    description: 'Video narration',
  },
};

interface TopicCardProps {
  topic: TopicSuggestion;
  onGenerateContent: (
    topic: string,
    chunks: string[],
    formats: ContentFormat[]
  ) => Promise<ContentGenerationResponse>;
}

function TopicCard({ topic, onGenerateContent }: TopicCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [selectedFormats, setSelectedFormats] = useState<ContentFormat[]>([
    'blog',
  ]);
  const [generatedContent, setGeneratedContent] =
    useState<ContentGenerationResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedFormat, setCopiedFormat] = useState<string | null>(null);

  const toggleFormat = (format: ContentFormat) => {
    setSelectedFormats((prev) =>
      prev.includes(format)
        ? prev.filter((f) => f !== format)
        : [...prev, format]
    );
  };

  const handleGenerate = async () => {
    if (selectedFormats.length === 0) return;
    setIsGenerating(true);
    try {
      const content = await onGenerateContent(
        topic.title,
        topic.relevant_chunks,
        selectedFormats
      );
      setGeneratedContent(content);
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = async (text: string, format: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedFormat(format);
    setTimeout(() => setCopiedFormat(null), 2000);
  };

  return (
    <Card className="transition-all duration-200 hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="text-lg text-teal-900">{topic.title}</CardTitle>
            <CardDescription className="mt-1">{topic.reasoning}</CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="shrink-0 cursor-pointer"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-4">
          {topic.relevant_chunks.length > 0 && (
            <div>
              <p className="text-sm font-medium text-teal-800 mb-2">
                Related Knowledge ({topic.relevant_chunks.length} chunks)
              </p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {topic.relevant_chunks.map((chunk, idx) => (
                  <p
                    key={idx}
                    className="text-sm text-slate-600 bg-slate-50 p-2 rounded border-l-2 border-teal-300"
                  >
                    {chunk}
                  </p>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="text-sm font-medium text-teal-800 mb-2">
              Generate Content
            </p>
            <div className="flex flex-wrap gap-2 mb-3">
              {(Object.keys(FORMAT_CONFIG) as ContentFormat[]).map((format) => (
                <Badge
                  key={format}
                  variant={selectedFormats.includes(format) ? 'default' : 'outline'}
                  className="cursor-pointer transition-colors"
                  onClick={() => toggleFormat(format)}
                >
                  {FORMAT_CONFIG[format].icon}
                  <span className="ml-1">{FORMAT_CONFIG[format].label}</span>
                </Badge>
              ))}
            </div>
            <Button
              onClick={handleGenerate}
              disabled={selectedFormats.length === 0 || isGenerating}
              className="w-full bg-teal-600 hover:bg-teal-700 cursor-pointer"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate {selectedFormats.length} Format
                  {selectedFormats.length !== 1 && 's'}
                </>
              )}
            </Button>
          </div>

          {generatedContent && (
            <div className="space-y-4 pt-4 border-t">
              {(Object.keys(FORMAT_CONFIG) as ContentFormat[]).map((format) => {
                const content = generatedContent[format];
                if (!content) return null;
                return (
                  <div key={format} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm font-medium text-teal-800">
                        {FORMAT_CONFIG[format].icon}
                        {FORMAT_CONFIG[format].label}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(content, format)}
                        className="h-8 cursor-pointer"
                      >
                        {copiedFormat === format ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <div className="bg-white border rounded-lg p-4 text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {content}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

export function DigestPanel() {
  const [digest, setDigest] = useState<DigestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateDigest = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await generateDigest();
      setDigest(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate digest');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateContent = async (
    topic: string,
    chunks: string[],
    formats: ContentFormat[]
  ) => {
    return generateContent({ topic, source_chunks: chunks, formats });
  };

  const formatDateRange = (start: string, end: string) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const options: Intl.DateTimeFormatOptions = {
      month: 'short',
      day: 'numeric',
    };
    return `${startDate.toLocaleDateString('en-US', options)} - ${endDate.toLocaleDateString('en-US', options)}`;
  };

  return (
    <div className="space-y-6">
      {!digest ? (
        <Card className="border-dashed border-2 border-teal-200 bg-teal-50/50">
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <div className="mx-auto w-12 h-12 rounded-full bg-teal-100 flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-teal-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-teal-900">
                  Weekly Digest
                </h3>
                <p className="text-sm text-teal-600 mt-1">
                  Generate a summary of your knowledge from the past week
                </p>
              </div>
              <Button
                onClick={handleGenerateDigest}
                disabled={isLoading}
                className="bg-teal-600 hover:bg-teal-700 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Digest
                  </>
                )}
              </Button>
              {error && (
                <p className="text-sm text-red-600 mt-2">{error}</p>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl text-teal-900">
                    Weekly Summary
                  </CardTitle>
                  <CardDescription className="flex items-center gap-1 mt-1">
                    <Calendar className="h-3 w-3" />
                    {formatDateRange(digest.week_start, digest.week_end)}
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateDigest}
                  disabled={isLoading}
                  className="cursor-pointer"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Refresh'
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700 leading-relaxed">{digest.summary}</p>
            </CardContent>
          </Card>

          <div>
            <h3 className="text-lg font-semibold text-teal-900 mb-4">
              Suggested Topics ({digest.suggested_topics.length})
            </h3>
            <div className="space-y-4">
              {digest.suggested_topics.map((topic, idx) => (
                <TopicCard
                  key={idx}
                  topic={topic}
                  onGenerateContent={handleGenerateContent}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
