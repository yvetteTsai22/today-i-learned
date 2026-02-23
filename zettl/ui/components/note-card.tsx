'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, Clock, FileText, Globe, Bot, Monitor, Pencil, Trash2, X, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { updateNote, deleteNote } from '@/lib/api';
import { cn } from '@/lib/utils';

type NoteSource = 'manual' | 'notion' | 'agent' | 'ui';

interface Note {
  id: string;
  content: string;
  source: NoteSource;
  tags: string[];
  created_at: string;
  updated_at: string;
}

interface NoteCardProps {
  note: Note;
  defaultExpanded?: boolean;
  className?: string;
  onUpdated?: (note: Note) => void;
  onDeleted?: (id: string) => void;
}

const SOURCE_CONFIG: Record<NoteSource, { label: string; icon: typeof FileText; className: string }> = {
  manual: {
    label: 'Manual',
    icon: FileText,
    className: 'bg-secondary text-secondary-foreground',
  },
  notion: {
    label: 'Notion',
    icon: Globe,
    className: 'bg-primary/10 text-primary',
  },
  agent: {
    label: 'AI Agent',
    icon: Bot,
    className: 'bg-chart-3/20 text-chart-3',
  },
  ui: {
    label: 'Capture',
    icon: Monitor,
    className: 'bg-chart-1/20 text-chart-1',
  },
};

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

// Simple markdown-like rendering for common patterns
function renderContent(content: string): React.ReactNode {
  // Split into paragraphs
  const paragraphs = content.split(/\n\n+/);

  return paragraphs.map((paragraph, i) => {
    // Handle headers
    if (paragraph.startsWith('### ')) {
      return (
        <h4 key={i} className="text-sm font-semibold text-foreground mt-3 mb-1">
          {paragraph.slice(4)}
        </h4>
      );
    }
    if (paragraph.startsWith('## ')) {
      return (
        <h3 key={i} className="text-base font-semibold text-foreground mt-4 mb-2">
          {paragraph.slice(3)}
        </h3>
      );
    }
    if (paragraph.startsWith('# ')) {
      return (
        <h2 key={i} className="text-lg font-bold text-foreground mt-4 mb-2">
          {paragraph.slice(2)}
        </h2>
      );
    }

    // Handle bullet lists
    if (paragraph.match(/^[-*]\s/m)) {
      const items = paragraph.split(/\n/).filter((line) => line.match(/^[-*]\s/));
      return (
        <ul key={i} className="list-disc list-inside space-y-1 text-sm text-muted-foreground my-2">
          {items.map((item, j) => (
            <li key={j}>{renderInlineFormatting(item.replace(/^[-*]\s/, ''))}</li>
          ))}
        </ul>
      );
    }

    // Handle code blocks
    if (paragraph.startsWith('```')) {
      const codeContent = paragraph.replace(/^```\w*\n?/, '').replace(/```$/, '');
      return (
        <pre key={i} className="bg-muted rounded-md p-3 text-xs font-mono overflow-x-auto my-2">
          <code>{codeContent}</code>
        </pre>
      );
    }

    // Regular paragraph
    return (
      <p key={i} className="text-sm text-muted-foreground leading-relaxed">
        {renderInlineFormatting(paragraph)}
      </p>
    );
  });
}

