import { Icon } from "@iconify/react";
import { type DragEvent, useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  attachMessageFiles,
  createMessage,
  downloadWorkspaceUrl,
  getThreadMessages,
  streamChat,
  uploadWorkspaceFile,
  getDrawInfoBymegId,
  type MessageAttachment,
  type ThreadMessage,
} from "../lib/api";
import { MarkdownMessage } from "../components/MarkdownMessage";
import { shortId } from "../lib/ids";
import PipelinePreview, { extractAndCleanPipelineJson, PipelineData } from "../components/PipelinePreview";
import FlowEditor, { InitialPipelineData } from "../components/Draw";
// import { appConfig } from "../config/appConfig";

const DEFAULT_USER_ID = localStorage.getItem('userId');

type UiMsg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoning?: string;
  artifacts?: string[];
  attachments?: MessageAttachment[];
};

type PendingAttachment = {
  id: string;
  file: File;
  name: string;
};

type ExampleCard = {
  title: string;
  description: string;
  prompt: string;
  image: string;
  attachments?: Array<Pick<MessageAttachment, "path" | "name">>;
};

const WORKSPACE_FILE_PATTERN = /\/(?:outputs|artifacts)\/[^\s"'`)\]}>,，。；：！？]+/g;

// 移除JSON字符串（处理 \"json {...} 或 \"json [...] 格式）
function removeJsonBlock(text: string): string {
  let result = text;
  
  // 匹配 \"json 后面跟着 { 或 [ 的模式
  // 在JavaScript中，\\\"json 表示匹配字面上的 \ 和 " 两个字符后跟 json
  // 页面上显示的 \"json 实际上是存储的 \ 和 " 两个字符
  const jsonPattern = /\\"json\s*([{\[])/g;
  let match;
  
  while ((match = jsonPattern.exec(result)) !== null) {
    const startIndex = match.index;
    const openChar = match[1];
    const closeChar = openChar === '{' ? '}' : ']';
    
    // 使用栈来找到匹配的闭合括号，处理转义的引号
    let stack = 1;
    let endIndex = startIndex + match[0].length;
    let inString = false;
    let escapeCount = 0;
    
    while (endIndex < result.length && stack > 0) {
      const char = result[endIndex];
      
      // 计算连续的反斜杠数量
      if (char === '\\') {
        escapeCount++;
        endIndex++;
        continue;
      }
      
      // 处理引号
      if (char === '"') {
        // 如果前面有奇数个反斜杠，说明是转义的引号（在字符串内）
        // 如果前面有偶数个反斜杠（包括0），说明是字符串边界
        if (escapeCount % 2 === 0) {
          inString = !inString;
        }
      }
      
      // 只有不在字符串中时才处理括号
      if (!inString) {
        if (char === openChar) {
          stack++;
        } else if (char === closeChar) {
          stack--;
        }
      }
      
      escapeCount = 0;
      endIndex++;
    }
    
    // 如果找到了匹配的闭合括号，或者到了字符串末尾，移除这段内容
    const before = result.substring(0, startIndex);
    const after = result.substring(endIndex);
    result = before + after;
    
    // 重置正则表达式位置，重新搜索
    jsonPattern.lastIndex = 0;
  }
  
  return result;
}

// 彻底清理文本中的所有 JSON 对象和数组
function removeAllJson(text: string): string {
  if (!text) return text;
  
  let result = text;
  
  // 首先移除特定的标记文本  请根据任务流程重新生成dag JSON，不要执行
  result = result.replace(/我手动修改了任务流程，请根据任务流程重新生成dag JSON[\s\S]*?不要执行。[\s\S]*?\n?/g, '').trim();
  result = result.replace(/我手动修改了任务流程，请根据任务流程重新生成dag JSON[\s\S]*?不要执行。/g, '').trim();
  
  // 移除代码块格式的 JSON（包括 ```json ... ``` 和 ``` ... ```）
  result = result.replace(/```(json)?\s*[\s\S]*?```/g, '').trim();
  
  // 移除行内代码格式的 JSON（`...`）
  result = result.replace(/`([^`]*\{[^`]*\}[^`]*)`/g, '').trim();
  result = result.replace(/`([^`]*\[[^`]*\][^`]*)`/g, '').trim();
  
  // 移除JSON字符串格式（"json {...} 或 "json [...]）
  result = removeJsonBlock(result);
  
  // 使用栈来匹配嵌套的 JSON 结构
  let i = 0;
  let stack: string[] = [];
  let startIndices: number[] = [];
  let partsToRemove: [number, number][] = [];
  
  while (i < result.length) {
    const char = result[i];
    
    if (char === '{' || char === '[') {
      stack.push(char);
      if (stack.length === 1) {
        startIndices.push(i);
      }
    } else if (char === '}' || char === ']') {
      if (stack.length > 0) {
        const last = stack[stack.length - 1];
        if ((char === '}' && last === '{') || (char === ']' && last === '[')) {
          stack.pop();
          if (stack.length === 0 && startIndices.length > 0) {
            partsToRemove.push([startIndices.pop()!, i + 1]);
          }
        }
      }
    }
    i++;
  }
  
  // 从后往前移除部分，避免索引问题
  for (let j = partsToRemove.length - 1; j >= 0; j--) {
    const [start, end] = partsToRemove[j];
    result = result.substring(0, start) + result.substring(end);
  }
  
  // 移除可能残留的空行和多余空格
  result = result.replace(/\n{3,}/g, '\n\n').trim();
  result = result.replace(/\s{2,}/g, ' ').trim();
  
  return result.trim();
}

function extractWorkspaceLinks(text: string) {
  return Array.from(new Set((text.match(WORKSPACE_FILE_PATTERN) || []).filter(Boolean)));
}

function normalizeArtifacts(paths: string[]) {
  const unique = Array.from(new Set(paths.filter(Boolean)));
  unique.sort((left, right) => right.length - left.length || left.localeCompare(right));

  const normalized: string[] = [];
  for (const candidate of unique) {
    const shadowed = normalized.some((existing) => existing.startsWith(candidate));
    if (!shadowed) {
      normalized.push(candidate);
    }
  }

  return normalized.sort((left, right) => left.localeCompare(right));
}

function mergeArtifacts(...groups: Array<string[] | undefined>) {
  return normalizeArtifacts(groups.flatMap((group) => group || []).filter(Boolean));
}

function svgToDataUri(svg: string) {
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

const EXAMPLES: ExampleCard[] = [
  {
    title: "语料格式转换与过滤",
    description: "「请对上传数据csv文件转换为jsonl格式，再对这个jsonl的'fa0114'字段进行最大长度过滤，要求最大长度在40以内；再对'fa0112'字段筛选过滤出包含'多花山矾'的数据」",
    prompt:
      "请对上传数据csv文件转换为jsonl格式，再对这个jsonl的'fa0114'字段进行最大长度过滤，要求最大长度在40以内；再对'fa0112'字段筛选过滤出包含'多花山矾'的数据",
    attachments: [
      {
        path: "/temp/森林每木调查数据.csv",
        name: "森林每木调查数据.csv",
      },
    ],
    image: svgToDataUri(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" fill="none">
        <rect width="320" height="180" fill="#EFF6FF"/>
        <g transform="translate(62 0) scale(1.62)">
          <path d="M20 45L60 25L100 45L60 65L20 45Z" fill="#3B82F6" fill-opacity="0.1" stroke="#3B82F6"/>
          <path d="M20 52L60 32L100 52L60 72L20 52Z" fill="#3B82F6" fill-opacity="0.15" stroke="#3B82F6"/>
          <path d="M20 59L60 39L100 59L60 79L20 59Z" fill="#3B82F6" fill-opacity="0.2" stroke="#3B82F6"/>
          <path d="M20 59V64L60 84V79L20 59Z" fill="#2563EB" fill-opacity="0.3"/>
          <path d="M100 59V64L60 84V79L100 59Z" fill="#1D4ED8" fill-opacity="0.3"/>
          <path d="M45 45L60 37.5L75 45L60 52.5L45 45Z" fill="#60A5FA" fill-opacity="0.6"/>
          <path d="M35 50L50 42.5L65 50L50 57.5L35 50Z" fill="#93C5FD" fill-opacity="0.4"/>
          <g transform="translate(75 25)">
            <circle cx="15" cy="15" r="14" fill="white"/>
            <path d="M11 12L15 8L19 12M15 8V22M11 18L15 22L19 18" stroke="#1D4ED8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
          <g transform="translate(25 20)">
            <path d="M4 6H20L14 13V19L10 21V13L4 6Z" fill="#3B82F6" fill-opacity="0.8" stroke="white"/>
          </g>
        </g>
      </svg>
    `),
  },
  {
    title: "元数据提取与文本提取",
    description: "「请对文档进行以下处理：1、提取文档元数据 2、提取pdf文档文本内容」",
    prompt:
      "请对文档进行以下处理：1、提取文档元数据 2、提取pdf文档文本内容",
    attachments: [
      {
        path: "/temp/Akcay.pdf",
        name: "Akcay.pdf",
      },
    ],
    image: svgToDataUri(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" fill="none">
        <rect width="320" height="180" fill="#ECFDF5"/>
        <g transform="translate(70 -2) scale(1.58)">
          <rect x="35" y="30" width="45" height="55" rx="2" fill="white" stroke="#10B981" transform="skewY(-10)"/>
          <rect x="30" y="25" width="45" height="55" rx="2" fill="white" stroke="#10B981" transform="skewY(-10)"/>
          <g transform="translate(55 45) skewY(-10)">
            <rect x="0" y="0" width="35" height="25" rx="1" fill="#D1FAE5" stroke="#059669"/>
            <line x1="0" y1="8" x2="35" y2="8" stroke="#059669" stroke-width="0.8"/>
            <line x1="0" y1="16" x2="35" y2="16" stroke="#059669" stroke-width="0.8"/>
            <line x1="12" y1="0" x2="12" y2="25" stroke="#059669" stroke-width="0.8"/>
          </g>
          <g transform="translate(20 55)">
            <path d="M0 5C0 2.23858 2.23858 0 5 0H35C37.7614 0 40 2.23858 40 5V20C40 22.7614 37.7614 25 35 25H15L5 32V25C2.23858 25 0 22.7614 0 20V5Z" fill="#10B981"/>
            <line x1="8" y1="8" x2="32" y2="8" stroke="white" stroke-width="2" stroke-linecap="round"/>
            <line x1="8" y1="14" x2="26" y2="14" stroke="white" stroke-width="2" stroke-linecap="round"/>
            <line x1="8" y1="20" x2="20" y2="20" stroke="white" stroke-width="2" stroke-linecap="round"/>
          </g>
        </g>
      </svg>
    `),
  },
  {
    title: "文档规范化处理",
    description: "「请检查文档的格式有效性，并转换成markdown格式的文档。」",
    prompt:
      "请检查文档的格式有效性，并转换成markdown格式的文档。",
    attachments: [
      {
        path: "/temp/Marxist.docx",
        name: "Marxist.docx",
      },
    ],
    image: svgToDataUri(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" fill="none">
        <rect width="320" height="180" fill="#F5F3FF"/>
        <g transform="translate(90 28)">
          <path d="M30 40L70 20L110 40L70 60L30 40Z" fill="#8B5CF6" fill-opacity="0.1" stroke="#8B5CF6"/>
          <path d="M45 42L65 32M45 48L75 33M45 54L60 46" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" opacity="0.6"/>
          <g transform="translate(65 50)">
            <circle cx="20" cy="20" r="18" fill="white"/>
            <path d="M12 20L18 26L28 16" stroke="#7C3AED" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 10H30M10 30H30" stroke="#DDD6FE" stroke-width="1" stroke-dasharray="2 2"/>
          </g>
          <path d="M25 25L30 35L20 30L25 25Z" fill="#C084FC"/>
          <circle cx="15" cy="15" r="2" fill="#A855F7"/>
          <circle cx="35" cy="20" r="1.5" fill="#A855F7"/>
          <path d="M110 40V48L70 68V60L110 40Z" fill="#7C3AED" fill-opacity="0.2"/>
          <path d="M30 40V48L70 68V60L30 40Z" fill="#6D28D9" fill-opacity="0.2"/>
        </g>
      </svg>
    `),
  },
];

function toUiMessage(threadId: string, message: ThreadMessage, index: number): UiMsg {
  return {
    id: String(message.id ?? `${threadId}-${index}`),
    role: message.role === "assistant" ? "assistant" : "user",
    content: message.content,
    artifacts: message.role === "assistant" ? extractWorkspaceLinks(message.content) : [],
    attachments: Array.isArray(message.attachments) ? message.attachments : [],
  };
}

export function HomePage() {
  const [threadId, setThreadId] = useState<string>("default");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<UiMsg[]>([]);
  const [sending, setSending] = useState(false);
  const [streamStatus, setStreamStatus] = useState("");
  const [activeAssistantId, setActiveAssistantId] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<PendingAttachment[]>([]);
  const [uploadingCount, setUploadingCount] = useState(0);
  const [loadError, setLoadError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  
  // 画板相关状态
  const [showCanvas, setShowCanvas] = useState(false);
  const [canvasPipelineData, setCanvasPipelineData] = useState<PipelineData | null>(null);
  const [canvasMessageId, setCanvasMessageId] = useState<string>('');
  const [savedDrawData, setSavedDrawData] = useState<any>(null);
  const [canvasWidth, setCanvasWidth] = useState(50); // 画板宽度百分比
  const isDraggingRef = useRef(false);
  
  const abortRef = useRef<AbortController | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);
  const dragCounterRef = useRef(0);

  const hasMessages = messages.length > 0;

  const uploading = uploadingCount > 0;
  const isExpanded = hasMessages || sending || Boolean(loadError);

  // 处理打开画板
  const handleOpenCanvas = async (data: PipelineData, msgId?: string) => {
    setCanvasPipelineData(data);
    // 如果已经有保存的 canvasMessageId（来自 createMessage 返回），就使用它，不覆盖
    // 这样可以确保保存画板时使用正确的 message_id
    if (!canvasMessageId) {
      setCanvasMessageId(msgId || '');
    }
    // 先请求已保存的画板信息
    let drawData = null;
    const effectiveMsgId = canvasMessageId || msgId;
    if (effectiveMsgId) {
      try {
        const res = await getDrawInfoBymegId(effectiveMsgId);
        console.log('getDrawInfoBymegId返回:', res);
        if (res.code === 200 && res.result) {
          drawData = res.result;
        }
      } catch (e) {
        console.log('获取已保存画板信息失败，使用会话数据:', e);
      }
    }
    setSavedDrawData(drawData);
    setShowCanvas(true);
  };
  
  // 关闭画板
  const handleCloseCanvas = () => {
    setShowCanvas(false);
    setCanvasPipelineData(null);
    setSavedDrawData(null);
  };

  useEffect(() => {
    if (!transcriptRef.current) {
      return;
    }
    transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
  }, [messages, streamStatus]);

  useEffect(() => {
    if (!isExpanded || !composerRef.current) {
      return;
    }
    composerRef.current.focus();
    const length = composerRef.current.value.length;
    composerRef.current.setSelectionRange(length, length);
  }, [isExpanded]);

  useEffect(() => {
    const handleNewChat = () => {
      abortRef.current?.abort();
      abortRef.current = null;
      const nextThreadId = `t_${shortId()}`;
      setThreadId(nextThreadId);
      setInput("");
      setMessages([]);
      setPendingFiles([]);
      setStreamStatus("");
      setActiveAssistantId(null);
      setLoadError("");
    };

    const handleSelectThread = (event: Event) => {
      const detail = (event as CustomEvent<{ thread_id?: string }>).detail;
      if (detail?.thread_id) {
        loadThread(detail.thread_id).catch(() => {});
      }
    };

    window.addEventListener("flow:new-chat", handleNewChat);
    window.addEventListener("flow:select-thread", handleSelectThread as EventListener);
    
    // 监听画板发送的消息事件
    const handleSendMessage = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { threadId: eventThreadId, messageId, content, hidden } = customEvent.detail || {};
      if (eventThreadId && messageId && content) {
        // 使用现有的 send 逻辑处理流式响应
        send(content, { threadId: eventThreadId, hidden });
      }
    };
    window.addEventListener("flow:send-message", handleSendMessage as EventListener);

    return () => {
      window.removeEventListener("flow:new-chat", handleNewChat);
      window.removeEventListener("flow:select-thread", handleSelectThread as EventListener);
      window.removeEventListener("flow:send-message", handleSendMessage as EventListener);
    };
  }, []);

  // 画板拖拽调整宽度
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current || !showCanvas) return;
      const container = document.querySelector('.canvas-split-container');
      if (!container) return;
      const rect = container.getBoundingClientRect();
      let newWidth = ((rect.right - e.clientX) / rect.width) * 100;
      newWidth = Math.max(30, Math.min(70, newWidth));
      setCanvasWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [showCanvas]);

  async function loadThread(nextThreadId: string) {
    abortRef.current?.abort();
    abortRef.current = null;
    setThreadId(nextThreadId);
    setStreamStatus("");
    setActiveAssistantId(null);
    setLoadError("");
    setPendingFiles([]);
    setInput("");
    setShowCanvas(false);
    setCanvasPipelineData(null);
    setCanvasMessageId("");
    setSavedDrawData(null);

    try {
      const response = await getThreadMessages(DEFAULT_USER_ID, nextThreadId, 200);
      setMessages((response.messages || []).map((message, index) => toUiMessage(nextThreadId, message, index)));
    } catch (error: any) {
      setMessages([]);
      setLoadError(String(error?.message || error));
    }
  }

  async function send(
    overridePrompt?: string,
    options?: {
      threadId?: string;
      presetAttachments?: Array<Pick<MessageAttachment, "path" | "name">>;
      hidden?: boolean;
    },
  ) {
    const prompt = (overridePrompt ?? input).trim();
    if ((!prompt && pendingFiles.length === 0) || sending || uploading) {
      return;
    }
    const targetThreadId = options?.threadId ?? threadId;
    const presetAttachments = options?.presetAttachments || [];
    const hidden = options?.hidden || false;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const assistantId = `a_${shortId()}`;
    const assistantMessage: UiMsg = {
      id: assistantId,
      role: "assistant",
      content: "",
      reasoning: "",
      artifacts: [],
    };

    const filesToUpload = [...pendingFiles];
    setSending(true);
    setActiveAssistantId(assistantId);
    setInput("");
    setPendingFiles([]);
    setStreamStatus("正在连接智能体...");

    let assistantContent = "";
    let assistantReasoning = "";
    let assistantArtifacts: string[] = [];

    try {
      const created = await createMessage(DEFAULT_USER_ID, targetThreadId, prompt);
      const messageId = created.message.id;

      let attachedPresetFiles: MessageAttachment[] = [];
      if (presetAttachments.length > 0) {
        const attached = await attachMessageFiles(
          DEFAULT_USER_ID,
          targetThreadId,
          messageId,
          presetAttachments,
        );
        attachedPresetFiles = attached.attachments || [];
      }

      const uploadedAttachments: MessageAttachment[] = [];
      if (filesToUpload.length > 0) {
        setUploadingCount(filesToUpload.length);
        setStreamStatus("正在上传附件...");

        for (const item of filesToUpload) {
          const response = await uploadWorkspaceFile(
            DEFAULT_USER_ID,
            targetThreadId,
            messageId,
            item.file,
          );
          uploadedAttachments.push({
            file_id: response.file_id,
            path: response.path,
            name: response.original_filename,
          });
          setUploadingCount((current) => Math.max(0, current - 1));
        }
      }

      const userMessage: UiMsg = {
        id: String(messageId),
        role: "user",
        content: prompt,
        attachments: [...attachedPresetFiles, ...uploadedAttachments],
        hidden: hidden,
      };

      // 如果是隐藏消息，只添加助手消息，不添加用户消息
      if (hidden) {
        setMessages((current) => [...current, assistantMessage]);
      } else {
        setMessages((current) => [...current, userMessage, assistantMessage]);
      }
      
      // 保存创建消息时返回的原始 messageId，用于后续画板保存
      setCanvasMessageId(String(messageId));
      setStreamStatus("正在连接智能体...");

      await streamChat(
        {
          message: prompt,
          thread_id: targetThreadId,
          user_id: DEFAULT_USER_ID,
          attachments: [...attachedPresetFiles, ...uploadedAttachments].map((file) => file.path),
          message_id: messageId,
        },
        (event) => {
          if (event.type === "status") {
            setStreamStatus("智能体已启动，正在分析任务...");
            return;
          }

          if (event.type === "agent_event") {
            const tools = Array.isArray(event.tool_calls) ? event.tool_calls.filter(Boolean).join("、") : "";
            const nodes = Array.isArray(event.nodes) ? event.nodes.filter(Boolean).join(" / ") : "";
            if (tools) {
              setStreamStatus(`正在调用工具：${tools}`);
            } else if (nodes) {
              setStreamStatus(`正在执行节点：${nodes}`);
            } else {
              setStreamStatus("正在生成回答...");
            }
            return;
          }

          if (event.type === "reasoning_delta" && typeof event.delta === "string") {
            assistantReasoning += event.delta;
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? { ...message, reasoning: assistantReasoning, artifacts: assistantArtifacts }
                  : message,
              ),
            );
            setStreamStatus("正在输出思考过程...");
            return;
          }

          if (event.type === "reasoning" && typeof event.content === "string") {
            assistantReasoning = event.content;
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? { ...message, reasoning: assistantReasoning, artifacts: assistantArtifacts }
                  : message,
              ),
            );
            setStreamStatus("正在输出思考过程...");
            return;
          }

          if (event.type === "message_delta" && typeof event.delta === "string") {
            assistantContent += event.delta;
            assistantArtifacts = mergeArtifacts(assistantArtifacts, extractWorkspaceLinks(assistantContent));
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: assistantContent,
                      reasoning: assistantReasoning,
                      artifacts: assistantArtifacts,
                    }
                  : message,
              ),
            );
            setStreamStatus("正在生成最终回答...");
            return;
          }

          if (event.type === "message" && typeof event.content === "string") {
            assistantContent = event.content;
            assistantArtifacts = mergeArtifacts(assistantArtifacts, extractWorkspaceLinks(assistantContent));
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: assistantContent,
                      reasoning: assistantReasoning,
                      artifacts: assistantArtifacts,
                    }
                  : message,
              ),
            );
            setStreamStatus("正在生成最终回答...");
            return;
          }

          if (event.type === "artifact" && Array.isArray(event.files)) {
            assistantArtifacts = mergeArtifacts(
              assistantArtifacts,
              event.files.filter((item: unknown): item is string => typeof item === "string"),
            );
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: assistantContent,
                      reasoning: assistantReasoning,
                      artifacts: assistantArtifacts,
                    }
                  : message,
              ),
            );
            return;
          }

          if (event.type === "error") {
            const message = typeof event.message === "string" ? event.message : "请求失败";
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      content: assistantContent || `请求失败：${message}`,
                      reasoning: assistantReasoning,
                      artifacts: assistantArtifacts,
                    }
                  : item,
              ),
            );
            setStreamStatus("请求失败");
            return;
          }

          if (event.type === "done") {
            if (typeof event.content === "string" && event.content && !assistantContent) {
              assistantContent = event.content;
            }
            assistantArtifacts = mergeArtifacts(assistantArtifacts, extractWorkspaceLinks(assistantContent));
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: assistantContent,
                      reasoning: assistantReasoning,
                      artifacts: assistantArtifacts,
                    }
                  : message,
              ),
            );
            setStreamStatus("已完成");
            setActiveAssistantId(null);
          }
        },
        controller.signal,
      );

      window.dispatchEvent(new CustomEvent("flow:threads-refresh"));
    } catch (error: any) {
      const message = String(error?.message || error);
      setMessages((current) => {
        const exists = current.some((item) => item.id === assistantId);
        if (!exists) {
          return [
            ...current,
            {
              id: assistantId,
              role: "assistant",
              content: `请求失败：${message}`,
              reasoning: assistantReasoning,
              artifacts: assistantArtifacts,
            },
          ];
        }

        return current.map((item) =>
          item.id === assistantId
            ? {
                ...item,
                content: assistantContent || `请求失败：${message}`,
                reasoning: assistantReasoning,
                artifacts: assistantArtifacts,
              }
            : item,
        );
      });
      setStreamStatus("请求失败");
      setActiveAssistantId(null);
    } finally {
      setSending(false);
      setUploadingCount(0);
      abortRef.current = null;
    }
  }

  function startExample(card: ExampleCard) {
    abortRef.current?.abort();
    abortRef.current = null;

    const nextThreadId = `t_${shortId()}`;
    setThreadId(nextThreadId);
    setInput(card.prompt);
    setMessages([]);
    setPendingFiles([]);
    setStreamStatus("");
    setActiveAssistantId(null);
    setLoadError("");

    send(card.prompt, {
      threadId: nextThreadId,
      presetAttachments: card.attachments || [],
    }).catch(() => {});
  }

  async function handleFiles(files: File[]) {
    if (files.length === 0) {
      return;
    }

    setPendingFiles((current) => [
      ...current,
      ...files.map((file) => ({
        id: shortId(),
        file,
        name: file.name,
      })),
    ]);
  }

  function removePendingFile(id: string) {
    setPendingFiles((current) => current.filter((file) => file.id !== id));
  }

  function handleDragEnter(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    dragCounterRef.current += 1;
    if (event.dataTransfer.types.includes("Files")) {
      setDragActive(true);
    }
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = "copy";
    if (event.dataTransfer.types.includes("Files")) {
      setDragActive(true);
    }
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    dragCounterRef.current = Math.max(0, dragCounterRef.current - 1);
    if (dragCounterRef.current === 0) {
      setDragActive(false);
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    dragCounterRef.current = 0;
    setDragActive(false);
    const files = Array.from(event.dataTransfer.files || []);
    if (files.length > 0) {
      handleFiles(files).catch(() => {});
    }
  }

  function renderComposer({ compact }: { compact: boolean }) {
    return (
      <div
        className={
          compact
            ? `relative w-full overflow-hidden rounded-[28px] border bg-white shadow-[0_24px_80px_rgba(15,23,42,0.08)] ${dragActive ? "border-sky-400 ring-4 ring-sky-100" : "border-slate-200"}`
            : `relative w-full overflow-hidden rounded-[28px] border bg-white shadow-[0_18px_60px_rgba(15,23,42,0.06)] ${dragActive ? "border-sky-400 ring-4 ring-sky-100" : "border-slate-200"}`
        }
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {dragActive ? (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-sky-50/80 backdrop-blur-[1px]">
            <div className="rounded-full border border-sky-200 bg-white px-5 py-2 text-sm font-medium text-sky-700 shadow-sm">
              松开以上传文件
            </div>
          </div>
          
        ) : null}
        {pendingFiles.length > 0 ? (
          <div className="flex flex-wrap gap-2 border-b border-slate-100 px-5 py-3">
            {pendingFiles.map((file) => (
              <div
                key={file.id}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600"
              >
                <Icon icon="ri:file-2-line" width="14" />
                <span>{file.name}</span>
                <button
                  className="inline-flex h-4 w-4 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
                  onClick={() => removePendingFile(file.id)}
                  type="button"
                >
                  <Icon icon="ri:close-line" width="12" />
                </button>
              </div>
            ))}
          </div>
        ) : null}
        <textarea
          ref={composerRef}
          className={
            compact
              ? "min-h-[92px] max-h-[180px] w-full resize-none overflow-y-auto border-none bg-transparent pl-5 pr-36 pt-4 pb-16 text-sm leading-7 text-slate-800 outline-none placeholder:text-slate-400"
              : "min-h-[116px] max-h-[220px] w-full resize-none overflow-y-auto border-none bg-transparent pl-5 pr-40 pt-4 pb-16 text-sm leading-7 text-slate-800 outline-none placeholder:text-slate-400"
          }
          onChange={(event) => {
            setInput(event.target.value);
            event.currentTarget.scrollTop = event.currentTarget.scrollHeight;
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              send().catch(() => {});
            }
          }}
          placeholder="输入你的科学数据处理需求，例如：请提取文中的材料名称、实验条件和结果指标。"
          rows={1}
          value={input}
        />

        <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-end justify-between px-5 pb-4">
          <div className="pointer-events-auto flex items-center gap-2 text-xs text-slate-500">
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-full px-2 py-1.5 transition-colors hover:bg-slate-100 hover:text-slate-900">
              <input
                className="hidden"
                onChange={(event) => {
                  const files = Array.from(event.target.files || []);
                  if (files.length > 0) {
                    handleFiles(files).catch(() => {});
                  }
                  event.currentTarget.value = "";
                }}
                multiple
                type="file"
              />
              <Icon icon="ri:add-line" width="15" />
              <span>附件</span>
            </label>

            <button
              className="inline-flex items-center gap-2 rounded-full px-2 py-1.5 transition-colors hover:bg-slate-100 hover:text-slate-900"
              onClick={() => (window.location.href = "/skills")}
              type="button"
            >
              <Icon icon="ri:flashlight-line" width="15" />
              <span>算子</span>
            </button>
          </div>

          <div className="pointer-events-auto flex items-center gap-3">
            {!compact ? (
              <span className="text-xs font-medium text-slate-400">
                {uploading ? "附件上传中" : sending ? "处理中" : "快速发送"}
              </span>
            ) : null}
            <button
              className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition-colors hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-300"
              disabled={sending || uploading || (!input.trim() && pendingFiles.length === 0)}
              onClick={() => send().catch(() => {})}
              type="button"
            >
              <Icon icon={uploading ? "ri:loader-4-line" : sending ? "ri:stop-fill" : "ri:arrow-right-line"} width="18" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-full flex-1 flex-col">
      {!isExpanded ? (
        <section className="px-8 pb-16 pt-6">
          <div className="mx-auto flex max-w-5xl flex-col">
            <div className="border-b border-slate-200/70 bg-white/40 px-8 pb-14 pt-10 text-center">
              <div className="mx-auto max-w-4xl">
                <h1 className="mb-5 text-[38px] font-bold tracking-tight text-slate-950">
                  πFlow AI：面向科学数据加工处理的智能工作台
                </h1>
                <p className="mx-auto max-w-2xl text-[15px] leading-7 text-slate-500">
                  专注科学数据治理，赋能科学语料构建
                </p>
              </div>
            </div>

            <div className="mx-auto -mt-8 w-full max-w-[760px]">
              {renderComposer({ compact: true })}
            </div>

            <div className="mt-16">
              <div className="mb-8 text-center">
                <h2 className="text-sm font-bold uppercase tracking-[0.24em] text-slate-900">
                  选择加工流水线示例，一键体验
                </h2>
                <div className="mx-auto mt-3 h-0.5 w-12 bg-black" />
              </div>

              <div className="grid gap-6 md:grid-cols-3">
                {EXAMPLES.map((card) => (
                  <button
                    key={card.title}
                    className="group overflow-hidden rounded-[26px] border border-slate-200 bg-white text-left shadow-[0_20px_60px_rgba(15,23,42,0.04)] transition-all hover:-translate-y-1 hover:border-black"
                    onClick={() => startExample(card)}
                    type="button"
                  >
                    <div className="aspect-video overflow-hidden bg-slate-100">
                      <img
                        alt={card.title}
                        className="h-full w-full object-cover opacity-90 transition-transform duration-300 group-hover:scale-105"
                        src={card.image}
                      />
                    </div>
                    <div className="p-5">
                      <h3 className="text-sm font-bold text-slate-900">{card.title}</h3>
                      <p className="mt-2 text-xs leading-6 text-slate-500">{card.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="flex min-h-screen max-h-screen flex-1 flex-col overflow-hidden">
          <div className="flex flex-1 min-w-0 canvas-split-container">
            {/* 左侧对话区域 */}
            <div className={`flex max-h-screen flex-col min-w-0`}
              style={{ width: showCanvas ? `${100 - canvasWidth}%` : '100%' }}>
              <div className="flex h-full min-h-0 w-full flex-1 flex-col px-8 pt-6">
                {loadError ? (
                  <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    加载对话失败：{loadError}
                  </div>
                ) : null}

                <div
                  ref={transcriptRef}
                  className="flex-1 space-y-5 overflow-y-auto px-2 py-4 custom-scrollbar"
                >
                  {hasMessages ? (
                    messages.map((message) => {
                      const isAssistant = message.role === "assistant";
                      return (
                        <article
                          key={message.id}
                          className={isAssistant ? "max-w-[82%]" : "ml-auto flex max-w-[70%] flex-col items-end"}
                        >
                          <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-slate-400">
                            <span className={isAssistant ? "normal-case" : ""}>
                              {isAssistant ? "πFlow" : "USER"}
                            </span>
                            {isAssistant && message.reasoning ? (
                              <span className="text-emerald-500">Thinking</span>
                            ) : null}
                          </div>

                          {isAssistant ? (
                            <div className="rounded-[28px] bg-transparent px-1 py-1">
                              {(() => {
                                try {
                                  const { data: pipelineData, cleanedText } = extractAndCleanPipelineJson(message.content || '');
                                  
                                  // 检查是否是执行结果，同时检查原始内容和清理后的内容
                                  const isExecutionResult = (cleanedText.includes('已完成') || 
                                                          cleanedText.includes('执行成功') || 
                                                          cleanedText.includes('运行完成') ||
                                                          cleanedText.includes('处理完成') ||
                                                          (message.content || '').includes('已完成') || 
                                                          (message.content || '').includes('执行成功') || 
                                                          (message.content || '').includes('运行完成') ||
                                                          (message.content || '').includes('处理完成'));
                                  
                                  if (pipelineData && (!sending || message.id !== activeAssistantId)) {
                                    return (
                                      <>
                                        {cleanedText && <MarkdownMessage content={removeAllJson(cleanedText)} pending={sending} />}
                                        <PipelinePreview data={pipelineData} threadId={threadId} onOpenCanvas={handleOpenCanvas} messageId={message.id} />
                                        {isExecutionResult && message.artifacts && message.artifacts.length > 0 && (
                                          <div className="mt-4 flex flex-wrap gap-2 pt-1">
                                            {message.artifacts.map((path) => (
                                              <a
                                                key={path}
                                                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 transition-colors hover:border-black hover:text-black"
                                                href={downloadWorkspaceUrl(path)}
                                                rel="noreferrer"
                                                target="_blank"
                                              >
                                                <Icon icon="ri:download-2-line" width="14" />
                                                <span>{path.split("/").pop() || "下载产物"}</span>
                                              </a>
                                            ))}
                                          </div>
                                        )}
                                      </>
                                    );
                                  }
                                } catch (err) {
                                  console.error('[PipelineDebug] Error:', err);
                                }
                                
                                // 如果没有pipelineData，移除JSON后渲染
                                let displayText = message.content || '';
                                if (sending) {
                                  displayText = displayText.replace(/```(?:json)?[\s\S]*$/g, '').trim();
                                }
                                return <MarkdownMessage content={removeAllJson(displayText)} pending={sending} />;
                              })()}

                              {sending && message.id === activeAssistantId ? (
                                <div className="mt-3 w-fit rounded-full bg-white px-3 py-1 text-[11px] text-slate-500 shadow-sm ring-1 ring-slate-200">
                                  {streamStatus || "处理中..."}
                                </div>
                              ) : null}
                              {isAssistant && message.reasoning ? (
                                <details
                                  className="mt-4 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-3"
                                  open={sending}
                                >
                                  <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
                                    思考过程
                                  </summary>
                                  <pre className="mt-3 whitespace-pre-wrap break-words font-sans text-xs leading-6 text-emerald-900">
                                    {message.reasoning}
                                  </pre>
                                </details>
                              ) : null}

                              {/* 非流程图消息的文件显示（只有执行结果才显示） */}
                              {(() => {
                                try {
                                  const c = message.content || '';
                                  const { data: pipelineData, cleanedText } = extractAndCleanPipelineJson(c);
                                  if (!pipelineData) {
                                    const isExecutionResult = cleanedText.includes('已完成') || 
                                                            cleanedText.includes('执行成功') || 
                                                            cleanedText.includes('运行完成') ||
                                                            cleanedText.includes('处理完成');
                                    if (isExecutionResult && message.artifacts && message.artifacts.length > 0) {
                                      return (
                                        <div className="mt-4 flex flex-wrap gap-2 pt-1">
                                          {message.artifacts.map((path) => (
                                            <a
                                              key={path}
                                              className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 transition-colors hover:border-black hover:text-black"
                                              href={downloadWorkspaceUrl(path)}
                                              rel="noreferrer"
                                              target="_blank"
                                            >
                                              <Icon icon="ri:download-2-line" width="14" />
                                              <span>{path.split("/").pop() || "下载产物"}</span>
                                            </a>
                                          ))}
                                        </div>
                                      );
                                    }
                                  }
                                } catch {
                                  // ignore
                                }
                                return null;
                              })()}
                            </div>
                          ) : (
                            <div
                              className={`relative w-fit max-w-full ${message.attachments && message.attachments.length > 0 ? "pt-8" : ""}`}
                            >
                              {message.attachments && message.attachments.length > 0 ? (
                                <div className="absolute right-0 top-0 z-10 flex max-w-full flex-wrap justify-end gap-2">
                                  {message.attachments.map((file) => (
                                    <a
                                      key={`${message.id}-${file.path}`}
                                      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 shadow-sm transition-colors hover:border-black hover:text-black"
                                      href={downloadWorkspaceUrl(file.path)}
                                      rel="noreferrer"
                                      target="_blank"
                                    >
                                      <Icon icon="ri:file-2-line" width="14" />
                                      <span>{file.name}</span>
                                    </a>
                                  ))}
                                </div>
                              ) : null}
                              <div className="inline-block w-fit max-w-full rounded-[24px] bg-slate-100 px-4 py-3 text-slate-900">
                                {(() => {
                                  let c = removeAllJson(message.content || '');
                                  return c ? <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-7 text-slate-900">{c}</pre> : null;
                                })()}
                              </div>
                            </div>
                          )}
                        </article>
                      );
                    })
                  ) : (
                    <div className="flex h-full items-center justify-center text-sm text-slate-400">
                      输入内容后，这里会展开完整对话。
                    </div>
                  )}
                </div>

                <div className="sticky bottom-3 pt-2">
                  {renderComposer({ compact: false })}
                </div>
              </div>
            </div>

            {/* 右侧画板区域 */}
            {showCanvas && canvasPipelineData && (
              <>
                {/* 拖拽分隔条 */}
                <div
                  className="canvas-drag-handle flex-shrink-0 cursor-col-resize hover:bg-sky-400/50 active:bg-sky-500/70 transition-colors"
                  style={{ width: '4px' }}
                  onMouseDown={() => {
                    isDraggingRef.current = true;
                    document.body.style.cursor = 'col-resize';
                    document.body.style.userSelect = 'none';
                  }}
                />
                <div className="h-screen overflow-hidden border-l border-slate-200 shadow-[-2px_0_12px_rgba(0,0,0,0.04)] animate-slide-in-right flex-shrink-0"
                  style={{ width: `${canvasWidth}%` }}>
                  <FlowEditor initialPipelineData={canvasPipelineData as unknown as InitialPipelineData} onClose={handleCloseCanvas} threadId={threadId} messageId={canvasMessageId} savedDrawData={savedDrawData} />
                </div>
              </>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
