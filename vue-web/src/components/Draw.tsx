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
  BaseEdge,
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
  Trash2,
  X,
  Upload,
  Eraser,
  Type,
  Calendar,
  Circle,
  Database,
  MessageSquare,
  Filter,
  Shuffle,
  Download,
  Package,
  MessageSquarePlus,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Search,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import './Draw.css';

// ==================== TypeScript 类型定义 ====================

interface NodeData {
  label: string;
  icon: string;
  operatorId: string;
  description?: string;
  params?: Record<string, any>;
  inputVar?: string;
  outputVar?: string;
  onDelete?: (id: string) => void;
  onUpdateParams?: (id: string, params: Record<string, any>) => void;
}

interface CustomEdgeData {
  onDelete?: (id: string) => void;
}

// ==================== 图标映射 ====================

const iconComponents: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  Upload,
  Eraser,
  Type,
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

// ==================== 参数配置 ====================

const paramLabels: Record<string, Record<string, string>> = {
  'file-upload': {
    filePath: 'file_path',
    fileType: 'file_type',
    encoding: 'encoding',
  },
  'empty-clean': {
    cleanMode: 'mode',
  },
  'space-clean': {
    spaceMode: 'scope',
  },
  'year-sort': {
    sortField: 'sort_field',
    sortOrder: 'order',
  },
};

const paramDisplayValues: Record<string, Record<string, any>> = {
  'file-upload': {
    fileType: { csv: 'CSV', excel: 'Excel', json: 'JSON' },
    encoding: { utf8: 'UTF-8', gb2312: 'GB2312', gbk: 'GBK' },
  },
  'empty-clean': {
    cleanMode: { all: '去除全空行', spaces: '去除仅含空格的行' },
  },
  'space-clean': {
    spaceMode: { trim: '首尾空格', extra: '多余空格', all: '所有空格' },
  },
  'year-sort': {
    sortField: { year: 'publish_year', title: 'title', author: 'author' },
    sortOrder: { asc: '升序', desc: '降序' },
  },
};

// ==================== 算子分类配置 ====================

const operatorCategories = [
  {
    key: 'input',
    label: '输入算子',
    operators: [
      { id: 'mysql-source', name: 'MySQL Source', icon: 'Database', category: 'input' as const },
      { id: 'kafka-reader', name: 'Kafka Reader', icon: 'MessageSquare', category: 'input' as const },
      { id: 'file-upload', name: '文件上传', icon: 'Upload', category: 'input' as const },
    ],
  },
  {
    key: 'process',
    label: '处理算子',
    operators: [
      { id: 'data-filter', name: 'Data Filter', icon: 'Filter', category: 'process' as const },
      { id: 'data-transformer', name: 'Data Transformer', icon: 'Shuffle', category: 'process' as const },
      { id: 'empty-clean', name: '空行清洗', icon: 'Eraser', category: 'process' as const },
      { id: 'space-clean', name: '空格清洗', icon: 'Type', category: 'process' as const },
      { id: 'year-sort', name: '年份排序', icon: 'Calendar', category: 'process' as const },
    ],
  },
  {
    key: 'output',
    label: '输出算子',
    operators: [
      { id: 'file-uploader', name: 'File Uploader', icon: 'Download', category: 'output' as const },
    ],
  },
];

// ==================== 自定义节点组件 ====================

