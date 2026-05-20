import { useEffect, useState } from 'react';
import { Icon } from '@iconify/react';
import './TaskManagePage.css';

// ==================== 模拟后端接口 ====================

interface Task {
  id: string;
  name: string;
  description: string;
  creator: string;
  createTime: string;
}

interface ApiResponse {
  code: number;
  message: string;
  data: {
    total: number;
    list: Task[];
  };
}

const taskNames = [
  'Financial_ETL_Core', 'User_Behavior_Analysis', 'Sales_Data_Sync',
  'Inventory_Update', 'Customer_ETL_Pipeline', 'Log_Analysis_Job',
  'Data_Migration_v2', 'Report_Generation', 'Email_Campaign_Analytics',
  'Payment_Processing', 'Fraud_Detection', 'Recommendation_Engine',
];
const descriptions = [
  '处理每日金融交易流水，包含多维清洗与风险校验流程...',
  '分析移动端用户点击流数据，生成实时热力图...',
  '同步各渠道销售数据至中央数据仓库...',
  '实时更新库存状态，触发补货预警...',
  '客户数据清洗与标准化处理流程...',
  '系统日志聚合分析，异常检测...',
];
const creators = ['Admin_System', 'Data_Scientist', 'ETL_Engineer', 'Data_Analyst'];

// 模拟后端 API 请求 - 支持搜索
function fetchTaskListApi(page: number, pageSize: number, keyword?: string): Promise<ApiResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      const allTasks: Task[] = [];
      const total = 421;
      // 生成所有数据
      for (let i = 0; i < total; i++) {
        const day = String(14 - Math.floor(i / 30)).padStart(2, '0');
        const hour = String(9 + (i % 12)).padStart(2, '0');
        const minute = String((i * 7) % 60).padStart(2, '0');
        const second = String((i * 13) % 60).padStart(2, '0');
        allTasks.push({
          id: `PL_${String(i + 1).padStart(6, '0')}`,
          name: taskNames[i % taskNames.length],
          description: descriptions[i % descriptions.length],
          creator: creators[i % creators.length],
          createTime: `2026-04-${day} ${hour}:${minute}:${second}`,
        });
      }
      // 搜索过滤
      let filtered = allTasks;
      if (keyword && keyword.trim()) {
        const kw = keyword.toLowerCase();
        filtered = allTasks.filter(t => 
          t.name.toLowerCase().includes(kw) || 
          t.id.toLowerCase().includes(kw)
        );
      }
      // 分页
      const start = (page - 1) * pageSize;
      const records = filtered.slice(start, start + pageSize);
      resolve({
        code: 200,
        message: 'success',
        data: { total: filtered.length, list: records },
      });
    }, 400);
  });
}


// 模拟创建任务 API
function createTaskApi(name: string, description: string): Promise<{ code: number; message: string }> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: '创建成功' });
    }, 800);
  });
}

// 模拟删除任务 API
function deleteTaskApi(taskId: string): Promise<{ code: number; message: string }> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: '删除成功' });
    }, 600);
  });
}

// ==================== 页面组件 ====================

