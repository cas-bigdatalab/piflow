import { Icon } from "@iconify/react";
import { type DragEvent, useEffect, useRef, useState,useCallback } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  listStorage,
  attachMessageFiles,
  createMessage,
  downloadWorkspaceUrl,
  getThreadMessages,
  streamChat,
  uploadWorkspaceFile,
  uploadWorkspaceFileAttach,
  uploadWorkspaceFileNew,
  uploadWorkSpaceFileNew,
  getDrawInfoBymegId,
  copyDefaultFiles,
  listDataspaceDirecory,
  iconBase,
  type MessageAttachment,
  type ThreadMessage,
} from "../lib/api";
import { MarkdownMessage } from "../components/MarkdownMessage";
import { shortId } from "../lib/ids";
import PipelinePreview, { extractAndCleanPipelineJson, PipelineData } from "../components/PipelinePreview";
import FlowEditor, { InitialPipelineData } from "../components/Draw";
import { 
  FolderOpen, X, ChevronRight, Upload, Folder, FileText, Download, Database, 
  Plus, History, Sparkles, LayoutDashboard, Clock, HardDrive, Blocks, 
  Users, Server, Search, ChevronLeft, ChevronDown, LayoutTemplate, FileStack
} from 'lucide-react';
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
  icon: React.ReactNode;
  iconBg: string;
  iconColor: string;
  bgGradient: string;
  attachments?: Array<Pick<MessageAttachment, "path" | "name">>;
};

