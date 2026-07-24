import React, { useCallback, useState, useRef, memo, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { shortId } from '../lib/ids';
import { saveDrawInfo, getAllSkills, listSkillsDetails, createMessage, streamChat, apiBase, listStorage, downloadWorkspaceUrl2 } from "../lib/api";

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
  Folder,
  FolderOpen,
  FileText,
  ChevronRight,
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
  output_params?: { 
    params: { 
      name: string; 
      type: string; 
      param_value?: string; // 新增：用于存储用户填写的值
      _value: string;
    }[] 
  };
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

interface NodeTooltipProps {
  text: string;
  target: HTMLElement | null;
  visible: boolean;
}

const NodeTooltip: React.FC<NodeTooltipProps> = ({ text, target, visible }) => {
  if (!visible || !target) return null;
  const rect = target.getBoundingClientRect();
  const style: React.CSSProperties = {
    position: 'fixed',
    top: rect.top - 8,
    left: rect.right,
    transform: 'translate(-100%, -100%)',
    background: 'rgba(0, 0, 0, 0.88)',
    color: '#fff',
    padding: '6px 10px',
    borderRadius: 6,
    fontSize: 12,
    lineHeight: 1.4,
    whiteSpace: 'normal',
    wordBreak: 'break-all',
    maxWidth: 300,
    zIndex: 100000,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
    pointerEvents: 'none',
  };
  return createPortal(<div className="node-param-tooltip" style={style}>{text}</div>, document.body);
};

const ParamValue: React.FC<{ value: string }> = ({ value }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [hovered, setHovered] = useState(false);
  const [isOverflow, setIsOverflow] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    setIsOverflow(el.scrollWidth > el.clientWidth);
  }, [value]);

  return (
    <>
      <div
        ref={ref}
        className="node-param-value"
        data-tooltip={String(value)}
        onMouseEnter={(e) => { if (isOverflow) setHovered(true); e.stopPropagation(); }}
        onMouseLeave={() => setHovered(false)}
        onClick={(e) => e.stopPropagation()}
      >{value}</div>
      <NodeTooltip text={String(value)} target={ref.current} visible={hovered && isOverflow} />
    </>
  );
};

