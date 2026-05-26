import { Icon } from "@iconify/react";
import { type DragEvent, useEffect, useRef, useState } from "react";
import {
  attachMessageFiles,
  createMessage,
  downloadWorkspaceUrl,
  getThreadMessages,
  streamChat,
  uploadWorkspaceFile,
  type MessageAttachment,
  type ThreadMessage,
} from "../lib/api";
import { MarkdownMessage } from "../components/MarkdownMessage";
import { shortId } from "../lib/ids";
import Draw from '../components/Draw'; // 引入画板组件
import RunDetails from '../components/RunDetails'; // 引入流程运行详情组件
const DEFAULT_USER_ID = "default_user";

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

type cards = {
  title: string;
  description: string;
  prompt: string;
  image: string;
  attachments?: Array<Pick<MessageAttachment, "path" | "name">>;
};

const WORKSPACE_FILE_PATTERN = /\/(?:outputs|artifacts)\/[^\s"'`)\]}>,，。；：！？]+/g;

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

const EXAMPLES: cards[] = [
  {
    title: "数据清洗与排序",
    description: "「请对上传数据分别进行空行清洗、空格清洗，并根据fa0116字段进行升序排序。」",
    prompt:
      "请对上传数据分别进行空行清洗、空格清洗，并根据fa0116字段进行升序排序。",
    attachments: [
      {
        path: "/temp/森林每木调查数据-blank-line-space.csv",
        name: "森林每木调查数据-blank-line-space.csv",
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

// 节点数据类型定义
interface FlowNode {
  id: string;
  label: string;
  bgColor: string;
  iconBgColor: string;
  icon: '';
}
// 自定义节点数据，与图片中的节点一一对应
const waterNodeArr: FlowNode[] = [
  {
    id: 'upload',
    label: '文件上传',
    bgColor: '#e8f3ff',
    iconBgColor: '#3b82f6',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
        <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" />
      </svg>
    ),
  },
  {
    id: 'empty-clean',
    label: '空行清洗',
    bgColor: '#fff3cd',
    iconBgColor: '#f59e0b',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
      </svg>
    ),
  },
  {
    id: 'space-clean',
    label: '空格清洗',
    bgColor: '#f3e8ff',
    iconBgColor: '#a855f7',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
        <path d="M5 4v3h5.5v12h3V7H19V4z" />
      </svg>
    ),
  },
  {
    id: 'sort',
    label: '年份排序',
    bgColor: '#dcfce7',
    iconBgColor: '#22c55e',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
      </svg>
    ),
  },
];

export function DialoguePage() {
  const [threadId, setThreadId] = useState<string>("default");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<UiMsg[]>([]);
  const [sending, setSending] = useState(false);
  //显示发送问题后预览流水线
  const [showQuestionPreview, setShowQuestionPreview] = useState(false);
  const [streamStatus, setStreamStatus] = useState("");
  const [activeAssistantId, setActiveAssistantId] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<PendingAttachment[]>([]);
  const [uploadingCount, setUploadingCount] = useState(0);
  const [loadError, setLoadError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [showDraw, setDraw] = useState(true);//是否显示画板
  const [showRunDetails, setRunDetails] = useState(false);//是否显示运行流程详情
  const abortRef = useRef<AbortController | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);
  const dragCounterRef = useRef(0);

  const hasMessages = messages.length > 0;

  const uploading = uploadingCount > 0;
  const isExpanded = hasMessages || sending || Boolean(loadError);
  // // 页面加载时请求登录接口
  // useEffect(() => {
  //   const login = async () => {
  //     try {
  //       let params={ username:'admin',password:'admin123' };
  //       let loginRes=await getLogin(params);
  //       localStorage.setItem('token',loginRes.access_token);
  //     } catch (error) {
  //       console.error('登录失败:', error);
  //     }
  //   };
    
  //   login();
  // }, []);
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

    return () => {
      window.removeEventListener("flow:new-chat", handleNewChat);
      window.removeEventListener("flow:select-thread", handleSelectThread as EventListener);
    };
  }, []);

  async function loadThread(nextThreadId: string) {
    abortRef.current?.abort();
    abortRef.current = null;
    setThreadId(nextThreadId);
    setStreamStatus("");
    setActiveAssistantId(null);
    setLoadError("");
    setPendingFiles([]);

    try {
      const response = await getThreadMessages(DEFAULT_USER_ID, nextThreadId, 200);
      setMessages((response.messages || []).map((message, index) => toUiMessage(nextThreadId, message, index)));
    } catch (error: any) {
      setMessages([]);
      setLoadError(String(error?.message || error));
    }
  }
  // 发送问题
  function sendQuestion(sta:boolean){
    setShowQuestionPreview(sta);
  }
  // 发送消息
  async function send(
    overridePrompt?: string,
    options?: {
      threadId?: string;
      presetAttachments?: Array<Pick<MessageAttachment, "path" | "name">>;
    },
  ) {
    const prompt = (overridePrompt ?? input).trim();
    if ((!prompt && pendingFiles.length === 0) || sending || uploading) {
      return;
    }
    const targetThreadId = options?.threadId ?? threadId;
    const presetAttachments = options?.presetAttachments || [];

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
      };

      setMessages((current) => [...current, userMessage, assistantMessage]);
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

  function startExample(card: cards) {
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
  // 打开编辑画板
  function openDraw(){
    setRunDetails(false);
    setDraw(true);
  }
  // 打开运行流程详情
  function openRunDetails(){
    setDraw(false);
    setRunDetails(true);
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
        {/* 生成问题回答预览流水线 */}
        {showQuestionPreview ? <div style={{
            width: '90%',
            margin: '16px auto',
            fontSize:'16px'
          }}>
            {/* 主卡片容器 */}
            <div style={{
              background: '#ffffff',
              borderRadius: '12px',
              padding: '16px',
              boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
            }}>
              {/* 头部文字 */}
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '20px' }}>
                {/* 左侧小图标 */}
                <div style={{
                  boxSizing:'border-box',
                  backgroundColor: '#000000',
                  width: '26px',
                  height: '26px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '6px',
                  flexShrink: 0,
                }}>
                  <svg width="18" height="18" viewBox="0 0 22 22" fill="#FFFFFF">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                  </svg>
                </div>
                <div style={{fontSize: '16px', lineHeight: 1.5, color: '#333333' }}>
                  我已根据您的需求生成了完整的科研数据清洗与排序流水线，包含以下 4 个加工环节：
                </div>
              </div>

              {/* 预览区域 */}
              <div style={{
                boxSizing:'border-box',
                borderRadius: '8px',
                padding: '20px',
                background: 'F9FAFB',
                marginBottom: '6px'
              }}>
                {/* 预览标题 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '16px', fontSize: '14px', color: '#333333' }}>
                  <span>流水线预览</span>
                  <span>|</span>
                  <span style={{ color: '#333333' }}>科研数据清洗与排序</span>
                </div>

                {/* 流水线 */}
                <div style={{ display: 'flex', alignItems: 'center',flexWrap:'wrap', marginBottom: '16px', gap: '8px' }}>
                  {waterNodeArr.map((oneNode, index) => (
                    <div key={oneNode.id} style={{ display: 'flex', alignItems: 'center',}}>
                      {/* 节点按钮 */}
                      <div style={{
                        boxSizing:'border-box',
                        borderRadius: '6px',
                        padding: '6px 12px',
                        whiteSpace: 'nowrap',
                        background: oneNode.bgColor,
                        fontSize: '14px',
                        fontWeight: 500,
                        color: '#333333',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}>
                        <div style={{
                          boxSizing:'border-box',
                          width: '18px',
                          height: '18px',
                          borderRadius: '3px',
                          background: oneNode.iconBgColor,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}>
                          {oneNode.icon}
                        </div>
                        {oneNode.label}
                      </div>
                      {/* 算子间连接线 */}
                      {index < waterNodeArr.length - 1 && (
                        <div style={{marginLeft:'5px'}}>
                          <svg width="14" height="14" viewBox="0 0 22 22" fill="#9ca3af">
                            <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
                          </svg>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* 状态的校验 */}
                <div style={{ fontSize: '14px', color: '#333333', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#9ca3af">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
                    </svg>
                    <span>4 个节点</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#9ca3af">
                      <path d="M16 13c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm-8 0c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm4-6c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 14c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z" />
                    </svg>
                    <span>3 条连线</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#16a34a' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#16a34a">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                    </svg>
                    <span>校验通过</span>
                  </div>
                </div>
              </div>

              {/* 底部按钮 */}
              <div style={{ display: 'flex', gap: '12px' }}>
                <button style={{
                  cursor: 'pointer',
                  boxSizing:'border-box',
                  borderRadius: '8px',
                  border: 'none',
                  padding: '8px 20px',
                  background: '#059669',
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '15px',
                  color: '#ffffff',
                  gap: '6px',
                }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  一键运行
                </button>
                <button style={{
                  cursor: 'pointer',
                  boxSizing:'border-box',
                  background: '#ffffff',
                  padding: '8px 20px',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '16px',
                  color: '#666666'
                }}
                onClick={() => openDraw()}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="#111827">
                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                  </svg>
                  打开画板编辑
                </button>
              </div>
            </div>

            {/* 底部时间戳 */}
            <div style={{ fontSize: '12px', color: '#999999', marginTop: '6px' }}>
              10:46 · AI 生成
            </div>
          </div> : <div></div>}
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
            if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
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
              <span>技能</span>
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
              // onClick={() => sendQuestion(true)}
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
        <section className="px-2 pb-2 pt-2" style={{width:'100%',display:'flex'}}>
          <div className="mx-auto" style={{width:showDraw || showRunDetails ? '35%' : '65%'}}>
            <div className="mx-auto -mt-8 w-full max-w-[760px]">
              {renderComposer({ compact: true })}
            </div>
          </div>
          {showDraw ?(
          <div className="mx-auto" style={{width:'70%',marginLeft:'10px'}}>
            <Draw></Draw>
          </div>) : <span></span>}
          {showRunDetails ?(
          <div className="mx-auto" style={{width:'70%',marginLeft:'10px'}}>
            <RunDetails></RunDetails>
          </div>) : <span></span>}
        </section>
      ) : (
        <section className="flex min-h-0 flex-1 flex-col px-8 pb-6 pt-6">
          <div className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col">
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
                          <MarkdownMessage content={message.content} pending={sending} />

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

                          {isAssistant && message.artifacts && message.artifacts.length > 0 ? (
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
                          ) : null}
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
                            <pre className="custom-scrollbar max-h-60 overflow-auto whitespace-pre-wrap break-words font-sans text-sm leading-7 text-slate-900">
                              {message.content}
                            </pre>
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

            <div className="sticky bottom-0 pt-2">
              {renderComposer({ compact: false })}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
