import { useEffect, useState } from 'react';
import { Icon } from '@iconify/react';
import './RunHistoryPage.css';

// ==================== 模拟后端接口 ====================

interface RunRecord {
  id: string;
  taskName: string;
  startTime: string;
  duration: string;
  status: 'running' | 'completed' | 'failed';
  progress: number;
}

interface ApiResponse {
  code: number;
  message: string;
  data: {
    total: number;
    running: number;
    completed: number;
    failed: number;
    successRate: number;
    list: RunRecord[];
  };
}

const taskNames = [
  'Financial_ETL_Core', 'User_Behavior_Analysis', 'Sales_Data_Sync',
  'Inventory_Update', 'Customer_ETL_Pipeline', 'Log_Analysis_Job',
  'Data_Migration_v2', 'Report_Generation', 'Email_Campaign_Analytics',
  'Payment_Processing', 'Fraud_Detection', 'Recommendation_Engine',
  'Search_Index_Update', 'Cache_Refresh', 'Backup_Database',
];
const statusPool: Array<'running' | 'completed' | 'failed'> = ['running', 'completed', 'completed', 'completed', 'failed'];
const durationPool = ['1m 20s', '2m 45s', '3m 10s', '5m 30s', '8m 45s', '12m 10s', '15m 22s', '0m 58s'];

// 模拟后端 API 请求
function fetchRunHistoryApi(page: number, pageSize: number, status?: string): Promise<ApiResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      const total = 8429;
      const records: RunRecord[] = [];
      for (let i = 0; i < pageSize; i++) {
        const idx = (page - 1) * pageSize + i;
        if (idx >= total) break;
        const day = String(14 - Math.floor(idx / 20)).padStart(2, '0');
        const hour = String(10 + (idx % 14)).padStart(2, '0');
        const minute = String((idx * 7) % 60).padStart(2, '0');
        const second = String((idx * 13) % 60).padStart(2, '0');
        const s = statusPool[idx % statusPool.length];
        const record: RunRecord = {
          id: `RUN_202604${day}_${String(idx + 1).padStart(3, '0')}`,
          taskName: taskNames[idx % taskNames.length],
          startTime: `2026-04-${day} ${hour}:${minute}:${second}`,
          duration: durationPool[idx % durationPool.length],
          status: s,
          progress: s === 'completed' ? 100 : s === 'running' ? Math.floor(Math.random() * 80 + 10) : 0,
        };
        // 如果有状态过滤
        if (status && status !== 'all' && record.status !== status) {
          continue;
        }
        records.push(record);
      }
      resolve({
        code: 200,
        message: 'success',
        data: {
          total: status && status !== 'all'
            ? status === 'running' ? 86 : status === 'completed' ? 8240 : 103
            : total,
          running: 86,
          completed: 8240,
          failed: 103,
          successRate: 98.8,
          list: records,
        },
      });
    }, 600);
  });
}

// ==================== 页面组件 ====================

export function RunHistoryPage() {
  const [records, setRecords] = useState<RunRecord[]>([]);
  const [stats, setStats] = useState({ total: 0, running: 0, completed: 0, failed: 0, successRate: 0 });
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;
  const totalPages = Math.ceil(stats.total / pageSize);

  // 请求后端数据
  const loadData = async (page: number, tab: string) => {
    setLoading(true);
    try {
      const res = await fetchRunHistoryApi(page, pageSize, tab);
      if (res.code === 200) {
        setRecords(res.data.list);
        setStats({
          total: res.data.total,
          running: res.data.running,
          completed: res.data.completed,
          failed: res.data.failed,
          successRate: res.data.successRate,
        });
      }
    } catch (err) {
      console.error('请求失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 初始化和页码/状态变化时请求数据
  useEffect(() => {
    loadData(currentPage, activeTab);
  }, [currentPage, activeTab]);

  // 切换 Tab 时重置页码
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setCurrentPage(1);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return (
          <span className="status-badge running">
            <span className="status-dot"></span>
            执行中
          </span>
        );
      case 'completed':
        return (
          <span className="status-badge completed">
            <Icon icon="fa-solid:check" width="12" />
            已完成
          </span>
        );
      case 'failed':
        return (
          <span className="status-badge failed">
            <Icon icon="fa-solid:times" width="12" />
            失败
          </span>
        );
      default:
        return null;
    }
  };

  const getProgressBar = (status: string, progress: number) => {
    if (status === 'failed') {
      return <div className="progress-bar failed">-</div>;
    }
    return (
      <div className="progress-bar">
        <div
          className={`progress-fill ${status}`}
          style={{ width: `${progress}%` }}
        />
        <span className="progress-text">{progress}%</span>
      </div>
    );
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
    <div className="run-history-page">
      {/* 统计卡片 */}
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

      {/* 页面标题 */}
      <div className="page-header">
        <h1 className="page-title">运行历史</h1>
        <div className="page-actions">
          <div className="search-box">
            <Icon icon="fa-solid:search" width="16" className="search-icon" />
            <input type="text" placeholder="按任务或实例ID搜索..." />
          </div>
          <button className="filter-btn">
            <Icon icon="fa-solid:filter" width="16" />
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
        ) : records.length === 0 ? (
          <div className="empty-state">暂无数据</div>
        ) : (
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
                <tr key={record.id}>
                  <td className="id-cell">{record.id}</td>
                  <td className="task-cell">{record.taskName}</td>
                  <td className="time-cell">{record.startTime}</td>
                  <td className="duration-cell">{record.duration}</td>
                  <td className="status-cell">{getStatusBadge(record.status)}</td>
                  <td className="progress-cell">{getProgressBar(record.status, record.progress)}</td>
                  <td className="action-cell">
                    <button className="action-btn">
                      <Icon icon="fa-solid:project-diagram" width="14" />
                      <span>溯源流水线</span>
                    </button>
                    <button className="action-btn">
                      <Icon icon="fa-solid:robot" width="14" />
                      <span>溯源至 AI</span>
                    </button>
                    <button className="icon-btn">
                      <Icon icon="fa-solid:eye" width="14" />
                    </button>
                    <button className="icon-btn delete">
                      <Icon icon="fa-solid:trash" width="14" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 分页 */}
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
      </div>
    </div>
  );
}