const ParamValueSpan: React.FC<{ value: string }> = ({ value }) => {
  const ref = useRef<HTMLSpanElement | null>(null);
  const [hovered, setHovered] = useState(false);
  const [isOverflow, setIsOverflow] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    setIsOverflow(el.scrollWidth > el.clientWidth);
  }, [value]);

  return (
    <>
      <span
        ref={ref}
        className="node-param-value"
        data-tooltip={String(value)}
        onMouseEnter={(e) => { if (isOverflow) setHovered(true); e.stopPropagation(); }}
        onMouseLeave={() => setHovered(false)}
        onClick={(e) => e.stopPropagation()}
      >{value}</span>
      <NodeTooltip text={String(value)} target={ref.current} visible={hovered && isOverflow} />
    </>
  );
};

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
        <ParamValueSpan value={String(getDisplayValue(key, value))} />
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
              {data.input_params.params.
                filter(param => !param._hidden)
                .map((inputItem, index) => (
                <div key={`input-${index}`} className="oneParams">
                  <div className="node-param-label">{inputItem.name}</div>
                  <ParamValue value={String(inputItem.param_value || '-')} />
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
                <div className="valueText">值</div> {/* 👈 新增“值”列 */}
              </div>
              {data.output_params.params.map((outputItem, index) => (
                <div key={`output-${index}`} className="oneParams">
                  <div className="node-param-label">{outputItem.name}</div>
                  <ParamValue value={String(outputItem.type)} />
                  <ParamValue value={String(outputItem._value || outputItem.param_value || '-')} /> {/* 👈 显示值 */}
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
  isSaved?: boolean; // 👈 声明为可选 boolean
  onClose?: () => void;
}

// ==================== 主画布组件====================

const FlowEditorInner: React.FC<FlowEditorProps> = ({ initialPipelineData, onClose, threadId, messageId: messageIdProp, savedDrawData,isSaved }) => {
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
  const [newTaskId, setNewTaskId] = useState<string>('');
  const [messageId, setMessageId] = useState<string>(messageIdProp || '');
  const [taskName, setTaskName] = useState<string>('');
  const [taskDescription, setTaskDescription] = useState<string>('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showFileModal, setShowFileModal] = useState(false);
  const [fileSystemItems, setFileSystemItems] = useState<any[]>([]);
  const [currentDirPath, setCurrentDirPath] = useState<string>('');
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [fileSelectParamIndex, setFileSelectParamIndex] = useState<number | null>(null);
  const prevNodesLengthRef = useRef<number>(nodes.length);

  //新增一个变量，节点中是否村子missing_skill_stop节点
  const [hasMissingSkillStop, setHasMissingSkillStop] = useState(false);
  const [isMissingSkillStop,setIsMissingSkillStop] = useState(false);
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
  // 在 FlowEditorInner 组件内，放在其他 useEffect 附近

  // 👇 把你的 useEffect 放在这里（合法位置）
  useEffect(() => {
    if (taskId) {
      // 执行后续逻辑，比如加载任务详情等
    }
  }, [taskId]);




const handleParamChange = (e, targetName) => {
  const newRefType = e.target.value;

  // ✅ 关键修改 4：深拷贝整个 params 数组，切断引用联系
  // 这一步对于 React Flow 的节点更新至关重要
  const deepClonedParams = JSON.parse(
    JSON.stringify(selectedNode.data.input_params.params)
  );

  // ✅ 关键修改 5：通过 findIndex 查找目标项，而不是用 index
  // 无论列表怎么隐藏、怎么排序，只要 name 对上了，就能改对地方
  const targetIndex = deepClonedParams.findIndex(p => p.name === targetName);

  if (targetIndex !== -1) {
    const targetParam = deepClonedParams[targetIndex];

    // --- 以下是根据你的截图结构进行的逻辑处理 ---

    // 1. 更新 refType
    targetParam._refType = newRefType;

    // 2. 根据模式切换值 (参考你之前的逻辑)
    if (newRefType === 'reference') {
      // 切换到引用模式：清空手动值，准备填引用值
      targetParam.param_value = ''; 
      // 如果有专门的引用字段，也可以在这里初始化
      // targetParam.ref_value = ''; 
    } else {
      // 切换回手动模式：如果之前有缓存的手动值，可以恢复，或者保持为空
      // 这里简单处理：如果 param_value 为空，可能需要用户重新输入
    }

    // 3. 更新 value_mode (根据你的截图，这个字段可能也需要联动更新)
    targetParam.value_mode = newRefType === 'reference' ? 'auto' : 'manual';
  }

  // ✅ 关键修改 6：构建新的 nodes 数组并更新
  setNodes((nds) =>
    nds.map((node) => {
      if (node.id === selectedNode.id) {
        return {
          ...node,
          data: {
            ...node.data,
            input_params: {
              ...node.data.input_params,
              params: deepClonedParams, // 放入修改后的新数组
            },
          },
        };
      }
      return node;
    })
  );
};

  // 删除节点
  const handleDeleteNode = () => {
    if (selectedNodeId) {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
      setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId));
      setSelectedNodeId(null);
    }
    setShowDeleteModal(false);
  };

  const loadDirectories = useCallback(async (dir_path?: string) => {
    setIsLoadingFiles(true);
    // 修改传参
    try {
      const userId = localStorage.getItem('userId') || '';
      const res = await listStorage(userId, dir_path);
      setFileSystemItems((res as any).items || []);
      setCurrentDirPath((res as any).dir_path || dir_path || '');
    } catch (err) {
      console.error('加载目录失败:', err);
      setFileSystemItems([]);
    } finally {
      setIsLoadingFiles(false);
    }
  }, []);

  const handleNavigateDir = useCallback(async (path: string) => {
    await loadDirectories(path);
  }, [loadDirectories]);

  const handleGoBack = useCallback(async () => {
    if (!currentDirPath) return;
    const parentPath = currentDirPath.substring(0, currentDirPath.lastIndexOf('/'));
    await loadDirectories(parentPath || undefined);
  }, [currentDirPath, loadDirectories]);

  const handleDownloadFile = useCallback(async (filePath: string) => {
    try {
      const url = downloadWorkspaceUrl2(filePath);
      const response = await fetch(url);
      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        console.error('文件下载失败:', errData?.message || '未知错误');
        return;
      }
      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = filePath.split('/').pop() || 'download';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\\n]*=((['\"]).*?\2|[^;\\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['\"]/g, '');
        }
      }
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('文件下载失败:', error);
    }
  }, []);

  const handleUploadFile = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingFile(true);
    try {
      const userId = localStorage.getItem('userId') || '';
      const form = new FormData();
      form.append('user_id', userId);
      form.append('dir_path', currentDirPath);
      form.append('file', file);
      const res = await fetch(`${apiBase()}/workspace/upload/path`, {
        method: 'POST',
        body: form
      });
      if (res.ok) {
        await loadDirectories(currentDirPath);
      }
    } catch (err) {
      console.error('文件上传失败:', err);
    } finally {
      setUploadingFile(false);
      e.target.value = '';
    }
  }, [currentDirPath, loadDirectories]);

  const handleSelectFileForParam = useCallback((filePath: string) => {
    if (fileSelectParamIndex === null || !selectedNodeId) {
      setShowFileModal(false);
      setFileSelectParamIndex(null);
      return;
    }
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === selectedNodeId) {
          const newParams = [...(n.data.input_params?.params || [])];
          if (newParams[fileSelectParamIndex]) {
            newParams[fileSelectParamIndex] = { ...newParams[fileSelectParamIndex], _value: filePath };
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
    setShowFileModal(false);
    setFileSelectParamIndex(null);
  }, [fileSelectParamIndex, selectedNodeId]);

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
// 在组件底部或控制台打印
useEffect(() => {
}, [selectedNode]);
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
        const loadedNodes: Node<NodeData>[] = [];
        const loadedEdges: Edge[] = [];
        isInitialized.current = false;

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


            // --- 新增：参数去重与值转移逻辑 ---
            const currentNode = savedDrawData.nodes[i];

            // 1. 确保 input_params 和 output_params 都是标准格式 { params: [] }
            let inputParamsArray = [];
            let outputParamsArray = [];

            if (currentNode.input_params?.params) {
              inputParamsArray = currentNode.input_params.params;
            } else if (Array.isArray(currentNode.input_params)) {
              inputParamsArray = currentNode.input_params;
            }

            if (currentNode.output_params?.params) {
              outputParamsArray = currentNode.output_params.params;
            } else if (Array.isArray(currentNode.output_params)) {
              outputParamsArray = currentNode.output_params;
            }

            // 2. 创建一个输出参数的 Map，方便快速查找
            const outputParamsMap = new Map();
            outputParamsArray.forEach((p) => {
              const paramName = p.name || p.param_name;
              if (paramName) {
                outputParamsMap.set(paramName, p);
              }
            });

            // 替换原来的 filteredInputParams = inputParamsArray.filter(...)
          const processedInputParams = inputParamsArray.map((inputParam) => {
            const inputParamName = inputParam.name || inputParam.param_name;
            if (!inputParamName) return inputParam; // 无名参数，跳过处理

            const outputParam = outputParamsMap.get(inputParamName);
            if (outputParam) {
              // 发现重名：转移值 + 标记隐藏 + required 设为 false
              const valueToTransfer = 
                inputParam.param_value !== undefined ? inputParam.param_value : 
                inputParam.value !== undefined ? inputParam.value : 
                '';

              // 返回修改后的 inputParam：标记隐藏、非必填
              return {
                ...inputParam,
                required: false,        // 👈 关键：设为非必填
                _hidden: true,          // 👈 自定义字段，UI 可据此隐藏
              };
            }

            return inputParam; // 无冲突，原样返回
          });

          // 如果你仍希望在 UI 中彻底不渲染这些参数，可以在后续使用时过滤：
          const filteredInputParams = processedInputParams.filter(param => !param._hidden);



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
        
          
          // 优先从 savedDrawData 里读取 output_params
          if (hasSavedOutputParams) {
            // let rawOutputParams = Array.isArray(n.output_params) ? n.output_params : n.output_params?.params || [];
            // outputParams = {
            //   params: rawOutputParams.map((p: any) => {
            //     // 确保 _value 总是有值，优先取 _value，其次取 param_value 或 value
            //     const value = p._value !== undefined ? p._value : (p.param_value !== undefined ? p.param_value : p.value);
            //     return {
            //       ...p,
            //       _value: String(value) // ✅ 确保 _value 被正确赋值
            //     };
            //   })
            // };
            
            outputParams = mapOutputParamsValues(n.output_params);
          }
                      
          // 对于source_stop和sink_stop这两个特殊算子，不要请求接口，使用固定的参数
         const isSpecialSkill = 
            skillId === 'piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop' ||
            skillId === 'piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop' ||
            skillId === 'piflow_engine.cn.piflow.engine.local.llm_file_transform_stop.LLMFileTransformStop';
          let skillDescription = '';
          if (isSpecialSkill) {
            // 特殊节点：强制 output_params 为空
            outputParams = { params: [] };
            if (skillId === 'piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop') {
                n.skill = n.skill || {};
                n.skill.name_zh = '文件源';
                n.skill.skill_name = 'source_stop';
                n.skill.skill_type = 'source';
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
                outputParams={ params: [] }
            } else if (skillId === 'piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop') {
              n.skill = n.skill || {};
                n.skill.name_zh = '文件保存';
                n.skill.skill_name = 'sink_stop';
                n.skill.skill_type = 'sink';
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
            } else if (skillId === 'piflow_engine.cn.piflow.engine.local.llm_file_transform_stop.LLMFileTransformStop') {
              n.skill = n.skill || {};
              n.skill.name_zh = 'llm算子';
              n.skill.skill_name = 'llm_chat';
              n.skill.skill_type = 'chat';

              // 固定输入参数（请根据实际需求调整字段）
              inputParams={
                  params: [
                    
                    {
                      name: "input",
                      type: "string",
                      param_name: "input",
                      param_type: "string",
                      value_mode: "manual",
                      param_value: "",
                      value_source: "user_input",
                      required: true
                    },
                    {
                      name: "instruction",
                      type: "string",
                      param_name: "instruction",
                      param_type: "String",
                      value_mode: "manual",
                      param_value: "",
                      value_source: "user_input",
                      required: true
                    },
                    {
                      name: "model",
                      type: "string",
                      param_name: "model",
                      param_type: "String",
                      value_mode: "manual",
                      param_value: "gpt-4o",
                      value_source: "user_input",
                      required: true
                    },
                    {
                      name: "api_key",
                      type: "string",
                      param_name: "api_key",
                      param_type: "string",
                      value_mode: "manual",
                      param_value: "",
                      value_source: "user_input",
                      required: true
                    },
                    {
                      name: "base_url",
                      type: "string",
                      param_name: "base_url",
                      param_type: "string",
                      value_mode: "manual",
                      param_value: "",
                      value_source: "user_input",
                      required: true
                    }
                  ]
                },

                // 固定输出参数：只有一个 out_path
                outputParams = {
                  params: [
                    {
                      name: "output",
                      type: "string",
                      param_name: "output",
                      param_type: "String"
                    }
                  ]
                };
            }
          } else {
            // 普通算子：先请求接口获取参数模板（含 required 字段）
            if (skillId) {
              
              try {
                const skillRes = await listSkillsDetails(skillId);
                if (skillRes.result) {
                  inputParams = skillRes.result.input_params;
                  outputParams = skillRes.result.output_params;
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
                }
              } catch (e) { console.error(`节点 ${i}: getAllSkills 失败:`, e); }
            }
            
            // 如果 API 都没返回，回退使用已保存数据
            if (!inputParams?.params && hasSavedInputParams) {
              inputParams = { params: n.input_params };
            }
            // 如果 savedDrawData 中有 icon_path，优先使用
            if (hasSavedIconPath) {
              nodeIconPath = n.icon_path;
            }
          }
          

          // 确保outputParamsMap里有当前节点的output_params
          if (outputParams?.params) {
            outputParamsMap[nodeId] = outputParams.params;
          }

       
          

          // 合并已保存的参数数据
          let mergedInputParams = inputParams;

          let mergedOutputParams = outputParams;
          if (outputParams?.params) {
            // 先用 savedDrawData 的值初始化 output_params
            const savedOutputParamsMap: Record<string, any> = {};
            const savedRawOutputParams = Array.isArray(n.output_params) 
              ? n.output_params 
              : n.output_params?.params || [];

            savedRawOutputParams.forEach((sp: any) => {
              const paramName = sp.param_name || sp.name || '';
              if (paramName) {
                savedOutputParamsMap[paramName] = sp;
              }
            });

            // 初始化 output_params 的 _value
            mergedOutputParams = {
              params: outputParams.params.map((paramDef: any) => {
                const paramName = paramDef.name || paramDef.param_name || '';
                const savedParam = savedOutputParamsMap[paramName];
                const finalValue = safeInitParamValue(savedParam || paramDef);
                return {
                  ...paramDef,
                  _value: finalValue,
                  param_value: finalValue,
                };
              })
            };

            // ===== 新增：从 input_params 中同步同名参数的值 =====
            if (mergedInputParams?.params) {
              const inputValueMap: Record<string, string> = {};
              mergedInputParams.params.forEach(param => {
                const name = param.name || param.param_name;
                if (name) {
                  // 取用户编辑后的值 _value，否则取 param_value
                  const val = (param._value !== undefined ? param._value : param.param_value);
                  if (val !== undefined && val !== '') {
                    inputValueMap[name] = String(val);
                  }
                }
              });

              // 更新 mergedOutputParams
              mergedOutputParams = {
                ...mergedOutputParams,
                params: mergedOutputParams.params.map(outParam => {
                  const name = outParam.name || outParam.param_name;
                  if (name && inputValueMap[name] !== undefined) {
                    return {
                      ...outParam,
                      _value: inputValueMap[name],
                      param_value: inputValueMap[name],
                    };
                  }
                  return outParam;
                })
              };
            }
          }

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
              output_params: mergedOutputParams,
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
        setIsLoading(false);
        return;
      }

      // 打印大模型返回的完整 JSON 数据
      console.log('========================================');
      console.log('=== 大模型返回的 DAG JSON 数据 ===');
      console.log('完整数据:', initialPipelineData);
      // initialPipelineData.nodes.forEach((node, index) => {
      //   console.log(`  节点 ${index + 1}:`);
      //   console.log(`    node_name: ${node.node_name}`);
      //   console.log(`    skill_name: ${node.skill_name}`);
      //   console.log(`    params:`, JSON.stringify(node.params || {}, null, 4));
      // });
      const pipelineNodes = initialPipelineData.nodes;
      const createdNodes: Node<NodeData>[] = [];
      const createdEdges: Edge[] = [];

      //新增节点中有missing_skill_stop的节点
      if (initialPipelineData.task.workflow_status){
        setIsMissingSkillStop(true);
      }
      // 创建节点名称到节点ID的映射（用于解析引用关系）
      const nodeNameToIdMap: Record<string, string> = {};
      const nodeIdToOutputParamsMap: Record<string, any> = {};
      
      // 第一步：先拓扑排序，确定节点的层次位置
      // 1.1 构建节点关系图
      const nodeIndexToNodeName: string[] = [];
      const nodeNameToIndexMap: Record<string, number> = {};
      pipelineNodes.forEach((node, index) => {
        nodeNameToIndexMap[node.node_name] = index;

        //新增节点中有missing_skill_stop的节点
        if (node.skill_name === 'missing_skill_stop'){
          setHasMissingSkillStop(true);
        }
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
          skillId = 'piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop';
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
          skillId = 'piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop';
          nodeNameToZhName[pNode.node_name] = '文件保存';
          nodeNameToZhName['sink_stop'] = '文件保存';
          // sink_stop 没有输出参数，不调用接口
          nodeIdToOutputParamsMap[nodeId] = { params: [] };
        } else {
          // 普通算子，调用接口获取信息
          try {
            const res = await getAllSkills(skillName);
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

        // ✅ 关键修复：如果 outputParams 不存在，从算子定义中获取，并初始化 _value
        if (!outputParams && skillDataFromAPI) {
          outputParams = skillDataFromAPI.output_params;
          if (outputParams?.params) {
            outputParams = {
              ...outputParams,
              params: outputParams.params.map(p => ({
                ...p,
                _value: p.param_value || p._value || '' // 初始化 _value
              }))
            };
          }
        }

        let iconPath = '';
        
        // 处理 DAG 节点的参数
        // params中每个属性是参数名，值可能是字符串或引用对象
        const dagParams = pNode.params || {};
        const nodeId = `node-${i + 1}`;
        
        // 构建 mergedInputParams
        let mergedInputParams;
        let skillDesc = '';
        
        // 对于 source_stop 和 sink_stop 特殊算子，使用fixArr中定义的参数结构，然后填入值
        if (skillName === 'source_stop') {
          skillId = 'piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop';
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
          // outputParams = {
          //   params: [{
          //     name: 'output',
          //     type: 'string',
          //     param_name: 'output',
          //     param_type: 'String'
          //   }]
          // };
          outputParams = {params:[]}
        } else if (skillName === 'sink_stop') {
          skillId = 'piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop';
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
              if (outputParams?.params) {
                outputParams = {
                  ...outputParams,
                  params: outputParams.params.map(p => ({
                    ...p,
                    _value: p._value || p.param_value || ''
                  }))
                };
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

          // 构建 mergedInputParams：合并DAG 参数到算子的 input_params
          mergedInputParams = inputParams;
          if (inputParams?.params && Array.isArray(inputParams.params)) {
            // 先构建算子参数的 map，方便查找
            const paramDefMap: Record<string, any> = {};
            inputParams.params.forEach((paramDef: any) => {
              paramDefMap[paramDef.name] = paramDef;
            });
            
            const newParamsList: any[] = [];
            
            // 先处理算子中定义的参数
            inputParams.params.forEach((paramDef: any) => {
              // 精确匹配：优先使用 paramDef.name 查找
              let paramValue = dagParams[paramDef.name];
              
              // 如果找不到，尝试使用 param_name 查找
              if (paramValue === undefined && paramDef.param_name) {
                paramValue = dagParams[paramDef.param_name];
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
                  newParamsList.push({
                    ...paramDef,
                    _refType: 'manual',
                    _value: String(paramValue),
                    _refValue: '',
                  });
                }
              } else {
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



            // --- 新增：参数去重与值转移逻辑 ---
            const currentNode = pNode;

            // 1. 确保 input_params 和 output_params 都是标准格式 { params: [] }
            let inputParamsArray = [];
            let outputParamsArray = [];

            if (currentNode.input_params?.params) {
              inputParamsArray = currentNode.input_params.params;
            } else if (Array.isArray(currentNode.input_params)) {
              inputParamsArray = currentNode.input_params;
            }

            if (currentNode.output_params?.params) {
              outputParamsArray = currentNode.output_params.params;
            } else if (Array.isArray(currentNode.output_params)) {
              outputParamsArray = currentNode.output_params;
            }

            // 2. 创建一个输出参数的 Map，方便快速查找
            const outputParamsMap = new Map();
            outputParamsArray.forEach((p) => {
              const paramName = p.name || p.param_name;
              if (paramName) {
                outputParamsMap.set(paramName, p);
              }
            });

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
      
      for (let i = 0; i < createdNodes.length; i++) {
        const node = createdNodes[i];
        const inputParams = node.data.input_params?.params || [];
        const outputParams = [...(node.data.output_params?.params || [])]; // 👈 关键：浅拷贝数组

        // 构建输入参数的值映射：paramName -> _value
        const inputValueMap: Record<string, string> = {};
        inputParams.forEach((param) => {
          const name = param.name || param.param_name;
          if (name && (param._value !== undefined || param.param_value !== undefined)) {
            inputValueMap[name] = String(param._value ?? param.param_value);
          }
        });

        // 更新输出参数：若同名，则设置 param_value 和 _value
        for (let j = 0; j < outputParams.length; j++) {
          const outParam = outputParams[j];
          const name = outParam.name || outParam.param_name;
          if (name && inputValueMap[name] !== undefined) {
            outputParams[j] = {
              ...outParam,
              param_value: inputValueMap[name],
              _value: inputValueMap[name], // 确保 UI 能显示
            };
          }
        }

        // 更新节点数据（创建新对象以触发 React 更新）
        if (node.data.output_params) {
          createdNodes[i] = {
            ...node,
            data: {
              ...node.data,
              output_params: {
                ...node.data.output_params,
                params: outputParams,
              },
            },
          };
        }
      }

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
    getAllSkills().then(resAllSkills=>{
      if(resAllSkills.code === 200){
        let fixArr = [
          {
            groupName: "基础",
            DagSkillInfoList: [
              {
                id: 9999999999998,
                skill_id: "piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop",
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
                      param_value: "",
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
                output_params: { params: [] },
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
                skill_id: "piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop",
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
                  ]
                },
                output_params: { params: [] },
                skill_type: "",
                language: "",
                command: "",
                icon_path: "",
                create_time: "",
                update_time: "",
                is_deleted: 0
              }
            ]
          },
          {
            groupName: "LLM类",
            DagSkillInfoList: [
              // 新增：LLM算子
              {
                id: 9999999999997,
                skill_id: "piflow_engine.cn.piflow.engine.local.llm_file_transform_stop.LLMFileTransformStop",
                skill_name: "llm_chat",
                name_zh: "LLM算子",
                version: "1.0.0",
                description: "调用大语言模型进行文本生成",
                file_path: "",
                input_params: {
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
                      name: "model",
                      type: "string",
                      param_name: "model",
                      param_type: "String",
                      value_mode: "manual",
                      param_value: "gpt-4o",
                      value_source: "user_input",
                      required: true
                    },
                    {
                      name: "api_key",
                      type: "string",
                      param_name: "api_key",
                      param_type: "string",
                      value_mode: "manual",
                      param_value: "",
                      value_source: "user_input",
                      required: true
                    },
                    {
                      name: "base_url",
                      type: "string",
                      param_name: "base_url",
                      param_type: "string",
                      value_mode: "manual",
                      param_value: "",
                      value_source: "user_input",
                      required: true
                    },
                    {
                      name: "input",
                      type: "string",
                      param_name: "input",
                      param_type: "string",
                      value_mode: "manual",
                      param_value: "",
                      value_source: "user_input",
                      required: true
                    }
                  ]
                },
                output_params: {
                  params: [
                    {
                      name: "output",
                      type: "string",
                      param_name: "output",
                      param_type: "String"
                    }
                  ]
                },
                // skill_type: "llm",
                language: "python",
                command: "",
                icon_path: "/storage/common/llm.png",
                create_time: "",
                update_time: "",
                is_deleted: 0
              }
            ]
          }
        ];
        const finalList = fixArr.concat(resAllSkills.result.data);
        // 打印第一个算子的信息
        if(finalList.length > 0 && finalList[0].DagSkillInfoList.length > 0) {
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

    // 找到指向当前节点的所有上游节点（通过 edges 的 target 和 source）
    const upstreamNodeIds = edges
      .filter((e) => e.target === currentNodeId)
      .map((e) => e.source);


    if (upstreamNodeIds.length === 0) {
      setIsLoadingReferences(false);
      return;
    }

    // 直接从上游节点的 output_params 获取出参
    const upstreamNodes = nodes.filter((n) => upstreamNodeIds.includes(n.id));
    
    const allOutputParams: { name: string; type: string; description: string; nodeId: string; nodeName: string }[] = [];
    
    upstreamNodes.forEach((upstreamNode) => {

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
  async (
    operator: {
      skill_id: string;
      skill_name: string;
      name_zh: string;
      icon_path: string;
      skill_type: string;
      description?: string;
    },
    position?: { x: number; y: number }
  ) => {
    nodeIdCounter.current += 1;
    const uniqueLabel = generateUniqueLabel(operator.name_zh);

    // 请求算子详情获取 input_params 和 output_params
    let inputParams = undefined;
    let outputParams = undefined;
    let operatorIconPath = operator.icon_path;
    let operatorDescription = operator.description || '';

    // 新增：对 LLM 算子、文件源和文件保存做特殊处理
    if (operator.skill_id === 'piflow_engine.cn.piflow.engine.local.llm_file_transform_stop.LLMFileTransformStop') {
      inputParams = {
        params: [
          {
            name: "instruction",
            type: "string",
            param_name: "instruction",
            param_type: "String",
            value_mode: "manual",
            param_value: "",
            value_source: "user_input",
            required: true
          },
          {
            name: "model",
            type: "string",
            param_name: "model",
            param_type: "String",
            value_mode: "manual",
            param_value: "",
            value_source: "user_input",
            required: true
          },
          {
            name: "api_key",
            type: "String",
            param_name: "api_key",
            param_type: "String",
            value_mode: "manual",
            param_value: "",
            value_source: "user_input",
            required: true
          },
          {
            name: "base_url",
            type: "String",
            param_name: "base_url",
            param_type: "String",
            value_mode: "manual",
            param_value: "",
            value_source: "user_input",
            required: true
          },
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
        ]
      };
      outputParams = {
        params: [
          { name: "output", type: "string", param_name: "output", param_type: "String" }
        ]
      };
      operatorIconPath = operator.icon_path || "/storage/common/llm.png";
      operatorDescription = operator.description || "调用大语言模型进行文本生成";
    } else if (operator.skill_id === 'piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop') {
        inputParams = {
                  params: [
                    {
                      name: "file_path",
                      type: "string",
                      param_name: "file_path",
                      param_type: "String",
                      value_mode: "manual",
                      param_value: "",
                      _refType: 'manual', //能弹出用户自己本地文件夹
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
    } else if (operator.skill_id === 'piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop') {
      inputParams = {
        params: [
          {
            name: "input",
            type: "string",
            param_name: "input",
            param_type: "String",
            value_mode: "manual",
            param_value: "", // 可设为空或示例值
            value_source: "local_file",
            required: true
          },
          {
            name: "path",
            type: "string",
            param_name: "path",
            param_type: "String",
            value_mode: "manual",
            param_value: "", // 默认保存路径
            value_source: "local_file",
            required: true
          },
          {
            name: "overwrite",
            type: "boolean",
            param_name: "overwrite",
            param_type: "Boolean",
            value_mode: "manual",
            param_value: true, // 默认覆盖
            value_source: "local_file"
          }
        ]
      };
      outputParams = { params: [] };
    } else {
      // 原有逻辑：尝试从 API 获取
      try {
        const res = await listSkillsDetails(operator.skill_id);
        if (res.result) {
          inputParams = res.result.input_params;
          outputParams = res.result.output_params;
          operatorIconPath = res.result.icon_path || operatorIconPath;
          operatorDescription = res.result.description || operatorDescription;
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
          }
        } catch (e) {
          console.error('handleAddNode: getAllSkills 失败:', e);
        }
      }
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
        const overlaps = nodes.some((node) => {
          const nodeRight = node.position.x + NODE_WIDTH;
          const nodeBottom = node.position.y + NODE_HEIGHT;
          const testRight = testX + NODE_WIDTH;
          const testBottom = testY + NODE_HEIGHT;
          return (
            testX < nodeRight &&
            testRight > node.position.x &&
            testY < nodeBottom &&
            testBottom > node.position.y
          );
        });

        if (!overlaps) {
          newPosition = { x: testX, y: testY };
          break;
        }

        // 尝试偏移
        offsetX = (Math.random() - 0.5) * 200;
        offsetY = (Math.random() - 0.5) * 200;
        attempt++;
      }

      if (!newPosition) {
        newPosition = { x: viewCenterX - NODE_WIDTH / 2, y: viewCenterY - 70 };
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
        operatorName: operator.skill_name,
        operatorZh: operator.name_zh,
        operatorType: operator.skill_type,
        description: operatorDescription,
        params: {},
        inputVar: 'input_data',
        outputVar: 'output_data',
        input_params: inputParams,
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
      setViewport({ x: targetX, y: targetY, zoom: currentViewport.zoom });
    }, 100);
  },
  [
    nodes,
    generateUniqueLabel,
    getViewport,
    setViewport,
    setNodes,
    setSelectedNodeId,
    setShowDeleteModal,
    setShowOperatorModal,
    extractSkillBySkillName,
  ]
);

// ==================== 通用工具函数 ====================

// 安全初始化 _value：仅当 _value 不存在时才用 param_value 或 value 填充
const safeInitParamValue = (p: any): string => {
  // 如果用户已经编辑过（_value 存在），就保留它
  if (p._value !== undefined && p._value !== null) {
    return String(p._value);
  }
  // 否则用后端返回的 param_value 或 value 初始化
  const initVal = p.param_value !== undefined ? p.param_value : p.value;
  return initVal !== undefined ? String(initVal) : '';
};

// 通用字段映射函数：确保参数对象中包含组件需要的 _value 字段（仅用于初始化）
const mapOutputParamsValues = (rawParams) => {
  if (!rawParams) return { params: [] };

  const paramsArray = Array.isArray(rawParams) ? rawParams : (rawParams.params || []);
  const mappedParams = paramsArray.map((p) => ({
    ...p,
    _value: safeInitParamValue(p), // 👈 关键：不再强制覆盖
  }));

  return { params: mappedParams };
};



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

  
  // 新的自动保存画板数据

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

      // ========== 开始：替换的核心逻辑 ==========
      // 1. 准备 nodesToSave 和 bindingMap (这部分保持不变)
      // 因为在节点中存在了来源的select选错位，导致了保存的inpuParams参数错误，在这重新保存的时候，把同名的使用outParams给inputParams再保存一次
     const nodesToSave = nodes.map(node => {
      if (node.type === 'comment') {
        return {
          node_id: node.id,
          node_name: node.data.label,
          node_type: 'comment',
          position: node.position,
          skill: null,
          input_params: node.data.input_params,
          output_params: node.data.output_params,
        };
      }

      // 先提取 outputParams 并建立 name -> param_value 的映射
      const rawOutputParams = node.data.output_params?.params || [];
      const outputParamValueMap: Record<string, string> = {};
      rawOutputParams.forEach((p: any) => {
      const name = p.name || p.param_name;
      if (name) {
        // 优先取 _value，其次 param_value，确保字符串化
        outputParamValueMap[name] = String(p._value ?? p.param_value ?? '');
      }
      });

        // 构建 inputParams
        const inputParams = (node.data.input_params?.params || []).map((p: any) => {
          let finalParamValue = p.param_value;

          // 如果是引用模式，保持原逻辑
          if (p._refType === 'reference' && p._refValue) {
            finalParamValue = {
              source_node: p._sourceNodeName || '',
              source_param: p._refValue,
            };
          } else {
            // 手动模式：优先用 _value，但若 output 中有同名参数且非引用，则用 output 的值覆盖
            const outputValue = outputParamValueMap[p.name || p.param_name];
            if (outputValue !== undefined && outputValue !== '') {
              finalParamValue = outputValue;
            } else {
              finalParamValue = p._value !== undefined ? p._value : p.param_value;
            }
          }

          return {
            name: p.name,
            param_name: p.param_name || p.name,
            param_type: p.param_type || p.type || 'string',
            param_value: finalParamValue,
            value_mode: p._refType === 'reference' ? 'reference' : 'manual',
            value_source: p.value_source || 'user_input',
            required: p.required || false,
          };
        });

        // 构建 outputParams（保持不变）
        const outputParams = rawOutputParams.map((p: any) => ({
          name: p.name,
          param_type: p.type || p.param_type || 'string',
          param_value: p._value || '', // 确保这里也包含了 _value
        }));

        return {
          node_id: node.id,
          node_name: node.data.label,
          node_type: 'operator',
          position: node.position,
          skill: {
            skill_id: node.data.operatorId,
            skill_name: node.data.operatorName,
            name_zh: node.data.operatorZh,
            skill_type: node.data.operatorType,
            icon_path: node.data.icon,
            description: node.data.description,
          },
          input_params: inputParams,
          output_params: outputParams,
        };
      });

      const bindingMap: Record<string, any> = {};
      nodes.forEach(node => {
        if (node.type === 'comment') return;
        const params = node.data.input_params?.params || [];
        params.forEach((param: any) => {
          if (param._refType === 'reference' && param._refValue) {
            const key = `${node.id}|${param.name}`;
            bindingMap[key] = {
              binding_id: shortId(),
              from_node_id: '', // 这里需要根据 _sourceNodeName 找到对应的 nodeId
              from_param_name: param._refValue,
              to_node_id: node.id,
              to_param_name: param.name
            };

            // 根据 _sourceNodeName 查找上游节点ID
            const upstreamNode = nodes.find(n => 
              n.data.operatorZh === param._sourceNodeName || 
              n.data.operatorName === param._sourceNodeName ||
              n.data.label === param._sourceNodeName
            );
            if (upstreamNode) {
              bindingMap[key].from_node_id = upstreamNode.id;
              // 如果 from_param_name 是 node-xxx_output 形式，只保留 output
              if (bindingMap[key].from_param_name.includes('_') && bindingMap[key].from_param_name.split('_')[0]?.startsWith('node-')) {
                const parts = bindingMap[key].from_param_name.split('_');
                bindingMap[key].from_param_name = parts[parts.length - 1];
              }
            }
          }
        });
      });

      // 2. 确定要使用的 taskId
      // 先尝试使用已有的 taskId
      let currentTaskId = taskId;

      // 如果没有 taskId，先调用 saveDrawInfo 获取一个
      if (!currentTaskId) {
        const tempParams = {
          dsl_version: "1.0",
          task: {
            dag_task_id: '', // 初始为空
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
          const res = await saveDrawInfo(tempParams);
          const taskIdFromRes = res.result?.dag_task_id || res.result?.task_id;
          if (taskIdFromRes) {
            setTaskId(taskIdFromRes); // 更新状态
            currentTaskId = taskIdFromRes; // 立即用于本次保存
          }
        } catch (error) {
          console.error('初次保存获取 taskId 失败:', error);
          // 如果失败，继续使用空字符串，由后端处理
        }
      }

      // 3. 使用确定的 currentTaskId 进行最终保存
      const finalParams = {
        dsl_version: "1.0",
        task: {
          dag_task_id: currentTaskId, // ✅ 关键：这里保证有值
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
        const res = await saveDrawInfo(finalParams);

        if (res.code === 200) {
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
      // ========== 结束：替换的核心逻辑 ==========
    }, 800);
  }, [nodes, edges, taskName, taskDescription, messageId, taskId, isInitialized.current]);

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
              for (const p of params) {
                if (p.required) {
                  // 如果是引用模式（_refType === 'reference'），则认为已填写
                  if (p._refType === 'reference' || (p.value_mode === 'reference' && p.binding_id)) {
                    continue;
                  }
                  const val = String(p._value ?? p.param_value ?? p._refValue ?? p.value ?? '');
                  if (!val.trim()) {
                    alert(`节点「${n.data.label}」的必填参数「${p.name}」未填写，请完善后再同步`);
                    return;
                  }
                }
              }
            }

            // 构造完整的画板JSON数据
            // const drawData = {
            //   dsl_version: "1.0",
            //   task: {
            //     // dag_task_id: taskId || '',
            //     dag_task_name: taskName,
            //     description: taskDescription,
            //     // message_id: messageId || ''
            //   },
            //   nodes: nodes
            //   .filter(n => n.type !== 'comment')
            //   .map(n => ({
            //     // node_id: n.id,
            //     node_name: n.data.label,
            //     // node_type: 'default',
            //     icon_path: n.data.icon || '',
            //     skill: {
            //       skill_name: n.data.operatorName
            //       // skill_id: n.data.operatorId,
            //       // version: '1.0',
            //     },
            //     // position: { x: n.position.x, y: n.position.y },
                
            //     // --- 修改 input_params 处理 (保持原有逻辑) ---
            //     input_params: (n.data.input_params?.params || [])
            //       .filter(p => {
            //         if (p._refType === 'reference') return true;
            //         const val = String(p._value ?? p.param_value ?? '');
            //         return val.trim() !== '';
            //       })
            //       .map(p => {
            //         const isReference = p._refType === 'reference';
            //         return {
            //           param_name: p.name,
            //           param_value: isReference ? '' : (p._value || ''),
            //           // value_mode: isReference ? 'reference' : 'manual',
            //           // binding_id: isReference ? generateUUID() : '',
            //         };
            //       }),
                  
            //     // --- 修改 output_params 处理 (关键修改点) ---
            //     // 将 output_params 中的 _value 映射为 param_value
            //     out_params: n.data.output_params?.params?.map(p => ({
            //       param_name: p.name || p.param_name || '',
            //       param_type: p.type || p.param_type || 'string',
            //       param_value: p._value || '', // 将用户填写的值放入 param_value
            //     })) || [],
            //   })),
            // };
            const drawData = {
              dsl_version: "1.0",
              task: {
                dag_task_name: taskName,
                description: taskDescription,
              },
              nodes: nodes
                .filter(n => n.type !== 'comment')
                .map(n => {
                  // --- 提取 output_params 的值映射 ---
                  const outParamsMap = new Map<string, string>();
                  (n.data.output_params?.params || []).forEach(p => {
                    const name = p.name || p.param_name || '';
                    if (name) {
                      outParamsMap.set(name, p._value || '');
                    }
                  });

                  return {
                    node_name: n.data.label,
                    icon_path: n.data.icon || '',
                    skill: {
                      skill_name: n.data.operatorName
                    },
                    input_params: (n.data.input_params?.params || [])
                      .filter(p => {
                        if (p._refType === 'reference') return true;
                        const val = String(p._value ?? p.param_value ?? '');
                        return val.trim() !== '';
                      })
                      .map(p => {
                        const isReference = p._refType === 'reference';
                        const paramName = p.name;

                        // 👇 如果是非引用参数，且 output_params 中有同名参数，则用 output 的值
                        let finalValue = isReference ? '' : (p._value ||p.param_value || '');
                        if (!isReference && outParamsMap.has(paramName)) {
                          finalValue = outParamsMap.get(paramName) || finalValue;
                        }

                        return {
                          param_name: paramName,
                          param_value: finalValue,
                        };
                      }),
                    out_params: (n.data.output_params?.params || []).map(p => ({
                      param_name: p.name || p.param_name || '',
                      param_type: p.type || p.param_type || 'string',
                      param_value: p._value || '',
                    })),
                  };
                }),
            };
            
            // 合并指令和画板数据为一条消息发送（带隐藏标记），避免触发两次 /message/create
            const combinedContent = '[HIDDEN]我手动修改了任务流程，并且修改了部分参数，请根据任务流程和新的参数重新生成dag JSON，不要执行\n\n' + JSON.stringify(drawData);
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
              (() => {
                // 获取所有输出参数的 name 集合（用于快速查找）
                const outputParamNames = new Set(
                  (selectedNode.data.output_params?.params || []).map((op: any) => op.name)
                );

                // 过滤输入参数：排除 name 存在于 output_param_names 中的项
                const filteredInputParams = (selectedNode.data.input_params.params || [])
                  .filter((param: any) => !outputParamNames.has(param.name));

                if (filteredInputParams.length === 0) return null;

                return (
                  <div className="draw-config-params-section">
                    <div className="draw-config-section-title">
                      <span className="draw-config-section-bar"></span>
                      <span className="draw-config-section-text">输入参数</span>
                    </div>

                    {filteredInputParams.map((param) => {
                      // ✅ 关键修改 1：不再使用 index，直接用 param.name 作为唯一标识
                      // 这样即使列表中有隐藏元素，React 也能精准对应 DOM 和数据
                      const uniqueKey = param.name;

                      return (
                        <div key={uniqueKey} className="draw-config-param-card">
                          {/* --- 第一行：参数名称 + 必填星号 + 问号tooltip + 类型标签 --- */}
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

                          {/* --- 第二行：来源 Select + 值输入框 --- */}
                          <div className="draw-config-param-value-row">
                            {/* ✅ 关键修改 2：Select 的 onChange 传入 param.name 而不是 index */}
                            <select
                              className="draw-config-source-select"
                              value={param._refType || 'manual'}
                              onChange={(e) => handleParamChange(e, param.name)}
                            >
                              <option value="manual">手动</option>
                              <option value="reference">引用</option>
                              <option value="dataSource">数据源</option>
                            </select>

                            {/* --- 值输入区域 --- */}
                            {param._refType === 'reference' ? (
                              // 1. 引用模式 UI
                              <div className="draw-config-ref-wrapper">
                                <div className="draw-config-ref-dropdown">
                                  <button
                                    className="draw-config-ref-trigger"
                                    onClick={() => {
                                      const dropdownKey = `${selectedNodeId}-${param.name}`;
                                      const newExpandedRefs = [...expandedRefDropdowns];
                                      const idx = newExpandedRefs.indexOf(dropdownKey);
                                      if (idx > -1) {
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
                                        {(function () {
                                          const matchedOpt = referenceOptions.find((o) => o.name === param._refValue);
                                          const fallbackOpt = !matchedOpt
                                            ? referenceOptions.find((o) => param._refValue?.endsWith(o.name) || o.name.endsWith(param._refValue || ''))
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

                                  {/* 引用下拉菜单内容 (保持不变) */}
                                  {expandedRefDropdowns.includes(`${selectedNodeId}-${param.name}`) && (
                                    <div className="draw-config-ref-dropdown-content">
                                      {!selectedOperatorForRef && (
                                        <>
                                          <div className="draw-config-ref-dropdown-header">
                                            <span className="draw-config-ref-dropdown-operator">选择算子</span>
                                          </div>
                                          <div className="draw-config-ref-dropdown-list">
                                            {Array.from(new Set(referenceOptions.map((o) => o.nodeId))).map((nodeId) => {
                                              const nodeOpts = referenceOptions.filter((o) => o.nodeId === nodeId);
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
                                                  <span className="draw-config-ref-item-operator" style={{ flex: 1 }}>
                                                    {nodeName}
                                                  </span>
                                                  <span className="draw-config-ref-item-count">{nodeOpts.length}个参数</span>
                                                </div>
                                              );
                                            })}
                                          </div>
                                        </>
                                      )}

                                      {selectedOperatorForRef && (
                                        <>
                                          <div className="draw-config-ref-dropdown-header">
                                            <span className="draw-config-ref-back" onClick={() => setSelectedOperatorForRef('')}>
                                              ← 返回
                                            </span>
                                            <span className="draw-config-ref-dropdown-param">选择参数</span>
                                          </div>
                                          <div className="draw-config-ref-dropdown-list">
                                            {referenceOptions
                                              .filter((o) => o.nodeId === selectedOperatorForRef)
                                              .map((opt) => (
                                                <div
                                                  key={`${opt.nodeId}_${opt.name}`}
                                                  className={`draw-config-ref-dropdown-item ${param._refValue === opt.name ? 'selected' : ''}`}
                                                  onClick={() => {
                                                    // ✅ 关键修改 3：引用选择器的更新逻辑也改为通过 name 查找
                                                    const refValue = opt.name;
                                                    const newParams = JSON.parse(JSON.stringify(selectedNode.data.input_params.params));
                                                    const targetIdx = newParams.findIndex((p) => p.name === param.name);
                                                    
                                                    if (targetIdx !== -1) {
                                                      newParams[targetIdx] = {
                                                        ...newParams[targetIdx],
                                                        _refValue: refValue,
                                                        _sourceNodeId: opt.nodeId || '',
                                                        _sourceNodeName: opt.nodeName || '',
                                                        _sourceParamName: opt.name || '',
                                                      };
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
                                                    setExpandedRefDropdowns(expandedRefDropdowns.filter((id) => id !== `${selectedNodeId}-${param.name}`));
                                                    setSelectedOperatorForRef('');
                                                  }}
                                                >
                                                  <span className="draw-config-ref-item-dot"></span>
                                                  <span className="draw-config-ref-item-param" style={{ flex: 1 }}>
                                                    {opt.name}
                                                  </span>
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
                              // 2. 手动输入/数据源模式 UI
                              param.name === 'file_path' && param._refType === 'manual' ? (
                                // 特殊处理：文件选择器
                                <input
                                  className="draw-config-value-input"
                                  value={param._value || param.param_value || ''}
                                  placeholder="请选择文件"
                                  title={param._value || param.param_value || ''}
                                  readOnly
                                  style={{ cursor: 'pointer', backgroundColor: '#f8fafc' }}
                                  onClick={async () => {
                                    setFileSelectParamIndex(index); 
                                    await loadDirectories();
                                    setShowFileModal(true);
                                  }}
                                />
                              ) : (
                                // 普通输入框
                               <input
                                className="draw-config-value-input"
                                value={param._refType === 'manual' ? (param._value ?? '') : ''}
                                placeholder={param._refType === 'dataSource' ? '数据源' : '请输入值'}
                                title={param._value ?? param.param_value ?? ''}
                                onChange={(e) => {
                                  const newParams = JSON.parse(JSON.stringify(selectedNode.data.input_params.params));
                                  const targetIdx = newParams.findIndex((p) => p.name === param.name);

                                  if (targetIdx !== -1) {
                                    newParams[targetIdx] = {
                                      ...newParams[targetIdx],
                                      _value: e.target.value, // 允许设为 ''
                                    };
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
                              />
                              )
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })()
            )}

            {/* 输出参数 */}
            {selectedNode.data.output_params?.params && selectedNode.data.output_params.params.length > 0 && (
              <div className="draw-config-params-section">
                <div className="draw-config-section-title">
                  <span className="draw-config-section-bar"></span>
                  <span className="draw-config-section-text">输出参数 </span>
                </div>
                {selectedNode.data.output_params.params.map((param: any, index: number) => (
                  <div key={`output-${index}`} className="draw-config-param-card output-card">
                    <div className="draw-config-param-header">
                      <div className="draw-config-param-name-row">
                        <span className="draw-config-param-name">{param.name}</span>
                      </div>
                      <span className="draw-config-param-type-tag">String</span>
                    </div>
                    {/* 新增输入框 */}
                    <div className="draw-config-param-value-row" style={{ marginTop: '8px' }}>
                      <input
                        className="draw-config-value-input"
                        placeholder="请输入输出值"
                        // 修改点：强制绑定 _value，或者确保优先读取最新的编辑值
                        value={param._value || ''} 
                        onChange={(e) => {
                          const newParams = [...selectedNode.data.output_params.params];
                          // 确保这里更新的是 _value
                          newParams[index] = { ...newParams[index], _value: e.target.value };
                          
                          setNodes((nds) =>
                            nds.map((n) => {
                              if (n.id === selectedNodeId) {
                                return {
                                  ...n,
                                  data: {
                                    ...n.data,
                                    output_params: { ...n.data.output_params, params: newParams },
                                  },
                                };
                              }
                              return n;
                            })
                          );
                        }}
                      />
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

      {/* 文件系统弹窗 */}
      {showFileModal && (
        <div className="file-system-overlay" onClick={() => { setShowFileModal(false); setFileSelectParamIndex(null); }}>
          <div className="file-system-modal" onClick={(e) => e.stopPropagation()}>
            <div className="file-system-header">
              <div className="file-system-title">
                <FolderOpen size={18} />
                <span>{fileSelectParamIndex !== null ? '选择文件' : '文件系统'}</span>
              </div>
              <button className="file-system-close" onClick={() => { setShowFileModal(false); setFileSelectParamIndex(null); }}>
                <X size={18} />
              </button>
            </div>

            <div className="file-system-path-bar">
              <button 
                className="file-system-back-btn" 
                onClick={handleGoBack}
                disabled={!currentDirPath}
              >
                <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} />
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
                  
                  <Upload size={14} />
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
                  <Folder size={48} style={{ color: '#94a3b8' }} />
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
                          <Folder size={18} style={{ color: '#3b82f6' }} />
                        ) : (
                          <FileText size={18} style={{ color: '#64748b' }} />
                        )}
                      </div>
                      <span className="file-system-item-name">{item.name}</span>
                      {item.type === 'file' && fileSelectParamIndex === null && (
                        <button
                          className="file-system-download-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownloadFile(item.path);
                          }}
                        >
                          <Download size={14} />
                        </button>
                      )}
                      {item.type === 'file' && fileSelectParamIndex !== null && (
                        <button
                          className="file-system-select-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectFileForParam(item.path);
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
      {/* 将提示成功信息修改一下位置，避免遮挡 */}
      {saveMessage && (
        <div className="save-message fixed top-[90px] right-4 z-50" >{saveMessage}</div>
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
