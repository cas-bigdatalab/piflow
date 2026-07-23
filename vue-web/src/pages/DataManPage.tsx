import React, { useState, useMemo } from 'react';
import './DataManPage.css';

// --- 模拟数据 (Mock Data) ---
const MOCK_DATA = [
  { id: 1, name: '2024年气象观测数据.csv', type: 'csv', size: '45.2 MB', date: '2025-07-10' },
  { id: 2, name: '实验结果_蛋白质组学.json', type: 'json', size: '12.8 MB', date: '2025-07-08' },
  { id: 3, name: '全球温度异常数据.xlsx', type: 'xlsx', size: '8.5 MB', date: '2025-07-05' },
  { id: 4, name: '用户行为日志.log', type: 'mdc', size: '1.2 GB', date: '2025-07-01' },
  { id: 5, name: '实验结果_蛋白质组学.json', type: 'json', size: '12.8 MB', date: '2025-07-08' },
  { id: 6, name: '全球温度异常数据.xlsx', type: 'xlsx', size: '8.5 MB', date: '2025-07-05' },
  { id: 7, name: '用户行为日志.log', type: 'mdc', size: '1.2 GB', date: '2025-07-01' },
  { id: 8, name: '实验结果_蛋白质组学.json', type: 'json', size: '12.8 MB', date: '2025-07-08' },
  { id: 9, name: '全球温度异常数据.xlsx', type: 'xlsx', size: '8.5 MB', date: '2025-07-05' },
  { id: 10, name: '用户行为日志.log', type: 'mdc', size: '1.2 GB', date: '2025-07-01' },
  
  { id: 11, name: '全球温度异常数据.xlsx', type: 'xlsx', size: '8.5 MB', date: '2025-07-05' },
  { id: 12, name: '用户行为日志.log', type: 'mdc', size: '1.2 GB', date: '2025-07-01' },
  { id: 13, name: '实验结果_蛋白质组学.json', type: 'json', size: '12.8 MB', date: '2025-07-08' },
  { id: 14, name: '全球温度异常数据.xlsx', type: 'xlsx', size: '8.5 MB', date: '2025-07-05' },
  { id: 15, name: '用户行为日志.log', type: 'mdc', size: '1.2 GB', date: '2025-07-01' },
];

// --- 模拟结果数据 (Mock Result Data) ---
const MOCK_RESULT_DATA = [
  { id: 101, taskName: '气象趋势分析', resultFile: '气象分析报告.csv', size: '3.2 MB', date: '2025-07-09' },
  { id: 102, taskName: '蛋白质互作网络', resultFile: '互作网络.json', size: '8.1 MB', date: '2025-07-07' },
];

