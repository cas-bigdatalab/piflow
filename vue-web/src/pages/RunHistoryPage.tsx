import { useEffect, useState, useRef } from 'react';
import { Icon } from '@iconify/react';
import { getProcesses, getExecutionDetail, stopDAGTask, getProcessStatusCounts, ExecutionItem, ExecutionDetailResponse, StopInfo, StatusCountsResponse } from '../lib/api';
import './RunHistoryPage.css';

export function RunHistoryPage() {
  const [records, setRecords] = useState<ExecutionItem[]>([]);
  const [stats, setStats] = useState({ total: 0, running: 0, completed: 0, failed: 0, successRate: 0 });
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [executionDetail, setExecutionDetail] = useState<ExecutionDetailResponse['result'] | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  
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
      const status = tab === 'all' ? undefined : tab;
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

  const fetchExecutionDetail = async (processId: string) => {
    try {
      const res = await getExecutionDetail(processId);
      if (res.code === 200 && res.result) {
        setExecutionDetail(res.result);
        
        if (!res.result.finished_at && res.result.status === 'RUNNING') {
          pollingRef.current = setTimeout(() => {
            fetchExecutionDetail(processId);
          }, 3000);
        }
      }
    } catch (err) {
      console.error('获取执行详情失败:', err);
    }
  };

  const handleViewDetail = async (processId: string) => {
    setShowDetailModal(true);
    setExecutionDetail(null);
    
    if (pollingRef.current) {
      clearTimeout(pollingRef.current);
    }
    
    await fetchExecutionDetail(processId);
  };

  const handleCloseDetail = () => {
    setShowDetailModal(false);
    setExecutionDetail(null);
    
    if (pollingRef.current) {
      clearTimeout(pollingRef.current);
    }
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
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
      }
    };
  }, []);

  useEffect(() => {
    loadData(currentPage, activeTab, searchKeyword);
    loadStatusCounts();
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

  const getStopStatusBadge = (stopStatus: string) => {
    const statusClass = stopStatus === 'SUCCESS' ? 'success' :
                        stopStatus === 'FAILED' ? 'failed' :
                        stopStatus === 'RUNNING' ? 'running' : 'unknown';
    
    return (
      <span className={`stop-status-badge ${statusClass}`}>
        {getStatusText(stopStatus)}
      </span>
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

      {showDetailModal && (
        <div className="detail-modal-overlay" onClick={handleCloseDetail}>
          <div className="detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="detail-modal-header">
              <h2>执行详情</h2>
              <button className="close-btn" onClick={handleCloseDetail}>
                <Icon icon="fa-solid:times" width="20" />
              </button>
            </div>
            
            {executionDetail ? (
              <div className="detail-modal-content">
                <div className="detail-section">
                  <h3>基本信息</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <span className="detail-label">实例ID:</span>
                      <span className="detail-value">{executionDetail.process_id}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">所属任务:</span>
                      <span className="detail-value">{executionDetail.flow_name || '-'}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">状态:</span>
                      <span className="detail-value">{getStatusBadge(executionDetail.status)}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">开始时间:</span>
                      <span className="detail-value">
                        {executionDetail.started_at ? new Date(executionDetail.started_at).toLocaleString() : '-'}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">结束时间:</span>
                      <span className="detail-value">
                        {executionDetail.finished_at ? new Date(executionDetail.finished_at).toLocaleString() : '-'}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">执行时长:</span>
                      <span className="detail-value">
                        {executionDetail.status === 'RUNNING' ? '-' : calculateDuration(executionDetail.started_at, executionDetail.finished_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3>统计信息</h3>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="stat-label">节点总数</span>
                      <span className="stat-value">{executionDetail.total_stop_count}</span>
                    </div>
                    <div className="stat-item success">
                      <span className="stat-label">成功</span>
                      <span className="stat-value">{executionDetail.success_stop_count}</span>
                    </div>
                    <div className="stat-item failed">
                      <span className="stat-label">失败</span>
                      <span className="stat-value">{executionDetail.failed_stop_count}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3>执行进度</h3>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div className="progress-container-inner">
                        <div 
                          className={`progress-fill ${executionDetail.progress !== null && executionDetail.progress <= 5 ? 'minimal' : ''}`} 
                          style={{ width: `${executionDetail.progress || 0}%`, minWidth: executionDetail.progress !== null && executionDetail.progress <= 5 ? '8px' : '0' }}
                        />
                      </div>
                      <span className="progress-text">{Math.round(executionDetail.progress || 0)}%</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3>结果数据</h3>
                  {executionDetail.status === 'SUCCESS' && executionDetail.final_output_paths && executionDetail.final_output_paths.length > 0 ? (
                    <div className="result-files">
                      {executionDetail.final_output_paths.map((file, index) => (
                        <button key={index} className="result-file-btn">
                          <Icon icon="fa-solid:download" width="14" />
                          <span>{file.split('/').pop() || file}</span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="no-result">
                      <span>暂无结果</span>
                    </div>
                  )}
                </div>

                {executionDetail.error_message && (
                  <div className="detail-section error">
                    <h3>错误信息</h3>
                    <div className="error-message">{executionDetail.error_message}</div>
                  </div>
                )}

                {executionDetail.stops && executionDetail.stops.length > 0 && (
                  <div className="detail-section">
                    <h3>节点详情</h3>
                    <div className="stops-list">
                      {executionDetail.stops.map((stop, index) => (
                        <div key={index} className="stop-item">
                          <div className="stop-header">
                            <span className="stop-name">{stop.stop_name}</span>
                            {getStopStatusBadge(stop.status)}
                          </div>
                          <div className="stop-details">
                            <div className="stop-detail-item">
                              <span className="stop-detail-label">Job ID:</span>
                              <span className="stop-detail-value">{stop.job_id}</span>
                            </div>
                            {stop.started_at && (
                              <div className="stop-detail-item">
                                <span className="stop-detail-label">开始时间:</span>
                                <span className="stop-detail-value">
                                  {new Date(stop.started_at).toLocaleString()}
                                </span>
                              </div>
                            )}
                            {stop.finished_at && (
                              <div className="stop-detail-item">
                                <span className="stop-detail-label">结束时间:</span>
                                <span className="stop-detail-value">
                                  {new Date(stop.finished_at).toLocaleString()}
                                </span>
                              </div>
                            )}
                            {stop.error_message && (
                              <div className="stop-detail-item error">
                                <span className="stop-detail-label">错误:</span>
                                <span className="stop-detail-value error">{stop.error_message}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="detail-modal-loading">
                <div className="loading-spinner"></div>
                <span>正在加载执行详情...</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
