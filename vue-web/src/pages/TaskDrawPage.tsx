import React, { useCallback, useState, useRef, memo, useEffect, useMemo } from 'react';
import { shortId, generateUUID } from '../lib/ids';
import { saveDrawInfo, getAllSkills, listSkillsDetails, getDrawTaskContent, apiBase } from "../lib/api";

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
import { useNavigate } from 'react-router-dom';
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
import '../components/Draw.css';

// ==================== 类型定义 ====================

interface NodeData {
  label: string;
  icon: string;
  operatorId: string;
  operatorName?: string;
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

// 算子分类数据（从后端接口获取后赋值）
let operatorCategories: {
  groupName: string;
  DagSkillInfoList: { skill_id: string; skill_name: string; name_zh: string; icon_path: string; skill_type: string; description?: string }[];
}[] = [];

// ==================== 自定义节点组件 ====================

const CustomNode: React.FC<NodeProps<NodeData>> = ({ id, data, selected }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = () => {
    data.onDelete?.(id);
    setShowDeleteConfirm(false);
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
        <span className="node-param-value">{getDisplayValue(key, value)}</span>
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
          <button className="node-expand-icon-btn" onClick={toggleExpand} title={isExpanded ? '收起参数' : '展开参数'}>
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
        <div className="node-params-panel">
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
                  <div className="node-param-value">{inputItem.param_value || '-'}</div>
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
                  <div className="node-param-value">{outputItem.type}</div>
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
        style={{ top: '50%' }}
      />

      {/* 删除确认弹窗 */}
      {showDeleteConfirm && (
        <div className="delete-confirm-overlay" onClick={() => setShowDeleteConfirm(false)}>
          <div className="delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="delete-confirm-header">
              <div className="delete-confirm-icon">!</div>
              <h3>确认删除此节点?</h3>
              <button className="delete-confirm-close" onClick={() => setShowDeleteConfirm(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="delete-confirm-body">
              <p>删除节点后会影响您当前组件的运行结果,请谨慎操作。</p>
            </div>
            <div className="delete-confirm-footer">
              <div className="delete-confirm-actions">
                <button className="delete-confirm-cancel" onClick={() => setShowDeleteConfirm(false)}>
                  取消
                </button>
                <button className="delete-confirm-confirm" onClick={handleConfirmDelete}>
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
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

// ==================== 自定义连线组件 ====================

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

// ==================== 节点和连线类型配置 ====================

const nodeTypes = {
  custom: MemoizedCustomNode,
  comment: MemoizedCommentNode,
};

const edgeTypes = {
  custom: CustomEdge,
};

// 节点间距配置
const NODE_WIDTH = 285;
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
      label: '空行清理',
      icon: 'Eraser',
      operatorId: 'empty-clean',
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

// ==================== 底部工具栏组件 ====================

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

// ==================== 算子库弹窗组件 ====================

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
  const handleDragStart = (e: React.DragEvent, operator: { skill_id: string; skill_name: string; name_zh: string; icon_path: string; skill_type: string; description?: string }) => {
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

// ==================== TaskDrawPage Props ====================

export interface TaskDrawPageProps {
  taskId: string;
  taskName: string;
  isEdit: boolean;
}

// ==================== 主画布组件 ====================

const FlowEditorInner: React.FC<TaskDrawPageProps> = ({ taskId: taskIdProp, taskName, isEdit }) => {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isOperatorLibraryOpen, setIsOperatorLibraryOpen] = useState(false);
  const [edgeType, setEdgeType] = useState<'bezier' | 'straight'>('bezier');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);  // 添加：加载状态
  const [operatorList, setOperatorList] = useState(operatorCategories);
  const [referenceOptions, setReferenceOptions] = useState<{ name: string; type: string; description: string; nodeId: string; nodeName: string }[]>([]);  // 来源下拉选项
  const [isLoadingReferences, setIsLoadingReferences] = useState(false);   // 加载来源状态
  const [taskId, setTaskId] = useState<string>('');
  const [isEditingNodeName, setIsEditingNodeName] = useState(false);
  const [editingNodeName, setEditingNodeName] = useState('');
  const [isDescExpanded, setIsDescExpanded] = useState(false);
  const [expandedRefDropdowns, setExpandedRefDropdowns] = useState<string[]>([]);
  const [showOperatorModal, setShowOperatorModal] = useState(false);  // 任务ID，保存后获取
  const [taskDescription, setTaskDescription] = useState<string>('');  // 任务描述
  const [zoomLevel, setZoomLevel] = useState(1);
  const isInitialized = useRef(false);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isFirstRender = useRef(true);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { zoomIn, zoomOut, fitView, screenToFlowPosition } = useReactFlow();

  // 获取选中的节点
  const selectedNode = nodes.find((m) => m.id === selectedNodeId);

  // 关闭配置面板
  const closeConfigPanel = () => {
    setNodes((nds) => nds.map((n) => ({ ...n, selected: false })));
    setSelectedNodeId(null);
  };

  // 删除选中节点
  const handleDeleteNode = () => {
    if (selectedNodeId) {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
      setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId));
      setSelectedNodeId(null);
    }
    setShowDeleteModal(false);
  };

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

  // Set initial taskId from props
  useEffect(() => {
    if (taskIdProp) {
      setTaskId(taskIdProp);
    }
  }, [taskIdProp]);

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

  // 编辑模式：加载画板数据
  useEffect(() => {
    if (!isEdit || !taskIdProp) return;

    const loadDSL = async () => {
      setIsLoading(true);
      try {
        const res = await getDrawTaskContent(taskIdProp);
        console.log('API返回:', res);
        if (res.code === 200 && res.result) {
          const dsl = res.result;
          // Convert DSL nodes to ReactFlow nodes
          const loadedNodes: Node<NodeData>[] = [];
          const loadedEdges: Edge[] = [];

          console.log('DSL数据:', dsl);
          console.log('节点数量:', dsl.nodes?.length);
          
          for (let i = 0; i < (dsl.nodes || []).length; i++) {
            const n = dsl.nodes[i];
            console.log('处理节点:', n);
            
            // Get skill details - use skill_id
            let inputParams = undefined;
            let outputParams = undefined;
            let skillIconPath = '';
            let skillDescription = '';
            const skillId = n.skill?.skill_id || n.skill_id;
            
            // 对于source_stop和sink_stop这两个特殊算子，不要请求接口，使用固定的参数
            const isSpecialSkill = skillId === 'cn.piflow.engine.local.source_file_stop.SourceFileStop' || 
                                    skillId === 'cn.piflow.engine.local.file_save_stop.FileSaveStop';
            
            if (isSpecialSkill) {
              console.log(`节点 ${i}: 特殊算子，不请求接口`);
              
              if (skillId === 'cn.piflow.engine.local.source_file_stop.SourceFileStop') {
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
              }
            } else {
              if (skillId) {
                try {
                  const skillRes = await listSkillsDetails(skillId);
                  console.log('算子详情:', skillRes);
                  if (skillRes.result) {
                    inputParams = skillRes.result.input_params;
                    outputParams = skillRes.result.output_params;
                    skillIconPath = skillRes.result.icon_path || '';
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
                } catch(e) { console.error('获取算子详情失败:', e); }
              }
              
              // 检查是否有 required 字段，没有的话再用 getAllSkills 获取
              const hasRequiredField = inputParams?.params?.some((p: any) => p.required !== undefined);
              if (!hasRequiredField) {
                try {
                  const skillName = n.skill?.skill_name || n.skill_name || n.node_name || '';
                  const listRes = await getAllSkills(skillName);
                  if (listRes.result?.data && listRes.result.data.length > 0) {
                    const skillData = listRes.result.data[0].DagSkillInfoList?.find((s: any) =>
                      s.skill_id === skillId || s.skill_name === skillName
                    ) || listRes.result.data[0].DagSkillInfoList[0];
                    if (skillData?.input_params?.params?.some((p: any) => p.required !== undefined)) {
                      console.log('使用 getAllSkills 获取参数模板 (含 required):', skillData.input_params);
                      inputParams = skillData.input_params;
                      outputParams = skillData.output_params || outputParams;
                      skillIconPath = skillData.icon_path || skillIconPath;
                      skillDescription = skillData.description || skillDescription;
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
                  }
                } catch(e) { console.error('getAllSkills 失败:', e); }
              }
            }

            // 合并后端保存的参数值到算子模板参数中
            const nodeId = n.node_id || `node-${i+1}`;
            let mergedInputParams = inputParams;
            if (inputParams?.params && n.input_params && Array.isArray(n.input_params)) {
              const savedParamsMap: Record<string, any> = {};
              n.input_params.forEach((sp: any) => {
                savedParamsMap[sp.param_name] = sp;
              });
              mergedInputParams = {
                ...inputParams,
                params: inputParams.params.map((tp: any) => {
                  const saved = savedParamsMap[tp.name];
                  const isReference = saved?.value_mode === 'reference';
                  return {
                    ...tp,
                    _refType: isReference ? 'reference' : 'manual',
                    _value: isReference ? '' : (saved?.param_value || tp.param_value || ''),
                    _refValue: isReference ? (saved?.param_value || '') : '',
                  };
                }),
              };
              console.log('合并后参数:', JSON.stringify(mergedInputParams, null, 2));
            }

            loadedNodes.push({
              id: nodeId,
              type: 'custom',
              position: n.position || { x: START_X + (NODE_WIDTH + NODE_GAP) * i, y: START_Y },
              data: {
                label: n.node_name || n.skill?.skill_name || '未命名节点',
                icon: n.icon_path || skillIconPath || '',
                operatorId: skillId || '',
                operatorName: n.skill?.skill_name || '',
                operatorType: n.skill?.skill_type || '',
                description: skillDescription,
                params: {},
                inputVar: 'input_data',
                outputVar: 'output_data',
                input_params: mergedInputParams,
                output_params: outputParams,
                onDelete: (delId: string) => {
                  setNodes((nds) => nds.filter((nn) => nn.id !== delId));
                  setEdges((eds) => eds.filter((e) => e.source !== delId && e.target !== delId));
                },
                onUpdateParams: (updId: string, params: Record<string, any>) => {
                  setNodes((nds) => nds.map((nn) => nn.id === updId ? { ...nn, data: { ...nn.data, params } } : nn));
                },
                onSelect: (selId: string) => { setSelectedNodeId(selId); setShowOperatorModal(false); },
              },
            });
          }
          
          console.log('加载的节点:', loadedNodes);
          console.log('加载的边:', loadedEdges);

          // Convert DSL edges
          for (const e of (dsl.edges || [])) {
            loadedEdges.push({
              id: e.edge_id || e.from_node_id + '-' + e.to_node_id,
              source: e.from_node_id,
              target: e.to_node_id,
              type: 'custom',
              data: { edgeType: 'bezier', onDelete: (delId: string) => { setEdges((eds) => eds.filter((ee) => ee.id !== delId)); } },
            });
          }

          nodeIdCounter.current = loadedNodes.length;
          setNodes(loadedNodes);
          setEdges(loadedEdges);
          
          // 获取任务描述
          if (dsl.task && dsl.task.description) {
            setTaskDescription(dsl.task.description);
          }
          
          isInitialized.current = true;
          setTimeout(() => { fitView({ padding: 0.2 }); }, 200);
        }
      } catch(err) {
        console.error('加载画板失败:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDSL();
  }, [isEdit, taskIdProp]);

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

    //   console.log('从后端获取画板数据:', { nodes: fetchedNodes, edges: fetchedEdges });

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
      if(resAllSkills.code === 200){
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
        setOperatorList(fixArr.concat(resAllSkills.result.data));
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
      if (upstreamNode.data.output_params?.params) {
        upstreamNode.data.output_params.params.forEach((param: any) => {
          allOutputParams.push({
            name: param.name || param.param_name || '',
            type: param.type || param.param_type || 'string',
            description: param.description || '',
            nodeId: upstreamNode.id,
            nodeName: upstreamNode.data.label || '',
          });
        });
      }
    });

    setReferenceOptions(allOutputParams);
    console.log('引用变量选项:', allOutputParams);
    setIsLoadingReferences(false);
  }, [edges, nodes]);

  // 当选中节点时，获取上游节点的出参数据（用于来源下拉）
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
      nodeIdCounter.current += 1;
      const uniqueLabel = generateUniqueLabel(operator.name_zh);

      // 请求算子详情获取 input_params 和 output_params
      let inputParams = undefined;
      let outputParams = undefined;
      let operatorIconPath = operator.icon_path;
      try {
        const res = await listSkillsDetails(operator.skill_id);
        if (res.result) {
          inputParams = res.result.input_params;
          outputParams = res.result.output_params;
          operatorIconPath = res.result.icon_path || operatorIconPath;
        }
      } catch (error) {
        console.error('获取算子详情失败:', error);
      }
      
      // 检查是否有 required 字段，没有的话用 getAllSkills 回退
      const hasRequiredField = inputParams?.params?.some((p: any) => p.required !== undefined);
      if (!hasRequiredField) {
        try {
          const listRes = await getAllSkills(operator.skill_name);
          if (listRes.result?.data && listRes.result.data.length > 0) {
            const skillData = listRes.result.data[0].DagSkillInfoList?.find((s: any) =>
              s.skill_id === operator.skill_id || s.skill_name === operator.skill_name
            ) || listRes.result.data[0].DagSkillInfoList[0];
            if (skillData?.input_params?.params?.some((p: any) => p.required !== undefined)) {
              inputParams = skillData.input_params;
              outputParams = skillData.output_params || outputParams;
              operatorIconPath = skillData.icon_path || operatorIconPath;
              console.log('handleAddNode: 使用 getAllSkills 参数模板 (含 required):', inputParams);
            }
          }
        } catch (e) { console.error('handleAddNode: getAllSkills 失败:', e); }
      }
      const newNode: Node<NodeData> = {
        id: `node-${nodeIdCounter.current}`,
        type: 'custom',
        position: position || {
          x: START_X + (NODE_WIDTH + NODE_GAP) * (nodes.length),
          y: START_Y,
        },
        data: {
          label: uniqueLabel,
          icon: operatorIconPath,
          operatorId: operator.skill_id,
          operatorName: operator.skill_name || '',
          operatorType: operator.skill_type || '',
          description: operator.description || getOperatorDescription(operator.skill_id),
          params: getDefaultParams(operator.skill_id),
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
      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes, setEdges, nodes.length, generateUniqueLabel]
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
      // 检查 nodes 中是否有引用类型的参数
      console.log('=== 保存前检查 ===');
      console.log('edges 数量:', edges.length);
      console.log('edges:', edges);
      console.log('nodes:', nodes.map(n => ({ id: n.id, label: n.data.label })));

      console.log('=== 保存前检查 nodes ===');
      nodes.forEach(node => {
        if (node.data.input_params?.params) {
          node.data.input_params.params.forEach(param => {
            console.log('Node:', node.id, 'Param:', param.name, '_refType:', param._refType, '_refValue:', param._refValue);
          });
        }
      });

      // 构造请求参数（按照接口文档结构）
      const params = {
        dsl_version: "1.0",
        task: {
          dag_task_id: taskId || '',  // 有则更新，无则创建
          dag_task_name: taskName,
          // description: '',
          // message_id: ''
        },
        nodes: nodes
            .filter(n => n.type !== 'comment')  // 过滤掉注释节点
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
                x: Math.round(n.position.x),
                y: Math.round(n.position.y),
              },
              input_params: (() => {
                console.log('=== 节点参数保存 ===');
                console.log('节点ID:', n.id, '节点名:', n.data.label);
                console.log('input_params原始数据:', JSON.stringify(n.data.input_params?.params, null, 2));
                return (n.data.input_params?.params || [])
                  .filter((p: any) => {
                    if (p._refType === 'reference') return true;
                    const val = String(p._value || p.param_value || '');
                    return val.trim() !== '';
                  })
                  .map((p: any) => {
                  console.log('参数:', p.name, '_value:', p._value, '_refType:', p._refType, '_refValue:', p._refValue);
                  const isRef = p._refType === 'reference';
                  return {
                    param_name: p.name || '',
                    value_mode: isRef ? 'reference' : 'manual',
                    param_type: p.type || '',
                    value_source: 'default',
                    param_value: isRef ? (p._refValue || '') : (p._value || p.param_value || ''),
                    binding_id: isRef ? generateUUID() : '',
                  };
                });
              })(),
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
          bindings: (() => {
            const bindingsList = [];

            console.log('=== bindings 生成 ===');
            console.log('edges 数量:', edges.length);
            console.log('edges 数据:', edges);
            console.log('nodes 数量:', nodes.length);

            // 遍历所有节点，查找有来源类型参数的节点
            nodes.forEach(node => {
              if (node.data.input_params?.params) {
                node.data.input_params.params.forEach(param => {
                  // 如果参数的来源类型是"引用"，则生成 binding（不检查 _refValue 是否有值）
                  if (param._refType === 'reference') {
                    // 找到上游节点（通过 edges 找到指向当前节点的边）
                    const upstreamEdge = edges.find(e => e.target === node.id);
                    if (upstreamEdge) {
                      // _refValue 的格式可能是 "paramName（type）"，需要提取参数名
                      // 如果 _refValue 为空，使用上游节点的第一个出参名称
                      let refParamName = param._refValue;
                      if (!refParamName) {
                        // 从上游节点的 output_params 中获取第一个参数名
                        const upstreamNode = nodes.find(n => n.id === upstreamEdge.source);
                        refParamName = upstreamNode?.data.output_params?.params?.[0]?.name || '';
                      } else if (refParamName.includes('（')) {
                        refParamName = refParamName.split('（')[0];
                      }

                      const binding = {
                        // binding_id: param._refValue || `binding_${upstreamEdge.source}_${node.id}_${param.name}`,
                        binding_id: generateUUID(),
                        from_node_id: upstreamEdge.source,
                        from_param_name: refParamName.trim() || param.name,
                        to_node_id: node.id,
                        to_param_name: param.name || '',
                      };
                      console.log('生成 binding:', binding);
                      bindingsList.push(binding);
                    }
                  }
                });
              }
            });
            return bindingsList;
          })()
      };

      console.log('保存画板请求参数:', params);

      setIsSaving(true);
      setSaveMessage('');

      try {
        // 调用保存接口
        const res = await saveDrawInfo(params);
        console.log('保存接口返回:', res);

        // 如果返回了任务ID，保存起来
        if (res?.result?.dag_task_id) {
          setTaskId(res.result.dag_task_id);
        }

        setIsSaving(false);
        setSaveMessage('已自动保存');
      } catch (error) {
        console.error('保存失败:', error);
        setIsSaving(false);
        setSaveMessage('保存失败');
      }

      // 3秒后清除消息
      setTimeout(() => {
        setSaveMessage('');
      }, 3000);
    }, 800);

    // 清理定时器
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [nodes, edges]);

  // 处理拖拽进入画布
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    setIsDragOver(true);
  }, []);

  // 处理拖拽离开画布
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  // 处理拖拽放置到画布
  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);