const CustomNode: React.FC<NodeProps<NodeData>> = ({ id, data, selected }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const Icon = getIcon(data.icon);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    data.onDelete?.(id);
  };

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  // 获取参数显示值
  const getDisplayValue = (paramKey: string, value: any): string => {
    const displayMap = paramDisplayValues[data.operatorId]?.[paramKey];
    if (displayMap && displayMap[value]) {
      return displayMap[value];
    }
    return String(value);
  };

  // 获取参数标签
  const getParamLabel = (paramKey: string): string => {
    return paramLabels[data.operatorId]?.[paramKey] || paramKey;
  };

  // 渲染参数项
  const renderParams = () => {
    if (!data.params) return null;
    
    return Object.entries(data.params).map(([key, value]) => (
      <div key={key} className="node-param-item">
        <span className="node-param-label">{getParamLabel(key)}:</span>
        <span className="node-param-value">{getDisplayValue(key, value)}</span>
      </div>
    ));
  };

  return (
    <div className={`custom-node ${selected ? 'selected' : ''}`}>
      <Handle 
        type="target" 
        position={Position.Left} 
        className="node-handle"
        style={{ top: '50%' }}
      />

      {/* 节点头部 */}
      <div className="node-header">
        <div className="node-header-left">
          <div className="node-icon-wrapper">
            <Icon size={18} className="node-icon" />
          </div>
          <span className="node-title">{data.label}</span>
        </div>
        <div className="node-header-right">
          <button className="node-delete-btn" onClick={handleDelete} title="删除节点">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* 展开/折叠按钮 */}
      <div className="node-expand-btn" onClick={toggleExpand}>
        <span>{isExpanded ? '收起参数' : '展开参数'}</span>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </div>

      {/* 参数内容 */}
      {isExpanded && (
        <div className="node-params-scroll-container">
          <div className="node-params-content">
            {/* 输入 */}
            <div className="node-section node-section-input">
              <div className="node-section-label">输入</div>
              <div className="node-param-item">
                <span className="node-param-value-var">{data.inputVar || 'data_stream'}</span>
              </div>
            </div>

            {/* 普通 */}
            <div className="node-section node-section-general">
              <div className="node-section-label">普通</div>
              {renderParams()}
            </div>

            {/* 输出 */}
            <div className="node-section node-section-output">
              <div className="node-section-label">输出</div>
              <div className="node-param-item">
                <span className="node-param-value-var">{data.outputVar || 'output_data'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 节点底部 */}
      <div className="node-footer">
        <span className="node-description">{data.description}</span>
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

const MemoizedCustomNode = memo(CustomNode);

// ==================== 注释节点组件 ====================

interface CommentNodeProps {
  id: string;
  data: {
    label: string;
    onChange?: (id: string, label: string) => void;
  };
}

const CommentNode: React.FC<NodeProps<{ label: string; onChange?: (id: string, label: string) => void }>> = ({ id, data }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState(data.label);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleDoubleClick = () => {
    setIsEditing(true);
  };

  const handleBlur = () => {
    setIsEditing(false);
    data.onChange?.(id, text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      setIsEditing(false);
      data.onChange?.(id, text);
    }
  };

  if (isEditing) {
    return (
      <div className="comment-node editing">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          className="comment-input"
          rows={3}
        />
      </div>
    );
  }

  return (
    <div className="comment-node" onDoubleClick={handleDoubleClick}>
      <div className="comment-text">{data.label}</div>
    </div>
  );
};

const MemoizedCommentNode = memo(CommentNode);

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

  // 计算贝塞尔曲线路径
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

  return (
    <g
      className="custom-edge"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 贝塞尔曲线 */}
      <path
        d={edgePath}
        stroke={isHovered ? '#1890ff' : '#b8b8b8'}
        strokeWidth={2}
        fill="none"
        style={{ transition: 'stroke 0.2s' }}
      />
      
      {/* 箭头 - 水平垂直三角形 */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="8"
          markerHeight="8"
          refX="7"
          refY="4"
          orient="auto"
        >
          <polygon
            points="0 0, 8 4, 0 8"
            fill={isHovered ? '#1890ff' : '#b8b8b8'}
            style={{ transition: 'fill 0.2s' }}
          />
        </marker>
      </defs>
      <path
        d={edgePath}
        stroke="transparent"
        strokeWidth={2}
        fill="none"
        markerEnd="url(#arrowhead)"
      />

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
  comment: MemoizedCommentNode,
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
      params: {
        filePath: '/data/input.csv',
        encoding: 'utf8',
      },
      inputVar: undefined,
      outputVar: 'records: 1,204',
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
      params: {
        cleanMode: 'all',
      },
      inputVar: 'data_stream',
      outputVar: 'cleaned_data',
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
      params: {
        spaceMode: 'trim',
      },
      inputVar: 'cleaned_data',
      outputVar: 'trimmed_data',
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
      params: {
        sortField: 'year',
        sortOrder: 'asc',
      },
      inputVar: 'trimmed_data',
      outputVar: 'sorted_data',
    },
  },
];

