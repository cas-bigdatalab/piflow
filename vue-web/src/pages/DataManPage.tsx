import  { useState, useMemo,useEffect,useRef } from 'react';
import './DataManPage.css';
import { listStorageNew,deleteData,apiBase,downLoadData } from "../lib/api";


// --- 模拟数据 (Mock Data) ---
// const MOCK_DATA = [];

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

// 封装“保存到 DataSpace”图标
export const SaveToDataSpaceIcon = ({ size = 13 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* 云朵形状 */}
    <path
      d="M18 10C18 7.23858 15.7614 5 13 5C11.5962 5 10.3103 5.58127 9.3923 6.5C8.47433 5.58127 7.18843 5 5.7846 5C3.02318 5 0.784607 7.23858 0.784607 10C0.784607 11.5962 1.36588 12.8821 2.28461 13.8C3.20333 14.7179 4.48923 15.3 5.89306 15.3H18V10Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {/* 向下的保存箭头 */}
    <path
      d="M12 12V18"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
    <path
      d="M15 15L12 18L9 15"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
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
  // 修改 useState 初始化处，显式指定泛型类型
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [fileTypeFilter, setFileTypeFilter] = useState('all');
  const [singleDeleteId, setSingleDeleteId] = useState<number | null>(null);
  // const currentData = activeTab === 'uploaded' ? MOCK_DATA : MOCK_RESULT_DATA;
  const [fileSystemItems, setFileSystemItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const [totalItems, setTotalItems] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // 新增列表内容
  useEffect(() => {
  const loadStorageData = async () => {
      try {
        setLoading(true); // 开始加载
        const userId = localStorage.getItem('userId') || '';
        // 传入搜索关键词（如果需要后端搜索）
        const res = await listStorageNew(userId, searchTerm, currentPage, pageSize);
        console.log("其中列表中的内容为", res);
        setFileSystemItems(res?.items || []);
        setTotalItems(res?.pagination?.total || 0);
      } catch (err) {
        console.error('加载存储数据失败:', err);
        setFileSystemItems([]);
        setTotalItems(0);
      } finally {
        setLoading(false);
      }
    };

    if (activeTab === 'uploaded') {
      loadStorageData();
    }
  }, [currentPage, pageSize, searchTerm]); // 注意依赖项
  // 然后直接使用
  const paginatedData = fileSystemItems; // 后端已分页
  // 总页数：使用后端返回的 totalItems
  const totalPages = Math.ceil(totalItems / pageSize);
  //删除方法
  const handleDelete = async (pathsToDelete: string[]) => {
    try {
      const userId = localStorage.getItem('userId') || '';
      if (!userId) {
          console.error('无法获取用户ID');
          return;
      }
      
      // 调用从 api.ts 导入的 deleteData 函数
      await deleteData(userId, pathsToDelete);
      
      console.log('删除成功，正在刷新列表...');
      // 删除成功后，刷新列表      
      setCurrentPage(1); // 切换到第一页
      const res = await listStorageNew(userId, searchTerm, currentPage, pageSize);
      setFileSystemItems(res?.items || []);
      setTotalItems(res?.pagination?.total || 0);
      
      // 清除选中状态
      setSelectedIds(new Set());
      setIsBatchMode(false);
      setSingleDeleteId(null);
    } catch (err) {
      console.error('删除失败:', err);
      alert('删除失败，请稍后重试');
    }
  };
  //上传方法
  const handleUpload = async () => {
    // ✅ 修改1：检查 selectedFile 是否存在
    if (!selectedFile) return;

    setUploading(true);
    try {
      const userId = localStorage.getItem('userId') || '';
      const formData = new FormData();
      formData.append('user_id', userId);
      // ✅ 修改2：上传 selectedFile
      formData.append('file', selectedFile);

      const res = await fetch(`${apiBase()}/workspace/upload/path`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        alert('上传成功！');
        setIsUploadModalOpen(false);
        // ✅ 修改3：上传成功后，清空 selectedFile
        setSelectedFile(null);
        setCurrentPage(1); // 跳回第一页
        await loadStorageData(); //调用刷新列表
      } else {
        throw new Error('上传失败');
      }
    } catch (err) {
      // ... 错误处理 ...
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

//下载方法
const downloadData = async (item: any,useLogo:boolean) => {
  try {
    const userId = localStorage.getItem('userId') || '';
    if (!userId) {
      alert('用户未登录');
      return;
    }
    if (useLogo){//批量下载
       const paths = fileSystemItems
        .filter(item => selectedIds.has(item.name) && item.path)
        .map(item => item.path);
      await downLoadData(userId, paths);
      
    } else { //单独下载
      const pathsToDelete = [item.path];
      await downLoadData(userId, pathsToDelete);
    }
  } catch (err) {
    console.error('下载失败:', err);
    alert('下载失败，请稍后重试');
  }
};

  const filteredData = useMemo(() => {
    if (activeTab !== 'uploaded') {
      // 如果未来支持 results tab，再补充逻辑
      return [];
    }

    return fileSystemItems.filter(item => {
      const matchesSearch = item.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());

      if (fileTypeFilter === 'all') return matchesSearch;
      return matchesSearch && item.type === fileTypeFilter;
    });
  }, [fileSystemItems, searchTerm, fileTypeFilter, activeTab]);
  
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
  const currentIds = new Set(fileSystemItems.map(item => item.id)); // 当前页
  const isAllSelected = fileSystemItems.length > 0 && 
                        fileSystemItems.every(item => selectedIds.has(item.id));
  if (isAllSelected) {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      fileSystemItems.forEach(item => newSet.delete(item.id));
      return newSet;
    });
  } else {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      fileSystemItems.forEach(item => newSet.add(item.id));
      return newSet;
    });
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
      {/* <div className="tabs-nav">
        <div className={`tab-item ${activeTab === 'uploaded' ? 'active' : ''}`} onClick={() => setActiveTab('uploaded')}>
          上传的数据
        </div>
        <div className={`tab-item ${activeTab === 'results' ? 'active' : ''}`} onClick={() => setActiveTab('results')}>
          结果数据 (0)
        </div>
      </div> */}

      {/* 批量操作栏 */}
      {isBatchMode && (
        <div className="batch-action-bar">
          <span>已选择 <strong>{selectedIds.size}</strong> 项</span>
          <div className="batch-action-buttons">
            <button className="action-btn btn-download" title="批量下载"
              onClick={() => {
                downloadData(selectedIds,true);
              }}
            >
              <DownloadIcon /> 批量下载
            </button>
             <button
              className="action-btn btn-accent"
              title="保存到DataSpace"
              onClick={() => setIsBatchModalOpen(true)}
              disabled={selectedIds.size === 0}
            >
              <SaveToDataSpaceIcon /> 保存到DataSpace
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
            
          />
          {/* value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)} */}
          {/* 先注释掉 */}
          {/* <select
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
          </select> */}
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
                <tr key={item.name}>
                  <td>
                    <input
                      type="checkbox"
                      className="checkbox-custom"
                      checked={selectedIds.has(item.name)}
                      onChange={() => toggleSelect(item.name)}
                    />
                  </td>
                  {activeTab === 'uploaded' ? (
                    <>
                      <td>
                        <div className="file-name-cell">
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
                      <td>{item.size  || "暂无数据"}</td>
                      <td>{item.last_modified}</td>
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
                      <button className="action-btnNew" title="下载"
                        onClick={() => {
                          if (item.path) {
                            downloadData(item,false);
                          }
                        }}
                      >
                        <DownloadIcon />
                      </button>
                      <button
                        className="action-btnNew"
                        title="删除"
                        onClick={() => { 
                          // 确保 item.path 存在，然后将其放入一个数组中
                          if (item.path) {
                            setSingleDeleteId(item); 
                            setIsBatchModalOpen(true); 
                          }
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
              {/* ✅ 核心修改：根据 selectedFile 是否存在，显示不同内容 */}
              {selectedFile ? (
                // 情况1：如果已选择文件，显示文件信息
                <div className="selected-file-info" style={{ padding: '16px', border: '1px solid #e8e8e8', borderRadius: '4px', marginBottom: '16px', textAlign: 'center' }}>
                  <p style={{ margin: '8px 0', fontSize: '16px' }}>
                    <strong>已选择文件：</strong> {selectedFile.name}
                  </p>
                  <p style={{ margin: '8px 0', color: '#666' }}>
                    <strong>大小：</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                // 情况2：如果未选择文件，显示原来的上传区域
                <div className="upload-drop-zone" onDragOver={(e) => e.preventDefault()} onClick={() => fileInputRef.current?.click()}>
                  <div className="upload-icon-wrapper">
                    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 10C4 8.89543 4.89543 8 6 8H18L22 12H42C43.1046 12 44 12.8954 44 14V38C44 39.1046 43.1046 40 42 40H6C4.89543 40 4 39.1046 4 38V10Z" fill="#FADB14"/>
                      <path d="M4 14H44V38C44 39.1046 43.1046 40 42 40H6C4.89543 40 4 39.1046 4 38V14Z" fill="#FFF566" fillOpacity="0.5"/>
                    </svg>
                  </div>
                  <p className="upload-main-text">点击或拖拽文件到此处上传</p>
                  <p className="upload-sub-text">支持 CSV, JSON, Excel, TXT, NetCDF, GeoTIFF, HDF5, 图片等格式，单个文件最大 500MB</p>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <span className="footer-hint">上传后将存储在「我上传的」数据列表中</span>
              <div className="action-buttons">
                <button className="btn-secondary" onClick={() => setIsUploadModalOpen(false)}>取消</button>
                <button  className="btn-primaryNew" 
                  onClick={handleUpload}
                  disabled={uploading}
                >
                  {uploading ? '上传中...' : '开始上传'}
                </button>
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
                  确定要删除文件 <strong>“{singleDeleteId.name || '该文件'}”</strong> 吗？此操作不可撤销。
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
                onClick={async () => {
                  let paths = [];
                  if (singleDeleteId !== null) {
                    // 单个删除：获取当前项的 path
                    if (singleDeleteId.path) {
                      paths = [singleDeleteId.path];
                    }
                  } else {
                    // 批量删除：从 fileSystemItems 中找出所有被选中的项，并提取它们的 path
                    paths = fileSystemItems
                      .filter(item => selectedIds.has(item.name) && item.path)
                      .map(item => item.path);
                  }

                  if (paths.length > 0) {
                    await handleDelete(paths);
                  }
                  setIsBatchModalOpen(false);
                  setSingleDeleteId(null);
                }}
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files?.[0] || null;
          setSelectedFile(file);
        }}
        accept=".csv,.json,.xlsx,.xls,.txt,.nc,.tiff,.tif,.hdf5,.h5,image/*"
      />
    </div>
  );
};

export default MyDataPage;