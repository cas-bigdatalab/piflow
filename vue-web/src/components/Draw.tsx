import React, { useCallback, useState, useRef, memo, useEffect, useMemo } from 'react';
import { shortId } from '../lib/ids';
import { saveDrawInfo, getAllSkills, listSkillsDetails, createMessage, streamChat, apiBase } from "../lib/api";

const DEFAULT_SKILL_ICON = "/storage/common/common.png";

function resolveIconUrl(icon?: string) {
  const rawIcon = (icon || "").trim();
  
  if (!rawIcon) {
    return apiBase() + DEFAULT_SKILL_ICON;
  }
  
  if (/^(https?:|data:)/.test(rawIcon)) {
    return rawIcon;
  }
  
  return apiBase() + rawIcon;
}
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  getBezierPath,
  getStraightPath,
  useReactFlow,
  ReactFlowProvider,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
  type EdgeProps,
  useOnViewportChange,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Play,
  Save,
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
  Minus,
  GitBranch,
  RotateCcw,
  Search,
  ChevronDown,
  ChevronUp,
  Edit3,
} from 'lucide-react';
import './Draw.css';

// ==================== 类型定义 ====================

interface NodeData {
  label: string;
  icon: string;
  operatorId: string;
  operatorName?: string;
  operatorZh?: string;
  operatorType?: string;
  description?: string;
  params?: Record<string, any>;
  inputVar?: string;
  outputVar?: string;
  onDelete?: (id: string) => void;
  onUpdateParams?: (id: string, params: Record<string, any>) => void;
  onUpdateLabel?: (id: string, label: string) => void;
  onSelect?: (id: string) => void;
  isSelected?: boolean;
  input_params?: { params: { name: string; param_value: string; type?: string }[] };
  output_params?: { params: { name: string; type: string }[] };
}

interface CustomEdgeData {
  edgeType?: 'bezier' | 'straight';
  onDelete?: (id: string) => void;
}

// 拖拽数据类型
interface DraggedOperator {
  id: string;
  name: string;
  icon: string;
  category: string;
}

// ==================== 图标组件映射 ====================

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

// 获取图标
const getIcon = (iconName: string) => {
  return iconComponents[iconName] || Circle;
};

// ==================== 参数配置 ====================

const paramLabels: Record<string, Record<string, string>> = {
  'file-upload': {
    filePath: '文件路径',
    format: '文件类型',
    encoding: '编码格式',
  },
  'empty-clean': {
    cleanMode: '清理模式',
  },
  'space-clean': {
    spaceMode: '清理范围',
  },
  'year-sort': {
    sortField: '排序字段',
    sortOrder: '排序顺序',
  },
};

const paramDisplayValues: Record<string, Record<string, Record<string, string>>> = {
  'file-upload': {
    format: { csv: 'CSV', excel: 'Excel', json: 'JSON', txt: 'TXT' },
    encoding: { utf8: 'UTF-8', gb2312: 'GB2312', gbk: 'GBK' },
  },
  'empty-clean': {
    cleanMode: { all: '移除所有空行', spaces: '移除仅含空格的行' },
  },
  'space-clean': {
    spaceMode: { trim: '首尾空格', extra: '多余空格', all: '所有空格' },
  },
  'year-sort': {
    sortField: { year: 'publish_year', title: 'title', author: 'author' },
    sortOrder: { asc: '升序', desc: '降序' },
  },
};

// ==================== 算子分类 ====================

// 生成 UUID 的兼容函数
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};


// 算子分类数据（从后端接口获取后赋值）
let operatorCategories: {
  groupName: string;
  DagSkillInfoList: { skill_id: string; skill_name: string; name_zh: string; icon_path: string; skill_type: string; description?: string }[];
}[] = [];

// ==================== 自定义节点组件 ====================

