import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MermaidBlock } from "./MermaidBlock";

type MarkdownMessageProps = {
  content: string;
  pending?: boolean;
};

const markdownComponents: Components = {
  a({ href, children, ...props }) {
    let resolvedHref = href;
    if (
      href &&
      typeof window !== "undefined" &&
      href.startsWith("/workspace/download")
    ) {
      resolvedHref = `${window.location.origin}${href}`;
    }

    return (
      <a
        {...props}
        className="markdown-link"
        href={resolvedHref}
        rel="noreferrer"
        target="_blank"
      >
        {children}
      </a>
    );
  },
  code({ inline, className, children, ...props }) {
    const code = String(children).replace(/\n$/, "");
    const language = className?.replace(/^language-/, "") || "";

    if (inline) {
      return (
        <code {...props} className="markdown-inline-code">
          {children}
        </code>
      );
    }

    if (language === "mermaid") {
      return <MermaidBlock chart={code} />;
    }

    return (
      <pre className="markdown-pre">
        <code {...props} className={className}>
          {code}
        </code>
      </pre>
    );
  },
  pre({ children }) {
    return <>{children}</>;
  },
};

export function MarkdownMessage({ content, pending = false }: MarkdownMessageProps) {
  const value = content || (pending ? "正在生成回答..." : "");

  return (
    <div className="markdown-message">
      <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
        {value}
      </ReactMarkdown>
    </div>
  );
}
