export type ChatRequest = {
  message: string;
  thread_id?: string;
  user_id?: string;
  attachments?: string[];
  message_id?: number;
};

export type ThreadTitle = {
  thread_id: string;
  title: string;
  updated_at: string;
};

export type ThreadMessage = {
  id: number;
  role: string;
  content: string;
  attachments?: Array<{
    file_id: number;
    path: string;
    name: string;
  }>;
};

export type MessageAttachment = {
  file_id?: number;
  path: string;
  name: string;
};

export type SkillItem = Record<string, unknown>;

const DEFAULT_BASE = "http://localhost:8080";

export function apiBase() {
  return (import.meta as any).env?.VITE_API_BASE || DEFAULT_BASE;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return (await res.json()) as T;
}

export async function getThreads(user_id: string) {
  return apiFetch<{ threads: ThreadTitle[] }>("/threads/getTitles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id }),
  });
}

export async function deleteThread(user_id: string, thread_id: string) {
  return apiFetch<{ success: boolean }>("/thread/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, thread_id }),
  });
}

export async function getThreadMessages(user_id: string, thread_id: string, limit = 200) {
  return apiFetch<{ messages: ThreadMessage[] }>("/thread/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, thread_id, limit }),
  });
}

export async function createMessage(user_id: string, thread_id: string, content: string, role = "user") {
  return apiFetch<{
    message: {
      id: number;
      user_id: string;
      thread_id: string;
      role: string;
      content: string;
      created_at: string;
    };
  }>("/message/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, thread_id, content, role }),
  });
}

export async function uploadWorkspaceFile(
  user_id: string,
  thread_id: string,
  message_id: number | string,
  file: File,
) {
  const form = new FormData();
  form.append("user_id", user_id);
  form.append("thread_id", thread_id);
  form.append("message_id", String(message_id));
  form.append("file", file);

  const res = await fetch(`${apiBase()}/workspace/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Upload failed ${res.status}: ${text}`);
  }
  return (await res.json()) as {
    file_id: number;
    user_id: string;
    thread_id: string;
    message_id: string;
    path: string;
    original_filename: string;
    size: number;
    content_type: string;
  };
}

export function downloadWorkspaceUrl(path: string) {
  const sp = new URLSearchParams({ path });
  return `${apiBase()}/workspace/download?${sp.toString()}`;
}

export async function listSkills(page = 1, page_size = 20, keyword = "") {
  const sp = new URLSearchParams({
    page: String(page),
    page_size: String(page_size),
    keyword,
  });
  return apiFetch<{
    code: number;
    data: SkillItem[];
    total: number;
    current_count: number;
    message?: string;
  }>(`/skills/list?${sp.toString()}`);
}

export type SseEvent = Record<string, any> & { type?: string };

function parseSseLines(buffer: string) {
  const events: Array<{ event?: string; data: string }> = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";
  for (const part of parts) {
    const lines = part.split("\n");
    let event: string | undefined;
    const dataLines: string[] = [];
    for (const line of lines) {
      if (line.startsWith("event:")) event = line.slice("event:".length).trim();
      if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).trimStart());
    }
    events.push({ event, data: dataLines.join("\n") });
  }
  return { events, remainder };
}

export async function streamChat(
  req: ChatRequest,
  onEvent: (ev: SseEvent) => void,
  signal?: AbortSignal,
) {
  const res = await fetch(`${apiBase()}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: req.message,
      thread_id: req.thread_id ?? "default",
      user_id: req.user_id ?? "default_user",
      attachments: req.attachments ?? [],
      message_id: req.message_id ?? null,
    }),
    signal,
  });

  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => "");
    throw new Error(`Stream failed ${res.status}: ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parsed = parseSseLines(buf);
    buf = parsed.remainder;
    for (const e of parsed.events) {
      try {
        const json = e.data ? JSON.parse(e.data) : {};
        onEvent(json);
      } catch {
        onEvent({ type: "message", raw: e.data, event: e.event });
      }
    }
  }
}
