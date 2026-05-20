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

export type SkillTypeStat = {
  type: string;
  count: number;
};
// const DEFAULT_BASE = "http://localhost:8080";
const DEFAULT_BASE = "http://10.0.87.112:8080";
export function apiBase() {
  return (import.meta as any).env?.VITE_API_BASE || DEFAULT_BASE;
}
// 登录
export async function getLogin(params:any) {
  let loginForm = new FormData();
  loginForm.append("username", params.username);
  loginForm.append("password", params.password);
  return apiFetch<{ threads: ThreadTitle[] }>("/login", {
    method: "POST",
    body: loginForm
  });
}


async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // 从 localStorage 获取 token
  const token = localStorage.getItem('token') || '';
  
  // 合并 headers，添加 token
  let headers2=init ? init.headers : {};
  const headers = {
    'Authorization': token ? `Bearer ${token}` : '',
    ...headers2
  };
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers
  });
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
// 保存画板
export async function saveDrawInfo(params:any) {
  return apiFetch<{ threads: ThreadTitle[] }>("/dag/panel/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
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

export async function attachMessageFiles(
  user_id: string,
  thread_id: string,
  message_id: number,
  attachments: Array<Pick<MessageAttachment, "path" | "name">>,
) {
  return apiFetch<{ attachments: MessageAttachment[] }>("/message/attach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, thread_id, message_id, attachments }),
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
// 获取算子库
export async function getAllSkills(page = '', page_size = '', keyword = "", type = "", skill_type = "") {
  // const sp = new URLSearchParams();
  // sp.set("page", String(page));
  // sp.set("page_size", String(page_size));
  // sp.set("keyword", keyword);
  // if (type) {
  //   sp.set("type", type);
  // }
  return apiFetch<{
    code: number;
    data: SkillItem[];
    total: number;
    current_count: number;
    message?: string;
  }>(`/dag/skill/listSkills`);
}
export function downloadWorkspaceUrl(path: string) {
  const sp = new URLSearchParams({ path });
  return `${apiBase()}/workspace/download?${sp.toString()}`;
}

export async function listSkills(page = 1, page_size = 20, keyword = "", type = "") {
  const sp = new URLSearchParams();
  sp.set("page", String(page));
  sp.set("page_size", String(page_size));
  sp.set("keyword", keyword);
  if (type) {
    sp.set("type", type);
  }
  return apiFetch<{
    code: number;
    data: SkillItem[];
    total: number;
    current_count: number;
    message?: string;
  }>(`/skills/list?${sp.toString()}`);
}
// 请求算子详情信息
export async function listSkillsDetails(skill_id:string) {
  return apiFetch<{
    code: number;
    result: Object;
    message?: string;
  }>(`/dag/skill/getSkillInfo?skill_id=${skill_id.toString()}`);
}

export async function getSkillTypes() {
  return apiFetch<{
    code: number;
    data: SkillTypeStat[];
    total: number;
    message?: string;
  }>("/skills/types");
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