// 封装下载图标
export const DownloadIcon = ({ size = 13 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="2"/>
    <path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

// 封装删除图标
export const DeleteIcon = ({ size = 13 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 6h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" strokeWidth="2"/>
    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2"/>
  </svg>
);

// 上传图标
export const UploadIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* 向上的箭头 */}
    <path
      d="M12 16V4M12 4L8 8M12 4L16 8"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {/* 底部的托盘 */}
    <path
      d="M20 16V18C20 19.1046 19.1046 20 18 20H6C4.89543 20 4 19.1046 4 18V16"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);

// 辅助函数：根据后缀获取 Tag 样式类名
const getTagClass = (type) => {
  const map = {
    csv: 'tag-csv',
    json: 'tag-json',
    xlsx: 'tag-xlsx',
    mdc: 'tag-mdc',
  };
  return map[type.toLowerCase()] || 'tag';
};

const MyDataPage = () => {
  const [activeTab, setActiveTab] = useState('uploaded'); // 'uploaded' | 'results'
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [fileTypeFilter, setFileTypeFilter] = useState('all');
  const [singleDeleteId, setSingleDeleteId] = useState<number | null>(null);
  const currentData = activeTab === 'uploaded' ? MOCK_DATA : MOCK_RESULT_DATA;
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // ✅ 先定义 filteredData（关键修复）
  const filteredData = currentData.filter(item => {
    const matchesSearch = (activeTab === 'uploaded' ? item.name : item.resultFile)
      .toLowerCase()
      .includes(searchTerm.toLowerCase());

    if (fileTypeFilter === 'all') return matchesSearch;

    if (activeTab === 'uploaded') {
      return matchesSearch && item.type === fileTypeFilter;
    } else {
      const resultExt = item.resultFile.split('.').pop()?.toLowerCase() || '';
      return matchesSearch && resultExt === fileTypeFilter;
    }
  });

  // 分页数据
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage, pageSize]);

  // 总页数
  const totalPages = Math.ceil(filteredData.length / pageSize);

  // 处理全选/单选
  const toggleSelect = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAll = () => {
    const currentIds = new Set(filteredData.map(item => item.id));
    const isAllSelected = filteredData.length > 0 && selectedIds.size === filteredData.length && filteredData.every(item => selectedIds.has(item.id));
    if (isAllSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(currentIds);
    }
  };

  return (
    <div className="my-data-container">
      {/* 头部区域 */}
      <div className="page-header">
        <h1 className="page-title">我的数据</h1>
      </div>
      <div className="page-header-desc">
        <p className="page-desc">管理您上传至数据工厂的所有文件与数据集及分析结果数据</p>
      </div>

      {/* 标签页导航 */}
      <div className="tabs-nav">
        <div className={`tab-item ${activeTab === 'uploaded' ? 'active' : ''}`} onClick={() => setActiveTab('uploaded')}>
          上传的数据
        </div>
        <div className={`tab-item ${activeTab === 'results' ? 'active' : ''}`} onClick={() => setActiveTab('results')}>
          结果数据 (0)
        </div>
      </div>

      {/* 批量操作栏 */}
      {isBatchMode && (
        <div className="batch-action-bar">
          <span>已选择 <strong>{selectedIds.size}</strong> 项</span>
          <div className="batch-action-buttons">
            <button className="action-btn btn-download" title="批量下载">
              <DownloadIcon /> 批量下载
            </button>
            <button
              className="action-btn btn-delete"
              title="批量删除"
              onClick={() => setIsBatchModalOpen(true)}
              disabled={selectedIds.size === 0}
            >
              <DeleteIcon /> 批量删除
            </button>
            <button
              className="action-btn btn-download"
              title="取消选择"
              onClick={() => {
                setIsBatchMode(false);
                setSelectedIds(new Set());
              }}
            >
              取消选择
            </button>
          </div>
        </div>
      )}

      {/* 工具栏：搜索与上传 */}
      <div className="toolbar">
        <div className="search-bar">
          <input
            type="text"
            className="search-input"
            placeholder="请输入文件名..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            className="filter-select"
            value={fileTypeFilter}
            onChange={(e) => setFileTypeFilter(e.target.value)}
          >
            <option value="all">全部类型</option>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
            <option value="xlsx">Excel</option>
            <option value="image">图片</option>
            <option value="txt">TXT</option>
            <option value="nc">NetCDF</option>
            <option value="tiff">GeoTIFF</option>
            <option value="hdf5">HDF5</option>
          </select>
        </div>
        <div className="btn-group">
          {isBatchMode ? (
            <button
              className="btn-secondary"
              onClick={() => {
                setIsBatchMode(false);
                setSelectedIds(new Set());
              }}
            >
              退出批量
            </button>
          ) : (
            <button
              className="btn-secondary"
              onClick={() => {
                setIsBatchMode(true);
                setSelectedIds(new Set());
              }}
              disabled={filteredData.length === 0}
            >
              批量管理
            </button>
          )}
          {activeTab === 'uploaded' && (
            <button className="btn-primaryNew" onClick={() => setIsUploadModalOpen(true)}>
              <UploadIcon size={16} />
              上传数据
            </button>
          )}
        </div>
      </div>

      {/* 数据表格 */}
      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '50px' }}>
                <input
                  type="checkbox"
                  className="checkbox-custom"
                  checked={filteredData.length > 0 && selectedIds.size === filteredData.length}
                  onChange={toggleSelectAll}
                />
              </th>
              {activeTab === 'uploaded' ? (
                <>
                  <th>文件名</th>
                  <th>类型</th>
                  <th>大小</th>
                  <th>上传时间</th>
                </>
              ) : (
                <>
                  <th>任务名称</th>
                  <th>结果文件</th>
                  <th>大小</th>
                  <th>完成时间</th>
                </>
              )}
              <th style={{ width: '100px' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.length > 0 ? (
              paginatedData.map((item) => (
                <tr key={item.id}>
                  <td>
                    <input
                      type="checkbox"
                      className="checkbox-custom"
                      checked={selectedIds.has(item.id)}
                      onChange={() => toggleSelect(item.id)}
                    />
                  </td>
                  {activeTab === 'uploaded' ? (
                    <>
                      <td>
                        <div className="file-name-cell">
                          <div>{item.type.substring(0, 3).toUpperCase()}</div>
                          <div className="file-info">
                            <span className="file-name-text">{item.name}</span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`tag ${getTagClass(item.type)}`}>
                          {item.type.toUpperCase()}
                        </span>
                      </td>
                      <td>{item.size}</td>
                      <td>{item.date}</td>
                    </>
                  ) : (
                    <>
                      <td>{item.taskName}</td>
                      <td>
                        <div className="file-name-cell">
                          <div>{item.resultFile.split('.').pop()?.substring(0, 3).toUpperCase() || 'FILE'}</div>
                          <div className="file-info">
                            <span className="file-name-text">{item.resultFile}</span>
                          </div>
                        </div>
                      </td>
                      <td>{item.size}</td>
                      <td>{item.date}</td>
                    </>
                  )}
                  <td>
                    <div className="action-btns">
                      <button className="action-btnNew" title="下载">
                        <DownloadIcon />
                      </button>
                      <button
                        className="action-btnNew"
                        title="删除"
                        onClick={() => {
                          setSingleDeleteId(item.id);
                          setIsBatchModalOpen(true);
                        }}
                      >
                        <DeleteIcon />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                  暂无数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* 分页控件 */}
      {totalPages > 1 && (
        <div className="pagination-controls" style={{ marginTop: '16px', display: 'flex', justifyContent: 'end', gap: '8px' }}>
          <button
            className="pagination-btn"
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            style={{
              padding: '4px 12px',
              border: '1px solid #d9d9d9',
              background: '#fff',
              borderRadius: '4px',
              cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
              opacity: currentPage === 1 ? 0.6 : 1,
            }}
          >
            上一页
          </button>

          {[...Array(totalPages)].map((_, i) => {
            const pageNum = i + 1;
            return (
              <button
                key={pageNum}
                className={`pagination-btn ${currentPage === pageNum ? 'active' : ''}`}
                onClick={() => setCurrentPage(pageNum)}
                style={{
                  padding: '4px 12px',
                  border: '1px solid #d9d9d9',
                  background: currentPage === pageNum ? '#10b981' : '#fff',
                  color: currentPage === pageNum ? '#fff' : '#000',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                {pageNum}
              </button>
            );
          })}

          <button
            className="pagination-btn"
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            style={{
              padding: '4px 12px',
              border: '1px solid #d9d9d9',
              background: '#fff',
              borderRadius: '4px',
              cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
              opacity: currentPage === totalPages ? 0.6 : 1,
            }}
          >
            下一页
          </button>
        </div>
      )}

      {/* 上传数据弹窗 */}
      {isUploadModalOpen && (
        <div className="modal-overlay" onClick={() => setIsUploadModalOpen(false)}>
          <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">上传数据</h3>
              <button className="close-btn" onClick={() => setIsUploadModalOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <div
                className="upload-drop-zone"
                onDragOver={(e) => e.preventDefault()}
                onClick={() => document.getElementById('file-upload-input')?.click()}
              >
                <div className="upload-icon-wrapper">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 10C4 8.89543 4.89543 8 6 8H18L22 12H42C43.1046 12 44 12.8954 44 14V38C44 39.1046 43.1046 40 42 40H6C4.89543 40 4 39.1046 4 38V10Z" fill="#FADB14"/>
                    <path d="M4 14H44V38C44 39.1046 43.1046 40 42 40H6C4.89543 40 4 39.1046 4 38V14Z" fill="#FFF566" fillOpacity="0.5"/>
                  </svg>
                </div>
                <p className="upload-main-text">点击或拖拽文件到此处上传</p>
                <p className="upload-sub-text">
                  支持 CSV, JSON, Excel, TXT, NetCDF, GeoTIFF, HDF5, 图片等格式，单个文件最大 500MB
                </p>
                <input
                  type="file"
                  id="file-upload-input"
                  style={{ display: 'none' }}
                  onChange={(e) => console.log('Selected file:', e.target.files?.[0])}
                />
              </div>
              <div className="form-group">
                <label className="form-label">数据描述 (可选)</label>
                <textarea className="form-textarea" placeholder="为这份数据添加描述，方便后续查找和使用" rows={3}></textarea>
              </div>
              <div className="form-group">
                <label className="form-label">数据标签 (可选)</label>
                <input type="text" className="form-input" placeholder="多个标签用逗号分隔，如：气象, 2024, 实验数据" />
              </div>
            </div>
            <div className="modal-footer">
              <span className="footer-hint">上传后将存储在「我上传的」数据列表中</span>
              <div className="action-buttons">
                <button className="btn-secondary" onClick={() => setIsUploadModalOpen(false)}>取消</button>
                <button className="btn-primaryNew">开始上传</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 批量管理弹窗 (用于删除确认) */}
      {isBatchModalOpen && (
        <div className="modal-overlay" onClick={() => setIsBatchModalOpen(false)}>
          <div className="batch-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">确认删除</h3>
              <button className="close-btn" onClick={() => setIsBatchModalOpen(false)}>×</button>
            </div>
            <div className="modal-body batch-options">
              {singleDeleteId !== null ? (
                <p>
                  确定要删除文件 <strong>“{currentData.find(d => d.id === singleDeleteId)?.name || '该文件'}”</strong> 吗？此操作不可撤销。
                </p>
              ) : (
                <p>
                  确定要删除选中的 <strong>{selectedIds.size}</strong> 个文件吗？此操作不可撤销。
                </p>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setIsBatchModalOpen(false)}>取消</button>
              <button
                className="btn-delete"
                onClick={() => {
                  if (singleDeleteId !== null) {
                    console.log('删除单个文件:', singleDeleteId);
                  } else {
                    console.log('批量删除:', Array.from(selectedIds));
                    setSelectedIds(new Set());
                  }
                  setIsBatchModalOpen(false);
                  setSingleDeleteId(null);
                  setIsBatchMode(false);
                }}
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyDataPage;