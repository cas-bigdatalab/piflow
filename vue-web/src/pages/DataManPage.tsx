// src/pages/DataManPage.tsx
import React, { useState } from 'react';
import './DataManPage.css';

const DataManPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const datasetList = [
    { id: 1, name: '用户行为数据', description: '2024年用户点击日志', createdAt: '2024-06-01' },
    { id: 2, name: '商品评论数据', description: '电商平台评论数据集', createdAt: '2024-05-28' },
  ];

  // ... 其他代码不变 ...
  return (
    <div className="pageContainer">
      <div className="mainContent">
        <h1 className="pageTitle">数据管理</h1>

        {/* 👇 新增白色卡片容器 */}
        <div className="contentCard">
          <div className="toolbar">
            <input
              type="text"
              placeholder="搜索数据集名称"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="searchInput"
            />
            <button className="createButton">新建数据集</button>
          </div>

          <div className="tableContainer">
            <table className="dataTable">
              <thead>
                <tr>
                  <th>数据集名称</th>
                  <th>描述</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {datasetList.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td>{item.description}</td>
                    <td>{item.createdAt}</td>
                    <td>
                      {/* 注意：改为链接样式，非按钮 */}
                      <span className="editLink">编辑</span>
                      <span className="deleteLink">删除</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span>共 {datasetList.length} 条</span>
          </div>
        </div> {/* 👈 关闭 contentCard */}
      </div>
    </div>
  );
};

export default DataManPage;