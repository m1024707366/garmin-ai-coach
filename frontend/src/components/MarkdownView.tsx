import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownViewProps {
  content: string
  className?: string
}

const markdownComponents: Components = {
  h1: ({ ...props }) => <h1 className="mb-4 mt-6 text-2xl font-bold text-slate-900" {...props} />,
  h2: ({ ...props }) => <h2 className="mb-3 mt-6 text-xl font-semibold text-slate-900" {...props} />,
  h3: ({ ...props }) => <h3 className="mb-2 mt-4 text-lg font-semibold text-slate-900" {...props} />,
  p: ({ ...props }) => <p className="mb-3 leading-relaxed text-slate-700" {...props} />,
  ul: ({ ...props }) => <ul className="mb-4 list-inside list-disc space-y-1 text-slate-700" {...props} />,
  ol: ({ ...props }) => <ol className="mb-4 list-inside list-decimal space-y-1 text-slate-700" {...props} />,
  strong: ({ ...props }) => <strong className="font-semibold text-slate-900" {...props} />,
  blockquote: ({ ...props }) => (
    <blockquote className="my-4 border-l-4 border-orange-400/80 pl-4 italic text-slate-600" {...props} />
  ),
  code: ({ ...props }) => (
    <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm font-mono text-slate-800" {...props} />
  ),
}

export function MarkdownView({ content, className = '' }: MarkdownViewProps) {
  return (
    <div className={`prose max-w-none ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