export function TaskManagePage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTaskName, setNewTaskName] = useState('');
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Task | null>(null);
  const [deleting, setDeleting] = useState(false);
  const pageSize = 10;
  const totalPages = Math.ceil(total / pageSize);

  // 请求后端数据
  const loadData = async (page: number, keyword?: string) => {
    setLoading(true);
    try {
      const res = await fetchTaskListApi(page, pageSize, keyword);
      if (res.code === 200) {
        setTasks(res.data.list);
        setTotal(res.data.total);
      }
    } catch (err) {
      console.error('请求失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 搜索防抖 + 分页变化，统一请求数据
  useEffect(() => {
    const timer = setTimeout(() => {
      loadData(currentPage, searchKeyword);
    }, searchKeyword ? 500 : 0);
    return () => clearTimeout(timer);
  }, [currentPage, searchKeyword]);

  // 创建任务
  const handleCreateTask = () => {
    const name = newTaskName.trim();
    if (!name) return;
    setSubmitting(true);
    createTaskApi(name, newTaskDesc).then((res) => {
      if (res.code === 200) {
        setShowCreateModal(false);
        setNewTaskName('');
        setNewTaskDesc('');
      }
      setSubmitting(false);
      setCurrentPage(1);
    }).catch(() => {
      setSubmitting(false);
    });
  };

  // 打开删除确认弹窗
  const handleDeleteClick = (task: Task) => {
    setDeleteTarget(task);
    setShowDeleteModal(true);
  };

  // 确认删除
  const handleConfirmDelete = () => {
    if (!deleteTarget) return;
    setDeleting(true);
    deleteTaskApi(deleteTarget.id).then((res) => {
      if (res.code === 200) {
        setShowDeleteModal(false);
        setDeleteTarget(null);
        setDeleting(false);
        // 刷新当前页数据
        loadData(currentPage, searchKeyword);
      }
    }).catch(() => {
      setDeleting(false);
    });
  };

  // 生成分页按钮
  const getPageNumbers = () => {
    const pages: number[] = [];
    const maxVisible = 5;
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <div className="task-manage-page">
      {/* 页面标题 */}
      <div className="page-header">
        <h1 className="page-title">任务管理</h1>
        <div className="page-actions">
          <div className="search-box">
            <Icon icon="fa-solid:search" width="16" className="search-icon" />
            <input
              type="text"
              placeholder="搜索任务名称..."
              value={searchKeyword}
              onChange={(e) => {
                setSearchKeyword(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          <button className="create-btn" onClick={() => setShowCreateModal(true)}>
            <Icon icon="fa-solid:plus" width="14" />
            <span>新建任务</span>
          </button>
        </div>
      </div>

      {/* 数据表格 */}
      <div className="data-table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <span>正在加载数据...</span>
          </div>
        ) : tasks.length === 0 ? (
          <div className="empty-state">暂无数据</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>任务名称</th>
                <th>描述</th>
                <th>创建人</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td className="name-cell">
                    <div className="task-name">{task.name}</div>
                    <div className="task-id">ID: {task.id}</div>
                  </td>
                  <td className="desc-cell">{task.description}</td>
                  <td className="creator-cell">{task.creator}</td>
                  <td className="time-cell">{task.createTime}</td>
                  <td className="action-cell">
                    <button className="icon-btn" title="查看" onClick={() => window.location.href = '/run-details'}>
                      <Icon icon="fa-solid:eye" width="14" />
                    </button>
                    <button className="icon-btn" title="编辑">
                      <Icon icon="fa-solid:edit" width="14" />
                    </button>
                    <button className="icon-btn" title="删除" onClick={() => handleDeleteClick(task)} style={{color: '#ef4444'}}>
                      <Icon icon="fa-solid:trash" width="14" />
                    </button>
                    <button className="icon-btn primary" title="运行">
                      <Icon icon="fa-solid:play" width="14" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 分页 */}
        {!loading && tasks.length > 0 && (
          <div className="pagination">
            <span className="pagination-info">
              显示第 {(currentPage - 1) * pageSize + 1} 到 {Math.min(currentPage * pageSize, total)} 条，共 {total.toLocaleString()} 条任务
            </span>
            <div className="pagination-controls">
              <button
                className="page-btn"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                上一页
              </button>
              {getPageNumbers().map((page) => (
                <button
                  key={page}
                  className={`page-btn ${page === currentPage ? 'active' : ''}`}
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </button>
              ))}
              {currentPage < totalPages - 2 && <span className="page-ellipsis">...</span>}
              {totalPages > 5 && (
                <button
                  className={`page-btn ${currentPage === totalPages ? 'active' : ''}`}
                  onClick={() => setCurrentPage(totalPages)}
                >
                  {totalPages}
                </button>
              )}
              <button
                className="page-btn"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 新建任务弹窗 */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="task-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>新建任务</h3>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>
                <Icon icon="fa-solid:times" width="16" />
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>任务名称</label>
                <input
                  type="text"
                  placeholder="请输入名称，例如：数据同步_核心库"
                  value={newTaskName}
                  onChange={(e) => setNewTaskName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>描述信息</label>
                <textarea
                  rows={4}
                  placeholder="描述此流水线的主要功能与数据来源..."
                  value={newTaskDesc}
                  onChange={(e) => setNewTaskDesc(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-cancel" onClick={() => setShowCreateModal(false)} disabled={submitting}>
                取消
              </button>
              <button className={`btn-confirm ${submitting ? 'is-loading' : ''}`} onClick={handleCreateTask} disabled={submitting}>
                {submitting && <span className="btn-spinner"></span>}
                {submitting ? '创建中...' : '确定创建'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 删除确认弹窗 */}
      {showDeleteModal && deleteTarget && (
        <div className="modal-overlay" onClick={() => { if (!deleting) { setShowDeleteModal(false); setDeleteTarget(null); } }}>
          <div className="task-modal-content delete-modal" onClick={(e) => e.stopPropagation()}>
            <div className="delete-modal-body">
              <div className="delete-icon-wrap">
                <Icon icon="fa-solid:trash-alt" width="28" />
              </div>
              <h3 className="delete-title">确认删除</h3>
              <p className="delete-desc">
                您确定要删除任务 <strong>{deleteTarget.name}</strong> 吗？此操作不可逆，将同步移除关联的定时调度任务。
              </p>
            </div>
            <div className="delete-modal-footer">
              <button className="btn-cancel" onClick={() => { setShowDeleteModal(false); setDeleteTarget(null); }} disabled={deleting}>
                取消
              </button>
              <button className={`btn-danger ${deleting ? 'is-loading' : ''}`} onClick={handleConfirmDelete} disabled={deleting}>
                {deleting && <span className="btn-spinner"></span>}
                {deleting ? '删除中...' : '确认删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
