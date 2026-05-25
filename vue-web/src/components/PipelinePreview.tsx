import { Icon } from "@iconify/react";
import { useMemo } from "react";
import { useNavigate } from "react-router-dom";

interface PipelineNode {
  node_name: string;
  skill_name?: string;
  params?: Record<string, unknown>;
}

interface PipelineTask {
  name: string;
  description?: string;
  nodes?: PipelineNode[];
}

export interface PipelineData {
  task: PipelineTask;
  nodes: PipelineNode[];
}

function tryParseAsPipeline(obj: unknown): PipelineData | null {
  if (!obj || typeof obj !== "object") return null;
  const record = obj as Record<string, unknown>;
  const task = record.task;
  if (!task || typeof task !== "object") return null;
  const taskRecord = task as Record<string, unknown>;
  if (typeof taskRecord.name !== "string") return null;
  let nodes: unknown[] | undefined;
  if (Array.isArray(record.nodes) && record.nodes.length > 0) {
    nodes = record.nodes;
  } else if (Array.isArray(taskRecord.nodes) && taskRecord.nodes.length > 0) {
    nodes = taskRecord.nodes;
  }
  if (!nodes) return null;
  return { task: taskRecord as PipelineTask, nodes: nodes as PipelineNode[] };
}

export function extractPipelineJson(text: string): PipelineData | null {
  if (!text || typeof text !== "string") return null;
  const trimmed = text.trim();
  try {
    const parsed = JSON.parse(trimmed);
    const result = tryParseAsPipeline(parsed);
    if (result) return result;
  } catch {}
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    try {
      const inner = JSON.parse(trimmed) as string;
      if (typeof inner === "string") {
        const innerParsed = JSON.parse(inner);
        const result = tryParseAsPipeline(innerParsed);
        if (result) return result;
      }
    } catch {}
  }
  const codeBlockRegex = /```[\s\S]*?\n([\s\S]*?)```/g;
  let match;
  while ((match = codeBlockRegex.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(match[1].trim());
      const result = tryParseAsPipeline(parsed);
      if (result) return result;
    } catch {}
  }
  return null;
}

// 边类型定义
interface PipelineEdge {
  id: string;
  source: string;
  target: string;
}

// 从nodes生成边
function generateEdges(nodes: PipelineNode[]): PipelineEdge[] {
  const edges: PipelineEdge[] = [];
  for (let i = 0; i < nodes.length - 1; i++) {
    edges.push({
      id: `e${i}-${i + 1}`,
      source: nodes[i].node_name,
      target: nodes[i + 1].node_name,
    });
  }
  return edges;
}

interface PipelinePreviewProps {
  data: PipelineData;
  threadId: string;
  onOpenCanvas?: (data: PipelineData, messageId?: string) => void;
}

export default function PipelinePreview({ data, threadId, onOpenCanvas, messageId }: PipelinePreviewProps) {
  const navigate = useNavigate();
  const { task, nodes } = data;

  const edges = useMemo(() => generateEdges(nodes), [nodes]);

  const handleRun = () => {
    // 保存pipeline数据到sessionStorage
    sessionStorage.setItem("pendingPipeline", JSON.stringify(data));
    sessionStorage.setItem("pipelineThreadId", threadId);
    navigate("/dialogue");
  };

  const handleEdit = () => {
    // 调用回调打开画板，而不是跳转页面
    if (onOpenCanvas) {
      onOpenCanvas(data, messageId);
    } else {
      // 兼容：如果没有回调，使用原来的方式
      sessionStorage.setItem("pendingPipeline", JSON.stringify(data));
      navigate("/dialogue");
    }
  };

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      {/* 标题和状态 */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon icon="ri:flow-chart" className="text-blue-600" width={20} />
          <span className="font-medium text-slate-900">{task.name}</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Icon icon="ri:node" width={14} />
            {nodes.length} 节点
          </span>
          <span className="flex items-center gap-1">
            <Icon icon="ri:arrow-right-line" width={14} />
            {edges.length} 边
          </span>
          <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-600">
            <Icon icon="ri:check-line" width={12} />
            验证通过
          </span>
        </div>
      </div>

      {/* 简易流程图 */}
      <div className="mb-4 flex items-center gap-2 overflow-x-auto rounded-lg bg-slate-50 p-3">
        {nodes.map((node, index) => (
          <div key={index} className="flex items-center gap-2">
            <div className="flex flex-col items-center">
              <div className="flex h-10 w-32 items-center justify-center rounded-lg border border-slate-200 bg-white px-2 shadow-sm">
                <div className="truncate text-center text-sm font-medium text-slate-700">
                  {node.node_name}
                </div>
              </div>
              {node.skill_name && (
                <div className="mt-1 truncate text-xs text-slate-400">
                  {node.skill_name}
                </div>
              )}
            </div>
            {index < nodes.length - 1 && (
              <Icon icon="ri:arrow-right-s-line" className="text-slate-400 flex-shrink-0" width={20} />
            )}
          </div>
        ))}
      </div>

      {/* 按钮组 */}
      <div className="flex gap-2">
        <button
          onClick={handleRun}
          className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800"
        >
          <Icon icon="ri:play-fill" width={16} />
          一键运行
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
        >
          <Icon icon="ri:edit-line" width={16} />
          打开画板编辑
        </button>
      </div>
    </div>
  );
}