// Handle inline formatting: **bold**, *italic*, `code`, [links](url)
function renderInlineFormatting(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Bold
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    // Italic
    const italicMatch = remaining.match(/\*(.+?)\*/);
    // Inline code
    const codeMatch = remaining.match(/`([^`]+)`/);
    // Links
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);

    const matches = [
      { match: boldMatch, type: 'bold' },
      { match: italicMatch, type: 'italic' },
      { match: codeMatch, type: 'code' },
      { match: linkMatch, type: 'link' },
    ].filter((m) => m.match !== null);

    if (matches.length === 0) {
      parts.push(remaining);
      break;
    }

    // Find earliest match
    const earliest = matches.reduce((a, b) =>
      (a.match!.index ?? Infinity) < (b.match!.index ?? Infinity) ? a : b
    );

    const match = earliest.match!;
    const index = match.index!;

    // Add text before match
    if (index > 0) {
      parts.push(remaining.slice(0, index));
    }

    // Add formatted content
    switch (earliest.type) {
      case 'bold':
        parts.push(
          <strong key={key++} className="font-semibold text-foreground">
            {match[1]}
          </strong>
        );
        break;
      case 'italic':
        parts.push(
          <em key={key++} className="italic">
            {match[1]}
          </em>
        );
        break;
      case 'code':
        parts.push(
          <code key={key++} className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono">
            {match[1]}
          </code>
        );
        break;
      case 'link':
        parts.push(
          <a
            key={key++}
            href={match[2]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline underline-offset-2 hover:text-primary/80"
          >
            {match[1]}
          </a>
        );
        break;
    }

    remaining = remaining.slice(index + match[0].length);
  }

  return parts.length === 1 ? parts[0] : parts;
}

export function NoteCard({ note, defaultExpanded = false, className, onUpdated, onDeleted }: NoteCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(note.content);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleSave = async () => {
    if (!editContent.trim()) return;
    setIsSaving(true);
    try {
      const updated = await updateNote(note.id, {
        content: editContent.trim(),
        tags: note.tags,
      });
      toast.success('Note updated');
      setIsEditing(false);
      onUpdated?.({ ...note, content: updated.content, tags: updated.tags, updated_at: updated.updated_at });
    } catch {
      toast.error('Failed to update note');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteNote(note.id);
      toast.success('Note deleted');
      onDeleted?.(note.id);
    } catch {
      toast.error('Failed to delete note');
    } finally {
      setIsDeleting(false);
      setConfirmDelete(false);
    }
  };

  const sourceConfig = SOURCE_CONFIG[note.source];
  const SourceIcon = sourceConfig.icon;

  // Preview: first 150 chars or first paragraph
  const previewLength = 150;
  const needsExpansion = note.content.length > previewLength;
  const preview = needsExpansion
    ? note.content.slice(0, previewLength).trim() + '...'
    : note.content;

  return (
    <Card
      className={cn(
        'group transition-all duration-200 hover:shadow-md cursor-pointer',
        'border-border/50 hover:border-border',
        className
      )}
      onClick={() => needsExpansion && setIsExpanded(!isExpanded)}
    >
      <CardHeader className="pb-2 space-y-2">
        {/* Top row: Source badge + Timestamp */}
        <div className="flex items-center justify-between gap-2">
          <Badge variant="secondary" className={cn('gap-1 text-xs', sourceConfig.className)}>
            <SourceIcon className="h-3 w-3" />
            {sourceConfig.label}
          </Badge>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatRelativeTime(note.created_at)}
          </span>
        </div>

        {/* Tags row */}
        {note.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {note.tags.map((tag) => (
              <Badge
                key={tag}
                variant="outline"
                className="text-xs font-normal px-2 py-0 h-5 bg-background"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        {/* Content area */}
        <div
          className={cn(
            'overflow-hidden transition-all duration-300 ease-in-out',
            isExpanded ? 'max-h-[2000px]' : 'max-h-24'
          )}
        >
          {isEditing ? (
            <Textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="min-h-[150px] resize-none text-sm"
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <div className="prose-sm">
              {isExpanded ? renderContent(note.content) : (
                <p className="text-sm text-muted-foreground leading-relaxed">{preview}</p>
              )}
            </div>
          )}
        </div>

        {/* Expand/Collapse indicator */}
        {needsExpansion && !isEditing && (
          <div
            className={cn(
              'flex items-center justify-center mt-2 pt-2 border-t border-border/50',
              'text-xs text-muted-foreground',
              'group-hover:text-foreground transition-colors'
            )}
          >
            <ChevronDown
              className={cn(
                'h-4 w-4 transition-transform duration-200',
                isExpanded && 'rotate-180'
              )}
            />
            <span className="ml-1">{isExpanded ? 'Show less' : 'Show more'}</span>
          </div>
        )}

        {/* Actions */}
        <div
          className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50"
          onClick={(e) => e.stopPropagation()}
        >
          {isEditing ? (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setIsEditing(false); setEditContent(note.content); }}
                disabled={isSaving}
                className="cursor-pointer"
              >
                <X className="h-3 w-3 mr-1" /> Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSave}
                disabled={isSaving || !editContent.trim()}
                className="cursor-pointer"
              >
                {isSaving ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Check className="h-3 w-3 mr-1" />}
                Save
              </Button>
            </>
          ) : confirmDelete ? (
            <>
              <span className="text-xs text-destructive">Delete this note?</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirmDelete(false)}
                disabled={isDeleting}
                className="cursor-pointer"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
                disabled={isDeleting}
                className="cursor-pointer"
              >
                {isDeleting ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Trash2 className="h-3 w-3 mr-1" />}
                Confirm
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setIsEditing(true); setIsExpanded(true); }}
                className="cursor-pointer"
              >
                <Pencil className="h-3 w-3 mr-1" /> Edit
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirmDelete(true)}
                className="text-destructive hover:text-destructive cursor-pointer"
              >
                <Trash2 className="h-3 w-3 mr-1" /> Delete
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