const CustomNode: React.FC<NodeProps<NodeData>> = ({ id, data, selected }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (data.onDelete) {
      data.onDelete(id);
    }
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
  const getParamLabel = (operatorId: string, paramKey: string): string => {
    return paramLabels[operatorId]?.[paramKey] || paramKey;
  };

  // 渲染参数项
  const renderParams = () => {
    if (!data.params) return null;
    return Object.entries(data.params).map(([key, value]) => (
      <div key={key} className="node-param-item">
        <span className="node-param-label">{getParamLabel(data.operatorId, key)}:</span>
        <span className="node-param-value" data-tooltip={String(getDisplayValue(key, value))}>{getDisplayValue(key, value)}</span>
      </div>
    ));
  };

  return (
    <div className={`custom-node ${selected ? 'selected' : ''}`} onClick={() => { data.onSelect?.(id); }}>
      <Handle
        type="target"
        position={Position.Left}
        className="node-handle"
        style={{ top: '60px' }}
      />

      {/* 节点顶部 */}
      <div className="node-header">
          <button className="node-expand-icon-btn" onClick={(e) => { e.stopPropagation(); toggleExpand(e); }} title={isExpanded ? '收起参数' : '展开参数'}>
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        <div className="node-header-left">
          <div className="node-title-wrapper">
            {data.operatorType && (
              <span className="node-operator-type">{data.operatorType.toUpperCase()}</span>
            )}
            <span className="node-title-text">
              {data.label}
            </span>
            {data.operatorName && (
              <span className="node-operator-info">{data.operatorName}</span>
            )}
          </div>
        </div>
        <div className="node-header-right">
          <button 
            className="node-delete-btn" 
            onClick={(e: React.MouseEvent) => { 
              e.stopPropagation(); 
              e.preventDefault();
              handleDeleteClick(e); 
            }} 
            title="删除节点"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* 展开参数详情 */}
      {isExpanded && (
        <div className="node-params-panel" onClick={(e) => { e.stopPropagation(); data.onSelect?.(id); }}>
          {/* 输入参数 */}
          {data.input_params?.params && data.input_params.params.length > 0 && (
            <div className="nodeParams">
              <div className="topTitle">
                <div className="labelText">输入</div>
                <div className="valueText">值</div>
              </div>
              {data.input_params.params.map((inputItem, index) => (
                <div key={`input-${index}`} className="oneParams">
                  <div className="node-param-label">{inputItem.name}</div>
                  <div className="node-param-value" data-tooltip={String(inputItem.param_value || '-')}>{inputItem.param_value || '-'}</div>
                </div>
              ))}
            </div>
          )}
          
          {/* 输出参数 */}
          {data.output_params?.params && data.output_params.params.length > 0 && (
            <div className="nodeParams">
              <div className="topTitle">
                <div className="labelText">输出</div>
                <div className="valueText">类型</div>
              </div>
              {data.output_params.params.map((outputItem, index) => (
                <div key={`output-${index}`} className="oneParams">
                  <div className="node-param-label">{outputItem.name}</div>
                  <div className="node-param-value" data-tooltip={String(outputItem.type)}>{outputItem.type}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className="node-handle"
        style={{ top: '60px' }}
      />
    </div>
  );
};

const MemoizedCustomNode = memo(CustomNode);

// ==================== 注释节点组件 ====================

interface CommentNodeData {
  label: string;
  onChange?: (id: string, label: string) => void;
}

const CommentNode: React.FC<NodeProps<CommentNodeData>> = ({ id, data }) => {
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

// ==================== 自定义连线组件====================

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

  // 从data中获取连线类型
  const edgeStyle = data?.edgeType || 'bezier';

  // 使用useMemo确保路径在edgeStyle变化时重新计算
  const [edgePath, labelX, labelY] = useMemo(() => {
    if (edgeStyle === 'straight') {
      return getStraightPath({ sourceX, sourceY, targetX, targetY });
    }
    return getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
      curvature: 0.4,
    });
  }, [edgeStyle, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition]);

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
        stroke="#94A3B8"
        strokeWidth={2}
        fill="none"
      />

      {/* 箭头 */}
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
            fill="#94A3B8"
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

// ==================== 节点和连线类型配置====================

const nodeTypes = {
  custom: MemoizedCustomNode,
  comment: MemoizedCommentNode,
};

const edgeTypes = {
  custom: CustomEdge,
};

// 节点间距配置
const NODE_WIDTH = 280;
const NODE_GAP = 80;
const NODE_HEIGHT = 120;
const START_X = 60;
const START_Y = 80;

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
      operatorName: 'file-upload',
      operatorType: 'input',
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
      label: '空行清理',
      icon: 'Eraser',
      operatorId: 'empty-clean',
      operatorName: 'empty-clean',
      operatorType: 'process',
      description: '移除空行',
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
      label: '空格清理',
      icon: 'Type',
      operatorId: 'space-clean',
      operatorName: 'space-clean',
      operatorType: 'process',
      description: '移除多余空格',
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
      operatorName: 'year-sort',
      operatorType: 'process',
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
  { id: 'edge-1', source: 'node-1', target: 'node-2', type: 'custom', data: { edgeType: 'bezier' } },
  { id: 'edge-2', source: 'node-2', target: 'node-3', type: 'custom', data: { edgeType: 'bezier' } },
  { id: 'edge-3', source: 'node-3', target: 'node-4', type: 'custom', data: { edgeType: 'bezier' } },
];

// ==================== 底部工具栏组件====================

interface FloatingToolbarProps {
  onOpenOperatorLibrary: () => void;
  onAddComment: () => void;
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  edgeType: 'bezier' | 'straight';
  onEdgeTypeChange: (type: 'bezier' | 'straight') => void;
}

const FloatingToolbar: React.FC<FloatingToolbarProps> = ({
  onOpenOperatorLibrary,
  onAddComment,
  zoom,
  onZoomIn,
  onZoomOut,
  onResetView,
  edgeType,
  onEdgeTypeChange,
}) => {
  return (
    <div className="floating-toolbar">
      <button className="toolbar-operator-btn" onClick={onOpenOperatorLibrary}>
        <Package size={16} />
        <span>算子库</span>
      </button>
      <div className="toolbar-divider"></div>
      <button className="toolbar-btn" onClick={onAddComment} title="添加注释">
        <MessageSquarePlus size={20} />
      </button>
      <div className="toolbar-divider"></div>

      {/* 连线类型切换 */}
      <div className="edge-type-toggle">
        <button
          className={`toolbar-btn ${edgeType === 'straight' ? 'active' : ''}`}
          onClick={() => onEdgeTypeChange('straight')}
          title="直线"
        >
          <Minus size={20} />
        </button>
        <button
          className={`toolbar-btn ${edgeType === 'bezier' ? 'active' : ''}`}
          onClick={() => onEdgeTypeChange('bezier')}
          title="曲线"
        >
          <GitBranch size={20} />
        </button>
      </div>

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

// ==================== 算子库弹窗组件====================

interface OperatorLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddNode: (operator: { skill_id: string; skill_name: string; name_zh: string; icon_path: string; skill_type: string; description?: string }, position?: { x: number; y: number }) => void;
  operatorList: { groupName: string; DagSkillInfoList: { skill_id: string; skill_name: string; name_zh: string; icon_path: string; skill_type: string; description?: string }[] }[];
}

const OperatorLibraryModal: React.FC<OperatorLibraryModalProps> = ({ isOpen, onClose, onAddNode, operatorList }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['input', 'process', 'output'])
  );
  const [hoveredOperator, setHoveredOperator] = useState<{ operator: typeof operatorList[0]['DagSkillInfoList'][0]; x: number; y: number } | null>(null);

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

  const filteredCategories = operatorList
    .map((category) => ({
      ...category,
      DagSkillInfoList: category.DagSkillInfoList.filter((op) =>
        (op.name_zh || op.skill_name || '').toLowerCase().includes(searchTerm.toLowerCase())
      ),
    }))
    .filter((category) => category.DagSkillInfoList.length > 0);

  // 处理拖拽开始
  const handleDragStart = (e: React.DragEvent, operator: { skill_id: string; skill_name: string;name_zh: string; icon_path: string; skill_type: string; description?: string }) => {
    // 拖拽开始时隐藏 tooltip
    setHoveredOperator(null);
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('application/json', JSON.stringify(operator));
    // 设置拖拽时的自定义图标
    const dragImage = document.createElement('div');
    dragImage.style.padding = '8px 12px';
    dragImage.style.background = '#1890ff';
    dragImage.style.color = '#fff';
    dragImage.style.borderRadius = '4px';
    dragImage.style.fontSize = '14px';
    dragImage.style.position = 'absolute';
    dragImage.style.top = '-1000px';
    dragImage.textContent = operator.name_zh;
    document.body.appendChild(dragImage);
    e.dataTransfer.setDragImage(dragImage, 0, 0);
    setTimeout(() => document.body.removeChild(dragImage), 0);
  };

  // 处理鼠标悬停
  const handleMouseEnter = (e: React.MouseEvent, operator: typeof operatorList[0]['DagSkillInfoList'][0]) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const tooltipWidth = 300;
    const tooltipHeight = 280;
    
    let x = rect.right + 10;
    let y = rect.top;
    
    if (x + tooltipWidth > window.innerWidth) {
      x = rect.left - tooltipWidth - 10;
    }
    
    if (y + tooltipHeight > window.innerHeight) {
      y = rect.top - tooltipHeight + rect.height;
      if (y < 10) {
        y = 10;
      }
    }
    
    setHoveredOperator({
      operator,
      x,
      y
    });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (hoveredOperator) {
      const tooltipWidth = 300;
      const tooltipHeight = 280;
      
      let x = e.clientX + 10;
      let y = e.clientY - 50;
      
      if (x + tooltipWidth > window.innerWidth) {
        x = e.clientX - tooltipWidth - 10;
      }
      
      if (y + tooltipHeight > window.innerHeight) {
        y = window.innerHeight - tooltipHeight - 10;
      }
      
      if (y < 10) {
        y = 10;
      }
      
      setHoveredOperator(prev => prev ? {
        ...prev,
        x,
        y
      } : null);
    }
  };

  const handleMouseLeave = () => {
    setHoveredOperator(null);
  };

  return (
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
          <div key={category.groupName} className="modal-category">
            <div className="modal-category-header" onClick={() => toggleCategory(category.groupName)}>
              <span>{category.groupName}</span>
              <ChevronDown
                size={16}
                className={`chevron ${expandedCategories.has(category.groupName) ? 'expanded' : ''}`}
              />
            </div>

            {expandedCategories.has(category.groupName) && (
              <div className="modal-operators">
                {category.DagSkillInfoList.map((operator) => {
                  return (
                    <div
                      key={operator.skill_id}
                      className="modal-operator-item"
                      draggable
                      onDragStart={(e) => handleDragStart(e, operator)}
                      onClick={() => {
                        onAddNode(operator);
                        onClose();
                      }}
                      onMouseEnter={(e) => handleMouseEnter(e, operator)}
                      onMouseMove={handleMouseMove}
                      onMouseLeave={handleMouseLeave}
                      style={{ cursor: 'grab' }}
                    >
                      <div className="modal-operator-icon">
                        <img
                          src={resolveIconUrl(operator.icon_path)}
                          alt={operator.name_zh}
                          style={{ width: '24px', height: '24px', objectFit: 'contain' }}
                        />
                      </div>
                      <span className="modal-operator-name">{operator.name_zh}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {hoveredOperator && hoveredOperator.operator.description && (
        <div
          className="operator-tooltip"
          style={{
            left: `${hoveredOperator.x}px`,
            top: `${hoveredOperator.y}px`
          }}
        >
          <div className="tooltip-header">{hoveredOperator.operator.name_zh}</div>
          <div className="tooltip-description">{hoveredOperator.operator.description}</div>
        </div>
      )}
    </div>
  );
};

// ==================== 外部传入的初始Pipeline 数据 ====================

export interface InitialPipelineNode {
  node_name: string;
  skill_name?: string;
  params?: Record<string, unknown>;
}

export interface InitialPipelineData {
  task: { name: string; description?: string };
  nodes: InitialPipelineNode[];
}

export interface FlowEditorProps {
  initialPipelineData?: InitialPipelineData | null;
  onClose?: () => void;
}

// ==================== 主画布组件====================

const FlowEditorInner: React.FC<FlowEditorProps> = ({ initialPipelineData, onClose, threadId, messageId: messageIdProp, savedDrawData }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>>(defaultNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isOperatorLibraryOpen, setIsOperatorLibraryOpen] = useState(false);
  const [edgeType, setEdgeType] = useState<'bezier' | 'straight'>('bezier');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);  // 添加：加载状态
  const [operatorList, setOperatorList] = useState(operatorCategories);
  const [referenceOptions, setReferenceOptions] = useState<{ name: string; type: string; description: string; nodeId: string; nodeName: string }[]>([]);  // 来源下拉选项
  const [isLoadingReferences, setIsLoadingReferences] = useState(false);   // 加载来源状态
  const [taskId, setTaskId] = useState<string>('');
  const [messageId, setMessageId] = useState<string>(messageIdProp || '');
  const [taskName, setTaskName] = useState<string>('');
  const [taskDescription, setTaskDescription] = useState<string>('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const prevNodesLengthRef = useRef<number>(nodes.length);

  // 键盘Delete键删除选中节点
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const tagName = target.tagName;
      if (tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT' || target.isContentEditable) {
        return;
      }
      if ((e.key === 'Delete' || e.key === 'Backspace') && selectedNodeId) {
        e.preventDefault();
        setShowDeleteModal(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNodeId]);

  // 删除节点
  const handleDeleteNode = () => {
    if (selectedNodeId) {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
      setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId));
      setSelectedNodeId(null);
    }
    setShowDeleteModal(false);
  };

  // 当 messageId prop 变化时更新 state
  useEffect(() => {
    if (messageIdProp) {
      setMessageId(messageIdProp);
    }
  }, [messageIdProp]);

  // 从 getAllSkills 返回的分组结构中按 skill_name 精确匹配算子信息
  const extractSkillBySkillName = useCallback((res: any, targetSkillName: string): any | null => {
    if (!res?.result?.data || !Array.isArray(res.result.data)) return null;
    const groups: any[] = res.result.data;
    let matched: any = null;
    // 遍历分组，在每个 DagSkillInfoList 中查找 skill_name 匹配的算子
    for (const group of groups) {
      const list: any[] = group?.DagSkillInfoList || [];
      for (const info of list) {
        if (info && info.skill_name === targetSkillName) {
          matched = info;
          break;
        }
      }
      if (matched) break;
    }
    // 如果按 skill_name 精确匹配失败，尝试按 name_zh 或模糊匹配
    if (!matched) {
      for (const group of groups) {
        const list: any[] = group?.DagSkillInfoList || [];
        for (const info of list) {
          if (info && (info.name_zh === targetSkillName || info.skill_id === targetSkillName)) {
            matched = info;
            break;
          }
        }
        if (matched) break;
      }
    }
    return matched;
  }, []);

  // 获取任务名称和描述（从 props 中提取，无需再调用接口）
  useEffect(() => {
    if (savedDrawData?.task) {
      setTaskName(savedDrawData.task.dag_task_name || '');
      setTaskDescription(savedDrawData.task.description || '');
    } else if (initialPipelineData?.task) {
      setTaskName(initialPipelineData.task.name || initialPipelineData.task.dag_task_name || '');
      setTaskDescription(initialPipelineData.task.description || '');
    }
  }, [savedDrawData, initialPipelineData]);

  const [isEditingNodeName, setIsEditingNodeName] = useState(false);
  const [editingNodeName, setEditingNodeName] = useState('');
  const [isDescExpanded, setIsDescExpanded] = useState(false);
  const [expandedRefDropdowns, setExpandedRefDropdowns] = useState<string[]>([]);
  const [selectedOperatorForRef, setSelectedOperatorForRef] = useState<string>('');  // 两级选择：当前选中的算子
  const [showOperatorModal, setShowOperatorModal] = useState(false);  // 任务ID，保存后获取
  const isInitialized = useRef(false);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isFirstRender = useRef(true);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { zoomIn, zoomOut, fitView, setViewport, screenToFlowPosition, getViewport } = useReactFlow();

  // 组件挂载时调整视口为靠左、垂直居中
  useEffect(() => {
    setZoomLevel(getViewport()?.zoom || 1);
    const timer = setTimeout(() => {
      if (nodes.length > 0) {
        fitNodesToViewLeft();
      }
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  // 计算垂直居中 Y 坐标
  const getVerticalCenterY = () => {
    const containerEl = reactFlowWrapper.current;
    const containerHeight = containerEl?.clientHeight || 800;
    return Math.max((containerHeight - NODE_HEIGHT) / 2, 50);
  };

  // 将视口调整为节点靠左、垂直居中显示（只在删除节点时自动调整）
  const fitNodesToViewLeft = useCallback(() => {
    if (nodes.length === 0) return;
    const wrapper = reactFlowWrapper.current;
    if (!wrapper) return;

    // 只在节点数量减少时自动调整视口
    if (nodes.length >= prevNodesLengthRef.current) {
      prevNodesLengthRef.current = nodes.length;
      return;
    }

    // 更新ref
    prevNodesLengthRef.current = nodes.length;

    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodes.forEach(n => {
      minX = Math.min(minX, n.position.x);
      maxX = Math.max(maxX, n.position.x + (NODE_WIDTH));
      minY = Math.min(minY, n.position.y);
      maxY = Math.max(maxY, n.position.y + NODE_HEIGHT);
    });

    const graphW = maxX - minX;
    const graphH = maxY - minY;
    const padding = 60;
    const zoom = Math.min(
      Math.max((w - padding * 2) / graphW, 1),
      Math.max((h - padding * 2) / graphH, 1),
      1.5
    );

    setViewport({
      x: padding - minX * zoom,
      y: (h - graphH * zoom) / 2 - minY * zoom,
      zoom,
    });
  }, [nodes, setViewport]);

  // 获取选中的节点
  const selectedNode = nodes.find((m) => m.id === selectedNodeId);

  // 关闭配置面板
  const closeConfigPanel = () => {
    setNodes((nds) => nds.map((n) => ({ ...n, selected: false })));
    setSelectedNodeId(null);
  };

  // 监听 nodes 数量变化，自动调整视口为靠左、垂直居中
  // 只在节点数量变化时调整，避免节点展开/收缩时触发
  useEffect(() => {
    if (nodes.length > 0 && isInitialized.current) {
      setTimeout(() => {
        fitNodesToViewLeft();
      }, 100);
    }
  }, [nodes.length, fitNodesToViewLeft]);

  // 监听所有视口变化（包括鼠标滚轮缩放和程序化调整），更新缩放百分比显示
  useOnViewportChange({
    onChange: (viewport) => {
      setZoomLevel(viewport.zoom);
    },
  });

  // 切换连线类型时更新所有现有连线
  useEffect(() => {
    setEdges((eds) =>
      eds.map((edge) => ({
        ...edge,
        data: {
          ...edge.data,
          edgeType,
        },
      }))
    );
  }, [edgeType, setEdges]);

  // 辅助函数：获取节点数组中的最大ID数字
  const getMaxNodeId = (nodes: any[]): number => {
    if (nodes.length === 0) return 0;
    const ids = nodes
      .map(n => n.id.replace('node-', ''))
      .filter(id => !isNaN(parseInt(id)))
      .map(id => parseInt(id));
    return ids.length > 0 ? Math.max(...ids) : 0;
  };

  const nodeIdCounter = useRef(4);

  // 加载外部传入的初始pipeline 数据
  useEffect(() => {
    if (isInitialized.current) return;

    const loadInitialPipeline = async () => {
      setIsLoading(true);

      // 优先使用已保存的画板数据（来自 getDSLJsonByMessageId 接口）
      if (savedDrawData && savedDrawData.nodes && savedDrawData.nodes.length > 0) {
        console.log('使用已保存的画板数据（来自接口）:', savedDrawData);
        const loadedNodes: Node<NodeData>[] = [];
        const loadedEdges: Edge[] = [];

        // 构建 nodeId -> output_params 的映射，用于后续查找引用
        const outputParamsMap: Record<string, any[]> = {};
        const nodeIdMap: Record<string, string> = {};
        for (let i = 0; i < savedDrawData.nodes.length; i++) {
          const n = savedDrawData.nodes[i];
          const nodeId = n.node_id || `node-${i+1}`;
          nodeIdMap[n.node_name || nodeId] = nodeId;
          
          // 统一处理 n.output_params 的不同格式
          let paramsArray: any[] = [];
          if (n.output_params?.params) {
            paramsArray = n.output_params.params;
          } else if (Array.isArray(n.output_params)) {
            paramsArray = n.output_params;
          }
          
          if (paramsArray.length > 0) {
            outputParamsMap[nodeId] = paramsArray;
          }
        }

        // 构建 bindingsMap：${to_node_id}|${to_param_name} -> binding
        const bindingsMap: Record<string, any> = {};
        if (savedDrawData.bindings && Array.isArray(savedDrawData.bindings)) {
          for (const binding of savedDrawData.bindings) {
            // 转换节点名称为节点ID
            let fromNodeId = binding.from_node_id;
            let toNodeId = binding.to_node_id;
            
            if (!fromNodeId.startsWith('node-')) {
              fromNodeId = nodeIdMap[fromNodeId] || fromNodeId;
            }
            if (!toNodeId.startsWith('node-')) {
              toNodeId = nodeIdMap[toNodeId] || toNodeId;
            }
            
            const key = `${toNodeId}|${binding.to_param_name}`;
            bindingsMap[key] = {
              ...binding,
              from_node_id: fromNodeId,
              to_node_id: toNodeId
            };
          }
        }
        console.log('=== bindingsMap ===', bindingsMap);

        // 为 savedDrawData 中的节点计算新的布局位置，避免重叠（带分层展示）
        const savedNodePositions: Record<string, { x: number; y: number }> = {};
        const savedNodesCount = savedDrawData.nodes.length;
        
        // 使用分层布局：从 edges 计算拓扑层级
        const savedNodeIdToIndex: Record<string, number> = {};
        savedDrawData.nodes.forEach((n, index) => {
          const nodeId = n.node_id || n.id || `node-${index + 1}`;
          savedNodeIdToIndex[nodeId] = index;
        });
        
        const savedInDegree: number[] = new Array(savedNodesCount).fill(0);
        const savedOutEdges: number[][] = new Array(savedNodesCount).fill(null).map(() => []);
        
        for (const e of (savedDrawData.edges || [])) {
          const sourceIdx = savedNodeIdToIndex[e.from_node_id];
          const targetIdx = savedNodeIdToIndex[e.to_node_id];
          if (sourceIdx !== undefined && targetIdx !== undefined) {
            savedInDegree[targetIdx]++;
            savedOutEdges[sourceIdx].push(targetIdx);
          }
        }
        
        const savedLevels: number[][] = [];
        const savedTempInDegree = [...savedInDegree];
        const savedProcessed = new Set<number>();
        
        let savedCurrentLevel: number[] = [];
        for (let i = 0; i < savedNodesCount; i++) {
          if (savedTempInDegree[i] === 0 && !savedProcessed.has(i)) {
            savedCurrentLevel.push(i);
            savedProcessed.add(i);
          }
        }
        
        while (savedCurrentLevel.length > 0) {
          savedLevels.push(savedCurrentLevel);
          const savedNextLevel: number[] = [];
          savedCurrentLevel.forEach(idx => {
            savedOutEdges[idx].forEach(targetIdx => {
              if (!savedProcessed.has(targetIdx)) {
                savedTempInDegree[targetIdx]--;
                if (savedTempInDegree[targetIdx] === 0) {
                  savedNextLevel.push(targetIdx);
                  savedProcessed.add(targetIdx);
                }
              }
            });
          });
          savedCurrentLevel = savedNextLevel;
        }
        
        for (let i = 0; i < savedNodesCount; i++) {
          if (!savedProcessed.has(i)) {
            savedLevels.push([i]);
          }
        }
        
        for (let levelIdx = 0; levelIdx < savedLevels.length; levelIdx++) {
          const level = savedLevels[levelIdx];
          level.forEach((nodeIndex, nodeInLevelIdx) => {
            const n = savedDrawData.nodes[nodeIndex];
            const nodeId = n.node_id || n.id || `node-${nodeIndex + 1}`;
            savedNodePositions[nodeId] = {
              x: START_X + levelIdx * (NODE_WIDTH + NODE_GAP),
              y: START_Y + nodeInLevelIdx * (NODE_HEIGHT + NODE_GAP)
            };
          });
        }

        for (let i = 0; i < savedDrawData.nodes.length; i++) {
          const n = savedDrawData.nodes[i];
          let inputParams = undefined;
          let outputParams = undefined;
          let nodeIconPath = n.icon_path || '';
          const skillId = n.skill?.skill_id || n.skill_id;
          const nodeId = n.node_id || `node-${i+1}`;

          // 检查 savedDrawData 中是否已经有完整的参数信息
          const hasSavedInputParams = n.input_params && Array.isArray(n.input_params) && n.input_params.length > 0;
          const hasSavedOutputParams = n.output_params && (Array.isArray(n.output_params) || n.output_params.params?.length > 0);
          const hasSavedIconPath = n.icon_path && n.icon_path !== '';
          
          console.log(`节点 ${i} (${n.node_name}):`, {
            hasSavedInputParams,
            hasSavedOutputParams,
            hasSavedIconPath,
            n_output_params: n.output_params,
          });
          
          // 优先从 savedDrawData 里读取 output_params
          if (hasSavedOutputParams) {
            if (Array.isArray(n.output_params)) {
              outputParams = { params: n.output_params };
            } else {
              outputParams = n.output_params;
            }
            console.log(`节点 ${i}: 从 savedDrawData 读取 outputParams:`, outputParams);
          }
          
          // 对于source_stop和sink_stop这两个特殊算子，不要请求接口，使用固定的参数
          const isSpecialSkill = skillId === 'cn.piflow.engine.local.source_file_stop.SourceFileStop' || 
                                  skillId === 'cn.piflow.engine.local.file_save_stop.FileSaveStop';
          let skillDescription = '';
          
          if (isSpecialSkill) {
            console.log(`节点 ${i}: 特殊算子，不请求接口`);
            
            // 特殊算子总是使用固定的参数定义，不依赖保存的数据
            if (skillId === 'cn.piflow.engine.local.source_file_stop.SourceFileStop') {
              n.skill = n.skill || {};
              n.skill.name_zh = '文件源';
              // source_stop的固定输入参数（只有file_path）
              inputParams = {
                params: [
                  {
                    name: "file_path",
                    type: "string",
                    param_name: "file_path",
                    param_type: "String",
                    value_mode: "manual",
                    param_value: "",
                    value_source: "local_file",
                    required: true
                  }
                ]
              };
              // source_stop的输出参数
              outputParams = {
                params: [{
                  name: "output",
                  type: "string",
                  param_name: "output",
                  param_type: "String"
                }]
              };
            } else {
              n.skill = n.skill || {};
              n.skill.name_zh = '文件保存';
              // sink_stop的固定输入参数
              inputParams = {
                params: [
                  {
                    name: "input",
                    type: "string",
                    param_name: "input",
                    param_type: "String",
                    value_mode: "manual",
                    param_value: "",
                    value_source: "local_file",
                    required: true
                  },
                  {
                    name: "path",
                    type: "string",
                    param_name: "path",
                    param_type: "String",
                    value_mode: "manual",
                    param_value: "",
                    value_source: "local_file",
                    required: true
                  },
                  {
                    name: "overwrite",
                    type: "boolean",
                    param_name: "overwrite",
                    param_type: "Boolean",
                    value_mode: "manual",
                    param_value: true,
                    value_source: "local_file",
                    required: true
                  }
                ]
              };
              // sink_stop没有输出参数
              outputParams = { params: [] };
            }
          } else {
            // 普通算子：先请求接口获取参数模板（含 required 字段）
            if (skillId) {
              try {
                const skillRes = await listSkillsDetails(skillId);
                if (skillRes.result) {
                  inputParams = skillRes.result.input_params;
                  outputParams = skillRes.result.output_params || outputParams;
                  nodeIconPath = skillRes.result.icon_path || nodeIconPath;
                  skillDescription = skillRes.result.description || '';
                  // 获取 skill_name、skill_type 和 name_zh
                  if (skillRes.result.skill_name) {
                    n.skill = n.skill || {};
                    n.skill.skill_name = skillRes.result.skill_name;
                  }
                  if (skillRes.result.skill_type) {
                    n.skill = n.skill || {};
                    n.skill.skill_type = skillRes.result.skill_type;
                  }
                  if (skillRes.result.name_zh) {
                    n.skill = n.skill || {};
                    n.skill.name_zh = skillRes.result.name_zh;
                  }
                  console.log(`节点 ${i}: 从 listSkillsDetails 获取参数模板:`, inputParams);
                }
              } catch (error) {
                console.error(`节点 ${i}: 获取算子详情失败:`, error);
              }
            }
            
            // 检查是否有 required 字段，没有的话再用 getAllSkills 获取
            const hasRequiredField = inputParams?.params?.some((p: any) => p.required !== undefined);
            if (!hasRequiredField) {
              try {
                const nodeName = n.node_name || n.skill?.skill_name || '';
                const listRes = await getAllSkills(nodeName);
                const skillData = extractSkillBySkillName(listRes, nodeName) || extractSkillBySkillName(listRes, skillId);
                if (skillData?.input_params?.params?.some((p: any) => p.required !== undefined)) {
                  inputParams = skillData.input_params;
                  outputParams = skillData.output_params || outputParams;
                  nodeIconPath = skillData.icon_path || nodeIconPath;
                  // 获取 skill_name、skill_type 和 name_zh
                  if (skillData.skill_name) {
                    n.skill = n.skill || {};
                    n.skill.skill_name = skillData.skill_name;
                  }
                  if (skillData.skill_type) {
                    n.skill = n.skill || {};
                    n.skill.skill_type = skillData.skill_type;
                  }
                  if (skillData.name_zh) {
                    n.skill = n.skill || {};
                    n.skill.name_zh = skillData.name_zh;
                  }
                  console.log(`节点 ${i}: 从 getAllSkills 获取参数模板 (含 required):`, inputParams);
                }
              } catch (e) { console.error(`节点 ${i}: getAllSkills 失败:`, e); }
            }
            
            // 如果 API 都没返回，回退使用已保存数据
            if (!inputParams?.params && hasSavedInputParams) {
              inputParams = { params: n.input_params };
              console.log(`节点 ${i}: 回退使用 savedDrawData 的 inputParams:`, inputParams);
            }
            // 如果 savedDrawData 中有 icon_path，优先使用
            if (hasSavedIconPath) {
              nodeIconPath = n.icon_path;
            }
          }
          
          console.log(`节点 ${i} 最终 outputParams:`, outputParams);

          // 确保outputParamsMap里有当前节点的output_params
          if (outputParams?.params) {
            outputParamsMap[nodeId] = outputParams.params;
          }

          // 合并已保存的参数数据
          let mergedInputParams = inputParams;
          
          // 如果有inputParams定义，以inputParams为基础，用savedDrawData中的值覆盖
          if (inputParams?.params) {
            // 构建保存的参数map
            const savedParamsMap: Record<string, any> = {};
            if (n.input_params && Array.isArray(n.input_params)) {
              n.input_params.forEach((sp: any) => {
                const paramName = sp.param_name || sp.name || '';
                if (paramName) {
                  savedParamsMap[paramName] = sp;
                }
              });
            }
            
            mergedInputParams = {
              params: inputParams.params.map((paramDef: any) => {
                const paramName = paramDef.name || paramDef.param_name || '';
                const savedParam = savedParamsMap[paramName];
                
                // 检查是否有对应的binding
                const bindingKey = `${nodeId}|${paramName}`;
                const binding = bindingsMap[bindingKey];
                const isReference = (savedParam?.value_mode === 'reference') || !!binding;
                
                let _refValue = '';
                let _sourceNodeName = '';
                if (isReference && binding) {
                  const fromNodeId = binding.from_node_id;
                  let fromParamName = binding.from_param_name;
                  
                  // 仅当前缀是 node- 格式时才剥离前缀
                  if (fromParamName.includes('_') && fromParamName.split('_')[0]?.startsWith('node-')) {
                    const parts = fromParamName.split('_');
                    fromParamName = parts[parts.length - 1];
                  }
                  
                  _refValue = fromParamName;
                  // 从 savedDrawData 中查找上游节点名称
                  const fromNode = savedDrawData.nodes.find((sn: any) => {
                    const snId = sn.id || sn.node_id || '';
                    return snId === fromNodeId || snId.endsWith(fromNodeId);
                  });
                  _sourceNodeName = fromNode?.data?.operatorZh || fromNode?.skill?.name_zh || fromNode?.data?.operatorName || fromNode?.skill?.skill_name || fromNode?.skill_name || fromNode?.node_name || fromNode?.data?.label || '';
                  console.log(`节点 ${nodeId} 参数 ${paramName} 的引用信息:`, {
                    binding,
                    _refValue,
                    _sourceNodeName
                  });
                }
                
                const paramValue = savedParam?.param_value;
                
                return {
                  ...paramDef,
                  name: paramName,
                  param_value: paramValue !== undefined ? String(paramValue) : (paramDef.param_value || paramDef.default_value || ''),
                  type: savedParam?.param_type || paramDef.type || '',
                  _refType: isReference ? 'reference' : 'manual',
                  _value: isReference ? '' : (paramValue !== undefined ? String(paramValue) : (paramDef.param_value || paramDef.default_value || '')),
                  _refValue: isReference ? _refValue : '',
                  _sourceNodeName: isReference ? _sourceNodeName : '',
                };
              }),
            };
          }

          const operatorName = n.skill?.skill_name || '';
          const operatorZh = n.skill?.name_zh || '';
          const operatorType = n.skill?.skill_type || n.skill_type || '';

          loadedNodes.push({
            id: nodeId,
            type: 'custom',
            position: savedNodePositions[nodeId] || { x: START_X + (NODE_WIDTH + NODE_GAP) * i, y: START_Y },
            data: {
              label: n.node_name || '未命名节点',
              icon: nodeIconPath,
              operatorId: skillId || '',
              operatorName,
              operatorZh,
              operatorType,
              description: skillDescription || n.skill?.description || '',
              params: {},
              inputVar: 'input_data',
              outputVar: 'output_data',
              input_params: mergedInputParams,
              output_params: outputParams,
              onDelete: (delId: string) => {
                setSelectedNodeId(delId);
                setShowDeleteModal(true);
              },
              onUpdateParams: (updId: string, params: Record<string, any>) => {
                setNodes((nds) => nds.map((nn) => nn.id === updId ? { ...nn, data: { ...nn.data, params } } : nn));
              },
              onSelect: (selId: string) => { setSelectedNodeId(selId); setShowOperatorModal(false); },
            },
          });
        }

        for (const e of (savedDrawData.edges || [])) {
          // 使用 nodeIdMap 将节点名称转换为节点ID
          let sourceId = e.from_node_id;
          let targetId = e.to_node_id;
          
          // 如果 sourceId 看起来是节点名称而不是节点ID，尝试转换
          if (!sourceId.startsWith('node-')) {
            sourceId = nodeIdMap[sourceId] || sourceId;
          }
          if (!targetId.startsWith('node-')) {
            targetId = nodeIdMap[targetId] || targetId;
          }
          
          loadedEdges.push({
            id: e.edge_id || sourceId + '-' + targetId,
            source: sourceId,
            target: targetId,
            type: 'custom',
            data: { edgeType: 'bezier', onDelete: (delId: string) => { setEdges((eds) => eds.filter((ee) => ee.id !== delId)); } },
          });
        }

        // 保存 dag_task_id
        if (savedDrawData.task?.dag_task_id) {
          setTaskId(savedDrawData.task.dag_task_id);
        }

        nodeIdCounter.current = loadedNodes.length;
        setNodes(loadedNodes);
        setEdges(loadedEdges);
        setIsLoading(false);
        isInitialized.current = true;
        setTimeout(() => { fitNodesToViewLeft(); }, 200);
        return;
      }

      // savedDrawData 为 null，使用会话中 DAG JSON
      if (!initialPipelineData || !initialPipelineData.nodes || initialPipelineData.nodes.length === 0) {
        console.log('savedDrawData 为 null，且 initialPipelineData 也没有数据');
        setIsLoading(false);
        return;
      }

      // 打印大模型返回的完整 JSON 数据
      console.log('========================================');
      console.log('=== 大模型返回的 DAG JSON 数据 ===');
      console.log('========================================');
      console.log('完整数据:', initialPipelineData);
      console.log('任务名称:', initialPipelineData.task.name);
      console.log('任务描述:', initialPipelineData.task.description);
      console.log('节点总数:', initialPipelineData.nodes.length);
      console.log('节点详情:');
      initialPipelineData.nodes.forEach((node, index) => {
        console.log(`  节点 ${index + 1}:`);
        console.log(`    node_name: ${node.node_name}`);
        console.log(`    skill_name: ${node.skill_name}`);
        console.log(`    params:`, JSON.stringify(node.params || {}, null, 4));
      });
      console.log('========================================');

      const pipelineNodes = initialPipelineData.nodes;

      const createdNodes: Node<NodeData>[] = [];
      const createdEdges: Edge[] = [];

      // 创建节点名称到节点ID的映射（用于解析引用关系）
      const nodeNameToIdMap: Record<string, string> = {};
      const nodeIdToOutputParamsMap: Record<string, any> = {};
      
      // 第一步：先拓扑排序，确定节点的层次位置
      // 1.1 构建节点关系图
      const nodeIndexToNodeName: string[] = [];
      const nodeNameToIndexMap: Record<string, number> = {};
      pipelineNodes.forEach((node, index) => {
        nodeIndexToNodeName.push(node.node_name);
        nodeNameToIndexMap[node.node_name] = index;
      });
      
      // 1.2 计算每个节点的入度和边关系
      const inDegree: number[] = new Array(pipelineNodes.length).fill(0);
      const nodeOutEdges: number[][] = new Array(pipelineNodes.length).fill(null).map(() => []);
      
      // 遍历所有节点的参数，构建图关系
      pipelineNodes.forEach((pNode, targetIndex) => {
        const dagParams = pNode.params || {};
        Object.values(dagParams).forEach((paramValue: any) => {
          if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
            const sourceNodeName = paramValue.source_node;
            const sourceIndex = nodeNameToIndexMap[sourceNodeName];
            
            if (sourceIndex !== undefined && sourceIndex !== targetIndex) {
              inDegree[targetIndex]++;
              nodeOutEdges[sourceIndex].push(targetIndex);
            }
          }
        });
      });
      
      // 1.3 拓扑排序，分层
      const levels: number[][] = [];
      const tempInDegree = [...inDegree];
      const processed = new Set<number>();
      
      // 找出起始节点（入度为0的节点）
      let currentLevel: number[] = [];
      for (let i = 0; i < pipelineNodes.length; i++) {
        if (tempInDegree[i] === 0 && !processed.has(i)) {
          currentLevel.push(i);
          processed.add(i);
        }
      }
      
      while (currentLevel.length > 0) {
        levels.push(currentLevel);
        
        // 处理下一层
        const nextLevel: number[] = [];
        currentLevel.forEach(index => {
          nodeOutEdges[index].forEach(targetIndex => {
            if (!processed.has(targetIndex)) {
              tempInDegree[targetIndex]--;
              if (tempInDegree[targetIndex] === 0) {
                nextLevel.push(targetIndex);
                processed.add(targetIndex);
              }
            }
          });
        });
        
        currentLevel = nextLevel;
      }
      
      // 处理未处理的节点（处理有环或其他情况）
      if (processed.size < pipelineNodes.length) {
        for (let i = 0; i < pipelineNodes.length; i++) {
          if (!processed.has(i)) {
            levels.push([i]);
          }
        }
      }
      
      // 1.4 构建节点索引到位置的映射 - 分层布局
      const nodeIndexToPositionMap: Record<number, { x: number; y: number }> = {};
      
      // 使用分层布局：按拓扑层级水平排列，同一层内多个节点（分支）垂直排列
      for (let levelIdx = 0; levelIdx < levels.length; levelIdx++) {
        const level = levels[levelIdx];
        level.forEach((nodeIndex, nodeInLevelIdx) => {
          nodeIndexToPositionMap[nodeIndex] = {
            x: START_X + levelIdx * (NODE_WIDTH + NODE_GAP),
            y: START_Y + nodeInLevelIdx * (NODE_HEIGHT + NODE_GAP)
          };
        });
      }

      // 第一步：先获取所有节点的算子信息，建立基础映射，收集output_params
      const nodeNameToZhName: Record<string, string> = {};
      for (let i = 0; i < pipelineNodes.length; i++) {
        const pNode = pipelineNodes[i];
        let skillId = pNode.skill_id || '';
        const skillName = pNode.skill_name;
        const nodeId = `node-${i + 1}`;
        nodeNameToIdMap[pNode.node_name] = nodeId;
        
        // 处理特殊算子名称，写死 skill_id
        if (skillName === 'source_stop') {
          skillId = 'cn.piflow.engine.local.source_file_stop.SourceFileStop';
          nodeNameToZhName[pNode.node_name] = '文件源';
          nodeNameToZhName['source_stop'] = '文件源';
          // source_stop 有输出参数，不调用接口
          nodeIdToOutputParamsMap[nodeId] = {
            params: [{
              name: 'output',
              type: 'string',
              param_name: 'output',
              param_type: 'String'
            }]
          };
        } else if (skillName === 'sink_stop') {
          skillId = 'cn.piflow.engine.local.file_save_stop.FileSaveStop';
          nodeNameToZhName[pNode.node_name] = '文件保存';
          nodeNameToZhName['sink_stop'] = '文件保存';
          // sink_stop 没有输出参数，不调用接口
          nodeIdToOutputParamsMap[nodeId] = { params: [] };
        } else {
          // 普通算子，调用接口获取信息
          try {
            const res = await getAllSkills(skillName);
            console.log(`请求算子详情 skillName=${skillName}:`, res);
            const skillData = extractSkillBySkillName(res, skillName);
            if (skillData) {
              const outputParams = skillData.output_params;
              nodeIdToOutputParamsMap[nodeId] = outputParams;
              // 优先使用 name_zh（中文名称），其次用 skillData.skill_name（如果是中文），否则回退英文 skillName
              const zhName = skillData.name_zh || skillData.skill_name || skillName;
              nodeNameToZhName[pNode.node_name] = zhName;
              // 再额外添加一个 key=skill_name 的映射，因为 DAG 引用中 source_node 可能是算子英文名
              nodeNameToZhName[skillName] = zhName;
              // 再添加 skill_id 作为 key，以防引用用算子ID
              if (skillData.skill_id) {
                nodeNameToZhName[skillData.skill_id] = zhName;
              }
            } else {
              nodeNameToZhName[pNode.node_name] = skillName;
              nodeNameToZhName[skillName] = skillName;
            }
          } catch (error) {
            console.error('获取算子库失败', error);
            nodeNameToZhName[pNode.node_name] = skillName;
            nodeNameToZhName[skillName] = skillName;
          }
        }
      }

      // 第二步：遍历创建完整节点，处理参数引用
        for (let i = 0; i < pipelineNodes.length; i++) {
        const pNode = pipelineNodes[i];
        let skillId = pNode.skill_id || '';
        const skillName = pNode.skill_name;
        let nodeName = pNode.node_name || '未命名节点';
        let nodeNameForOperator = pNode.skill_name || '';
        let nodeTypeForOperator = '';
        
        // 获取算子详情信息
        let inputParams = undefined;
        let outputParams = nodeIdToOutputParamsMap[`node-${i + 1}`];
        let iconPath = '';
        
        // 处理 DAG 节点的参数
        // params中每个属性是参数名，值可能是字符串或引用对象
        const dagParams = pNode.params || {};
        const nodeId = `node-${i + 1}`;

        console.log(`节点 ${nodeName} 的 DAG 参数:`, dagParams);
        
        // 构建 mergedInputParams
        let mergedInputParams;
        let skillDesc = '';
        
        // 对于 source_stop 和 sink_stop 特殊算子，使用fixArr中定义的参数结构，然后填入值
        if (skillName === 'source_stop') {
          skillId = 'cn.piflow.engine.local.source_file_stop.SourceFileStop';
          nodeTypeForOperator = 'input';
          
          // source_stop的输入参数只有file_path
          const sourceStopInputParams = [
            {
              name: "file_path",
              type: "string",
              param_name: "file_path",
              param_type: "String",
              value_mode: "manual",
              param_value: "",
              value_source: "local_file"
            }
          ];
          
          // 把DAG中的参数值填进去
          const newInputParamsList = sourceStopInputParams.map((paramDef) => {
            // 精确匹配：优先使用 paramDef.name 查找
            let paramValue = dagParams[paramDef.name];
            
            // 如果找不到，尝试使用 param_name 查找
            if (paramValue === undefined && paramDef.param_name) {
              paramValue = dagParams[paramDef.param_name];
            }
            
            if (paramValue !== undefined) {
              if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
                const sourceNodeName = paramValue.source_node;
                const sourceParamName = paramValue.source_param;
                
                return {
                  ...paramDef,
                  _refType: 'reference',
                  _value: '',
                  param_value: '',
                  _refValue: sourceParamName,
                  _sourceNodeName: nodeNameToZhName[sourceNodeName] || sourceNodeName,
                  _sourceParamName: sourceParamName,
                };
              } else {
                return {
                  ...paramDef,
                  _refType: 'manual',
                  _value: String(paramValue),
                  param_value: String(paramValue),
                  _refValue: '',
                };
              }
            } else {
                return {
                  ...paramDef,
                  _refType: 'manual',
                  _value: paramDef.param_value || paramDef.default_value || '',
                  param_value: paramDef.param_value || paramDef.default_value || '',
                  _refValue: '',
                };
              }
          });
          
          mergedInputParams = { params: newInputParamsList };
          
          // source_stop的输出参数是output
          outputParams = {
            params: [{
              name: 'output',
              type: 'string',
              param_name: 'output',
              param_type: 'String'
            }]
          };
          
          console.log(`节点 ${nodeName}: source_stop 特殊算子，使用fixArr定义的参数结构:`, mergedInputParams);
        } else if (skillName === 'sink_stop') {
          skillId = 'cn.piflow.engine.local.file_save_stop.FileSaveStop';
          nodeTypeForOperator = 'output';
          
          // 使用fixArr中定义的sink_stop参数结构
          const sinkStopParamDefs = [
            {
              name: "input",
              type: "string",
              param_name: "input",
              param_type: "String",
              value_mode: "manual",
              param_value: "",
              value_source: "local_file"
            },
            {
              name: "path",
              type: "string",
              param_name: "path",
              param_type: "String",
              value_mode: "manual",
              param_value: "",
              value_source: "local_file"
            },
            {
              name: "overwrite",
              type: "boolean",
              param_name: "overwrite",
              param_type: "Boolean",
              value_mode: "manual",
              param_value: true,
              value_source: "local_file"
            }
          ];
          
          // 把DAG中的参数值填进去
          const newParamsList = sinkStopParamDefs.map((paramDef) => {
            // 精确匹配：优先使用 paramDef.name 查找
            let paramValue = dagParams[paramDef.name];
            
            // 如果找不到，尝试使用 param_name 查找
            if (paramValue === undefined && paramDef.param_name) {
              paramValue = dagParams[paramDef.param_name];
            }
            
            if (paramValue !== undefined) {
              if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
                const sourceNodeName = paramValue.source_node;
                const sourceParamName = paramValue.source_param;
                
                return {
                  ...paramDef,
                  _refType: 'reference',
                  _value: '',
                  param_value: '', // 节点显示用
                  _refValue: sourceParamName,
                  _sourceNodeName: nodeNameToZhName[sourceNodeName] || sourceNodeName,
                  _sourceParamName: sourceParamName,
                };
              } else {
                return {
                  ...paramDef,
                  _refType: 'manual',
                  _value: String(paramValue),
                  param_value: String(paramValue), // 节点显示用
                  _refValue: '',
                };
              }
            } else {
              return {
                ...paramDef,
                _refType: 'manual',
                _value: paramDef.param_value || paramDef.default_value || '',
                param_value: paramDef.param_value || paramDef.default_value || '', // 节点显示用
                _refValue: '',
              };
            }
          });
          
          mergedInputParams = { params: newParamsList };
          
          console.log(`节点 ${nodeName}: sink_stop 特殊算子，使用fixArr定义的参数结构:`, mergedInputParams);
        } else {
          // 普通算子，调用接口获取参数信息并合并
          try {
            const res = await getAllSkills(skillName);
            const skillData = extractSkillBySkillName(res, skillName);
            if (skillData) {
              inputParams = skillData.input_params;
              if (!outputParams) {
                outputParams = skillData.output_params;
              }
              skillId = skillData.skill_id;
              iconPath = skillData.icon_path || '';
              skillDesc = skillData.description || '';
              // 使用算子中文名称填充 operatorZh；不修改节点 label
              if (skillData.name_zh) {
                // 只更新 operatorZh 显示用，不替换 nodeName（保持节点展示名）
              }
              if (skillData.skill_name) {
                nodeNameForOperator = skillData.skill_name;
              }
              if (skillData.skill_type) {
                nodeTypeForOperator = skillData.skill_type;
              }
              // 将从API得到的中文算子名称写入 operatorZh 映射，确保节点 data.operatorZh 使用中文
              if (skillData.name_zh) {
                nodeNameToZhName[pNode.node_name] = skillData.name_zh;
              }
            }
          } catch (error) {
            console.error('获取算子库失败', error);
          }

          console.log(`节点 ${nodeName} 的算子 input_params:`, inputParams);
          console.log(`节点 ${nodeName} 的 output_params:`, outputParams);

          // 构建 mergedInputParams：合并DAG 参数到算子的 input_params
          mergedInputParams = inputParams;
          if (inputParams?.params && Array.isArray(inputParams.params)) {
            // 先构建算子参数的 map，方便查找
            const paramDefMap: Record<string, any> = {};
            inputParams.params.forEach((paramDef: any) => {
              paramDefMap[paramDef.name] = paramDef;
            });
            
            // 调试日志：打印 DAG 参数和算子参数定义
            console.log(`[DEBUG] 节点 ${nodeName}: DAG params =`, dagParams);
            console.log(`[DEBUG] 节点 ${nodeName}: 算子 paramDefs =`, inputParams.params.map((p: any) => ({ name: p.name, default_value: p.default_value, param_value: p.param_value })));
            
            const newParamsList: any[] = [];
            
            // 先处理算子中定义的参数
            inputParams.params.forEach((paramDef: any) => {
              // 精确匹配：优先使用 paramDef.name 查找
              let paramValue = dagParams[paramDef.name];
              
              // 调试日志：显示每个参数的查找结果
              console.log(`[DEBUG] 节点 ${nodeName}: 参数 "${paramDef.name}" -> dagParams["${paramDef.name}"] =`, paramValue, `(类型:${typeof paramValue})`);
              
              // 如果找不到，尝试使用 param_name 查找
              if (paramValue === undefined && paramDef.param_name) {
                paramValue = dagParams[paramDef.param_name];
                console.log(`[DEBUG] 节点 ${nodeName}: 参数 "${paramDef.name}" 通过 param_name 查找 -> dagParams["${paramDef.param_name}"] =`, paramValue);
              }
              
              // 如果 DAG 参数中有这个参数，则使用 DAG 参数的值
              if (paramValue !== undefined) {
                // 判断参数值类型
                if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
                  // 引用类型：{source_node: "节点名", source_param: "输出参数名"}
                  const sourceNodeName = paramValue.source_node;
                  const sourceParamName = paramValue.source_param;
                  
                  // 使用 JSON 中原始的 source_param 值作为引用值
                  // 不进行转换，保持与 JSON 内容一致
                  const refValue = sourceParamName;
                  
                  newParamsList.push({
                    ...paramDef,
                    _refType: 'reference',
                    _value: '',
                    _refValue: refValue,
                    _sourceNodeName: nodeNameToZhName[sourceNodeName] || sourceNodeName,
                    _sourceParamName: sourceParamName,
                  });
                } else {
                  // 手动类型：字符串、数字、布尔等
                  console.log(`[DEBUG] 节点 ${nodeName}: 参数 "${paramDef.name}" 使用 DAG 值 "${String(paramValue)}"`);
                  newParamsList.push({
                    ...paramDef,
                    _refType: 'manual',
                    _value: String(paramValue),
                    _refValue: '',
                  });
                }
              } else {
                // DAG 参数中没有这个参数，使用默认值
                console.log(`[DEBUG] 节点 ${nodeName}: 参数 "${paramDef.name}" 未在 DAG 中找到，使用默认值 "${paramDef.param_value || paramDef.default_value || ''}"`);
                newParamsList.push({
                  ...paramDef,
                  _refType: 'manual',
                  _value: paramDef.param_value || paramDef.default_value || '',
                  _refValue: '',
                });
              }
            });
            
            // 不再处理DAG中有但算子中没有的参数
            // 只保留算子定义中存在的参数，DAG中多余的参数将被忽略
            
            mergedInputParams = {
              ...inputParams,
              params: newParamsList,
            };
          } else if (Object.keys(dagParams).length > 0) {
            // 如果算子没有定义 input_params，但 DAG 有参数，则创建 input_params
            const dagParamsList = Object.entries(dagParams).map(([name, value]) => {
              if (typeof value === 'object' && value !== null && 'source_node' in value) {
                const sourceNodeName = value.source_node;
                const sourceParamName = value.source_param;
                
                // _refValue是纯参数名，和option.value匹配
                let refValue = sourceParamName;
                
                return {
                  name: name,
                  type: 'string',
                  param_name: name,
                  param_type: 'String',
                  param_value: '',
                  _refType: 'reference',
                  _value: '',
                  _refValue: refValue,
                  _sourceNodeName: nodeNameToZhName[sourceNodeName] || sourceNodeName,
                  _sourceParamName: sourceParamName,
                };
              } else {
                return {
                  name: name,
                  type: 'string',
                  param_name: name,
                  param_type: 'String',
                  param_value: '',
                  _refType: 'manual',
                  _value: String(value),
                  _refValue: '',
                };
              }
            });
            mergedInputParams = { params: dagParamsList };
          }
        }

        const newNode: Node<NodeData> = {
          id: nodeId,
          type: 'custom',
          position: nodeIndexToPositionMap[i] || {
            x: START_X + (NODE_WIDTH + NODE_GAP) * i,
            y: START_Y,
          },
          data: {
            label: nodeName,
            icon: iconPath,
            operatorId: skillId,
            operatorName: nodeNameForOperator || '',
            // 优先从映射表中查找中文名称：尝试 node_name 和 skill_name 两个 key
            operatorZh: nodeNameToZhName[pNode.node_name] || nodeNameToZhName[skillName] || '',
            operatorType: nodeTypeForOperator,
            description: skillDesc,
            params: dagParams,
            inputVar: 'input_data',
            outputVar: 'output_data',
            input_params: mergedInputParams,
            output_params: outputParams,
            onDelete: (delId: string) => {
              setSelectedNodeId(delId);
              setShowDeleteModal(true);
            },
            onUpdateParams: (updId: string, params: Record<string, any>) => {
              setNodes((nds) =>
                nds.map((n) => {
                  if (n.id === updId) {
                    return { ...n, data: { ...n.data, params } };
                  }
                  return n;
                })
              );
            },
            onSelect: (selId: string) => {
              setSelectedNodeId(selId);
              setShowOperatorModal(false);
            },
          },
        };
        createdNodes.push(newNode);

        // 创建边：根据 params 中的引用关系创建连线
        for (const [paramKey, paramValue] of Object.entries(dagParams)) {
          if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
            const sourceNodeName = paramValue.source_node;
            const sourceNodeId = nodeNameToIdMap[sourceNodeName];
            if (sourceNodeId && sourceNodeId !== nodeId) {
              // 检查是否已存在这条连线
              const edgeExists = createdEdges.some(
                e => e.source === sourceNodeId && e.target === nodeId
              );
              if (!edgeExists) {
                createdEdges.push({
                  id: `edge-${sourceNodeId}-${nodeId}`,
                  source: sourceNodeId,
                  target: nodeId,
                  type: 'custom',
                  data: { 
                    edgeType: 'bezier', 
                    onDelete: (delId: string) => {
                      setEdges((eds) => eds.filter((e) => e.id !== delId));
                    }
                  },
                });
              }
            }
          }
        }
      }

      console.log('创建的节点', createdNodes);
      console.log('创建的边:', createdEdges);

      nodeIdCounter.current = pipelineNodes.length;
      setNodes(createdNodes);
      setEdges(createdEdges);
      setIsLoading(false);
      isInitialized.current = true;

      setTimeout(() => {
        fitNodesToViewLeft();
      }, 200);
    };

    loadInitialPipeline();
  }, [initialPipelineData, savedDrawData]);

  // 模拟请求后端接口获取画板数据
  useEffect(() => {
    // 模拟 API 请求，延迟返回数据
    // setTimeout(() => {
    //   // 模拟从后端获取的画板数据
    //   const fetchedNodes = [
    //     {
    //       id: 'node-1',
    //       type: 'custom',
    //       position: { x: 50, y: 200 },
    //       data: {
    //         label: '文件上传',
    //         icon: 'Upload',
    //         operatorId: 'file-upload',
    //         description: 'CSV文件',
    //         params: { filePath: '/data/input.csv', encoding: 'utf8' },
    //         inputVar: undefined,
    //         outputVar: 'records: 1,204',
    //       },
    //     },
    //     {
    //       id: 'node-2',
    //       type: 'custom',
    //       position: { x: 350, y: 200 },
    //       data: {
    //         label: '空行清洗',
    //         icon: 'Eraser',
    //         operatorId: 'empty-clean',
    //         description: '去除空行',
    //         params: { cleanMode: 'all' },
    //         inputVar: 'data_stream',
    //         outputVar: 'cleaned_data',
    //       },
    //     },
    //     {
    //       id: 'node-3',
    //       type: 'custom',
    //       position: { x: 650, y: 200 },
    //       data: {
    //         label: '空格清洗',
    //         icon: 'Type',
    //         operatorId: 'space-clean',
    //         description: '去除多余空格',
    //         params: { spaceMode: 'trim' },
    //         inputVar: 'cleaned_data',
    //         outputVar: 'trimmed_data',
    //       },
    //     },
    //     {
    //       id: 'node-4',
    //       type: 'custom',
    //       position: { x: 950, y: 200 },
    //       data: {
    //         label: '年份排序',
    //         icon: 'Calendar',
    //         operatorId: 'year-sort',
    //         description: '按年份升序',
    //         params: { sortField: 'year', sortOrder: 'asc' },
    //         inputVar: 'trimmed_data',
    //         outputVar: 'sorted_data',
    //       },
    //     },
    //   ];

    //   const fetchedEdges = [
    //     { id: 'edge-1', source: 'node-1', target: 'node-2', type: 'custom', data: { edgeType: 'bezier' } },
    //     { id: 'edge-2', source: 'node-2', target: 'node-3', type: 'custom', data: { edgeType: 'bezier' } },
    //     { id: 'edge-3', source: 'node-3', target: 'node-4', type: 'custom', data: { edgeType: 'bezier' } },
    //   ];

    //   console.log('从后端获取画板数据', { nodes: fetchedNodes, edges: fetchedEdges });

    //   // 获取最大节点ID，用于后续新增节点
    //   nodeIdCounter.current = getMaxNodeId(fetchedNodes);

    //   // 为节点和连线添加回调函数
    //   const nodesWithCallbacks = fetchedNodes.map((node) => ({
    //     ...node,
    //     data: {
    //       ...node.data,
    //       onDelete: (id: string) => {
    //         setNodes((nds) => nds.filter((n) => n.id !== id));
    //         setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
    //       },
    //       onUpdateParams: (id: string, params: Record<string, any>) => {
    //         setNodes((nds) =>
    //           nds.map((n) => {
    //             if (n.id === id) {
    //               return { ...n, data: { ...n.data, params } };
    //             }
    //             return n;
    //           })
    //         );
    //       },
    //       onSelect: (id: string) => setSelectedNodeId(id),
    //       onUpdateLabel: (id: string, label: string) => {
    //         const otherLabels = nodes.filter(n => n.id !== id).map(n => n.data.label);
    //         let finalLabel = label;
    //         if (otherLabels.includes(label)) {
    //           let counter = 1;
    //           while (otherLabels.includes(`${label}_${counter}`)) {
    //             counter++;
    //           }
    //           finalLabel = `${label}_${counter}`;
    //         }
    //         setNodes((nds) =>
    //           nds.map((n) => {
    //             if (n.id === id) {
    //               return { ...n, data: { ...n.data, label: finalLabel } };
    //             }
    //             return n;
    //           })
    //         );
    //       },
    //     },
    //   }));

    //   const edgesWithCallbacks = fetchedEdges.map((edge) => ({
    //     ...edge,
    //     data: {
    //       edgeType: edge.data?.edgeType || 'bezier',
    //       onDelete: (id: string) => {
    //         setEdges((eds) => eds.filter((e) => e.id !== id));
    //       },
    //     },
    //   }));

    //   setNodes(nodesWithCallbacks);
    //   setEdges(edgesWithCallbacks);
    // 模拟请求 /suanzi 接口获取算子数据
    getAllSkills().then(resAllSkills=>{
      console.log('getAllSkills 返回结果:', resAllSkills);
      if(resAllSkills.code === 200){
        console.log('resAllSkills.result.data:', resAllSkills.result.data);
       let fixArr=[
           {
              groupName: "基础",
              "DagSkillInfoList": [
                  {
                      id: 9999999999998,
                      skill_id: "cn.piflow.engine.local.source_file_stop.SourceFileStop",
                      skill_name: "文件源",
                      name_zh: "文件源",
                      version: "1.0.0",
                      description: "本skill是用于文件源",
                      file_path: "",
                      input_params: {
                          params: [
                              {
                                  name: "filePath",
                                  type: "string",
                                  param_name: "filePath",
                                  param_type: "String",
                                  value_mode: "manual",
                                  param_value: "workspace/temp/森林每木调查数据-blank-line-space.csv",
                                  value_source: "local_file"
                              },
                              {
                                  name: "output",
                                  type: "string",
                                  param_name: "filePath",
                                  param_type: "String",
                                  value_mode: "manual",
                                  param_value: "workspace/outputs/森林每木调查数据-blank-space.csv",
                                  value_source: "local_file"
                              }
                          ]
                      },
                      output_params: {
                          params: [

                          ]
                      },
                      skill_type: "",
                      language: "",
                      command: "",
                      icon_path: "",
                      create_time: "",
                      update_time: "",
                      is_deleted: 0
                  },
                  {
                      id: 9999999999999,
                      skill_id: "cn.piflow.engine.local.file_save_stop.FileSaveStop",
                      skill_name: "文件保存",
                      name_zh: "文件保存",
                      version: "1.0.0",
                      description: "本skill是用于文件保存",
                      file_path: "",
                      input_params: {
                          params: [
                              {
                                  name: "path",
                                  type: "string",
                                  param_name: "path",
                                  param_type: "String",
                                  value_mode: "manual",
                                  param_value: "workspace/temp/森林每木调查数据-blank-line-space.csv",
                                  value_source: "local_file"
                              },
                              {
                                  name: "overwrite",
                                  type: "boolean",
                                  param_name: "overwrite",
                                  param_type: "Boolean",
                                  value_mode: "manual",
                                  param_value: true,
                                  value_source: "local_file"
                              }
                          ]
                      },
                      output_params: {
                          params: [

                          ]
                      },
                      skill_type: "",
                      language: "",
                      command: "",
                      icon_path: "",
                      create_time: "",
                      update_time: "",
                      is_deleted: 0
                  }
              ]
          }
        ]
        const finalList = fixArr.concat(resAllSkills.result.data);
        console.log('设置 operatorList，finalList:', finalList);
        // 打印第一个算子的信息
        if(finalList.length > 0 && finalList[0].DagSkillInfoList.length > 0) {
          console.log('第一个算子信息:', finalList[0].DagSkillInfoList[0]);
        }
        setOperatorList(finalList);
        isInitialized.current = true;
      }
    })
  }, []);

  const onConnect = useCallback(
    (connection: Connection) => {
      const edge = {
        ...connection,
        type: 'custom',
        data: {
          edgeType,
          onDelete: (id: string) => {
            setEdges((eds) => eds.filter((e) => e.id !== id));
          },
        },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges, edgeType]
  );

  // 获取引用类型的数据源列表（直接从上游节点的 output_params 获取）
  const fetchReferenceOptions = useCallback(async (currentNodeId: string) => {
    setIsLoadingReferences(true);
    setReferenceOptions([]);

    console.log('=== fetchReferenceOptions 被调用 ===', {
      currentNodeId,
      nodes: nodes.map(n => ({ id: n.id, label: n.data.label, has_output_params: !!n.data.output_params?.params })),
      edges,
    });

    // 找到指向当前节点的所有上游节点（通过 edges 的 target 和 source）
    const upstreamNodeIds = edges
      .filter((e) => e.target === currentNodeId)
      .map((e) => e.source);

    console.log('上游节点ID:', upstreamNodeIds);

    if (upstreamNodeIds.length === 0) {
      setIsLoadingReferences(false);
      return;
    }

    // 直接从上游节点的 output_params 获取出参
    const upstreamNodes = nodes.filter((n) => upstreamNodeIds.includes(n.id));
    console.log('上游节点:', upstreamNodes.map(n => ({ id: n.id, output_params: n.data.output_params })));
    
    const allOutputParams: { name: string; type: string; description: string; nodeId: string; nodeName: string }[] = [];
    
    upstreamNodes.forEach((upstreamNode) => {
      console.log(`检查上游节点 ${upstreamNode.id} 的 output_params:`, upstreamNode.data.output_params);

      // 获取上游节点的中文显示名
      const zhName = upstreamNode.data.operatorZh || upstreamNode.data.operatorName || upstreamNode.data.label || '';

      // 优先从 output_params 获取
      if (upstreamNode.data.output_params?.params && upstreamNode.data.output_params.params.length > 0) {
        upstreamNode.data.output_params.params.forEach((param: any) => {
          const paramName = param.name || param.param_name || '';
          const paramType = param.type || param.param_type || 'string';
          allOutputParams.push({
            name: paramName,
            type: paramType,
            description: param.description || '',
            nodeId: upstreamNode.id,
            nodeName: zhName,
          });
        });
      } else {
        // 如果没有 output_params，检查 input_params（处理 source_stop 等特殊算子）
        console.log(`上游节点 ${upstreamNode.id} 没有 output_params，检查 input_params:`, upstreamNode.data.input_params);
        if (upstreamNode.data.input_params?.params) {
          // 查找名为 "output" 的参数
          const outputParam = upstreamNode.data.input_params.params.find(
            (p: any) => (p.name || p.param_name) === 'output'
          );
          if (outputParam) {
            const paramName = outputParam.name || outputParam.param_name || 'output';
            const paramType = outputParam.type || outputParam.param_type || 'string';
            allOutputParams.push({
              name: paramName,
              type: paramType,
              description: outputParam.description || '',
              nodeId: upstreamNode.id,
              nodeName: zhName,
            });
          } else {
            // 如果也找不到 output 参数，创建一个默认的 output 参数
            allOutputParams.push({
              name: 'output',
              type: 'string',
              description: '',
              nodeId: upstreamNode.id,
              nodeName: zhName,
            });
          }
        }
      }
    });

    setReferenceOptions(allOutputParams);
    console.log('引用变量选项:', allOutputParams);
    setIsLoadingReferences(false);
  }, [edges, nodes]);

  // 当选中节点时，获取上游节点的出参数据（用于来源下拉选择）
  useEffect(() => {
    if (selectedNodeId) {
      fetchReferenceOptions(selectedNodeId);
    }
  }, [selectedNodeId, fetchReferenceOptions]);

  // 辅助函数:生成唯一的节点名称
  const generateUniqueLabel = useCallback((baseName: string): string => {
    const existingLabels = nodes.map((n) => n.data.label);
    if (!existingLabels.includes(baseName)) {
      return baseName;
    }
    let counter = 1;
    let newLabel = `${baseName}_${counter}`;
    while (existingLabels.includes(newLabel)) {
      counter += 1;
      newLabel = `${baseName}_${counter}`;
    }
    return newLabel;
  }, [nodes]);

  const handleAddNode = useCallback(
    async (operator: { skill_id: string; skill_name: string; name_zh: string; icon_path: string; skill_type: string; description?: string }, position?: { x: number; y: number }) => {
      console.log('handleAddNode 被调用，operator 数据:', operator);
      nodeIdCounter.current += 1;
      const uniqueLabel = generateUniqueLabel(operator.name_zh);

      // 请求算子详情获取 input_params 和 output_params
      let inputParams = undefined;
      let outputParams = undefined;
      let operatorIconPath = operator.icon_path;
      let operatorDescription = operator.description || '';
      try {
        console.log('请求算子详情，skill_id:', operator.skill_id);
        const res = await listSkillsDetails(operator.skill_id);
        console.log('算子详情返回结果:', res);
        if (res.result) {
          inputParams = res.result.input_params;
          outputParams = res.result.output_params;
          operatorIconPath = res.result.icon_path || operatorIconPath;
          operatorDescription = res.result.description || operatorDescription;
          console.log('最终使用的图标路径:', operatorIconPath);
          console.log('最终使用的描述:', operatorDescription);
        }
      } catch (error) {
        console.error('获取算子详情失败:', error);
      }
      
      // 检查是否有 required 字段，没有的话用 getAllSkills 回退
      const hasRequiredField = inputParams?.params?.some((p: any) => p.required !== undefined);
      if (!hasRequiredField) {
        try {
          const listRes = await getAllSkills(operator.skill_name);
          const skillData = extractSkillBySkillName(listRes, operator.skill_name) || extractSkillBySkillName(listRes, operator.skill_id);
          if (skillData?.input_params?.params?.some((p: any) => p.required !== undefined)) {
            inputParams = skillData.input_params;
            outputParams = skillData.output_params || outputParams;
            operatorIconPath = skillData.icon_path || operatorIconPath;
            console.log('handleAddNode: 使用 getAllSkills 参数模板 (含 required):', inputParams);
          }
        } catch (e) { console.error('handleAddNode: getAllSkills 失败:', e); }
      }
      
      // 计算新节点的位置
      let newPosition = position;
      if (!newPosition) {
        // 获取当前视图信息
        const currentViewport = getViewport();
        const wrapperEl = reactFlowWrapper.current;
        const containerW = wrapperEl?.clientWidth || window.innerWidth;
        const containerH = wrapperEl?.clientHeight || window.innerHeight;
        // 计算视图中心在画布上的坐标
        const viewCenterX = (containerW / 2 - currentViewport.x) / currentViewport.zoom;
        const viewCenterY = (containerH / 2 - currentViewport.y) / currentViewport.zoom;
        
        // 检查是否会与现有节点重叠，如果重叠则偏移
        let offsetX = 0;
        let offsetY = 0;
        let attempt = 0;
        const maxAttempts = 50;
        
        while (attempt < maxAttempts) {
          const testX = viewCenterX - NODE_WIDTH / 2 + offsetX;
          const testY = viewCenterY - 70 + offsetY;
          
          // 检查是否与现有节点重叠
          const overlaps = nodes.some(node => {
            const nodeRight = node.position.x + NODE_WIDTH;
            const nodeBottom = node.position.y + NODE_HEIGHT;
            const testRight = testX + NODE_WIDTH;
            const testBottom = testY + NODE_HEIGHT;
            
            return !(testRight < node.position.x || testX > nodeRight || 
                     testBottom < node.position.y || testY > nodeBottom);
          });
          
          if (!overlaps) {
            newPosition = { x: testX, y: testY };
            break;
          }
          
          // 螺旋式偏移
          offsetX += (attempt % 2 === 0 ? 1 : -1) * (NODE_GAP * Math.floor(attempt / 2 + 1));
          if (attempt % 2 === 1) {
            offsetY += NODE_GAP;
          }
          attempt++;
        }
        
        // 如果所有尝试都失败，使用原始位置
        if (!newPosition) {
          newPosition = {
            x: viewCenterX - NODE_WIDTH / 2,
            y: viewCenterY - 70,
          };
        }
      }
      
      const newNode: Node<NodeData> = {
        id: `node-${nodeIdCounter.current}`,
        type: 'custom',
        position: newPosition,
        data: {
          label: uniqueLabel,
          icon: operatorIconPath,
          operatorId: operator.skill_id,
          operatorName: operator.skill_name || '',
          operatorZh: operator.name_zh || '',
          operatorType: operator.skill_type || '',
          description: operatorDescription,
          params: {},
          inputVar: 'input_data',
          outputVar: 'output_data',
          input_params: inputParams,
          output_params: outputParams,
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
          onSelect: (id: string) => {
            setSelectedNodeId(id);
            setShowOperatorModal(false);
          },
          onUpdateLabel: (id: string, label: string) => {
            // 获取当前节点以外的所有节点标签
            const otherLabels = nodes.filter(n => n.id !== id).map(n => n.data.label);

            // 生成唯一名称（如果冲突则添加后缀）
            let finalLabel = label;
            if (otherLabels.includes(label)) {
              let counter = 1;
              while (otherLabels.includes(`${label}_${counter}`)) {
                counter++;
              }
              finalLabel = `${label}_${counter}`;
            }

            setNodes((nds) =>
              nds.map((n) => {
                if (n.id === id) {
                  return { ...n, data: { ...n.data, label: finalLabel } };
                }
                return n;
              })
            );
          },
        },
      };
      
      // 添加新节点
      setNodes((nds) => [...nds, newNode]);
      
      // 自动调整视图，将新节点放到视野中心（保持当前缩放级别）
      setTimeout(() => {
        const currentViewport = getViewport();
        const wrapperEl = reactFlowWrapper.current;
        const containerW = wrapperEl?.clientWidth || window.innerWidth;
        const containerH = wrapperEl?.clientHeight || window.innerHeight;
        // 计算新节点的中心点
        const nodeCenterX = newPosition.x + NODE_WIDTH / 2;
        const nodeCenterY = newPosition.y + 70;
        // 计算需要移动的偏移量
        const targetX = containerW / 2 - nodeCenterX * currentViewport.zoom;
        const targetY = containerH / 2 - nodeCenterY * currentViewport.zoom;
        // 使用 setViewport 移动视图，保持当前的缩放级别
        setViewport(
          {
            x: targetX,
            y: targetY,
            zoom: currentViewport.zoom,
          },
          { duration: 500 }
        );
      }, 100);
    },
    [setNodes, setEdges, nodes, generateUniqueLabel, getViewport, setViewport]
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

  // 自动保存画板数据
  useEffect(() => {
    // 跳过首次渲染（初始化时不需要保存）
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    // 跳过未初始化的状态
    if (!isInitialized.current) return;

    // 防抖：清除上一次的定时器
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    // 设置新的定时器，800ms 后执行保存
    autoSaveTimerRef.current = setTimeout(async () => {
      // 检查nodes 中是否有引用类型的参数
      console.log('=== 保存前检查===');
      console.log('edges 数量:', edges.length);
      console.log('edges:', edges);
      console.log('nodes:', nodes.map(n => ({ id: n.id, label: n.data.label })));
      
      console.log('=== 保存前检查nodes ===');
      nodes.forEach(node => {
        console.log('Node:', node.id, 'Icon:', node.data.icon);
        if (node.data.input_params?.params) {
          node.data.input_params.params.forEach(param => {
            console.log('Node:', node.id, 'Param:', param.name, '_refType:', param._refType, '_refValue:', param._refValue);
          });
        }
      });
      
      // 预生成所有引用参数的 binding 映射：nodeId|paramName -> binding 对象
      const bindingMap: Record<string, any> = {};
      nodes.forEach(node => {
        if (node.data.input_params?.params) {
          node.data.input_params.params.forEach(param => {
            if (param._refType === 'reference') {
              const upstreamEdge = edges.find(e => e.target === node.id);
              if (upstreamEdge) {
                let refParamName = param._refValue;
                if (!refParamName) {
                  const upstreamNode = nodes.find(n => n.id === upstreamEdge.source);
                  refParamName = upstreamNode?.data.output_params?.params?.[0]?.name || '';
                } else if (String(refParamName).includes('（')) {
                  refParamName = String(refParamName).split('（')[0];
                } else if (String(refParamName).includes('_') && !String(refParamName).startsWith('node-')) {
                  const parts = String(refParamName).split('_');
                  if (parts.length > 1 && parts[0].startsWith('node-')) {
                    refParamName = parts[parts.length - 1];
                  }
                }
                const bid = generateUUID();
                const key = `${node.id}|${param.name}`;
                bindingMap[key] = {
                  binding_id: bid,
                  from_node_id: upstreamEdge.source,
                  from_param_name: String(refParamName ?? '').trim() || param.name,
                  to_node_id: node.id,
                  to_param_name: param.name || '',
                };
              }
            }
          });
        }
      });
      
      // 构造请求参数（按照接口文档结构）
      const nodesToSave = nodes
            .filter(n => n.type !== 'comment')
            .map(n => ({
              node_id: n.id,
              node_name: n.data.label,
              node_type: 'default',
              icon_path: n.data.icon || '',
              skill: {
                skill_id: n.data.operatorId,
                skill_name: n.data.operatorName || '',
                name_zh: n.data.operatorZh || '',
                version: '1.0',
              },
              position: {
                x: n.position.x,
                y: n.position.y,
              },
              input_params: (n.data.input_params?.params || [])
                .filter(p => {
                  if (p._refType === 'reference') return true;
                  const val = String(p._value ?? p.param_value ?? '');
                  return val.trim() !== '';
                })
                .map(p => {
                  const isReference = p._refType === 'reference';
                  const savedValue = isReference ? (p._refValue || '') : (p._value || '');
                  const bindingKey = `${n.id}|${p.name}`;
                  const existingBinding = bindingMap[bindingKey];
                  return {
                    param_name: p.name,
                    param_value: savedValue,
                    value_mode: isReference ? 'reference' : 'manual',
                    binding_id: isReference ? (existingBinding?.binding_id || generateUUID()) : '',
                  };
                }),
              out_params: n.data.output_params?.params?.map(p => ({
                param_name: p.name || p.param_name || '',
                param_type: p.type || p.param_type || 'string',
              })) || [],
            }));
      console.log('准备保存的 nodes 数据:', nodesToSave);
      const params = {
        dsl_version: "1.0",
        task: {
          dag_task_id: taskId || '',
          dag_task_name: taskName,
          description: taskDescription,
          message_id: messageId || ''
        },
        nodes: nodesToSave,
        edges: edges.map(e => ({
          edge_id: e.id,
          from_node_id: e.source,
          to_node_id: e.target,
        })),
        bindings: Object.values(bindingMap)
      };

      try {
        const res = await saveDrawInfo(params);
        if (res.code === 200) {
          setTaskId(res.result?.dag_task_id || '');
          setSaveMessage('保存成功！');
          setTimeout(() => setSaveMessage(''), 2000);
        } else {
          setSaveMessage('保存失败：' + (res.message || '未知错误'));
          setTimeout(() => setSaveMessage(''), 3000);
        }
      } catch (error) {
        console.error('保存失败:', error);
        setSaveMessage('保存失败：网络错误');
        setTimeout(() => setSaveMessage(''), 3000);
      }
      
      setIsSaving(false);
    }, 800);
  }, [nodes, edges, taskId, messageId]);

  return (
    <div className="draw-container">
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      )}
      
      {/* 头部区域 */}
      <div className="flow-header">
        <div className="header-left">
          <h2>画板编辑</h2>
          <div className="task-info">
            <div className="task-name">
              <span className="value">{taskName}</span>
            </div>
            <div className="task-description">
              <span className="value">{taskDescription}</span>
            </div>
          </div>
        </div>
        <div className="header-right">
          {/* <button 
            className="export-btn"
            onClick={() => {
              if (initialPipelineData) {
                const jsonStr = JSON.stringify(initialPipelineData, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `${taskName || 'dag'}_${Date.now()}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
              } else {
                alert('没有可导出的JSON数据');
              }
            }}
            title="导出JSON"
          >
            <Download size={16} />
            <span>导出JSON</span>
          </button> */}
          <button className="sync-back-btn" onClick={() => {
            // 校验必填参数
            for (const n of nodes) {
              if (n.type === 'comment') continue;
              const params = n.data.input_params?.params || [];
              console.log('params',params)
              for (const p of params) {
                if (p.required) {
                  const val = String(p._value ?? p.param_value ?? p._refValue ?? p.value ?? '');
                  if (!val.trim()) {
                    alert(`节点「${n.data.label}」的必填参数「${p.name}」未填写，请完善后再同步`);
                    return;
                  }
                }
              }
            }

            // 构造完整的画板JSON数据
            const drawData = {
              dsl_version: "1.0",
              task: {
                dag_task_id: taskId || '',
                dag_task_name: taskName,
                description: taskDescription,
                message_id: messageId || ''
              },
              nodes: nodes
                .filter(n => n.type !== 'comment')
                .map(n => ({
                  node_id: n.id,
                  node_name: n.data.label,
                  node_type: 'default',
                  icon_path: n.data.icon || '',
                  skill: {
                    skill_id: n.data.operatorId,
                    version: '1.0',
                  },
                  position: {
                    x: n.position.x,
                    y: n.position.y,
                  },
                  input_params: (n.data.input_params?.params || [])
                    .filter(p => {
                      if (p._refType === 'reference') return true;
                      const val = String(p._value ?? p.param_value ?? '');
                      return val.trim() !== '';
                    })
                    .map(p => {
                      const isReference = p._refType === 'reference';
                      return {
                        param_name: p.name,
                        param_value: isReference ? '' : (p._value || ''),
                        value_mode: isReference ? 'reference' : 'manual',
                        binding_id: isReference ? generateUUID() : '',
                      };
                    }),
                  out_params: n.data.output_params?.params?.map(p => ({
                    param_name: p.name || p.param_name || '',
                    param_type: p.type || p.param_type || 'string',
                  })) || [],
                })),
              edges: edges.map(e => ({
                edge_id: e.id,
                from_node_id: e.source,
                to_node_id: e.target,
              })),
            };
            
            // 合并指令和画板数据为一条消息发送（带隐藏标记），避免触发两次 /message/create
            const combinedContent = '[HIDDEN]我手动修改了任务流程，请根据任务流程重新生成dag JSON，不要执行\n\n' + JSON.stringify(drawData);
            window.dispatchEvent(new CustomEvent('flow:send-message', { 
              detail: { 
                threadId, 
                messageId, 
                content: combinedContent,
                hidden: true
              } 
            }));
            onClose();
          }}>
            同步并返回对话
          </button>
          <button className="only-back-btn" onClick={() => {
            setNodes([]);
            setEdges([]);
            onClose();
          }}>
            仅返回对话
          </button>
        </div>
      </div>
      
      <ReactFlow
        ref={reactFlowWrapper}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        className="react-flow-container"
        defaultViewport={{ zoom: 1, x: 0, y: 0 }}
        minZoom={0.2}
        maxZoom={2}
        deleteKeyCode={null}
        onDrop={(e) => {
          e.preventDefault();
          const operatorData = e.dataTransfer.getData('application/json');
          if (operatorData) {
            try {
              const operator = JSON.parse(operatorData);
              const position = screenToFlowPosition({ x: e.clientX, y: e.clientY });
              handleAddNode(operator, position);
            } catch (error) {
              console.error('解析拖拽数据失败:', error);
            }
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={36} size={1.5} />
      </ReactFlow>

      <FloatingToolbar
        onOpenOperatorLibrary={() => setIsOperatorLibraryOpen(true)}
        onAddComment={handleAddComment}
        zoom={zoomLevel}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onResetView={() => fitNodesToViewLeft()}
        edgeType={edgeType}
        onEdgeTypeChange={setEdgeType}
      />

      {/* 右侧参数配置面板 - 新样式 */}
      {selectedNode && (
        <div className="draw-config-panel">
          {/* 关闭按钮 */}
          <div className="closeCon">
            <div className="draw-config-close">
              <X size={18} onClick={closeConfigPanel} />
              {/* <button className="draw-config-close" onClick={closeConfigPanel}>
                
              </button> */}
            </div>
          </div>
          
          {/* 头部：中文名称 + 编辑图标 */}
          <div className="draw-config-header">
            <div className="draw-config-title-row">
              <div className="draw-config-icon-wrapper">
                <span style={{ fontSize: '16px', color: '#0f172a' }}>◆</span>
              </div>
              {isEditingNodeName ? (
                <input
                  className="draw-config-title-input"
                  value={editingNodeName}
                  onChange={(e) => setEditingNodeName(e.target.value)}
                  onBlur={() => {
                    const trimmedName = String(editingNodeName ?? '').trim();
                    if (trimmedName && trimmedName !== selectedNode.data.label) {
                      const uniqueName = generateUniqueLabel(trimmedName);
                      setNodes((nds) =>
                        nds.map((n) => {
                          if (n.id === selectedNodeId) {
                            return { ...n, data: { ...n.data, label: uniqueName } };
                          }
                          return n;
                        })
                      );
                    }
                    setIsEditingNodeName(false);
                  }}
                  autoFocus
                />
              ) : (
                <span className="draw-config-title">{selectedNode.data.label}</span>
              )}
            </div>
            <button
              className="draw-config-edit-btn"
              onClick={() => {
                setIsEditingNodeName(true);
                setEditingNodeName(selectedNode.data.label);
              }}
              title="编辑节点名称"
            >
              <Edit3 size={14} />
            </button>
          </div>

          {/* 英文名称 + 类型 + 连接状态 */}
          <div className="draw-config-meta">
            <span className="draw-config-meta-name">{selectedNode.data.operatorName || selectedNode.data.operatorId || ''}</span>
            {selectedNode.data.operatorType && (
              <span className="draw-config-meta-type">{selectedNode.data.operatorType}</span>
            )}
          </div>

          {/* 算子描述 - 可折叠（在英文名称下方） */}
          {selectedNode.data.description && (
            <div className="draw-config-desc-section">
              <div
                className="draw-config-desc-header"
                onClick={() => setIsDescExpanded(!isDescExpanded)}
              >
                <span className={`draw-config-desc-arrow ${isDescExpanded ? 'expanded' : ''}`}>▼</span>
                <span className="draw-config-desc-title">算子描述</span>
              </div>
              {isDescExpanded && (
                <div className="draw-config-desc-content">
                  {selectedNode.data.description}
                </div>
              )}
            </div>
          )}

          <div className="draw-config-body">

            {/* 输入参数 */}
            {selectedNode.data.input_params?.params && selectedNode.data.input_params.params.length > 0 && (
              <div className="draw-config-params-section">
                <div className="draw-config-section-title">
                  <span className="draw-config-section-bar"></span>
                  <span className="draw-config-section-text">输入参数</span>
                </div>

                {selectedNode.data.input_params.params.map((param: any, index: number) => (
                  <div key={`input-${index}`} className="draw-config-param-card">
                    {/* 第一行：参数名称 + 必填星号 + 问号tooltip + 类型标签 */}
                    <div className="draw-config-param-header">
                      <div className="draw-config-param-name-row">
                        <span className="draw-config-param-name">{param.name}</span>
                        {param.required && <span className="draw-config-param-required">*</span>}
                        {param.description && (
                          <div className="draw-config-param-tooltip" title={param.description}>
                            ?
                          </div>
                        )}
                      </div>
                      <span className="draw-config-param-type-tag">{param.type || '-'}</span>
                    </div>

                    {/* 第二行：来源 + 值 */}
                    <div className="draw-config-param-value-row">
                      <select
                        className="draw-config-source-select"
                        value={param._refType || 'manual'}
                        onChange={(e) => {
                          const newRefType = e.target.value;
                          const newParams = [...selectedNode.data.input_params.params];
                          const isChangingToReference = newRefType === 'reference' && param._refType !== 'reference';
                          newParams[index] = {
                            ...newParams[index],
                            _refType: newRefType,
                            _value: newRefType === 'reference' ? '' : (param._value || param.param_value || param._refValue || ''),
                            _refValue: isChangingToReference ? (referenceOptions.length > 0 ? referenceOptions[0].name : '') : (newRefType === 'reference' ? param._refValue || '' : '')
                          };

                          if (newRefType === 'reference' && referenceOptions.length === 0) {
                            alert('没有可用的引用选项，请确保有上游节点连接');
                          }

                          setNodes((nds) =>
                            nds.map((n) => {
                              if (n.id === selectedNodeId) {
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
                        }}
                      >
                        <option value="manual">手动</option>
                        <option value="reference">引用</option>
                        <option value="dataSource">数据源</option>
                      </select>

                      {param._refType === 'reference' ? (
                        <div className="draw-config-ref-wrapper">
                          <div className="draw-config-ref-dropdown">
                            <button
                              className="draw-config-ref-trigger"
                              onClick={() => {
                                // 切换展开状态
                                const dropdownKey = `${selectedNodeId}-${param.name}`;
                                const newExpandedRefs = [...expandedRefDropdowns];
                                const idx = newExpandedRefs.indexOf(dropdownKey);
                                if (idx > -1) {
                                  // 关闭时重置选中的算子
                                  newExpandedRefs.splice(idx, 1);
                                  setSelectedOperatorForRef('');
                                } else {
                                  newExpandedRefs.push(dropdownKey);
                                }
                                setExpandedRefDropdowns(newExpandedRefs);
                              }}
                            >
                              {param._refValue ? (
                                <span className="draw-config-ref-selected">
                                  {(function() {
                                    const matchedOpt = referenceOptions.find(o => o.name === param._refValue);
                                    const fallbackOpt = !matchedOpt
                                      ? referenceOptions.find(o => param._refValue?.endsWith(o.name) || o.name.endsWith(param._refValue || ''))
                                      : null;
                                    const nodeName = matchedOpt?.nodeName || fallbackOpt?.nodeName || param._sourceNodeName || '未知';
                                    return nodeName + ' / ' + (matchedOpt?.name || fallbackOpt?.name || param._refValue);
                                  })()}
                                </span>
                              ) : (
                                <span className="draw-config-ref-placeholder">选择算子 / 参数...</span>
                              )}
                              <span className="draw-config-ref-arrow">▼</span>
                            </button>

                            {expandedRefDropdowns.includes(`${selectedNodeId}-${param.name}`) && (
                              <div className="draw-config-ref-dropdown-content">
                                {/* 第一级：算子列表 */}
                                {!selectedOperatorForRef && (
                                  <>
                                    <div className="draw-config-ref-dropdown-header">
                                      <span className="draw-config-ref-dropdown-operator">选择算子</span>
                                    </div>
                                    <div className="draw-config-ref-dropdown-list">
                                      {/* 按算子分组显示 */}
                                      {Array.from(new Set(referenceOptions.map(o => o.nodeId))).map((nodeId) => {
                                        const nodeOpts = referenceOptions.filter(o => o.nodeId === nodeId);
                                        const nodeName = nodeOpts[0]?.nodeName || nodeId;
                                        return (
                                          <div
                                            key={nodeId}
                                            className={`draw-config-ref-dropdown-item ${param._sourceNodeId === nodeId ? 'selected' : ''}`}
                                            onClick={() => {
                                              setSelectedOperatorForRef(nodeId);
                                            }}
                                            title={nodeName}
                                          >
                                            <span className="draw-config-ref-item-dot"></span>
                                            <span className="draw-config-ref-item-operator" style={{ flex: 1 }}>{nodeName}</span>
                                            <span className="draw-config-ref-item-count">{nodeOpts.length}个参数</span>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </>
                                )}
                                {/* 第二级：参数列表 */}
                                {selectedOperatorForRef && (
                                  <>
                                    <div className="draw-config-ref-dropdown-header">
                                      <span className="draw-config-ref-back" onClick={() => setSelectedOperatorForRef('')}>← 返回</span>
                                      <span className="draw-config-ref-dropdown-param">选择参数</span>
                                    </div>
                                    <div className="draw-config-ref-dropdown-list">
                                      {referenceOptions.filter(o => o.nodeId === selectedOperatorForRef).map((opt) => (
                                        <div
                                          key={`${opt.nodeId}_${opt.name}`}
                                          className={`draw-config-ref-dropdown-item ${param._refValue === opt.name ? 'selected' : ''}`}
                                          onClick={() => {
                                            const refValue = opt.name;
                                            const newParams = [...selectedNode.data.input_params.params];
                                            newParams[index] = {
                                              ...newParams[index],
                                              _refValue: refValue,
                                              _sourceNodeId: opt.nodeId || '',
                                              _sourceNodeName: opt.nodeName || '',
                                              _sourceParamName: opt.name || '',
                                            };
                                            setNodes((nds) =>
                                              nds.map((n) => {
                                                if (n.id === selectedNodeId) {
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
                                            // 关闭下拉并重置选中的算子
                                            setExpandedRefDropdowns(expandedRefDropdowns.filter(id => id !== `${selectedNodeId}-${param.name}`));
                                            setSelectedOperatorForRef('');
                                          }}
                                        >
                                          <span className="draw-config-ref-item-dot"></span>
                                          <span className="draw-config-ref-item-param" style={{ flex: 1 }}>{opt.name}</span>
                                          <span className="draw-config-ref-item-type">{opt.type}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <input
                          className="draw-config-value-input"
                          value={param._value || param.param_value || ''}
                          placeholder={param._refType === 'dataSource' ? '数据源' : '请输入值'}
                          onChange={(e) => {
                            const newParams = [...selectedNode.data.input_params.params];
                            newParams[index] = { ...newParams[index], _value: e.target.value };
                            setNodes((nds) =>
                              nds.map((n) => {
                                if (n.id === selectedNodeId) {
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
                          }}
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 输出参数 */}
            {selectedNode.data.output_params?.params && selectedNode.data.output_params.params.length > 0 && (
              <div className="draw-config-params-section">
                <div className="draw-config-section-title">
                  <span className="draw-config-section-bar"></span>
                  <span className="draw-config-section-text">输出参数</span>
                </div>

                {selectedNode.data.output_params.params.map((param: any, index: number) => (
                  <div key={`output-${index}`} className="draw-config-param-card output-card">
                    <div className="draw-config-param-header">
                      <div className="draw-config-param-name-row">
                        <span className="draw-config-param-name">{param.name}</span>
                      </div>
                      <span className="draw-config-param-type-tag">{param.type || '-'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {isOperatorLibraryOpen && (
        <OperatorLibraryModal
          isOpen={isOperatorLibraryOpen}
          onClose={() => setIsOperatorLibraryOpen(false)}
          onAddNode={handleAddNode}
          operatorList={operatorList}
        />
      )}

      {/* Delete键删除确认弹窗 */}
      {showDeleteModal && (
        <div className="delete-confirm-overlay" onClick={() => setShowDeleteModal(false)}>
          <div className="delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="delete-confirm-header">
              <div className="delete-confirm-icon">!</div>
              <h3>确认删除此节点？</h3>
              <button className="delete-confirm-close" onClick={() => setShowDeleteModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="delete-confirm-body">
              <p>删除后将无法恢复，确定要删除该节点吗？</p>
            </div>
            <div className="delete-confirm-footer">
              <div className="delete-confirm-actions">
                <button className="delete-confirm-cancel" onClick={() => setShowDeleteModal(false)}>
                  取消
                </button>
                <button className="delete-confirm-confirm" onClick={handleDeleteNode}>
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {saveMessage && (
        <div className="save-message">{saveMessage}</div>
      )}
    </div>
  );
};

const FlowEditor: React.FC<FlowEditorProps> = (props) => {
  return (
    <ReactFlowProvider>
      <FlowEditorInner {...props} />
    </ReactFlowProvider>
  );
};

export default FlowEditor;
