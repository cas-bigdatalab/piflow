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

export type DagSkillInfo = {
  id?: number;
  skill_id?: string;
  skill_name?: string;
  version?: string;
  description?: string;
  file_path?: string;
  input_params?: any;
  output_params?: any;
  skill_type?: string;
  language?: string;
  command?: string;
  icon_path?: string;
  create_time?: string;
  update_time?: string;
  is_deleted?: number;
};

export type SkillGroup = {
  groupName: string;
  DagSkillInfoList: DagSkillInfo[];
};
export function apiBase() {
  return import.meta.env.VITE_API_BASE;
}

function absoluteApiBase() {
  const configured = (apiBase() || "").trim().replace(/\/+$/, "");
  if (configured) {
    return configured;
  }
  if (typeof window !== "undefined" && window.location?.origin) {
    return window.location.origin.replace(/\/+$/, "");
  }
  return "";
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
  console.log("✅ uploadWorkspaceFile called with file:", file);
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
//数据空间上传
export async function uploadWorkSpaceFileNew(
  user_id: string,
  file: File,
) {
  const form = new FormData();
  form.append("user_id", user_id);
  form.append("file", file);

  const res = await fetch(`${apiBase()}/workspace/upload/path`, { method: "POST", body: form });
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
export async function getAllSkills(keyword = "") {
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
  }>(keyword ? `/dag/skill/listSkills?keyword=${keyword}` : `/dag/skill/listSkills`);
}
export function downloadWorkspaceUrl(path: string) {
  const token = localStorage.getItem('token') || '';
  const sp = new URLSearchParams({ 
    path: encodeURIComponent(path),
    token 
  });
  return `${absoluteApiBase()}/workspace/download?${sp.toString()}`;
}
export function downloadWorkspaceUrl2(path: string) {
  // const token = localStorage.getItem('token') || '';
  // const sp = new URLSearchParams({ 
  //   path: encodeURIComponent(path),
  //   token 
  // });
  return `${absoluteApiBase()}/workspace/download?path=${path}&user_id=${localStorage.getItem('userId')}`;
}
export function downloadWorkspaceUrl3(path: string) {
  // const token = localStorage.getItem('token') || '';
  // const sp = new URLSearchParams({ 
  //   path: encodeURIComponent(path),
  //   token 
  // });
  return `${absoluteApiBase()}/workspace/download?path=${path}&user_id=${localStorage.getItem('userId')}`;
}
export async function listSkills(page = 1, page_size = 20, keyword = "", skill_type = "") {
  const sp = new URLSearchParams();
  sp.set("page", String(page));
  sp.set("page_size", String(page_size));
  sp.set("keyword", keyword);
  if (skill_type) {
    sp.set("skill_type", skill_type);
  }
  return apiFetch<{
    code: number;
    data: SkillItem[];
    total: number;
    current_count: number;
    message?: string;
  }>(`/dag/skill/listSkills?${sp.toString()}`);
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
  }>("/dag/skill/getSkillTypeCounts");
}

// 获取分组的算子列表
export async function getSkillGroups() {
  return apiFetch<{
    code: number;
    data: SkillGroup[];
    message?: string;
  }>("/dag/skill/listSkills");
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
      user_id: req.user_id ?? localStorage.getItem('userId'),
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
// 根据画板信息给大模型发消息
export async function sendMessages(
  user_id: string,
  thread_id: string,
  message_id: number,
  attachments: Array<Pick<MessageAttachment, "path" | "name">>,
  message: string
) {
  return apiFetch<{ attachments: MessageAttachment[] }>("/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, thread_id, message_id, attachments,message }),
  });
}

// ==================== 任务管理 API ====================

export interface Task {
  id: number;
  dag_task_id: string;
  dag_task_name: string;
  description: string;
  create_user_id: string | null;
  create_time: string;
  message_id?: string;
  dag_task_type?: number;
  is_deleted?: number;
  update_time?: string;
}

export interface TaskListResponse {
  code: number;
  message: string;
  result: {
    total: number;
    page: number;
    page_size: number;
    data: Task[];
  };
}

// 查询任务列表
export async function getTasks(page: number, page_size: number, keyword?: string) {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', String(page_size));
  if (keyword && keyword.trim()) {
    params.set('keyword', keyword.trim());
  }
  return apiFetch<TaskListResponse>(`/dag/task/getTasks?${params.toString()}`);
}

// 创建任务
export async function createTask(params:object) {
  return apiFetch("/dag/task/createTask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
  });
}

// 更新任务
export async function updateTask(dag_task_id: string, dag_name: string, description: string) {
  const params = new URLSearchParams();
  params.set('dag_task_id', dag_task_id);
  params.set('dag_name', dag_name);
  params.set('description', description);
  return apiFetch<{ code: number; message: string }>(`/dag/task/updateTask?${params.toString()}`);
}

// 删除任务
export async function deleteTask(dag_task_id: string) {
//  let params = {dag_task_id:dag_task_id};
  return apiFetch<{ attachments: MessageAttachment[] }>("/dag/task/deleteTask", {
    method: "POST",
    // body: JSON.stringify(params)
    body: dag_task_id, // 直接传字符串，不 JSON.stringify
  });
}

