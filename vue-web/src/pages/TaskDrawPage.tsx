import React, { useCallback, useState, useRef, memo, useEffect, useMemo } from 'react';
import { shortId } from '../lib/ids';
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
    <div className={`custom-node ${selected ? 'selected' : ''}`}>
      <Handle
        type="target"
        position={Position.Left}
        className="node-handle"
        style={{ top: '50%' }}
      />

      {/* 节点顶部 */}
      <div className="node-header">
          <button className="node-expand-icon-btn" onClick={toggleExpand} title={isExpanded ? '收起参数' : '展开参数'}>
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        <div className="node-header-left">
          <div className="node-icon-wrapper-small">
            <img
              src={resolveIconUrl(data.icon)}
              alt={data.label}
              className="node-icon-small"
            />
          </div>
          <span
            className="node-title-text"
            onClick={(e) => { e.stopPropagation(); data.onSelect?.(id); }}
          >
            {data.label}
          </span>
        </div>
        <div className="node-header-right">
          <button className="node-delete-btn" onClick={handleDeleteClick} title="删除节点">
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
  const [showOperatorModal, setShowOperatorModal] = useState(false);  // 任务ID，保存后获取
  const [taskDescription, setTaskDescription] = useState<string>('');  // 任务描述
  const isInitialized = useRef(false);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isFirstRender = useRef(true);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { zoomIn, zoomOut, fitView, screenToFlowPosition } = useReactFlow();

  // 获取选中的节点
  const selectedNode = nodes.find((m) => m.id === selectedNodeId);

  // 关闭配置面板
  const closeConfigPanel = () => setSelectedNodeId(null);

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
            const skillId = n.skill?.skill_id || n.skill_id;
            
            if (skillId) {
              try {
                const skillRes = await listSkillsDetails(skillId);
                console.log('算子详情:', skillRes);
                if (skillRes.result) {
                  inputParams = skillRes.result.input_params;
                  outputParams = skillRes.result.output_params;
                  skillIconPath = skillRes.result.icon_path || '';
                }
              } catch(e) { console.error('获取算子详情失败:', e); }
            }

            // 合并后端保存的参数值到算子模板参数中
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

            const nodeId = n.node_id || `node-${i+1}`;
            loadedNodes.push({
              id: nodeId,
              type: 'custom',
              position: n.position || { x: START_X + (NODE_WIDTH + NODE_GAP) * i, y: START_Y },
              data: {
                label: n.node_name || n.skill?.skill_name || '未命名节点',
                icon: n.icon_path || skillIconPath || '',
                operatorId: skillId || '',
                description: '',
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
                return (n.data.input_params?.params || []).map((p: any) => {
                  console.log('参数:', p.name, '_value:', p._value, '_refType:', p._refType, '_refValue:', p._refValue);
                  const isRef = p._refType === 'reference';
                  return {
                    param_name: p.name || '',
                    value_mode: isRef ? 'reference' : 'manual',
                    param_type: p.type || '',
                    value_source: 'default',
                    param_value: isRef ? (p._refValue || '') : (p._value || p.param_value || ''),
                    binding_id: isRef ? crypto.randomUUID() : '',
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
                        binding_id: crypto.randomUUID(),
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
          >
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
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
            zoom={1}
            onZoomIn={zoomIn}
            onZoomOut={zoomOut}
            onResetView={fitView}
            edgeType={edgeType}
            onEdgeTypeChange={setEdgeType}
          />

          {/* 右侧参数配置面板 */}
          {selectedNode && (
            <div className="config-panel">
              <div className="config-panel-header">
                <h3>参数配置</h3>
                {/* <div className="config-panel-task-info">
                  <div className="config-task-name">
                    <span className="config-task-value">{taskName}</span>
                  </div>
                  <div className="config-task-desc">
                    <span className="config-task-value">{taskDescription}</span>
                  </div>
                </div> */}
                <button className="config-panel-close" onClick={closeConfigPanel}>
                  <X size={20} />
                </button>
              </div>
              {(() => {
                return (
              <div className="config-panel-body">
                {/* 节点名称 + 编辑按钮 */}
                <div className="config-node-header">
                  <div className="config-node-info">
                    {isEditingNodeName ? (
                      <input
                        className="config-node-name-input"
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
                      <span className="config-node-name">{selectedNode.data.label}</span>
                    )}
                    <button
                      className="edit-name-btn"
                      onClick={() => {
                        setIsEditingNodeName(true);
                        setEditingNodeName(selectedNode.data.label);
                      }}
                      title="编辑节点名称"
                    >
                      <Edit3 size={14} />
                    </button>
                  </div>
                </div>

                {/* 节点描述 */}
                {selectedNode.data.description && (
                  <div className="config-node-desc">
                    <div
                      className={`config-desc-text ${!isDescExpanded && selectedNode.data.description.length > 100 ? 'collapsed' : ''}`}
                      onClick={() => {
                        if (selectedNode.data.description.length > 100) {
                          setIsDescExpanded(!isDescExpanded);
                        }
                      }}
                    >
                      {isDescExpanded || selectedNode.data.description.length <= 100
                        ? selectedNode.data.description
                        : selectedNode.data.description.slice(0, 100) + '...'}
                    </div>
                  </div>
                )}

                {/* 输入参数表格 */}
                {selectedNode.data.input_params?.params && selectedNode.data.input_params.params.length > 0 && (
                  <div className="config-params-section" >
                    <div className="config-params-title" style={{marginTop:'10px'}}>
                      <span className="config-params-title-text">输入</span>
                      {/* <span className="config-params-title-count">{selectedNode.data.input_params.params.length}</span> */}
                    </div>
                    <div className="config-params-table-wrapper">
                      <table className="config-params-table">
                        <thead>
                          <tr>
                            <th className="col-param-name" style={{color:'#999999'}}>参数名</th>
                            <th className="col-ref" style={{color:'#999999'}}>来源</th>
                            <th className="col-value" style={{color:'#999999'}}>值</th>
                            <th className="col-type" style={{color:'#999999'}}>类型</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedNode.data.input_params.params.map((param, index) => (
                            <tr key={`input-${index}`}>
                              <td className="col-param-name">
                                <span className="param-name-text">{param.name}</span>
                              </td>
                              <td className="col-ref">
                                <select
                                  className="config-param-select"
                                  value={param._refType || 'manual'}
                                  onChange={(e) => {
                                    const newRefType = e.target.value;
                                    const newParams = [...selectedNode.data.input_params.params];
                                    // 只有当从引用类型改为其他类型时才清空引用值
                                    // 如果是改为引用类型，保留原有的引用值
                                    const isChangingToReference = newRefType === 'reference' && param._refType !== 'reference';
                                    newParams[index] = {
                                      ...newParams[index],
                                      _refType: newRefType,
                                      _value: newRefType === 'reference' ? '' : (param._value || param.param_value || ''),
                                      _refValue: isChangingToReference ? (referenceOptions.length > 0 ? referenceOptions[0].name : '') : (newRefType === 'reference' ? param._refValue || '' : '')
                                    };

                                    // 如果选择引用，但 referenceOptions 为空，提示用户
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
                              </td>
                              <td className="col-value">
                                {param._refType === 'reference' ? (
                                  <>
                                    {console.log('渲染来源下拉框:', {
                                      paramName: param.name,
                                      refValue: param._refValue,
                                      referenceOptionsCount: referenceOptions.length,
                                      referenceOptions: referenceOptions
                                    })}
                                    <select
                                      className="config-param-select ref-select"
                                      value={param._refValue || ''}
                                    onChange={(e) => {
                                      const selectedOpt = referenceOptions.find(opt => opt.name === e.target.value);
                                      const refValue = e.target.value;
                                      const newParams = [...selectedNode.data.input_params.params];
                                      newParams[index] = { 
                                        ...newParams[index], 
                                        _refValue: refValue,
                                        _sourceNodeId: selectedOpt?.nodeId || '',
                                        _sourceNodeName: selectedOpt?.nodeName || '',
                                        _sourceParamName: selectedOpt?.name || '',
                                      };
                                      console.log('选择引用值:', {
                                        paramName: newParams[index].name,
                                        _refValue: refValue,
                                        _sourceNodeId: selectedOpt?.nodeId,
                                        _sourceNodeName: selectedOpt?.nodeName,
                                        _sourceParamName: selectedOpt?.name,
                                      });
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
                                    {referenceOptions.map((opt) => (
                                      <option key={`${opt.nodeId}_${opt.name}`} value={opt.name}>
                                        {opt.name}
                                      </option>
                                    ))}
                                  </select>
                                  </>
                                ) : (
                                  <input
                                    className="config-param-input"
                                    value={param._value || ''}
                                    placeholder={param._refType === 'dataSource' ? '数据源' : '值'}
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
                              </td>
                              <td className="col-type">
                                <span className="param-type-text">{param.type || '-'}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 输出参数表格 */}
                {selectedNode.data.output_params?.params && selectedNode.data.output_params.params.length > 0 && (
                  <div className="config-params-section">
                    <div className="config-params-title" style={{marginTop:'10px'}}>
                      <span className="config-params-title-text">输出</span>
                    </div>
                    <div className="config-params-table-wrapper">
                      <table className="config-params-table output-table">
                        <thead>
                          <tr>
                            <th className="col-param-name" style={{color:'#999999',width:'100px'}}>参数名</th>
                            <th className="col-type" style={{color:'#999999',width:'100px'}}>类型</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedNode.data.output_params.params.map((param, index) => (
                            <tr key={`output-${index}`}>
                              <td className="col-param-name">
                                <span className="param-name-text">{param.name}</span>
                              </td>
                              <td className="col-type">
                                <span className="param-type-text">{param.type || '-'}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
              );
              })()}
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
