import React, { useState } from 'react';
import './DataManPage.css';

// --- 模拟数据 (Mock Data) ---
const MOCK_DATA = [
  { id: 1, name: '2024年气象观测数据.csv', type: 'csv', size: '45.2 MB', date: '2025-07-10' },
  { id: 2, name: '实验结果_蛋白质组学.json', type: 'json', size: '12.8 MB', date: '2025-07-08' },
  { id: 3, name: '全球温度异常数据.xlsx', type: 'xlsx', size: '8.5 MB', date: '2025-07-05' },
  { id: 4, name: '用户行为日志.log', type: 'mdc', size: '1.2 GB', date: '2025-07-01' },
];
// --- 模拟结果数据 (Mock Result Data) ---
const MOCK_RESULT_DATA = [
  { id: 101, taskName: '气象趋势分析', resultFile: '气象分析报告.csv', size: '3.2 MB', date: '2025-07-09' },
  { id: 102, taskName: '蛋白质互作网络', resultFile: '互作网络.json', size: '8.1 MB', date: '2025-07-07' },
];
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

// 辅助函数：获取图标背景色
const getIconColor = (type) => {
  const map = {
    csv: '#1890ff',
    json: '#52c41a',
    xlsx: '#722ed1',
    mdc: '#f5222d',
  };
  return map[type.toLowerCase()] || '#ccc';
};

const MyDataPage = () => {
  const [activeTab, setActiveTab] = useState('uploaded'); // 'uploaded' | 'results'
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());

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
    if (selectedIds.size === MOCK_DATA.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(MOCK_DATA.map(item => item.id)));
    }
  };

  // 简单的搜索过滤
  const currentData = activeTab === 'uploaded' ? MOCK_DATA : MOCK_RESULT_DATA;

  const filteredData = currentData.filter(item => 
    (activeTab === 'uploaded' 
      ? item.name 
      : item.resultFile
    ).toLowerCase().includes(searchTerm.toLowerCase())
  );

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
        <div 
          className={`tab-item ${activeTab === 'uploaded' ? 'active' : ''}`}
          onClick={() => setActiveTab('uploaded')}
        >
          上传的数据
        </div>
        <div 
          className={`tab-item ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          结果数据 (0)
        </div>
      </div>

      {/* 工具栏：搜索与上传 */}
      <div className="toolbar">
        <input 
          type="text" 
          className="search-input" 
          placeholder="请输入文件名..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        
        <button className="btn-primary">
          <span>+</span> 上传数据
        </button>
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
            {filteredData.length > 0 ? (
              filteredData.map((item) => (
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
                    <button className="action-btn" title="下载">⬇️</button>
                    <button className="action-btn" title="删除">🗑️</button>
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
    </div>
  );
};

export default MyDataPage;