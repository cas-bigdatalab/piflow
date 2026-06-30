import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Icon } from '@iconify/react';
import { getTasks, createTask, updateTask, deleteTask, Task,runDAGTask } from '../lib/api';
import { toast } from '../components/Toast';
import './TaskManagePage.css';

// ==================== 页面组件 ====================

export function TaskManagePage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTaskName, setNewTaskName] = useState('');
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [newTaskNameError, setNewTaskNameError] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Task | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editTarget, setEditTarget] = useState<Task | null>(null);
  const [editTaskName, setEditTaskName] = useState('');
  const [editTaskDesc, setEditTaskDesc] = useState('');
  const [editTaskNameError, setEditTaskNameError] = useState(false);
  const [updating, setUpdating] = useState(false);
  const pageSize = 10;
  const totalPages = Math.ceil(total / pageSize);


  // 在 TaskManagePage.tsx 中，替换 handleRun 为：
  const handleRun = async (taskId: string, taskName: string) => {
    try {
      const response = await runDAGTask(taskId);
      if (response.code === 200 && response.result) {
        const processId = response.result.process_id;
        toast.success(`任务「${taskName}」已提交运行，请前往【运行历史】查看执行状态。执行实例ID：${processId}`);
      } else {
        toast.error('运行失败: ' + (response.message || '未知错误'));
      }
    } catch (error) {
      console.error('运行任务失败:', error);
      toast.error('操作失败: ' + (error instanceof Error ? error.message : '未知错误'));
    }
  };

  // 请求后端数据
  const loadData = async (page: number, keyword?: string) => {
    setLoading(true);
    try {
      const res = await getTasks(page, pageSize, keyword);
      if (res.code === 200) {
        setTasks(res.result.data);
        setTotal(res.result.total);
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
  const handleCreateTask = async () => {
    const trimmedName = newTaskName.trim();
    if (!trimmedName) {
      setNewTaskNameError(true);
      return;
    }
    setNewTaskNameError(false);
    setSubmitting(true);
    try {
      let params={
        task_name:trimmedName,
        description:newTaskDesc
      }
      let res = await createTask(params);
      if (res.code === 200) {
        setShowCreateModal(false);
        setNewTaskName('');
        setNewTaskDesc('');
        setNewTaskNameError(false);
        toast.success('创建成功');
        // 跳转到画板页面
        if (res.result?.dag_task_id) {
          navigate(`/task-draw?taskId=${res.result.dag_task_id}&taskName=${encodeURIComponent(trimmedName)}&description=${encodeURIComponent(newTaskDesc)}`);
        } else {
          // 刷新列表
          await loadData(1, searchKeyword);
        }
      } else {
        toast.error(res.message || '创建失败');
      }
    } catch (err) {
      console.error('创建失败:', err);
      toast.error('创建失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  // 打开删除确认弹窗
  const handleDeleteClick = (task: Task) => {
    setDeleteTarget(task);
    setShowDeleteModal(true);
  };

  // 确认删除
  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await deleteTask(deleteTarget.dag_task_id);
      if (res.code === 200) {
        setShowDeleteModal(false);
        setDeleteTarget(null);
        // 刷新当前页数据
        await loadData(currentPage, searchKeyword);
      } else {
        // 显示接口返回的错误消息
        toast.error(res.message || '删除失败');
      }
    } catch (err) {
      console.error('删除失败:', err);
      toast.error('删除失败，请稍后重试');
    } finally {
      setDeleting(false);
    }
  };

  // 打开编辑弹窗
  const handleEditClick = (task: Task) => {
    setEditTarget(task);
    setEditTaskName(task.dag_task_name);
    setEditTaskDesc(task.description || '');
    setShowEditModal(true);
  };

  // 确认编辑
  const handleConfirmEdit = async () => {
    if (!editTarget) return;
    const name = editTaskName.trim();
    if (!name) {
      setEditTaskNameError(true);
      return;
    }
    setEditTaskNameError(false);
    setUpdating(true);
    try {
      const res = await updateTask(editTarget.dag_task_id, name, editTaskDesc);
      if (res.code === 200) {
        setShowEditModal(false);
        setEditTarget(null);
        setEditTaskName('');
        setEditTaskDesc('');
        setEditTaskNameError(false);
        // 刷新当前页数据
        await loadData(currentPage, searchKeyword);
      } else {
        toast.error(res.message || '更新失败');
      }
    } catch (err) {
      console.error('更新失败:', err);
      toast.error('更新失败，请稍后重试');
    } finally {
      setUpdating(false);
    }
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
                <tr key={task.dag_task_id}>
                  <td className="name-cell">
                    <div className="task-name">{task.dag_task_name}</div>
                    <div className="task-id">ID: {task.dag_task_id}</div>
                  </td>
                  <td className="desc-cell">{task.description || '-'}</td>
                  <td className="creator-cell">{task.create_user_id || 'System'}</td>
                  <td className="time-cell">{task.create_time}</td>
                  <td className="action-cell">
                    <button className="icon-btn" title="查看" onClick={() => window.location.href = '/run-details'}>
                      <Icon icon="fa-solid:eye" width="14" />
                    </button>
                    <button className="icon-btn" title="编辑" onClick={() => navigate(`/task-draw?taskId=${task.dag_task_id}&taskName=${encodeURIComponent(task.dag_task_name)}&description=${encodeURIComponent(task.description || '')}&isEdit=true`)}>
                      <Icon icon="fa-solid:edit" width="14" />
                    </button>
                    <button className="icon-btn" title="删除" onClick={() => handleDeleteClick(task)} style={{color: '#ef4444'}}>
                      <Icon icon="fa-solid:trash" width="14" />
                    </button>
                    <button
                        className="icon-btn primary" 
                        title="运行" 
                        onClick={() => handleRun(task.dag_task_id, task.dag_task_name)}
                      >
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
        <div className="modal-overlay">
          <div className="task-modal-content">
            <div className="modal-header">
              <h3>新建任务</h3>
              <button 
                className="modal-close" 
                onClick={() => {
                  setShowCreateModal(false);
                  setNewTaskNameError(false);
                }}
              >
                <Icon icon="fa-solid:times" width="16" />
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label><span className="required-mark">*</span> 任务名称</label>
                <input
                  type="text"
                  placeholder="请输入名称，例如：数据同步_核心库"
                  value={newTaskName}
                  onChange={(e) => {
                    setNewTaskName(e.target.value);
                    if (newTaskNameError && e.target.value.trim()) {
                      setNewTaskNameError(false);
                    }
                  }}
                  className={newTaskNameError ? 'error' : ''}
                />
                {newTaskNameError && <div className="error-message">请输入任务名称</div>}
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
              <button 
                className="btn-cancel" 
                onClick={() => {
                  setShowCreateModal(false);
                  setNewTaskNameError(false);
                }}
                disabled={submitting}
              >
                取消
              </button>
              <button 
                className={`btn-confirm ${submitting ? 'is-loading' : ''}`} 
                onClick={handleCreateTask} 
                disabled={submitting}
              >
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
                您确定要删除任务 <strong>{deleteTarget.dag_task_name}</strong> 吗？此操作不可逆，将同步移除关联的定时调度任务。
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
      {/* 编辑任务弹窗 */}
      {showEditModal && editTarget && (
        <div className="modal-overlay">
          <div className="task-modal-content">
            <div className="modal-header">
              <h3>编辑任务</h3>
              <button 
                className="modal-close" 
                onClick={() => {
                  setShowEditModal(false);
                  setEditTaskNameError(false);
                }}
              >
                <Icon icon="fa-solid:times" width="16" />
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label><span className="required-mark">*</span> 任务名称</label>
                <input
                  type="text"
                  placeholder="请输入名称"
                  value={editTaskName}
                  onChange={(e) => {
                    setEditTaskName(e.target.value);
                    if (editTaskNameError && e.target.value.trim()) {
                      setEditTaskNameError(false);
                    }
                  }}
                  className={editTaskNameError ? 'error' : ''}
                />
                {editTaskNameError && <div className="error-message">请输入任务名称</div>}
              </div>
              <div className="form-group">
                <label>描述信息</label>
                <textarea
                  rows={4}
                  placeholder="描述此流水线的主要功能..."
                  value={editTaskDesc}
                  onChange={(e) => setEditTaskDesc(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-cancel" 
                onClick={() => {
                  setShowEditModal(false);
                  setEditTaskNameError(false);
                }}
                disabled={updating}
              >
                取消
              </button>
              <button 
                className={`btn-confirm ${updating ? 'is-loading' : ''}`} 
                onClick={handleConfirmEdit} 
                disabled={updating}
              >
                {updating && <span className="btn-spinner"></span>}
                {updating ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
