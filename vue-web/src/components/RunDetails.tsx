import React, { useCallback, useState, useEffect, useRef, memo, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Database, Filter, Square, Download, ArrowLeft, Check, Play, X, ChevronUp, ChevronDown } from 'lucide-react';
import { getExecutionDetail, stopDAGTask, downloadWorkspaceUrl2, getDrawTaskContent } from '../lib/api';
import {
  ReactFlow,
  Background,
  Handle,
  Position,
  getBezierPath,
  getStraightPath,
  ReactFlowProvider,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeProps,
  type EdgeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import '../components/Draw.css';

interface StopInfo {
  stop_name: string;
  status: string;
  job_id: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  progress?: number;
  processed_records?: number;
  total_records?: number;
}

interface ExecutionDetail {
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
  stops: StopInfo[];
  final_output_paths: string[];
}

interface LogEntry {
  time: string;
  node: string;
  message: string;
}

type RunNodeData = Record<string, unknown> & {
  label: string;
  operatorName?: string;
  operatorType?: string;
  runStatus?: string;
  progress?: number;
};

const statusConfig: Record<string, { label: string; color: string; bgColor: string; borderColor: string }> = {
  SUCCESS: { label: '已完成', color: '#22c55e', bgColor: '#dcfce7', borderColor: '#22c55e' },
  RUNNING: { label: '执行中', color: '#1f2937', bgColor: '#ffffff', borderColor: '#1f2937' },
  FAILED: { label: '执行失败', color: '#ef4444', bgColor: '#fee2e2', borderColor: '#ef4444' },
  SUBMITTED: { label: '已提交', color: '#f59e0b', bgColor: '#fef3c7', borderColor: '#f59e0b' },
  PENDING: { label: '等待执行', color: '#9ca3af', bgColor: '#f9fafb', borderColor: '#d1d5db' },
};

const getStatusInfo = (status: string) => {
  return statusConfig[status] || { label: status, color: '#6b7280', bgColor: '#f3f4f6', borderColor: '#d1d5db' };
};

const calculateDuration = (startTime: string | null, endTime: string | null): string => {
  if (!startTime) return '-';
  const start = new Date(startTime).getTime();
  const end = endTime ? new Date(endTime).getTime() : Date.now();
  const duration = Math.floor((end - start) / 1000);
  if (duration < 60) return `${duration}s`;
  if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
  return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
};

type RunNodeType = Node<RunNodeData>;

const RunFlowNode: React.FC<NodeProps<RunNodeType>> = ({ id, data, selected }) => {
  const stopStatus = getStatusInfo(data.runStatus || 'PENDING');
  const isCompleted = data.runStatus === 'SUCCESS';
  const isRunningStop = data.runStatus === 'RUNNING';
  const isFailed = data.runStatus === 'FAILED';
  const isPending = !data.runStatus || data.runStatus === 'PENDING' || data.runStatus === 'SUBMITTED';

  return (
    <div
      className={`custom-node ${selected ? 'selected' : ''} ${isCompleted ? 'completed-node' : ''} ${isRunningStop ? 'running-node' : ''}`}
      style={{
        border: `2px solid ${stopStatus.borderColor}`,
        boxShadow: isCompleted ? `0 4px 16px ${stopStatus.color}25` : isRunningStop ? '0 4px 16px rgba(0,0,0,0.1)' : '0 4px 16px rgba(0,0,0,0.06)',
        position: 'relative',
        width: '160px',
        minWidth: '160px',
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        padding: '8px 12px',
        boxSizing: 'border-box',
        animation: isCompleted ? 'nodeBorderPulse 2s ease-in-out infinite' : undefined,
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="node-handle"
        style={{ top: '50%' }}
      />

      <div className="node-header" style={{ paddingBottom: '4px' }}>
        <div className="node-header-left">
          <div className="node-title-wrapper">
            {data.operatorType && (
              <span className="node-operator-type" style={{ fontSize: '9px' }}>{data.operatorType.toUpperCase()}</span>
            )}
            <span className="node-title-text" style={{ fontSize: '12px' }}>{data.label}</span>
            {data.operatorName && (
              <span className="node-operator-info" style={{ fontSize: '10px' }}>{data.operatorName}</span>
            )}
          </div>
        </div>
      </div>

      <div style={{
        padding: '4px 0 0',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'flex-start',
      }}>
        {data.progress != null && (
          <span style={{
            fontSize: '11px', fontWeight: 500,
            color: isCompleted ? '#22c55e' : isRunningStop ? '#1f2937' : isFailed ? '#ef4444' : '#9ca3af'
          }}>
            {isCompleted ? `已完成 ${data.progress}%` :
             isRunningStop ? `执行中 ${data.progress}%` :
             isFailed ? '执行失败' : '等待执行'}
          </span>
        )}
      </div>

      <div style={{
        position: 'absolute', top: '-8px', right: '-8px',
        width: '20px', height: '20px',
        borderRadius: '50%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        backgroundColor: isPending ? '#9CA3AF' : '#10B981',
        border: '2px solid #ffffff',
        boxShadow: isPending ? '0 2px 8px rgba(156, 163, 175, 0.4)' : '0 2px 8px rgba(16, 185, 129, 0.4)',
        animation: isCompleted ? 'statusGlow 1.5s ease-in-out infinite' : undefined,
      }}>
        {isCompleted && <Check size={11} style={{ color: '#ffffff' }} />}
        {isRunningStop && <Play size={11} style={{ color: '#ffffff' }} />}
        {isFailed && <X size={11} style={{ color: '#ffffff' }} />}
        {isPending && <div style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#ffffff' }} />}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="node-handle"
        style={{ top: '50%' }}
      />
    </div>
  );
};

const MemoizedRunFlowNode = memo(RunFlowNode);

type RunEdgeData = Record<string, unknown> & {
  sourceStatus?: string;
  targetStatus?: string;
};

const RunCustomEdge: React.FC<EdgeProps<Edge<RunEdgeData>>> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
}) => {
  const [edgePath] = useMemo(() => {
    return getStraightPath({
      sourceX,
      sourceY,
      targetX,
      targetY,
    });
  }, [sourceX, sourceY, targetX, targetY]);

  const sourceStatus = data?.sourceStatus as string;
  const targetStatus = data?.targetStatus as string;
  
  const isCompleted = sourceStatus === 'SUCCESS' && targetStatus === 'SUCCESS';
  const isRunning = sourceStatus === 'RUNNING' || targetStatus === 'RUNNING';
  const isFailed = sourceStatus === 'FAILED' || targetStatus === 'FAILED';

  const edgeColor = isCompleted ? '#22c55e' : isFailed ? '#ef4444' : isRunning ? '#1f2937' : '#94A3B8';

  return (
    <g>
      {/* 主连接线 - 浅色背景 */}
      <path
        d={edgePath}
        stroke={isCompleted ? '#d1fae5' : isFailed ? '#fee2e2' : '#e2e8f0'}
        strokeWidth="4"
        fill="none"
        strokeLinecap="round"
        strokeDasharray="6,4"
      />
      
      {/* 带箭头的线 */}
      <defs>
        <marker
          id={`arrowhead-${id}`}
          markerWidth="12"
          markerHeight="12"
          refX="9"
          refY="6"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <polygon
            points="0 0, 12 6, 0 12"
            fill={edgeColor}
            stroke={edgeColor}
            strokeWidth={1}
          >
            {(isCompleted || isRunning) && (
              <animate
                attributeName="opacity"
                values="0.7;1;0.7"
                dur="0.8s"
                repeatCount="indefinite"
              />
            )}
          </polygon>
        </marker>
        <marker
          id={`arrowhead-pulse-${id}`}
          markerWidth="16"
          markerHeight="16"
          refX="12"
          refY="8"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <polygon
            points="0 0, 16 8, 0 16"
            fill={edgeColor}
            opacity="0.4"
          >
            {(isCompleted || isRunning) && (
              <animate
                attributeName="opacity"
                values="0;0.6;0"
                dur="1s"
                repeatCount="indefinite"
              />
            )}
          </polygon>
        </marker>
        <filter id={`glow-${id}`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      
      {/* 主箭头线 */}
      <path
        d={edgePath}
        stroke={edgeColor}
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeDasharray="6,4"
        markerEnd={`url(#arrowhead-${id})`}
        style={{
          filter: isCompleted ? `url(#glow-${id})` : undefined,
        }}
      />

      {/* 箭头脉冲效果 */}
      {(isCompleted || isRunning) && (
        <path
          d={edgePath}
          stroke="transparent"
          strokeWidth={2}
          fill="none"
          markerEnd={`url(#arrowhead-pulse-${id})`}
        />
      )}

      {/* 流动动画效果 - 小横线流动（跟随路径方向旋转） */}
      {(isCompleted || isRunning) && (
        <g>
          <g>
            <line x1="-10" y1="0" x2="10" y2="0" stroke={edgeColor} strokeWidth="2" strokeLinecap="round" filter={`url(#glow-${id})`}>
              <animateMotion
                dur="1.5s"
                repeatCount="indefinite"
                path={edgePath}
                rotate="auto"
              />
              <animate
                attributeName="opacity"
                values="1;0.3;1"
                dur="1.5s"
                repeatCount="indefinite"
              />
              <animate
                attributeName="stroke-width"
                values="2;3;2"
                dur="1.5s"
                repeatCount="indefinite"
              />
            </line>
          </g>
          <g>
            <line x1="-10" y1="0" x2="10" y2="0" stroke={edgeColor} strokeWidth="2" strokeLinecap="round" opacity="0.8">
              <animateMotion
                dur="1.5s"
                repeatCount="indefinite"
                path={edgePath}
                rotate="auto"
                begin="0.3s"
              />
              <animate
                attributeName="opacity"
                values="0.8;0.2;0.8"
                dur="1.5s"
                repeatCount="indefinite"
                begin="0.3s"
              />
            </line>
          </g>
          <g>
            <line x1="-10" y1="0" x2="10" y2="0" stroke={edgeColor} strokeWidth="2" strokeLinecap="round" opacity="0.6">
              <animateMotion
                dur="1.5s"
                repeatCount="indefinite"
                path={edgePath}
                rotate="auto"
                begin="0.6s"
              />
              <animate
                attributeName="opacity"
                values="0.6;0.1;0.6"
                dur="1.5s"
                repeatCount="indefinite"
                begin="0.6s"
              />
            </line>
          </g>
          <g>
            <line x1="-10" y1="0" x2="10" y2="0" stroke={edgeColor} strokeWidth="2" strokeLinecap="round" opacity="0.4">
              <animateMotion
                dur="1.5s"
                repeatCount="indefinite"
                path={edgePath}
                rotate="auto"
                begin="0.9s"
              />
              <animate
                attributeName="opacity"
                values="0.4;0;0.4"
                dur="1.5s"
                repeatCount="indefinite"
                begin="0.9s"
              />
            </line>
          </g>
        </g>
      )}
    </g>
  );
};

const MemoizedRunCustomEdge = memo(RunCustomEdge);

const runNodeTypes = {
  custom: MemoizedRunFlowNode,
};

const runEdgeTypes = {
  'run-edge': MemoizedRunCustomEdge,
};

const RunDetails: React.FC<{ processId: string }> = ({ processId }) => {
  const navigate = useNavigate();
  const [executionData, setExecutionData] = useState<ExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [flowNodes, setFlowNodes] = useState<RunNodeType[]>([]);
  const [flowEdges, setFlowEdges] = useState<Edge[]>([]);
  const [dslLoading, setDslLoading] = useState(false);

  const handleBack = () => navigate('/run-history');
  const loadingRef = useRef(false);

  const loadDSL = useCallback(async (dagTaskId: string, stops: StopInfo[]) => {
    setDslLoading(true);
    try {
      const res: any = await getDrawTaskContent(dagTaskId);
      console.log('DSL数据:', res);
      if (res.code === 200 && res.result) {
        const dsl = res.result;

        const stopStatusMap: Record<string, string> = {};
        const stopProgressMap: Record<string, number> = {};
        stops.forEach((s) => {
          stopStatusMap[s.stop_name] = s.status;
          stopProgressMap[s.stop_name] = s.progress || (s.status === 'SUCCESS' ? 100 : 0);
        });

        const nodesList: any[] = dsl.nodes || [];

        // === 处理 edges/bindings 并建立 ID 映射 ===
        // edges 中可能用 "node-1" 格式的 ID，需要映射到 nodes 中实际的 node_id（UUID）
        const rawEdges: any[] = (dsl.edges && dsl.edges.length > 0) ? dsl.edges : (dsl.bindings || []);

        // 建立 "node-X"（或直接数字索引）到实际 node_id 的映射
        // nodes[i] 的索引 i(0-based) 对应 "node-(i+1)"
        const indexedIdToNodeId: Record<string, string> = {};
        const idToNode: Record<string, any> = {};
        nodesList.forEach((n: any, idx: number) => {
          idToNode[n.node_id] = n;
          indexedIdToNodeId[`node-${idx + 1}`] = n.node_id;
          indexedIdToNodeId[`node_${idx + 1}`] = n.node_id;
          indexedIdToNodeId[`${idx + 1}`] = n.node_id;
          // 如果节点的 node_id 本身就是 "node-X" 格式，直接映射
          indexedIdToNodeId[n.node_id] = n.node_id;
        });

        // 将 edges 中的 from_node_id/to_node_id 转换为实际的 node_id
        const resolvedEdges: { from: string; to: string; label?: string }[] = rawEdges.map((e: any) => ({
          from: indexedIdToNodeId[e.from_node_id] || e.from_node_id,
          to: indexedIdToNodeId[e.to_node_id] || e.to_node_id,
          label: e.edge_id || e.from_node_id + '-' + e.to_node_id,
        }));

        // === 基于 resolved edges 做拓扑排序 ===
        const inDegree: Record<string, number> = {};
        const outgoing: Record<string, string[]> = {};
        nodesList.forEach((n: any) => {
          inDegree[n.node_id] = 0;
          outgoing[n.node_id] = [];
        });
        resolvedEdges.forEach((e) => {
          if (inDegree[e.to] !== undefined) inDegree[e.to]++;
          if (outgoing[e.from] !== undefined) outgoing[e.from].push(e.to);
        });

        // BFS 拓扑排序
        const orderedIds: string[] = [];
        const queue: string[] = [];
        Object.keys(inDegree).forEach((id) => { if (inDegree[id] === 0) queue.push(id); });
        const inDegCopy: Record<string, number> = { ...inDegree };
        while (queue.length > 0) {
          const id = queue.shift() as string;
          orderedIds.push(id);
          (outgoing[id] || []).forEach((nextId) => {
            inDegCopy[nextId]--;
            if (inDegCopy[nextId] === 0) queue.push(nextId);
          });
        }
        // 若存在环或孤立节点，用数组顺序兜底
        if (orderedIds.length !== nodesList.length) {
          nodesList.forEach((n: any) => {
            if (!orderedIds.includes(n.node_id)) orderedIds.push(n.node_id);
          });
        }

        // === 计算布局：按拓扑序横向排列；有分叉时纵向错开 ===
        const nodePositionMap: Record<string, { x: number; y: number }> = {};
        // 按拓扑序给每个节点分配 column（层级）
        const nodeLevel: Record<string, number> = {};
        orderedIds.forEach((id, idx) => {
          // 初始化为拓扑索引（简单但对分叉不够好）
          nodeLevel[id] = idx;
        });
        // 用 edges 重新计算更准确的层级：每个节点的层级 = 上游节点最大层级 + 1
        const nodeLevel2: Record<string, number> = {};
        orderedIds.forEach((id) => {
          // 找到所有指向当前节点的上游节点
          const upstreamNodes = resolvedEdges.filter(e => e.to === id).map(e => e.from);
          if (upstreamNodes.length === 0) {
            nodeLevel2[id] = 0;
          } else {
            nodeLevel2[id] = Math.max(...upstreamNodes.map(u => nodeLevel2[u] !== undefined ? nodeLevel2[u] : 0)) + 1;
          }
        });

        // 按层级分组，同一层级的节点纵向排列
        const levelToNodes: Record<number, string[]> = {};
        Object.keys(nodeLevel2).forEach((id) => {
          const lvl = nodeLevel2[id];
          if (!levelToNodes[lvl]) levelToNodes[lvl] = [];
          levelToNodes[lvl].push(id);
        });

        const LEVEL_GAP = 320; // 横向间距
        const ROW_GAP = 180;  // 纵向间距
        const START_X = 100;
        const START_Y = 180;

        Object.keys(levelToNodes).map(k => parseInt(k)).sort((a, b) => a - b).forEach((level) => {
          const nodesAtLevel = levelToNodes[level];
          const count = nodesAtLevel.length;
          nodesAtLevel.forEach((nodeId, rowIdx) => {
            nodePositionMap[nodeId] = {
              x: START_X + level * LEVEL_GAP,
              y: START_Y + rowIdx * ROW_GAP,
            };
          });
        });

        // === 构建 ReactFlow 节点和边 ===
        const loadedNodes: RunNodeType[] = [];
        orderedIds.forEach((nodeId) => {
          const n = idToNode[nodeId];
          const nodeName = n.node_name || '';
          const runStatus = stopStatusMap[nodeName] || 'PENDING';
          const progress = stopProgressMap[nodeName] || 0;
          const pos = nodePositionMap[nodeId] || { x: START_X, y: START_Y };

          loadedNodes.push({
            id: nodeId,
            type: 'custom' as const,
            position: pos,
            data: {
              label: nodeName,
              operatorName: n.skill?.skill_name || '',
              operatorType: n.skill?.skill_type || '',
              runStatus,
              progress,
            },
          });
        });

        const loadedEdges: Edge<RunEdgeData>[] = [];
        resolvedEdges.forEach((e, idx) => {
          const sourceNode = idToNode[e.from];
          const targetNode = idToNode[e.to];
          const sourceNodeName = sourceNode?.node_name || '';
          const targetNodeName = targetNode?.node_name || '';
          
          loadedEdges.push({
            id: `edge-${idx}`,
            source: e.from,
            target: e.to,
            type: 'run-edge',
            data: {
              sourceStatus: stopStatusMap[sourceNodeName],
              targetStatus: stopStatusMap[targetNodeName],
            },
          });
        });

        setFlowNodes(loadedNodes);
        setFlowEdges(loadedEdges);
      }
    } catch (error) {
      console.error('加载DSL数据失败:', error);
    } finally {
      setDslLoading(false);
    }
  }, []);

  const loadExecutionDetail = useCallback(async () => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    try {
      const response = await getExecutionDetail(processId);
      if (response.code === 200 && response.result) {
        setExecutionData(response.result);
        const newLogs: LogEntry[] = response.result.stops.map((stop: StopInfo) => {
          const startTime = stop.started_at ? new Date(stop.started_at) : null;
          const timeStr = startTime ? startTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
          if (stop.status === 'SUCCESS') {
            return { time: timeStr, node: stop.stop_name, message: `Done: ${stop.processed_records || stop.total_records || 'N/A'} recs` };
          } else if (stop.status === 'RUNNING') {
            return { time: timeStr, node: stop.stop_name, message: `Progress updated: ${stop.processed_records || 0} recs.` };
          } else if (stop.status === 'FAILED') {
            return { time: timeStr, node: stop.stop_name, message: `Error: ${stop.error_message || 'Unknown error'}` };
          }
          return null;
        }).filter((log): log is LogEntry => log !== null);
        setLogs(newLogs);

        if (response.result.dag_task_id) {
          loadDSL(response.result.dag_task_id, response.result.stops);
        }

        if (response.result.status === 'RUNNING' || response.result.status === 'SUBMITTED') {
          pollingRef.current = setTimeout(() => {
            loadingRef.current = false;
            loadExecutionDetail();
          }, 5000);
          return;
        }
      }
    } catch (error) {
      console.error('加载执行详情失败:', error);
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, [processId, loadDSL]);

  useEffect(() => {
    loadExecutionDetail();
    return () => {
      if (pollingRef.current) clearTimeout(pollingRef.current);
      loadingRef.current = false;
    };
  }, [loadExecutionDetail]);

  useEffect(() => {
    if (logContainerRef.current) logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
  }, [logs]);

  const handleStopExecution = async () => {
    if (!window.confirm('确定要停止执行吗？')) return;
    try {
      await stopDAGTask(processId);
      alert('已停止执行');
      loadExecutionDetail();
    } catch (error) {
      console.error('停止执行失败:', error);
      alert('停止执行失败');
    }
  };

  if (loading) {
    return (
      <div style={{ height: '100vh', background: '#f5f7fa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px', height: '40px',
            border: '3px solid #f3f3f3',
            borderTop: '3px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }} />
          <span style={{ color: '#64748b', fontSize: '14px' }}>加载中...</span>
        </div>
      </div>
    );
  }

  if (!executionData) {
    return (
      <div style={{ height: '100vh', background: '#f5f7fa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#64748b', fontSize: '14px' }}>无法获取执行详情</span>
      </div>
    );
  }

  const statusInfo = getStatusInfo(executionData.status);
  const isRunning = executionData.status === 'RUNNING';

  return (
    <ReactFlowProvider>
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: '20px', boxSizing: 'border-box' }}>
        <style>{`
          @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
          @keyframes rdLineFlow {
            0% { stroke-dashoffset: 36; }
            100% { stroke-dashoffset: 0; }
          }
          @keyframes rdShadowExpand {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
            100% { box-shadow: 0 0 0 18px rgba(16, 185, 129, 0); }
          }
          @keyframes nodeBorderPulse {
            0%, 100% { 
              box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4), 0 4px 16px rgba(34, 197, 94, 0.25);
            }
            50% { 
              box-shadow: 0 0 0 8px rgba(34, 197, 94, 0), 0 4px 24px rgba(34, 197, 94, 0.35);
            }
          }
          @keyframes statusGlow {
            0%, 100% { 
              box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5);
            }
            50% { 
              box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
            }
          }
          @keyframes arrowPulse {
            0%, 100% { 
              opacity: 0.7;
              transform: scale(0.9);
            }
            50% { 
              opacity: 1;
              transform: scale(1.1);
            }
          }
          @keyframes flowDot {
            0% { 
              offset-distance: 0%;
              opacity: 1;
            }
            100% { 
              offset-distance: 100%;
              opacity: 0;
            }
          }
        `}</style>

        <div style={{ height: '64px', background: '#ffffff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>RUN_{processId}</span>
              <span style={{
                fontSize: '13px', fontWeight: 600, padding: '4px 14px', borderRadius: '20px',
                backgroundColor: statusInfo.bgColor, color: statusInfo.color,
                boxShadow: `0 2px 8px ${statusInfo.color}20`
              }}>{statusInfo.label}</span>
            </div>
            <div style={{ display: 'flex', gap: '24px' }}>
              <span style={{ fontSize: '12px', color: '#64748b' }}>所属流水线: {executionData.flow_name || '-'}</span>
              <span style={{ fontSize: '12px', color: '#64748b' }}>开始时间: {executionData.started_at ? new Date(executionData.started_at).toLocaleString('zh-CN') : '-'}</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button onClick={handleBack} style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '8px 16px', border: 'none', borderRadius: '10px',
              fontSize: '13px', fontWeight: 500, cursor: 'pointer',
              background: '#f8fafc', color: '#475569',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 4px rgba(0,0,0,0.04)'
            }}>
              <ArrowLeft size={14} />
              <span>返回历史进程列表</span>
            </button>
            {isRunning && (
              <button onClick={handleStopExecution} style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '8px 16px', border: 'none', borderRadius: '10px',
                fontSize: '13px', fontWeight: 500, cursor: 'pointer',
                background: '#fef2f2', color: '#dc2626',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(220, 38, 38, 0.15)'
              }}>
                <Square size={14} fill="currentColor" />
                <span>停止执行</span>
              </button>
            )}
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', gap: '20px', overflow: 'hidden' }}>
          <div style={{ flex: 1, background: '#f5f7fa', borderRadius: '16px', boxShadow: '0 8px 32px rgba(0,0,0,0.06)', position: 'relative', overflow: 'hidden' }}>
            {dslLoading ? (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: '#64748b', fontSize: '14px' }}>加载画板数据...</span>
              </div>
            ) : flowNodes.length > 0 ? (
              <ReactFlow
                nodes={flowNodes}
                edges={flowEdges}
                nodeTypes={runNodeTypes}
                edgeTypes={runEdgeTypes}
                fitView
                nodesDraggable={false}
                nodesConnectable={false}
                elementsSelectable={false}
                panOnDrag={true}
                zoomOnScroll={true}
                proOptions={{ hideAttribution: true }}
              >
                <Background variant={BackgroundVariant.Dots} gap={36} size={1.5} />
              </ReactFlow>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: '#64748b', fontSize: '14px' }}>暂无画板数据</span>
              </div>
            )}
          </div>

          <div style={{
            width: '440px', background: '#0f172a', borderRadius: '16px',
            display: 'flex', flexDirection: 'column', overflow: 'hidden',
            flexShrink: 0,
            boxShadow: '0 8px 32px rgba(0,0,0,0.15)'
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '20px 24px', background: '#1e293b', borderBottom: '1px solid #334155'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#22c55e', boxShadow: '0 0 8px #22c55e' }} />
                <span style={{ fontSize: '15px', fontWeight: 600, color: '#f1f5f9' }}>运行日志</span>
              </div>
              {isRunning && <span style={{ fontSize: '12px', color: '#22c55e', fontWeight: 500 }}>实时同步中...</span>}
            </div>
            <div ref={logContainerRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
              {logs.length > 0 ? (
                logs.map((log, index) => (
                  <div key={index} style={{
                    display: 'flex', flexWrap: 'wrap', gap: '10px',
                    padding: '12px 16px', marginBottom: '8px',
                    background: '#1e293b', borderRadius: '8px',
                    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace", fontSize: '12px', lineHeight: 1.6
                  }}>
                    <span style={{ color: '#94a3b8', fontWeight: 500 }}>[{log.time}]</span>
                    <span style={{ color: '#38bdf8', fontWeight: 500 }}>[{log.node}]</span>
                    <span style={{ color: '#e2e8f0', wordBreak: 'break-word' }}>{log.message}</span>
                  </div>
                ))
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>
                  <span>暂无日志信息</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={{
          padding: '16px 20px', background: '#ffffff', borderTop: '1px solid #e2e8f0',
          display: 'flex', flexDirection: 'column', gap: '16px',
          marginTop: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '32px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>节点总数</span>
              <span style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>{executionData.total_stop_count}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>成功</span>
              <span style={{ fontSize: '20px', fontWeight: 700, color: '#16a34a' }}>{executionData.success_stop_count}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>失败</span>
              <span style={{ fontSize: '20px', fontWeight: 700, color: '#dc2626' }}>{executionData.failed_stop_count}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>跳过</span>
              <span style={{ fontSize: '20px', fontWeight: 700, color: '#f59e0b' }}>{executionData.skipped_stop_count}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', paddingLeft: '24px', borderLeft: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>执行时长</span>
              <span style={{ fontSize: '18px', fontWeight: 600, color: '#334155' }}>{calculateDuration(executionData.started_at, executionData.finished_at)}</span>
            </div>
          </div>

          {executionData.final_output_paths && executionData.final_output_paths.length > 0 && (
            <div style={{
              padding: '16px', background: '#f8fafc',
              borderRadius: '10px', border: '1px solid #e2e8f0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <Download size={16} style={{ color: '#2563eb' }} />
                <span style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>结果文件</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {executionData.final_output_paths.map((file: string, index: number) => (
                  <a key={index} href={downloadWorkspaceUrl2(file)} target="_blank" rel="noopener noreferrer" style={{
                    display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px',
                    background: '#ffffff', color: '#2563eb', textDecoration: 'none',
                    borderRadius: '8px', fontSize: '13px', fontWeight: 500,
                    border: '1px solid #dbeafe',
                    boxShadow: '0 2px 8px rgba(37, 99, 235, 0.08)',
                    transition: 'all 0.2s ease'
                  }}>
                    <Download size={14} />
                    <span>{file.split('/').pop() || file}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </ReactFlowProvider>
  );
};

export default RunDetails;
