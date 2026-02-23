"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { MermaidDiagram } from "@/components/mermaid-diagram"

interface MarkdownContentProps {
  content: string
  className?: string
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div className={className}>
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // Headings
        h1: ({ children }) => (
          <h1 className="text-xl font-bold text-foreground mt-6 mb-3">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-lg font-semibold text-foreground mt-5 mb-2">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-base font-semibold text-foreground mt-4 mb-2">{children}</h3>
        ),

        // Paragraphs
        p: ({ children }) => (
          <p className="text-sm text-muted-foreground leading-relaxed mb-3">{children}</p>
        ),

        // Lists
        ul: ({ children }) => (
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground mb-3 ml-2">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground mb-3 ml-2">
            {children}
          </ol>
        ),
        li: ({ children }) => <li className="leading-relaxed">{children}</li>,

        // Code blocks — detect mermaid language for diagram rendering
        code: ({ className: codeClassName, children, ...props }) => {
          const match = /language-(\w+)/.exec(codeClassName || "")
          const language = match?.[1]
          const codeString = String(children).replace(/\n$/, "")

          // Mermaid diagram
          if (language === "mermaid") {
            return <MermaidDiagram chart={codeString} />
          }

          // Inline code (no language class, not inside a <pre>)
          if (!language) {
            return (
              <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono">
                {children}
              </code>
            )
          }

          // Regular code block
          return (
            <code className={codeClassName} {...props}>
              {children}
            </code>
          )
        },

        // Wrap code blocks in styled pre
        pre: ({ children }) => (
          <pre className="bg-muted rounded-md p-3 text-xs font-mono overflow-x-auto mb-3">
            {children}
          </pre>
        ),

        // Inline formatting
        strong: ({ children }) => (
          <strong className="font-semibold text-foreground">{children}</strong>
        ),
        em: ({ children }) => <em className="italic">{children}</em>,

        // Links
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline underline-offset-2 hover:text-primary/80"
          >
            {children}
          </a>
        ),

        // Blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-primary pl-4 my-3 text-sm text-muted-foreground italic">
            {children}
          </blockquote>
        ),

        // Tables (from remark-gfm)
        table: ({ children }) => (
          <div className="overflow-x-auto mb-3">
            <table className="min-w-full text-sm border-collapse">{children}</table>
          </div>
        ),
        th: ({ children }) => (
          <th className="border border-border px-3 py-2 text-left font-semibold bg-muted text-foreground">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-border px-3 py-2 text-muted-foreground">{children}</td>
        ),

        // Horizontal rule
        hr: () => <hr className="my-4 border-border" />,
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  )
}