const WORKSPACE_FILE_PATTERN = /\/(?:outputs|artifacts)\/[^\s"'`)\]}>,，。；：！？]+/g;

function removeJsonBlock(text: string): string {
  let result = text;
  const jsonPattern = /\\"json\s*([{\[])/g;
  let match;
  
  while ((match = jsonPattern.exec(result)) !== null) {
    const startIndex = match.index;
    const openChar = match[1];
    const closeChar = openChar === '{' ? '}' : ']';
    
    let stack = 1;
    let endIndex = startIndex + match[0].length;
    let inString = false;
    let escapeCount = 0;
    
    while (endIndex < result.length && stack > 0) {
      const char = result[endIndex];
      
      if (char === '\\') {
        escapeCount++;
        endIndex++;
        continue;
      }
      
      if (char === '"') {
        if (escapeCount % 2 === 0) {
          inString = !inString;
        }
      }
      
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
    
    const before = result.substring(0, startIndex);
    const after = result.substring(endIndex);
    result = before + after;
    
    jsonPattern.lastIndex = 0;
  }
  
  return result;
}

function removeAllJson(text: string): string {
  if (!text) return text;
  
  let result = text;
  
  result = result.replace(/我手动修改了任务流程，请根据任务流程重新生成dag JSON[\s\S]*?不要执行。[\s\S]*?\n?/g, '').trim();
  result = result.replace(/我手动修改了任务流程，请根据任务流程重新生成dag JSON[\s\S]*?不要执行。/g, '').trim();
  
  result = result.replace(/```(json)?\s*[\s\S]*?```/g, '').trim();
  
  result = result.replace(/`([^`]*\{[^`]*\}[^`]*)`/g, '').trim();
  result = result.replace(/`([^`]*\[[^`]*\][^`]*)`/g, '').trim();
  
  result = removeJsonBlock(result);
  
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
  
  for (let j = partsToRemove.length - 1; j >= 0; j--) {
    const [start, end] = partsToRemove[j];
    result = result.substring(0, start) + result.substring(end);
  }
  
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

// ============ 示例卡片配置 - 4个卡片，新样式 ============
const EXAMPLES: ExampleCard[] = [
  {
    title: "元数据提取与文本提取",
    description: "「请对文档进行以下处理：1、提取文档元数据 2、提取pdf文档文本内容」",
    prompt:
      "请对文档进行以下处理：1、提取文档元数据 2、提取pdf文档文本内容",
    icon: <FileText className="w-5 h-5" />,
    iconBg: "bg-purple-100",
    iconColor: "text-purple-600",
    bgGradient: "from-purple-50/60 to-white",
    attachments: [
      {
        path: "/temp/Akcay.pdf",
        name: "Akcay.pdf",
      },
    ],
  },
  {
     title: "文档规范化处理",
    description: "「请检查文档的格式有效性，并转换成markdown格式的文档。」",
    prompt:
      "请检查文档的格式有效性，并转换成markdown格式的文档。",
    icon: <Database className="w-5 h-5" />,
    iconBg: "bg-emerald-100",
    iconColor: "text-emerald-600",
    bgGradient: "from-emerald-50/60 to-white",
    attachments: [
      {
        path: "/temp/森林每木调查数据.csv",
        name: "森林每木调查数据.csv",
      },
    ],
  },
  {
   title: "语料格式转换与过滤",
    description: "「请对上传数据csv文件转换为jsonl格式，再对这个jsonl的'fa0114'字段进行最大长度过滤，要求最大长度在40以内；再对'fa0112'字段筛选过滤出是'多花山矾'的数据」",
    prompt:
      "请对上传数据csv文件转换为jsonl格式，再对这个jsonl的'fa0114'字段进行最大长度过滤，要求最大长度在40以内；再对'fa0112'字段筛选过滤出是'多花山矾'的数据",
    icon: <Sparkles className="w-5 h-5" />,
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
    bgGradient: "from-blue-50/60 to-white",
  }
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
  const [pendingFilesNew,setPendingFilesNew] = useState("");
  const [uploadingCount, setUploadingCount] = useState(0);
  const [loadError, setLoadError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  
  const [showCanvas, setShowCanvas] = useState(false);
  const [canvasPipelineData, setCanvasPipelineData] = useState<PipelineData | null>(null);
  const [canvasMessageId, setCanvasMessageId] = useState<string>('');
  const [savedDrawData, setSavedDrawData] = useState<any>(null);
  const [canvasWidth, setCanvasWidth] = useState(50);
  const [canvasKey, setCanvasKey] = useState(0);
  const isDraggingRef = useRef(false);
  const canvasMessageIdRef = useRef('');
  
  const abortRef = useRef<AbortController | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);
  const dragCounterRef = useRef(0);

  const hasMessages = messages.length > 0;

  const uploading = uploadingCount > 0;
  const isExpanded = hasMessages || sending || Boolean(loadError);
  const [isSaved, setIsSaved] = useState(false);
  
  const [showFileModal, setShowFileModal] = useState(false);
  const [showFileModalSource,setShowFileModalSource]= useState(false);
  const [fileSelectParamIndex, setFileSelectParamIndex] = useState<number | null>(null);
  const [currentDirPath, setCurrentDirPath] = useState<string | null>(null);
  const [fileSystemItems, setFileSystemItems] = useState<Array<{ name: string; path: string; type: 'file' | 'directory' }>>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [isUploadingFileShow,setIsUpLoadingFileShow] = useState('');
  
  const [dataSources, setDataSources] = useState<{ id: string; name: string }[]>([]);
  const [isLoadingDataSources, setIsLoadingDataSources] = useState(false);
  
  const [selectedDataSourceId, setSelectedDataSourceId] = useState<string>('');
  const [storagePath, setStoragePath] = useState<string>('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [pendingDataSource, setPendingDataSource] = useState<{ sourceId: string; path: string } | null>(null);
  const [sourceFileName, setSourceFileName] = useState('')

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleGoBack = () => {
    if (!currentDirPath) return;
    const parts = currentDirPath.split('/').filter(Boolean);
    if (parts.length === 0) {
      setCurrentDirPath(null);
    } else {
      parts.pop();
      setCurrentDirPath(parts.length > 0 ? '/' + parts.join('/') : null);
    }
    loadFileSystem(currentDirPath ? '/' + parts.join('/') : null);
  };

  const loadDataSources = useCallback(async () => {
    setIsLoadingDataSources(true);
    try {
      const res = await listDataspaceDirecory(); 
      if (Array.isArray(res.result.items)) { 
        setDataSources(res.result.items.map(item => ({ source_id: item.source_id, database_name: item.database_name,name:item.name })));
      }
    } catch (err) {
      console.error('加载数据源失败:', err);
      setDataSources([]);
    } finally {
      setIsLoadingDataSources(false);
    }
  }, []);

  const loadFileSystem = async (path: string | null = currentDirPath) => {
    setIsLoadingFiles(true);
    try {
      const userId = localStorage.getItem('userId') || '';
      const res = await listStorage(userId, path || '/');
      setFileSystemItems(res.items || []);
      setShowFileModal(true)
    } catch (err) {
      console.error('加载文件系统失败', err);
      setFileSystemItems([]);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const userId = localStorage.getItem('userId') || '';
    const uploadPath = currentDirPath || '/';
    setUploadingFile(true);
    try {
      await uploadWorkSpaceFileNew(userId, file);
      await loadFileSystem(currentDirPath);
    } catch (err) {
      console.error('上传失败', err);
    } finally {
      setUploadingFile(false);
      e.target.value = '';
    }
  };

  const handleSelectFileForParam = (path: string) => {
    window.dispatchEvent(new CustomEvent('flow:select-file-for-param', {
      detail: { paramIndex: fileSelectParamIndex, filePath: path }
    }));
    setShowFileModal(false);
    setFileSelectParamIndex(null);
  };

  useEffect(() => {
    const handleOpenFileModal = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setShowFileModal(true);
      setFileSelectParamIndex(detail?.paramIndex ?? null);
      setCurrentDirPath(null);
      loadFileSystem(null);
    };
    window.addEventListener('flow:open-file-modal', handleOpenFileModal as EventListener);
    return () => {
      window.removeEventListener('flow:open-file-modal', handleOpenFileModal as EventListener);
    };
  }, []);

  const handleNavigateDir = (path: string) => {
    setCurrentDirPath(path);
    loadFileSystem(path);
  };

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = "./downloadFile/用户手册.pdf";
    link.download = "用户手册";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenCanvas = async (data: PipelineData, msgId?: string) => {
    setCanvasPipelineData(data);
    const currentMsgId = canvasMessageIdRef.current;
    if (!currentMsgId) {
      canvasMessageIdRef.current = msgId || '';
      setCanvasMessageId(msgId || '');
    }
    let drawData = null;
    let currentIsSaved = false;
    const effectiveMsgId = canvasMessageIdRef.current || msgId;
    if (effectiveMsgId) {
      try {
        const res = await getDrawInfoBymegId(effectiveMsgId);
        if (res.code === 200 && res.result) {
          drawData = res.result;
          currentIsSaved = true;
        } else {
          currentIsSaved = false;
        }
      } catch (e) {
        console.log('获取已保存画板信息失败，使用会话数据:', e);
      }
    }
    setSavedDrawData(drawData);
    setCanvasKey(prev => prev + 1);
    setShowCanvas(true);
    setIsSaved(currentIsSaved);
  };
  
  const handleCloseCanvas = () => {
    setShowCanvas(false);
    setCanvasPipelineData(null);
    setSavedDrawData(null);
    canvasMessageIdRef.current = '';
    setCanvasMessageId('');
  };

  useEffect(() => {
    if (canvasPipelineData) {
      console.log("画板数据已更新:", canvasPipelineData);
    }
  }, [canvasPipelineData]);

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
      setShowCanvas(false);
      setCanvasPipelineData(null);
      setCanvasMessageId("");
      setSavedDrawData(null);
      canvasMessageIdRef.current = '';
    };

    const handleSelectThread = (event: Event) => {
      const detail = (event as CustomEvent<{ thread_id?: string }>).detail;
      if (detail?.thread_id) {
        loadThread(detail.thread_id).catch(() => {});
      }
    };

    window.addEventListener("flow:new-chat", handleNewChat);
    window.addEventListener("flow:select-thread", handleSelectThread as EventListener);
    
    const handleSendMessage = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { threadId: eventThreadId, messageId, content, hidden } = customEvent.detail || {};
      if (eventThreadId && messageId && content) {
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
    let targetThreadId = options?.threadId ?? threadId;
    if (targetThreadId === "default") {
      targetThreadId = `t_${shortId()}`;
      setThreadId(targetThreadId);
    }
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
    window.dispatchEvent(new CustomEvent("flow:sending-start"));
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
        attachedPresetFiles = (attached.attachments || []).map(f => ({ ...f, _isPreset: true }));
      }

      const uploadedAttachments: MessageAttachment[] = [];
      if (filesToUpload.length > 0) {
        setUploadingCount(filesToUpload.length);
        setStreamStatus("正在上传附件...");
        if (isUploadingFileShow == 'kongjian'){
          const response = await uploadWorkspaceFileNew(
            DEFAULT_USER_ID,
            targetThreadId,
            messageId,
            pendingFilesNew,
          );
          uploadedAttachments.push({
            file_id: response.file_id,
            path: response.file_path,
            name: response.original_filename,
          });
          setUploadingCount((current) => Math.max(0, current - 1));
        } else if (isUploadingFileShow == 'file') {
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
        } else if (isUploadingFileShow == 'source') {
          const attachmentNew = [
            {
              path: pendingFilesNew,
              name: sourceFileName,
              type_code: "dataspace",
              source_id: selectedNodeId
            }
          ]
          const response = await uploadWorkspaceFileAttach(
            DEFAULT_USER_ID,
            targetThreadId,
            messageId,
            attachmentNew,
          );
          uploadedAttachments.push({
            file_id: response.attachments[0].file_id,
            path: response.attachments[0].path,
            name: response.attachments[0].name,
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

      if (hidden) {
        setMessages((current) => [...current, assistantMessage]);
      } else {
        setMessages((current) => [...current, userMessage, assistantMessage]);
      }
      
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
      window.dispatchEvent(new CustomEvent("flow:sending-end"));
    }
  }

  async function startExample(card: ExampleCard) {
    abortRef.current?.abort();
    abortRef.current = null;

    const userId = localStorage.getItem('userId') || '';
    try {
      await copyDefaultFiles(userId);
    } catch (e) {
      console.error('复制默认文件失败:', e);
    }

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

    setTimeout(() => {
      window.dispatchEvent(new CustomEvent("flow:threads-refresh"));
    }, 2000);
  }

  async function handleFiles(files: File[]) {
    setIsUpLoadingFileShow('file');
    setShowFileModal(false);
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

  async function handleFilesNew(files: File[]) {
    setIsUpLoadingFileShow('kongjian');
    setShowFileModal(false);
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
    setPendingFilesNew(files[0].path); 
  }

  async function handleFilesSource(files: File[]) {
    setIsUpLoadingFileShow('source');
    setShowFileModal(false);
    if (!files) {
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
    setPendingFilesNew(files[0].path); 
  }

  const handleDataSourceConfirm = useCallback((sourceId: string, path: string) => {
    console.log('Selected Data Source:', sourceId);
    setSelectedNodeId(sourceId)
    console.log('Storage Path:', path);
    
    setPendingFilesNew(path);  
    setPendingDataSource({ sourceId, path });
    const fileName = path.split('/').pop() || '';
    setSourceFileName(fileName);
    const mockFile = new File([""], path.split('/').pop() || "file", {
      type: "application/octet-stream"
    }) as any;
    mockFile.path = path;
    setPendingFilesNew(mockFile.path); 
    handleFilesSource([mockFile]);
  }, []);

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

  // ========== 侧边栏导航项 ==========
  const navItems = [
    { icon: <LayoutDashboard className="w-4 h-4" />, label: "智能编排", active: true },
    { icon: <Clock className="w-4 h-4" />, label: "任务管理" },
    { icon: <History className="w-4 h-4" />, label: "运行历史" },
    { divider: true },
    { icon: <HardDrive className="w-4 h-4" />, label: "数据管理", subItems: ["我的数据", "数据连接"] },
    { icon: <Blocks className="w-4 h-4" />, label: "算子管理" },
    { icon: <LayoutTemplate className="w-4 h-4" />, label: "工作流模板管理" },
    { divider: true },
    { icon: <Users className="w-4 h-4" />, label: "组织管理", subItems: ["组织成员", "计算资源管理", "组织信息", "角色权限"] },
  ];

  const recentChats = [
    { title: "请批量提取PDF文档的...", date: "2026.09.03" },
    { title: "请对文档进行以下处..", date: "2026.09.03" },
    { title: "请对文档进行以下处.", date: "2026.09.01" },
    { title: "请对文档进行以下处..", date: "2026.08.27" },
  ];

  function renderComposer({ compact }: { compact: boolean }) {
    return (
      <div
        className={
          compact
            ? `relative w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm ${dragActive ? "border-blue-400 ring-4 ring-blue-100" : ""}`
            : `relative w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm ${dragActive ? "border-blue-400 ring-4 ring-blue-100" : ""}`
        }
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {dragActive ? (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-blue-50/80 backdrop-blur-[1px]">
            <div className="rounded-full border border-blue-200 bg-white px-4 py-1.5 text-xs font-medium text-blue-700 shadow-sm">
              松开以上传文件
            </div>
          </div>
        ) : null}
        {pendingFiles.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 border-b border-slate-100 px-4 py-2.5">
            {pendingFiles.map((file) => (
              <div
                key={file.id}
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-[11px] text-slate-600"
              >
                <Icon icon="ri:file-2-line" width="13" />
                <span>{file.name}</span>
                <button
                  className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
                  onClick={() => removePendingFile(file.id)}
                  type="button"
                >
                  <Icon icon="ri:close-line" width="11" />
                </button>
              </div>
            ))}
          </div>
        ) : null}
        <textarea
          ref={composerRef}
          className={
            compact
              ? "min-h-[140px] max-h-[220px] w-full resize-none overflow-y-auto border-none bg-transparent px-6 pt-5 pb-16 text-sm leading-6 text-slate-800 outline-none placeholder:text-slate-400"
              : "min-h-[140px] max-h-[220px] w-full resize-none overflow-y-auto border-none bg-transparent px-6 pt-5 pb-16 text-sm leading-6 text-slate-800 outline-none placeholder:text-slate-400"
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

        <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-end justify-between px-6 pb-5">
          <div className="pointer-events-auto flex items-center gap-2 text-sm text-slate-500">
            {/* 保留原有的附件、数据空间、数据源、算子按钮 */}
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:bg-slate-50">
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
              <Plus className="w-4 h-4" />
              <span>附件</span>
            </label>
            <button
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:bg-slate-50"
              onClick={() => {
                setShowFileModal(true);
                setFileSelectParamIndex(null);
                setCurrentDirPath(null);
                loadFileSystem(null);
              }}
              type="button"
            >
              <History className="w-4 h-4" />
              <span>数据空间</span>
            </button>
            <button
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:bg-slate-50"
              onClick={async () => {
                setShowFileModalSource(true);              
                await loadDataSources();
              }}
              type="button"
            >
              <Database className="w-4 h-4" />
              <span>数据源</span>
            </button>
            <button
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:bg-slate-50"
              onClick={() => (window.location.href = "/skills")}
              type="button"
            >
              <Sparkles className="w-4 h-4" />
              <span>算子</span>
            </button>
          </div>

          <div className="pointer-events-auto flex items-center gap-2">
            {!compact ? (
              <span className="text-[10px] font-medium text-slate-400">
                {uploading ? "附件上传中" : sending ? "处理中" : "快速发送"}
              </span>
            ) : null}
            <button
              className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-white shadow-md transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={sending || uploading || (!input.trim() && pendingFiles.length === 0)}
              onClick={() => send().catch(() => {})}
              type="button"
            >
              <Icon icon={uploading ? "ri:loader-4-line" : sending ? "ri:stop-fill" : "ri:arrow-up-line"} width="18" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex min-h-screen"
      style={{
        background:
          "radial-gradient(ellipse 700px 360px at 50% -4px, rgba(49, 155, 0, .105) 0%, rgba(49, 155, 0, .030) 47%, transparent 74%), #ffffff",
      }}
    >

      {/* ===== 主内容区 ===== */}
      <main className="flex-1 min-w-0">
        {/* 右上角用户手册下载按钮 */}
        <div className="fixed right-6 top-4 z-50">
          <button
            onClick={() => handleDownload()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer shadow-sm border border-slate-200"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>用户手册下载</span>
          </button>
        </div>

        {!isExpanded ? (
          <section className="px-8 pb-16 pt-6">
            <div className="mx-auto flex max-w-4xl flex-col">
              {/* 头部区域 */}
              <div className="px-6 pb-6 pt-8 text-center">
                <div className="mx-auto max-w-3xl">
                  <div
                    style={{
                      margin: "0 auto 20px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      position: "relative",
                      zIndex: 2,
                    }}
                  >
                    <img
                      src={`${iconBase().replace(/\/+$/, "")}/storage/icon/logo.png`}
                      style={{ width: "56px", height: "56px" }}
                    />
                  </div>
                  <h1 className="mb-2 text-3xl font-bold tracking-tight text-slate-900">
                    今天想完成什么科研任务？
                  </h1>
                  <p className="text-sm text-slate-500">
                    描述科研任务，πFlow 将协助你生成、调整并运行可执行工作流。
                  </p>
                  <div className="mx-auto mt-3 h-0.5 w-12 bg-emerald-500 rounded-full" />
                </div>
              </div>

              {/* 输入框 */}
              <div className="mx-auto w-full max-w-3xl">
                {renderComposer({ compact: true })}
              </div>

              {/* 示例卡片 - 4个卡片，新样式 */}
              <div className="mt-12">
                <div className="mb-5 text-center">
                  <span className="text-xs font-medium text-slate-400 tracking-wider">
                    从示例开始
                  </span>
                </div>

                <div className="grid gap-4 md:grid-cols-2 items-stretch">
                  {EXAMPLES.map((card) => (
                    <button
                      key={card.title}
                      className={`group flex h-full min-h-[168px] flex-col overflow-hidden rounded-xl border border-slate-200/80 bg-gradient-to-br ${card.bgGradient} text-left transition-all hover:-translate-y-1 hover:shadow-md hover:border-slate-300 p-5`}
                      onClick={() => startExample(card)}
                      type="button"
                    >
                      <div className="flex items-start justify-between">
                        <div className={`rounded-lg p-2.5 ${card.iconBg} ${card.iconColor} shadow-sm`}>
                          {card.icon}
                        </div>
                        <svg 
                          className="w-4 h-4 text-slate-300 transition-transform group-hover:translate-x-0.5" 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                      <h3 className="mt-3 text-sm font-semibold text-slate-800">{card.title}</h3>
                      <p className="mt-1 text-xs leading-5 text-slate-500">{card.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>
        ) : (
          <section className="flex min-h-screen max-h-screen flex-1 flex-col overflow-hidden bg-[#f8fafc]">
            <div className="flex flex-1 min-w-0 canvas-split-container">
              <div className={`flex max-h-screen flex-col min-w-0 bg-[#f8fafc]`}
                style={{ width: showCanvas ? `${100 - canvasWidth}%` : '100%' }}>
                <div className="flex h-full min-h-0 w-full flex-1 flex-col px-6 pt-4">
                  {loadError ? (
                    <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                      加载对话失败：{loadError}
                    </div>
                  ) : null}

                  <div
                    ref={transcriptRef}
                    className="flex-1 space-y-4 overflow-y-auto px-2 py-3 custom-scrollbar"
                  >
                    {hasMessages ? (
                      messages.map((message) => {
                        const isAssistant = message.role === "assistant";
                        return (
                          <article
                            key={message.id}
                            className={isAssistant ? "max-w-[80%]" : "ml-auto flex max-w-[70%] flex-col items-end"}
                          >
                            <div className="mb-1.5 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-slate-400">
                              <span className={isAssistant ? "normal-case font-medium text-slate-600" : "font-medium text-slate-600"}>
                                {isAssistant ? "πFlow" : "USER"}
                              </span>
                              {isAssistant && message.reasoning ? (
                                <span className="text-emerald-600">Thinking</span>
                              ) : null}
                            </div>

                            {isAssistant ? (
                              <div className="rounded-2xl bg-white px-5 py-4 shadow-sm border border-slate-100">
                                {(() => {
                                  try {
                                    const { data: pipelineData, cleanedText } = extractAndCleanPipelineJson(message.content || '');
                                    
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
                                          <PipelinePreview data={pipelineData} threadId={threadId} onOpenCanvas={handleOpenCanvas} messageId={message.id} disabled={showCanvas} />
                                          {isExecutionResult && message.artifacts && message.artifacts.length > 0 && (
                                            <div className="mt-3 flex flex-wrap gap-2 pt-1">
                                              {message.artifacts.map((path) => (
                                                <a
                                                  key={path}
                                                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 transition-colors hover:border-slate-400 hover:text-slate-800"
                                                  href={downloadWorkspaceUrl(path)}
                                                  rel="noreferrer"
                                                  target="_blank"
                                                >
                                                  <Icon icon="ri:download-2-line" width="13" />
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
                                  
                                  let displayText = message.content || '';
                                  if (sending) {
                                    displayText = displayText.replace(/```(?:json)?[\s\S]*$/g, '').trim();
                                  }
                                  return <MarkdownMessage content={removeAllJson(displayText)} pending={sending} />;
                                })()}

                                {sending && message.id === activeAssistantId ? (
                                  <div className="mt-2 w-fit rounded-full bg-slate-100 px-3 py-0.5 text-[10px] text-slate-500">
                                    {streamStatus || "处理中..."}
                                  </div>
                                ) : null}
                                {isAssistant && message.reasoning ? (
                                  <details
                                    className="mt-3 rounded-xl border border-emerald-100 bg-emerald-50/60 p-3"
                                    open={sending}
                                  >
                                    <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-700">
                                      思考过程
                                    </summary>
                                    <pre className="mt-2 whitespace-pre-wrap break-words font-sans text-xs leading-5 text-emerald-800">
                                      {message.reasoning}
                                    </pre>
                                  </details>
                                ) : null}

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
                                          <div className="mt-3 flex flex-wrap gap-2 pt-1">
                                            {message.artifacts.map((path) => (
                                              <a
                                                key={path}
                                                className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 transition-colors hover:border-slate-400 hover:text-slate-800"
                                                href={downloadWorkspaceUrl(path)}
                                                rel="noreferrer"
                                                target="_blank"
                                              >
                                                <Icon icon="ri:download-2-line" width="13" />
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
                                className={`relative w-fit max-w-full ${message.attachments && message.attachments.length > 0 ? "pt-7" : ""}`}
                              >
                                {message.attachments && message.attachments.length > 0 ? (
                                  <div className="absolute right-0 top-0 z-10 flex max-w-full flex-wrap justify-end gap-1.5">
                                    {message.attachments.map((file) => {
                                      const isPreset = (file as any)._isPreset;
                                      if (isPreset) {
                                        return (
                                          <span
                                            key={`${message.id}-${file.path}`}
                                            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[10px] font-medium text-slate-500 shadow-sm cursor-default"
                                          >
                                            <Icon icon="ri:file-2-line" width="12" />
                                            <span>{file.name}</span>
                                          </span>
                                        );
                                      }
                                      return (
                                        <a
                                          key={`${message.id}-${file.path}`}
                                          className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[10px] font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-400 hover:text-slate-800"
                                          href={downloadWorkspaceUrl(file.path)}
                                          rel="noreferrer"
                                          target="_blank"
                                        >
                                          <Icon icon="ri:file-2-line" width="12" />
                                          <span>{file.name}</span>
                                        </a>
                                      );
                                    })}
                                  </div>
                                ) : null}
                                <div className="inline-block w-fit max-w-full rounded-2xl bg-white px-4 py-3 text-slate-800 shadow-sm border border-slate-100">
                                  {(() => {
                                    let c = removeAllJson(message.content || '');
                                    return c ? <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-6 text-slate-800">{c}</pre> : null;
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

                  <div className="sticky bottom-2 pt-2">
                    {renderComposer({ compact: false })}
                  </div>
                </div>
              </div>

              {showCanvas && canvasPipelineData && (
                <>
                  <div 
                    className="canvas-drag-handle flex-shrink-0 cursor-col-resize hover:bg-slate-300 active:bg-slate-400 transition-colors"
                    style={{ width: '3px', background: '#e2e8f0' }}
                    onMouseDown={() => {
                      isDraggingRef.current = true;
                      document.body.style.cursor = 'col-resize';
                      document.body.style.userSelect = 'none';
                    }}
                  />
                  <div className="h-screen overflow-hidden bg-white shadow-[-2px_0_12px_rgba(0,0,0,0.04)] flex-shrink-0"
                    style={{ width: `${canvasWidth}%` }}>
                    <FlowEditor key={canvasKey} initialPipelineData={canvasPipelineData as unknown as InitialPipelineData} onClose={handleCloseCanvas} threadId={threadId} messageId={canvasMessageId} savedDrawData={savedDrawData}
                      isSaved={isSaved} />
                  </div>
                </>
              )}
            </div>
          </section>
        )}

        {/* 文件系统弹窗 */}
        {showFileModal && (
          <div className="file-system-overlay" onClick={() => { setShowFileModal(false); setFileSelectParamIndex(null); }}>
            <div className="file-system-modal" onClick={(e) => e.stopPropagation()}>
              <div className="file-system-header">
                <div className="file-system-title">
                  <FolderOpen size={16} />
                  <span>{fileSelectParamIndex !== null ? '选择文件' : '文件系统'}</span>
                </div>
                <button className="file-system-close" onClick={() => { setShowFileModal(false); setFileSelectParamIndex(null); }}>
                  <X size={16} />
                </button>
              </div>

              <div className="file-system-path-bar">
                <button 
                  className="file-system-back-btn" 
                  onClick={handleGoBack}
                  disabled={!currentDirPath}
                >
                  <ChevronRight size={13} style={{ transform: 'rotate(180deg)' }} />
                </button>
                <div className="file-system-path">
                  {currentDirPath ? (
                    <span>{currentDirPath}</span>
                  ) : (
                    <span>根目录</span>
                  )}
                </div>
              </div>

              <div className="file-system-actions">
                {fileSelectParamIndex === null && (
                  <label className="file-system-upload-btn">
                    <Upload size={13} />
                    <span>{uploadingFile ? '上传中...' : '上传文件'}</span>
                    <input
                      type="file"
                      onChange={handleUploadFile}
                      className="file-system-upload-input"
                      disabled={uploadingFile}
                    />
                  </label>
                )}
                {fileSelectParamIndex !== null && (
                  <span className="file-system-hint">双击文件或点击"选择"按钮选中文件</span>
                )}
              </div>

              <div className="file-system-content">
                {isLoadingFiles ? (
                  <div className="file-system-loading">
                    <span>加载中...</span>
                  </div>
                ) : fileSystemItems.length === 0 ? (
                  <div className="file-system-empty">
                    <Folder size={40} style={{ color: '#94a3b8' }} />
                    <span>该目录为空</span>
                  </div>
                ) : (
                  <div className="file-system-list">
                    {fileSystemItems.map((item, index) => (
                      <div
                        key={index}
                        className={`file-system-item ${item.type}`}
                        onClick={() => {
                          if (item.type === 'directory') {
                            handleNavigateDir(item.path);
                          }
                        }}
                        onDoubleClick={() => {
                          if (item.type === 'file' && fileSelectParamIndex !== null) {
                            handleSelectFileForParam(item.path);
                          }
                        }}
                      >
                        <div className="file-system-item-icon">
                          {item.type === 'directory' ? (
                            <Folder size={16} style={{ color: '#3b82f6' }} />
                          ) : (
                            <FileText size={16} style={{ color: '#64748b' }} />
                          )}
                        </div>
                        <span className="file-system-item-name">{item.name}</span>
                        {item.type === 'file' && (
                          <button
                            className="file-system-select-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFilesNew([item])
                            }}
                          >
                            选择
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 数据源弹窗 */}
        {showFileModalSource && (
          <div className="file-system-overlay">
            <div className="file-system-modalSource" onClick={(e) => e.stopPropagation()}>
              <div className="file-system-header">
                <div className="file-system-title">
                  <Database size={16} />
                  <span>选择数据源</span>
                </div>
                <button 
                  className="file-system-close" 
                  onClick={() => {
                    setShowFileModalSource(false);
                    setSelectedDataSourceId('');
                    setStoragePath('');
                  }}
                >
                  <X size={16} />
                </button>
              </div>

              <div className="file-system-content" style={{ padding: '16px' }}>
                {isLoadingDataSources ? (
                  <div className="file-system-loading">
                    <span>加载数据源...</span>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">目标数据源</label>
                      <select
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        value={selectedDataSourceId}
                        onChange={(e) => {
                          setSelectedDataSourceId(e.target.value);
                        }}
                      >
                        <option value="">请选择数据源</option>
                        {dataSources.map((ds) => (
                          <option key={ds.source_id} value={ds.source_id}>
                            {ds.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">存储路径</label>
                      <input
                        type="text"
                        placeholder="请输入存储路径"
                        value={storagePath}
                        onChange={(e) => setStoragePath(e.target.value)}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                      <button
                        type="button"
                        className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onClick={() => {
                          setShowFileModalSource(false);
                          setSelectedDataSourceId('');
                          setStoragePath('');
                        }}
                      >
                        取消
                      </button>
                      <button
                        type="button"
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                        disabled={!selectedDataSourceId || !storagePath.trim()}
                        onClick={() => {
                          if (selectedDataSourceId && storagePath.trim()) {
                            setNodes((nds) =>
                              nds.map((n) => {
                                if (n.id === selectedNodeId) {
                                  const newParams = [...(n.data.input_params?.params || [])];
                                  const dsIndex = newParams.findIndex((p) => p.name === 'datasource_id');
                                  if (dsIndex !== -1) {
                                    newParams[dsIndex] = {
                                      ...newParams[dsIndex],
                                      _value: selectedDataSourceId,
                                      param_value: selectedDataSourceId,
                                    };
                                  }
                                  const rpIndex = newParams.findIndex((p) => p.name === 'relative_path');
                                  if (rpIndex !== -1) {
                                    newParams[rpIndex] = {
                                      ...newParams[rpIndex],
                                      _value: storagePath.trim(),
                                      param_value: storagePath.trim(),
                                    };
                                  }
                                  return {
                                    ...n,
                                    data: {
                                      ...n.data,
                                      input_params: { ...n.data.input_params, params: newParams },
                                    },
                                  };
                                }
                                return n;
                              })
                            );

                            handleDataSourceConfirm(selectedDataSourceId, storagePath.trim());
                          }
                          setShowFileModalSource(false);
                          setSelectedDataSourceId('');
                          setStoragePath('');
                        }}
                      >
                        确定
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}