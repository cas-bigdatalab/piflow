import React, { useCallback, useState, useRef, memo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  getBezierPath,
  useReactFlow,
  ReactFlowProvider,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
  type EdgeProps,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Play,
  X,
  Upload,
  Eraser,
  Type,
  Calendar,
  Circle,
  Database,
  Square,
  MessageSquare,
  Filter,
  Shuffle,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import './RunDetails.css';

// 字段类型定义

type NodeStatus = 'completed' | 'running' | 'pending';
type EdgeStatus = 'completed' | 'running' | 'pending';

interface NodeData {
  label: string;
  icon: string;
  operatorId: string;
  description?: string;
  status?: NodeStatus;
  progress?: number;
  progressText?: string;
  onDelete?: (id: string) => void;
}

interface CustomEdgeData {
  onDelete?: (id: string) => void;
  status?: EdgeStatus;
}

// 映射的图标

const iconComponents: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  Upload,
  Eraser,
  Type,
  Square,
  Calendar,
  Database,
  MessageSquare,
  Filter,
  Shuffle,
  Download,
  Circle,
};

const getIcon = (iconName: string) => {
  return iconComponents[iconName] || Circle;
};

// ==================== 自定义节点组件 ====================

const CustomNode: React.FC<NodeProps<NodeData>> = ({ id, data, selected }) => {
  const Icon = getIcon(data.icon);
  const status = data.status || 'pending';

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={18} className="node-status-icon status-completed" />;
      case 'running':
        return <Loader2 size={18} className="node-status-icon status-running" />;
      default:
        return <Circle size={18} className="node-status-icon status-pending" />;
    }
  };

  return (
    <div className={`custom-node node-${status} ${selected ? 'selected' : ''}`}>
      <Handle
        type="target"
        position={Position.Left}
        className={`node-handle handle-${status}`}
        style={{ top: '50%' }}
      />

      {/* 节点头部 */}
      <div className="node-header">
        <div className="node-header-left">
          <div className={`node-icon-wrapper icon-${status}`}>
            <Icon size={18} className="node-icon" />
          </div>
          <span className="node-title">{data.label}</span>
        </div>
        <div className="node-header-right">
          {getStatusIcon()}
        </div>
      </div>

      {/* 状态信息 */}
      <div className="node-status-area">
        {status === 'completed' && (
          <div className="status-line completed">
            <span className="status-text">{data.progressText || 'Done'}</span>
            <span className="status-percent">100%</span>
          </div>
        )}
        {status === 'running' && (
          <div className="status-line running">
            <span className="status-text">{data.progressText || 'Processing...'}</span>
            <span className="status-percent">{data.progress || 0}%</span>
          </div>
        )}
        {status === 'pending' && (
          <div className="status-line pending">
            <span className="status-text">等待执行</span>
          </div>
        )}
      </div>

      {/* 进度条 */}
      {(status === 'completed' || status === 'running') && (
        <div className="node-progress-bar">
          <div
            className={`progress-fill progress-${status}`}
            style={{ width: `${status === 'completed' ? 100 : (data.progress || 0)}%` }}
          />
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className={`node-handle handle-${status}`}
        style={{ top: '50%' }}
      />
    </div>
  );
};

const MemoizedCustomNode = memo(CustomNode);

// ==================== 自定义连线组件（带删除按钮）====================

type CustomEdgeType = Edge<CustomEdgeData>;

const CustomEdge: React.FC<EdgeProps<CustomEdgeType>> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const status = data?.status || 'pending';

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    data?.onDelete?.(id);
  };

  const getStrokeColor = () => {
    if (isHovered) return '#1890ff';
    switch (status) {
      case 'completed': return '#52c41a';
      case 'running': return '#1890ff';
      default: return '#b8b8b8';
    }
  };

  const getArrowColor = () => {
    if (isHovered) return '#1890ff';
    switch (status) {
      case 'completed': return '#52c41a';
      case 'running': return '#1890ff';
      default: return '#b8b8b8';
    }
  };

  return (
    <g
      className={`custom-edge edge-${status}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 曲线 */}
      <path
        d={edgePath}
        stroke={getStrokeColor()}
        strokeWidth={2}
        fill="none"
        strokeDasharray={status === 'pending' ? '6 4' : 'none'}
        style={{ transition: 'stroke 0.2s' }}
      />

      {/* 箭头 */}
      <defs>
        <marker
          id={`arrowhead-${id}`}
          markerWidth="8"
          markerHeight="8"
          refX="7"
          refY="4"
          orient="auto"
        >
          <polygon
            points="0 0, 8 4, 0 8"
            fill={getArrowColor()}
            style={{ transition: 'fill 0.2s' }}
          />
        </marker>
      </defs>
      <path
        d={edgePath}
        stroke="transparent"
        strokeWidth={2}
        fill="none"
        markerEnd={`url(#arrowhead-${id})`}
      />

      {/* 执行中动画 */}
      {status === 'running' && (
        <circle r="3" fill="#1890ff">
          <animateMotion dur="2s" repeatCount="indefinite" path={edgePath} />
        </circle>
      )}

      {isHovered && (
        <foreignObject
          x={labelX - 12}
          y={labelY - 12}
          width={24}
          height={24}
          className="edge-delete-container"
        >
          <button className="edge-delete-btn" onClick={handleDelete} title="删除连线">
            <X size={12} />
          </button>
        </foreignObject>
      )}
    </g>
  );
};

// ==================== 主画布组件 ====================

const nodeTypes = {
  custom: MemoizedCustomNode,
};

const edgeTypes = {
  custom: CustomEdge,
};

// 节点间距配置
const NODE_WIDTH = 240;
const NODE_GAP = 60;
const START_X = 50;
const START_Y = 200;

// 默认节点数据 - 水平排列
const defaultNodes: Node<NodeData>[] = [
  {
    id: 'node-1',
    type: 'custom',
    position: { x: START_X, y: START_Y },
    data: {
      label: '文件上传',
      icon: 'Upload',
      operatorId: 'file-upload',
      description: 'CSV文件',
      status: 'completed',
      progress: 100,
      progressText: 'Done: 1,204 recs',
    },
  },
  {
    id: 'node-2',
    type: 'custom',
    position: { x: START_X + (NODE_WIDTH + NODE_GAP), y: START_Y },
    data: {
      label: '空行清洗',
      icon: 'Eraser',
      operatorId: 'empty-clean',
      description: '去除空行',
      status: 'running',
      progress: 42,
      progressText: 'Proc: 506 recs',
    },
  },
  {
    id: 'node-3',
    type: 'custom',
    position: { x: START_X + (NODE_WIDTH + NODE_GAP) * 2, y: START_Y },
    data: {
      label: '空格清洗',
      icon: 'Type',
      operatorId: 'space-clean',
      description: '去除多余空格',
      status: 'pending',
    },
  },
  {
    id: 'node-4',
    type: 'custom',
    position: { x: START_X + (NODE_WIDTH + NODE_GAP) * 3, y: START_Y },
    data: {
      label: '年份排序',
      icon: 'Calendar',
      operatorId: 'year-sort',
      description: '按年份升序',
      status: 'pending',
    },
  },
];

const defaultEdges: Edge[] = [
  { id: 'edge-1', source: 'node-1', target: 'node-2', type: 'custom', data: { status: 'completed' } },
  { id: 'edge-2', source: 'node-2', target: 'node-3', type: 'custom', data: { status: 'running' } },
  { id: 'edge-3', source: 'node-3', target: 'node-4', type: 'custom', data: { status: 'pending' } },
];

// ==================== 右侧日志面板组件 ====================

interface LogEntry {
  time: string;
  node: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
}

const mockLogs: LogEntry[] = [
  { time: '10:20:15', node: '文件上传', message: 'Initializing...', type: 'info' },
  { time: '10:20:16', node: '文件上传', message: 'Reading file from disk...', type: 'info' },
  { time: '10:20:17', node: '文件上传', message: 'Done: 1,204 records loaded.', type: 'success' },
  { time: '10:20:18', node: '空行清洗', message: 'Processing records...', type: 'info' },
  { time: '10:21:02', node: '空行清洗', message: 'Slow throughput detected...', type: 'warning' },
  { time: '10:22:15', node: '空行清洗', message: 'Progress updated: 506 recs.', type: 'info' },
];

const LogPanel: React.FC = () => {
  const [logs] = useState<LogEntry[]>(mockLogs);
  const logListRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logListRef.current) {
      logListRef.current.scrollTop = logListRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogIcon = (type: LogEntry['type']) => {
    switch (type) {
      case 'success':
        return <span className="log-icon success">✓</span>;
      case 'warning':
        return <span className="log-icon warning">⚠</span>;
      case 'error':
        return <span className="log-icon error">✗</span>;
      default:
        return <span className="log-icon info">●</span>;
    }
  };

  return (
    <div className="log-panel">
      <div className="log-header">
        <span>运行日志</span>
        <span className="log-status">实时同步中...</span>
      </div>
      <div className="log-list" ref={logListRef}>
        {logs.map((log, index) => (
          <div key={index} className={`log-entry ${log.type}`}>
            <span className="log-time">[{log.time}]</span>
            <span className="log-node">[{log.node}]</span>
            <span className="log-message">{log.message}</span>
            {getLogIcon(log.type)}
          </div>
        ))}
      </div>
    </div>
  );
};

// ==================== 底部工具栏组件 ====================

interface FloatingToolbarProps {
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
}

const FloatingToolbar: React.FC<FloatingToolbarProps> = ({
  zoom,
  onZoomIn,
  onZoomOut,
  onResetView,
}) => {
  return (
    <div className="floating-toolbar">
      <button className="toolbar-btn" onClick={onZoomIn} title="放大">
        <ZoomIn size={20} />
      </button>
      <button className="toolbar-btn" onClick={onZoomOut} title="缩小">
        <ZoomOut size={20} />
      </button>
      <span className="zoom-level">{Math.round(zoom * 100)}%</span>
      <button className="toolbar-btn" onClick={onResetView} title="重置视图">
        <RotateCcw size={20} />
      </button>
    </div>
  );
};

// ==================== 主画布组件 ====================

const FlowEditorInner: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const isInitialized = useRef(false);
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  // 初始化默认节点
  useEffect(() => {
    if (!isInitialized.current) {
      const nodesWithCallbacks = defaultNodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          onDelete: (id: string) => {
            setNodes((nds) => nds.filter((n) => n.id !== id));
            setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
          },
        },
      }));

      const edgesWithCallbacks = defaultEdges.map((edge) => ({
        ...edge,
        data: {
          ...edge.data,
          onDelete: (id: string) => {
            setEdges((eds) => eds.filter((e) => e.id !== id));
          },
        },
      }));

      setNodes(nodesWithCallbacks);
      setEdges(edgesWithCallbacks);
      isInitialized.current = true;
    }
  }, [setNodes, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) => {
      const edge = {
        ...connection,
        type: 'custom',
        data: {
          status: 'pending' as EdgeStatus,
          onDelete: (id: string) => {
            setEdges((eds) => eds.filter((e) => e.id !== id));
          },
        },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  return (
    <div className="flow-canvas-container">
      {/* Header */}
      <div className="flow-header">
        <div className="header-left">
          <h2>科研数据清洗与排序</h2>
          <span className="header-desc">对科研文献数据进行空行清洗、空格清洗、按年份升序排序</span>
        </div>
        <div className="header-right">
          <button className="stop-btn">
            <Square size={14} fill="currentColor" />
            <span>停止执行</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flow-content">
        <div className="reactflow-wrapper">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            attributionPosition="bottom-left"
          >
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>

          {/* Floating Toolbar */}
          <FloatingToolbar
            zoom={1}
            onZoomIn={zoomIn}
            onZoomOut={zoomOut}
            onResetView={fitView}
          />
        </div>

        {/* 右侧日志面板 */}
        <LogPanel />
      </div>
    </div>
  );
};

// 辅助函数
const getOperatorDescription = (id: string): string => {
  const descriptions: Record<string, string> = {
    'file-upload': 'CSV文件',
    'empty-clean': '去除空行',
    'space-clean': '去除多余空格',
    'year-sort': '按年份升序',
    'mysql-source': 'MySQL',
    'kafka-reader': 'Kafka',
    'data-filter': 'Filter',
    'data-transformer': 'Transform',
    'file-uploader': 'File Output',
  };
  return descriptions[id] || '';
};

const FlowEditor: React.FC = () => {
  return (
    <ReactFlowProvider>
      <FlowEditorInner />
    </ReactFlowProvider>
  );
};

export default FlowEditor;