const defaultEdges: Edge[] = [
  { id: 'edge-1', source: 'node-1', target: 'node-2', type: 'custom' },
  { id: 'edge-2', source: 'node-2', target: 'node-3', type: 'custom' },
  { id: 'edge-3', source: 'node-3', target: 'node-4', type: 'custom' },
];

// ==================== 底部工具栏组件 ====================

interface FloatingToolbarProps {
  onOpenOperatorLibrary: () => void;
  onAddComment: () => void;
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
}

const FloatingToolbar: React.FC<FloatingToolbarProps> = ({
  onOpenOperatorLibrary,
  onAddComment,
  zoom,
  onZoomIn,
  onZoomOut,
  onResetView,
}) => {
  return (
    <div className="floating-toolbar">
      <button className="toolbar-btn" onClick={onOpenOperatorLibrary} title="算子库">
        <Package size={20} />
      </button>
      <div className="toolbar-divider"></div>
      <button className="toolbar-btn" onClick={onAddComment} title="添加注释">
        <MessageSquarePlus size={20} />
      </button>
      <div className="toolbar-divider"></div>
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

// ==================== 算子库弹窗组件 ====================

interface OperatorLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddNode: (operator: { id: string; name: string; icon: string; category: string }) => void;
}

const OperatorLibraryModal: React.FC<OperatorLibraryModalProps> = ({ isOpen, onClose, onAddNode }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['input', 'process', 'output'])
  );

  if (!isOpen) return null;

  const toggleCategory = (key: string) => {
    setExpandedCategories((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  const filteredCategories = operatorCategories
    .map((category) => ({
      ...category,
      operators: category.operators.filter((op) =>
        op.name.toLowerCase().includes(searchTerm.toLowerCase())
      ),
    }))
    .filter((category) => category.operators.length > 0);

  return (
    <>
      <div className="modal-overlay" onClick={onClose}></div>
      <div className="operator-modal">
        <div className="modal-header">
          <h3>算子库</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-search">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="搜索算子..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="modal-content">
          {filteredCategories.map((category) => (
            <div key={category.key} className="modal-category">
              <div className="modal-category-header" onClick={() => toggleCategory(category.key)}>
                <span>{category.label}</span>
                <ChevronDown
                  size={16}
                  className={`chevron ${expandedCategories.has(category.key) ? 'expanded' : ''}`}
                />
              </div>

              {expandedCategories.has(category.key) && (
                <div className="modal-operators">
                  {category.operators.map((operator) => {
                    const Icon = getIcon(operator.icon);
                    return (
                      <div
                        key={operator.id}
                        className="modal-operator-item"
                        onClick={() => {
                          onAddNode(operator);
                          onClose();
                        }}
                      >
                        <div className="modal-operator-icon">
                          <Icon size={20} />
                        </div>
                        <span className="modal-operator-name">{operator.name}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

// ==================== 主画布组件 ====================

const FlowEditorInner: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isOperatorLibraryOpen, setIsOperatorLibraryOpen] = useState(false);
  const isInitialized = useRef(false);
  const nodeIdCounter = useRef(4);
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
          onUpdateParams: (id: string, params: Record<string, any>) => {
            setNodes((nds) =>
              nds.map((n) => {
                if (n.id === id) {
                  return {
                    ...n,
                    data: { ...n.data, params },
                  };
                }
                return n;
              })
            );
          },
        },
      }));

      const edgesWithCallbacks = defaultEdges.map((edge) => ({
        ...edge,
        data: {
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
          onDelete: (id: string) => {
            setEdges((eds) => eds.filter((e) => e.id !== id));
          },
        },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  const handleAddNode = useCallback(
    (operator: { id: string; name: string; icon: string; category: string }) => {
      nodeIdCounter.current += 1;
      const newNode: Node<NodeData> = {
        id: `node-${nodeIdCounter.current}`,
        type: 'custom',
        position: {
          x: START_X + (NODE_WIDTH + NODE_GAP) * (nodes.length),
          y: START_Y,
        },
        data: {
          label: operator.name,
          icon: operator.icon,
          operatorId: operator.id,
          description: getOperatorDescription(operator.id),
          params: getDefaultParams(operator.id),
          inputVar: 'input_data',
          outputVar: 'output_data',
          onDelete: (id: string) => {
            setNodes((nds) => nds.filter((n) => n.id !== id));
            setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
          },
          onUpdateParams: (id: string, params: Record<string, any>) => {
            setNodes((nds) =>
              nds.map((n) => {
                if (n.id === id) {
                  return {
                    ...n,
                    data: { ...n.data, params },
                  };
                }
                return n;
              })
            );
          },
        },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes, setEdges]
  );

  // 添加注释
  const handleAddComment = useCallback(() => {
    const commentId = `comment-${Date.now()}`;
    const newComment: Node<NodeData> = {
      id: commentId,
      type: 'comment',
      position: {
        x: 100 + Math.random() * 200,
        y: 100 + Math.random() * 200,
      },
      data: {
        label: '双击编辑注释',
        onChange: (id: string, label: string) => {
          setNodes((nds) =>
            nds.map((n) => {
              if (n.id === id) {
                return {
                  ...n,
                  data: { ...n.data, label },
                };
              }
              return n;
            })
          );
        },
      },
    };
    setNodes((nds) => [...nds, newComment]);
  }, [setNodes]);

  return (
    <div className="flow-canvas-container">
      {/* Header */}
      <div className="flow-header">
        <div className="header-left">
          <h2>科研数据清洗与排序</h2>
          <span className="header-desc">对科研文献数据进行空行清洗、空格清洗、按年份升序排序</span>
        </div>
        <div className="header-right">
          <button className="run-btn">
            <Play size={16} fill="currentColor" />
            <span>运行</span>
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
            onOpenOperatorLibrary={() => setIsOperatorLibraryOpen(true)}
            onAddComment={handleAddComment}
            zoom={1}
            onZoomIn={zoomIn}
            onZoomOut={zoomOut}
            onResetView={fitView}
          />
        </div>
      </div>

      {/* Operator Library Modal */}
      <OperatorLibraryModal
        isOpen={isOperatorLibraryOpen}
        onClose={() => setIsOperatorLibraryOpen(false)}
        onAddNode={handleAddNode}
      />
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

const getDefaultParams = (id: string): Record<string, any> => {
  const params: Record<string, Record<string, any>> = {
    'file-upload': {
      filePath: '/data/input.csv',
      encoding: 'utf8',
    },
    'empty-clean': {
      cleanMode: 'all',
    },
    'space-clean': {
      spaceMode: 'trim',
    },
    'year-sort': {
      sortField: 'year',
      sortOrder: 'asc',
    },
    'mysql-source': {
      host: 'localhost',
      port: 3306,
    },
    'kafka-reader': {
      brokers: 'localhost:9092',
      topic: '',
    },
    'data-filter': {
      condition: '',
      mode: 'include',
    },
    'data-transformer': {
      transform: '',
    },
    'file-uploader': {
      outputPath: '',
      format: 'csv',
    },
  };
  return params[id] || {};
};

const FlowEditor: React.FC = () => {
  return (
    <ReactFlowProvider>
      <FlowEditorInner />
    </ReactFlowProvider>
  );
};

export default FlowEditor;