// 获取画板内容
export async function getDrawTaskContent(dag_task_id: string) {
  return apiFetch(`/dag/panel/getDSLJson?dag_task_id=${dag_task_id.toString()}`, {
    method: "POST",
    body: JSON.stringify({dag_task_id:dag_task_id})
  });
}
// 根据消息id请求查看是否有画板信息
export async function getDrawInfoBymegId(message_id:string) {
  return apiFetch<{
    code: number;
    result: Object;
    message?: string;
  }>(`/dag/panel/getDSLJsonByMessageId?message_id=${message_id.toString()}`);
}

// ==================== DAG 运行 API ====================

export interface RunDAGResponse {
  code: number;
  message: string;
  result: {
    dag_task_id: string;
    process_id: string;
    status: string;
  };
}

export interface StopDAGResponse {
  code: number;
  message: string;
  result: {
    process_id: string;
    status: string;
  };
}

export async function runDAGTask(dag_task_id: string) {
  return apiFetch<RunDAGResponse>("/dag/runtime/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dag_task_id)
  });
}

export async function stopDAGTask(process_id: string) {
  return apiFetch<StopDAGResponse>("/dag/runtime/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(process_id)
  });
}

// ==================== 执行详情 API ====================

export interface StopInfo {
  job_id: string;
  stop_name: string;
  stop_uuid: string | null;
  bundle: string | null;
  status: string;
  input_ports: any[];
  output_ports: any[];
  workspace_path: string | null;
  log_path: string | null;
  stdout_log_path: string | null;
  stderr_log_path: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ExecutionDetailResponse {
  code: number;
  message: string;
  result: {
    process_id: string;
    dag_task_id?: string;
    flow_uuid: string | null;
    flow_name: string;
    status: string;
    progress: number | null;
    total_stop_count: number;
    success_stop_count: number;
    failed_stop_count: number;
    skipped_stop_count: number;
    workspace_path: string | null;
    log_path: string | null;
    error_message: string | null;
    started_at: string | null;
    finished_at: string | null;
    created_at: string | null;
    updated_at: string | null;
    stops: StopInfo[];
    final_output_paths: string[];
  };
}

// 查询执行详情
export async function getExecutionDetail(process_id: string) {
  const params = new URLSearchParams();
  params.set('process_id', process_id);
  return apiFetch<ExecutionDetailResponse>(`/dag/runtime/execution/detail?${params.toString()}`);
}

// ==================== 运行历史 API ====================

export interface ExecutionItem {
  process_id: string;
  dag_task_id: string | null;
  flow_uuid: string | null;
  flow_name: string | null;
  status: string | null;
  progress: number | null;
  total_stop_count: number;
  success_stop_count: number;
  failed_stop_count: number;
  skipped_stop_count: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ExecutionsResponse {
  code: number;
  message: string;
  result: {
    dag_task_id: string;
    page: number;
    page_size: number;
    total: number;
    items: ExecutionItem[];
  };
}

export interface StatusCountsResponse {
  code: number;
  message: string;
  result: {
    keyword: string | null;
    dag_task_id: string | null;
    total: number;
    running_count: number;
    completed_count: number;
    failed_count: number;
  };
}

// 按任务查询运行历史
export async function getExecutions(dag_task_id: string, page: number = 1, page_size: number = 20, status?: string) {
  const params = new URLSearchParams();
  params.set('dag_task_id', dag_task_id);
  params.set('page', String(page));
  params.set('page_size', String(page_size));
  if (status) {
    params.set('status', status);
  }
  return apiFetch<ExecutionsResponse>(`/dag/runtime/executions?${params.toString()}`);
}

// 全局分页查询运行实例
export async function getProcesses(page: number = 1, page_size: number = 20, options?: {
  status?: string;
  dag_task_id?: string;
  running_only?: boolean;
  keyword?: string;
}) {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', String(page_size));
  if (options?.status) {
    params.set('status', options.status);
  }
  if (options?.dag_task_id) {
    params.set('dag_task_id', options.dag_task_id);
  }
  if (options?.running_only) {
    params.set('running_only', 'true');
  }
  if (options?.keyword) {
    params.set('keyword', options.keyword);
  }
  return apiFetch<{
    code: number;
    message: string;
    result: {
      page: number;
      page_size: number;
      total: number;
      items: ExecutionItem[];
    };
  }>(`/dag/runtime/processes?${params.toString()}`);
}

export async function getProcessStatusCounts() {
  return apiFetch<StatusCountsResponse>('/dag/runtime/processes/status-counts');
}

export interface LogPathsResponse {
  code: number;
  message: string;
  result: {
    job_id: string;
    stdout_path?: string;
    stderr_path?: string;
    log_content?: string;
  };
}

export async function getStopLogPaths(job_id: string) {
  const params = new URLSearchParams();
  params.set('job_id', job_id);
  return apiFetch<LogPathsResponse>(`/dag/runtime/stop/log-paths?${params.toString()}`);
}

// ==================== 存储文件 API ====================

export interface StorageItem {
  name: string;
  type: 'directory' | 'file';
  path: string;
  size: number | null;
  last_modified: string | null;
}

export interface StorageListResponse {
  user_id: string;
  dir_path: string;
  items: StorageItem[];
}

export interface SaveToStorageResponse {
  code: number;
  message: string;
  result: {
    path: string;
  };
}

export async function listStorage(user_id: string, dir_path?: string) {
  const body: Record<string, string> = { user_id };
  if (dir_path) {
    body.dir_path = dir_path;
  }
  return apiFetch<StorageListResponse>("/workspace/list", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

//我的数据管理页面列表方法
export async function listStorageNew(
  user_id: string,
  dir_path?: string,
  page?: number,
  page_size?: number
) {
  const body = {
    user_id,
    ...(dir_path !== undefined && { dir_path }),
    ...(page !== undefined && { page }),
    ...(page_size !== undefined && { page_size }),
  };
  return apiFetch<StorageListResponse>("/workspace/list", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
//我的数据管理中删除接口
export async function deleteData(user_id: string, paths?: string[]) {
  const body = {
    user_id,
    paths: paths ?? [], // 确保 path 是数组，避免 undefined
  };
  return apiFetch<StorageListResponse>("/workspace/delete/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
//我的数据下载和批量下载接口共用
// export async function downLoadData(user_id: string, paths?: string[]) {
//   const body = {
//     user_id,
//     paths: paths ?? [], // 确保 path 是数组，避免 undefined
//   };
//   return apiFetch<StorageListResponse>("/workspace/download/batch", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify(body),
//   });
// }


// lib/api.ts
export const downLoadData = async (userId: string, paths: string[]) => {
  const response = await fetch(`${apiBase()}/workspace/download/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, paths }),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "未知错误");
    throw new Error(`下载失败: ${response.status} ${response.statusText} - ${errorText}`);
  }

  // 尝试从 Content-Disposition 获取文件名
  const contentDisposition = response.headers.get('Content-Disposition');
  let fileName = 'download.zip'; // 默认文件名，后端批量下载通常返回 zip
  if (contentDisposition) {
    // 支持 RFC 2183 格式，如 filename="xxx.zip" 或 filename*=UTF-8''xxx.zip
    const utf8Filename = contentDisposition.match(/filename\*=UTF-8''(.+)/i);
    if (utf8Filename && utf8Filename[1]) {
      try {
        fileName = decodeURIComponent(utf8Filename[1]);
      } catch {
        fileName = 'download.zip';
      }
    } else {
      const asciiFilename = contentDisposition.match(/filename="?([^"]+)"?/i);
      if (asciiFilename && asciiFilename[1]) {
        fileName = asciiFilename[1];
      }
    }
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName; // 确保指定 download 属性
  document.body.appendChild(a);
  a.click();
  // 清理
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};


export async function copyDefaultFiles(user_id: string) {
  return apiFetch<{ success: boolean; message: string }>("/workspace/temp/copy-default-files", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id })
  });
}

export async function saveToStorage(user_id: string, target_path: string, local_path: string) {
  return apiFetch<SaveToStorageResponse>("/storage/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, target_path, local_path })
  });
}

//新增数据源列表
export async function listDataspace() {
  return apiFetch<SaveToStorageResponse>("/datasource/catalog/list", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });
}

//数据源实例列表
export async function listDataspaceDirecory() {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/list", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });
}

//单击数据源类型后查询是否新增哪些字段内容
export async function detailFiled(type_code: string) {
  return apiFetch<SaveToStorageResponse>("/datasource/catalog/detail", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type_code })
  });
}

//不同数据源下新增实例接口
export async function detailCreate(forData: any) {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( forData )
  });
}
//不同数据源下新增实例接口
export async function detailUpdate(forData: any) {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( forData )
  });
}

//实例详情接口
export async function detail(source_id: string) {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/detail", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( {source_id} )
  });
}

//测试接口未保存
export async function validate(formData: any) {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( formData )
  });
}

//测试接口保存后
export async function validateById(source_id: string) {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/validate/by-id", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( {source_id} )
  });
}

//删除接口
export async function deleteSource(source_id: string) {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( {source_id} )
  });
}


//首页新建对话中新增中的上传文件接口
export async function uploadWorkspaceFileNew(user_id: string,thread_id: string,message_id: string,dir_path:string) {
  return apiFetch<SaveToStorageResponse>("/message/bind-directory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( {user_id,thread_id,message_id,dir_path} )
  });
}

//数据源新增对话上传接口
export async function uploadWorkspaceFileAttach(user_id: string,thread_id: string,message_id: string,attachments: Array<string>) {
  return apiFetch<SaveToStorageResponse>("/message/attach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( {user_id,thread_id,message_id,attachments} )
  });
}

//保存到dataspace数据源接口
export async function uploadSource(user_id: string,source_id: string,workspace_paths: string[],target_dir:string) {
  return apiFetch<SaveToStorageResponse>("/dataspace/source/workspace/path/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify( {user_id,source_id,workspace_paths,target_dir} )
  });
}