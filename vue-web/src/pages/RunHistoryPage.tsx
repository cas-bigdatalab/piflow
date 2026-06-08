import { useEffect, useState, useRef } from 'react';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router-dom';
import { getProcesses, stopDAGTask, getProcessStatusCounts, ExecutionItem, StatusCountsResponse } from '../lib/api';
import './RunHistoryPage.css';

export function RunHistoryPage() {
  const navigate = useNavigate();
  const [records, setRecords] = useState<ExecutionItem[]>([]);
  const [stats, setStats] = useState({ total: 0, running: 0, completed: 0, failed: 0, successRate: 0 });
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchKeyword, setSearchKeyword] = useState('');
  const listPollingRef = useRef<NodeJS.Timeout | null>(null);
  
  const pageSize = 10;
  const totalPages = Math.ceil(stats.total / pageSize);

  const calculateDuration = (startTime: string | null, endTime: string | null) => {
    if (!startTime) return '-';
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : Date.now();
    const duration = Math.floor((end - start) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  const getStatusText = (status: string | null) => {
    if (!status) return '未知';
    const statusMap: { [key: string]: string } = {
      'SUBMITTED': '已提交',
      'RUNNING': '执行中',
      'SUCCESS': '已完成',
      'FAILED': '失败',
      'SKIPPED': '已跳过',
      'STOPPED': '已停止',
    };
    return statusMap[status] || status;
  };

  const loadData = async (page: number, tab: string, keyword?: string) => {
    setLoading(true);
    try {
      // 把 tab 名称映射到接口需要的 status 值
      let status: string | undefined;
      if (tab === 'all') {
        status = undefined;
      } else if (tab === 'running') {
        status = 'RUNNING';
      } else if (tab === 'completed') {
        status = 'SUCCESS';
      } else if (tab === 'failed') {
        status = 'FAILED';
      } else {
        status = tab;
      }
      const res = await getProcesses(page, pageSize, { status, running_only: tab === 'running', keyword });
      
      if (res.code === 200 && res.result) {
        setRecords(res.result.items);
      }
    } catch (err) {
      console.error('请求失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 轮询刷新时不显示 loading，避免闪烁
  const refreshData = async (page: number, tab: string, keyword?: string) => {
    try {
      let status: string | undefined;
      if (tab === 'all') {
        status = undefined;
      } else if (tab === 'running') {
        status = 'RUNNING';
      } else if (tab === 'completed') {
        status = 'SUCCESS';
      } else if (tab === 'failed') {
        status = 'FAILED';
      } else {
        status = tab;
      }
      const res = await getProcesses(page, pageSize, { status, running_only: tab === 'running', keyword });
      
      if (res.code === 200 && res.result) {
        setRecords(res.result.items);
      }
    } catch (err) {
      console.error('请求失败:', err);
    }
  };

  const loadStatusCounts = async () => {
    try {
      const res = await getProcessStatusCounts();
      if (res.code === 200 && res.result) {
        const { total, running_count, completed_count, failed_count } = res.result;
        setStats({
          total,
          running: running_count,
          completed: completed_count,
          failed: failed_count,
          successRate: total > 0 ? 
            Number.parseFloat(((completed_count / total) * 100).toFixed(1)) : 0
        });
      }
    } catch (err) {
      console.error('获取状态统计失败:', err);
    }
  };

  const handleViewDetail = (processId: string) => {
    navigate(`/run-details?processId=${processId}`);
  };

  const handleStopExecution = async (processId: string) => {
    if (!window.confirm('确定要停止该运行吗？')) {
      return;
    }
    
    try {
      const res = await stopDAGTask(processId);
      if (res.code === 200) {
        alert('停止成功');
        loadData(currentPage, activeTab);
      }
    } catch (err) {
      console.error('停止执行失败:', err);
      alert('停止失败，请重试');
    }
  };

  useEffect(() => {
    return () => {
      if (listPollingRef.current) {
        clearInterval(listPollingRef.current);
      }
    };
  }, []);

  useEffect(() => {
    loadData(currentPage, activeTab, searchKeyword);
    loadStatusCounts();
    
    // 启动列表轮询，每隔10秒静默刷新一次
    if (listPollingRef.current) {
      clearInterval(listPollingRef.current);
    }
    listPollingRef.current = setInterval(() => {
      refreshData(currentPage, activeTab, searchKeyword);
      loadStatusCounts();
    }, 10000);
    
    return () => {
      if (listPollingRef.current) {
        clearInterval(listPollingRef.current);
      }
    };
  }, [currentPage, activeTab, searchKeyword]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setCurrentPage(1);
  };

  const handleSearch = () => {
    setCurrentPage(1);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getStatusBadge = (status: string | null) => {
    const statusClass = status === 'RUNNING' ? 'running' : 
                        status === 'SUCCESS' ? 'completed' : 
                        status === 'FAILED' ? 'failed' : 'unknown';
    
    return (
      <span className={`status-badge ${statusClass}`}>
        {status === 'RUNNING' && <span className="status-dot"></span>}
        {status === 'SUCCESS' && <Icon icon="fa-solid:check" width="12" />}
        {status === 'FAILED' && <Icon icon="fa-solid:times" width="12" />}
        {getStatusText(status)}
      </span>
    );
  };

  const getProgressBar = (status: string | null, progress: number | null) => {
    const progressValue = progress !== null ? Math.round(progress * 100) : 0;
    const statusClass = status === 'RUNNING' ? 'running' : 
                        status === 'SUCCESS' ? 'completed' : 
                        status === 'FAILED' ? 'failed' : '';
    
    if (status === 'FAILED') {
      return <div className="progress-bar failed">-</div>;
    }
    
    return (
      <div className="progress-bar">
        <div className="progress-container-inner">
          <div
            className={`progress-fill ${statusClass}`}
            style={{ width: `${progressValue}%` }}
          />
        </div>
        <span className="progress-text">{progressValue}%</span>
      </div>
    );
  };

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
    <div className="run-history-page">
      <div className="stats-header">
        <div className="stats-cards">
          <div className={`stat-card ${activeTab === 'all' ? 'active' : ''}`} onClick={() => handleTabChange('all')}>
            <span className="stat-label all">全部</span>
            <span className="stat-value all">{stats.total.toLocaleString()}</span>
          </div>
          <div className={`stat-card ${activeTab === 'running' ? 'active2' : ''}`} onClick={() => handleTabChange('running')}>
            <span className="stat-label running">执行中</span>
            <span className="stat-value running">{stats.running}</span>
          </div>
          <div className={`stat-card ${activeTab === 'completed' ? 'active3' : ''}`} onClick={() => handleTabChange('completed')}>
            <span className="stat-label completed">已完成</span>
            <span className="stat-value completed">{stats.completed.toLocaleString()}</span>
          </div>
          <div className={`stat-card ${activeTab === 'failed' ? 'active4' : ''}`} onClick={() => handleTabChange('failed')}>
            <span className="stat-label failed">执行失败</span>
            <span className="stat-value failed">{stats.failed}</span>
          </div>
        </div>
        <div className="stats-summary">
          <div className="summary-item">
            <span className="summary-label">总实例数</span>
            <span className="summary-value">{stats.total.toLocaleString()}</span>
          </div>
          <div className="summary-item">
            <span className="summary-dot success"></span>
            <span className="summary-label">成功率</span>
            <span className="summary-value success">{stats.successRate}%</span>
          </div>
        </div>
      </div>

      <div className="page-header">
        <h1 className="page-title">运行历史</h1>
        <div className="page-actions">
          <div className="search-box">
            <Icon icon="fa-solid:search" width="16" className="search-icon" />
            <input 
              type="text" 
              placeholder="按任务或实例ID搜索..." 
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onKeyDown={handleSearchKeyDown}
            />
          </div>
          <button className="filter-btn" onClick={handleSearch}>
            <Icon icon="fa-solid:filter" width="16" />
          </button>
        </div>
      </div>

      <div className="page-content">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <span>正在加载数据...</span>
          </div>
        ) : records.length === 0 ? (
          <div className="empty-state">
            <Icon icon="fa-solid:folder-open" width="48" />
            <p>暂无运行记录</p>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>执行实例ID</th>
                    <th>所属任务</th>
                    <th>开始时间</th>
                    <th>执行时长</th>
                    <th>状态</th>
                    <th>进度</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.process_id}>
                      <td className="id-cell">{record.process_id}</td>
                      <td className="task-cell">{record.flow_name || record.dag_task_id || '-'}</td>
                      <td className="time-cell">{record.started_at ? new Date(record.started_at).toLocaleString() : '-'}</td>
                      <td className="duration-cell">{calculateDuration(record.started_at, record.finished_at)}</td>
                      <td className="status-cell">{getStatusBadge(record.status)}</td>
                      <td className="progress-cell">{getProgressBar(record.status, record.progress)}</td>
                      <td className="action-cell">
                        <button 
                          className="icon-btn" 
                          title="查看详情"
                          onClick={() => handleViewDetail(record.process_id)}
                        >
                          <Icon icon="fa-solid:eye" width="14" />
                        </button>
                        {record.status === 'RUNNING' && (
                          <button 
                            className="icon-btn stop" 
                            title="停止执行"
                            onClick={() => handleStopExecution(record.process_id)}
                          >
                            <Icon icon="fa-solid:stop" width="14" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {!loading && records.length > 0 && (
              <div className="pagination">
                <span className="pagination-info">
                  显示第 {(currentPage - 1) * pageSize + 1} 到 {Math.min(currentPage * pageSize, stats.total)} 条，共 {stats.total.toLocaleString()} 条运行记录
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
          </>
        )}
      </div>
    </div>
  );
}