      const data = e.dataTransfer.getData('application/json');
      if (!data) return;

      try {
        const operator: DraggedOperator = JSON.parse(data);

        // 计算放置位置(转换为画布坐标)
        const position = screenToFlowPosition({
          x: e.clientX,
          y: e.clientY,
        });

        // 调整位置使节点中心对准鼠标位置
        const adjustedPosition = {
          x: position.x - NODE_WIDTH / 2,
          y: position.y - 40,
        };

        await handleAddNode(operator, adjustedPosition);
      } catch (error) {
        console.error('Failed to parse dragged operator:', error);
      }
    },
    [handleAddNode, screenToFlowPosition]
  );

  return (
    <div className="flow-canvas-container">
      {/* 加载中显示 */}
      {isLoading && (
        <div className="flow-loading-overlay">
          <div className="flow-loading-content">
            <div className="flow-loading-spinner"></div>
            <span>加载画板数据...</span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flow-header">
        <div className="header-left">
          <h2>{taskName}</h2>
          <span className="header-desc">{taskDescription}</span>
        </div>
        <div className="header-right">
          <span className="auto-save-status">
            {isSaving && <span className="save-saving">保存中...</span>}
            {!isSaving && saveMessage && <span className="save-message">{saveMessage}</span>}
            {!isSaving && !saveMessage && <span className="save-idle">已保存</span>}
          </span>
          {/* <button className="run-btn" onClick={()=>{
            saveDrawInfo()
          }}>
            <Play size={16} fill="currentColor" />
            <span>保存</span>
          </button> */}
          <button className="config-panel-close" onClick={() => navigate(-1)}>
            <span>返回</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flow-content">
        <div
          className="reactflow-wrapper"
          ref={reactFlowWrapper}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            position: 'relative',
            width: '100%',
            height: '100%',
          }}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            deleteKeyCode={null}
            onViewportChange={(viewport: any) => setZoomLevel(viewport.zoom)}
          >
            <Background variant={BackgroundVariant.Dots} gap={36} size={1.5} />
          </ReactFlow>

          {/* 拖拽时的视觉反馈遮罩 */}
          {isDragOver && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(24, 144, 255, 0.1)',
                border: '2px dashed #1890ff',
                pointerEvents: 'none',
                zIndex: 1000,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  background: '#1890ff',
                  color: '#fff',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: 500,
                }}
              >
                释放以创建节点
              </div>
            </div>
          )}

          {/* Operator Library Modal */}
          {isOperatorLibraryOpen && (
            <OperatorLibraryModal
              isOpen={isOperatorLibraryOpen}
              onClose={() => setIsOperatorLibraryOpen(false)}
              onAddNode={handleAddNode}
              operatorList={operatorList}
            />
          )}

          {/* Floating Toolbar */}
          <FloatingToolbar
            onOpenOperatorLibrary={() => setIsOperatorLibraryOpen(true)}
            onAddComment={handleAddComment}
            zoom={zoomLevel}
            onZoomIn={zoomIn}
            onZoomOut={zoomOut}
            onResetView={fitView}
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
                        const trimmedName = editingNodeName.trim();
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
                    {/* <ChevronDown className={`draw-config-desc-arrow ${isDescExpanded ? 'expanded' : ''}`} size={14} /> */}
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
                                    const newExpandedRefs = [...expandedRefDropdowns];
                                    const idx = newExpandedRefs.indexOf(`${selectedNodeId}-${param.name}`);
                                    if (idx > -1) {
                                      newExpandedRefs.splice(idx, 1);
                                    } else {
                                      newExpandedRefs.push(`${selectedNodeId}-${param.name}`);
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
                                    <div className="draw-config-ref-dropdown-header">
                                      <span>算子</span>
                                      <span>参数</span>
                                    </div>
                                    {referenceOptions.length === 0 ? (
                                      <div className="draw-config-ref-dropdown-empty">暂无可用引用</div>
                                    ) : (
                                      referenceOptions.map((opt) => (
                                        <div
                                          key={`${opt.nodeId}_${opt.name}`}
                                          className="draw-config-ref-dropdown-item"
                                          onClick={() => {
                                            const newParams = [...selectedNode.data.input_params.params];
                                            newParams[index] = {
                                              ...newParams[index],
                                              _refValue: opt.name,
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
                                            setExpandedRefDropdowns(expandedRefDropdowns.filter(id => id !== `${selectedNodeId}-${param.name}`));
                                          }}
                                        >
                                          <span className="draw-config-ref-item-dot"></span>
                                          <span className="draw-config-ref-item-operator">{opt.nodeName || opt.nodeId}</span>
                                          <div className="draw-config-ref-item-param-wrapper">
                                            <span className="draw-config-ref-item-param">{opt.name}</span>
                                            <span className="draw-config-ref-item-type">{opt.type}</span>
                                          </div>
                                        </div>
                                      ))
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

          {/* 删除确认弹窗 */}
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
        </div>
      </div>
    </div>
  );
};

// ==================== 辅助函数 ====================

const getOperatorDescription = (id: string): string => {
  const descriptions: Record<string, string> = {
    'file-upload': 'CSV文件',
    'empty-clean': '移除空行',
    'space-clean': '移除多余空格',
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
      format: 'csv',
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

// ==================== 导出组件 ====================

const TaskDrawPageWrapper: React.FC<TaskDrawPageProps> = (props) => {
  return (
    <ReactFlowProvider>
      <FlowEditorInner {...props} />
    </ReactFlowProvider>
  );
};
export { TaskDrawPageWrapper as TaskDrawPage };
