import React from 'react';
import { Database, Globe, HardDrive, Activity, Cloud, Layers, BookOpen, CloudRain, Server, 
    Plus, Search, MoreHorizontal, Trash2, Edit3, PlayCircle, Link as LinkIcon,X
} from 'lucide-react';
import { useState } from 'react';
import './DataManConnectionsPage.css';
// --- 类型定义 ---
interface ConnectionItem {
  id: string;
  title: string;
  type: string;
  iconColor: string; // 图标背景色
  iconComponent: React.ElementType;
  details: { label: string; value: string }[];
}

interface DataSourceItem {
  id: string;
  name: string;
  desc: string;
  iconColor: string;
  iconComponent: React.ElementType;
}

// --- 支持的数据源图标组件 (简化版) ---
const IconMySQL = () => <Database className="icon-base text-blue-600" />;
const IconMariaDB = () => <Database className="icon-base text-red-600" />;
const IconPostgreSQL = () => <Database className="icon-base text-indigo-600" />;
const IconSQLServer = () => <Database className="icon-base text-red-500" />;
const IconDM = () => <div className="text-xs font-bold text-red-700">达梦</div>;
const IconOceanBase = () => <div className="text-xs font-bold text-blue-500">OB</div>;
const IconTimescale = () => <Activity className="icon-base text-orange-500" />;
const IconPostGIS = () => <Globe className="icon-base text-green-600" />;
const IconMinIO = () => <HardDrive className="icon-base text-red-500" />;
const IconHive = () => <Layers className="icon-base text-yellow-500" />;
const IconDataSpace = () => <Cloud className="icon-base text-purple-500" />;
const IconRestAPI = () => <div className="text-xs font-bold text-white bg-red-500 px-1 rounded">API</div>;
const IconWeather = () => <CloudRain className="icon-base text-cyan-500" />;
const IconScience = () => <div className="icon-science"><div className="icon-science-dot" /></div>;
const IconKafka = () => <div className="text-xs font-bold text-black"></div>;
const IconRabbitMQ = () => <div className="icon-mq-orange">MQ</div>;
const IconMilvus = () => <div className="icon-mq-cyan">M</div>;
const IconFAISS = () => <div className="grid-faiss"><div className="bg-blue-500"/><div className="bg-blue-300"/><div className="bg-blue-300"/><div className="bg-blue-500"/></div>;
const IconRAG = () => <BookOpen className="icon-base text-emerald-500" />;

// --- 模拟数据 ---
const connections: ConnectionItem[] = [
  { id: '1', title: '生产环境-MySQL主库', type: 'MySQL', iconColor: 'bg-blue-100', iconComponent: IconMySQL, details: [{ label: '地址', value: '192.168.1.100:3306' }, { label: '库', value: 'prod_db' }, { label: '创建', value: '2025-06-20' }] },
  { id: '2', title: 'GIS空间数据库', type: 'PostgreSQL', iconColor: 'bg-indigo-100', iconComponent: IconPostgreSQL, details: [{ label: '地址', value: '10.0.0.5:5432' }, { label: '库', value: 'gis_data' }, { label: '创建', value: '2025-06-15' }] },
  { id: '3', title: '对象存储-MinIO', type: 'MinIO', iconColor: 'bg-red-100', iconComponent: IconMinIO, details: [{ label: '地址', value: 'minio.local:9000' }, { label: '库', value: 'data-lake' }, { label: '创建', value: '2025-06-10' }] },
  { id: '4', title: '实时数据流-Kafka', type: 'Kafka', iconColor: 'bg-gray-100', iconComponent: IconKafka, details: [{ label: '地址', value: 'kafka-cluster:9092' }, { label: '库', value: 'sensor-stream' }, { label: '创建', value: '2025-06-05' }] },
  { id: '5', title: '第三方API-数据服务', type: 'REST API', iconColor: 'bg-red-50', iconComponent: IconRestAPI, details: [{ label: '地址', value: 'api.provider.com:443' }, { label: '创建', value: '2025-05-28' }] },
  { id: '6', title: '向量检索库-Milvus', type: 'Milvus', iconColor: 'bg-cyan-100', iconComponent: IconMilvus, details: [{ label: '地址', value: 'milvus.local:19530' }, { label: '库', value: 'embeddings' }, { label: '创建', value: '2025-05-20' }] },
  { id: '7', title: '科研文献知识库', type: 'RAG知识库', iconColor: 'bg-emerald-100', iconComponent: IconRAG, details: [{ label: '地址', value: 'rag.local:8000' }, { label: '库', value: 'papers' }, { label: '创建', value: '2025-05-15' }] },
  { id: '8', title: '北京气象站-WS001', type: '自动气象站', iconColor: 'bg-cyan-50', iconComponent: IconWeather, details: [{ label: '地址', value: '192.168.2.10:502' }, { label: '创建', value: '2025-05-10' }] },
  { id: '9', title: 'Hadoop大数据集群', type: 'Hive', iconColor: 'bg-yellow-100', iconComponent: IconHive, details: [{ label: '地址', value: 'hive-master:10000' }, { label: '库', value: 'bigdata' }, { label: '创建', value: '2025-05-01' }] },
];

const dataSources: DataSourceItem[] = [
  { id: 'ds1', name: 'MySQL', desc: '最流行的开源关系型数据库', iconColor: 'bg-blue-50', iconComponent: IconMySQL },
  { id: 'ds2', name: 'MariaDB', desc: 'MySQL的开源替代分支', iconColor: 'bg-red-50', iconComponent: IconMariaDB },
  { id: 'ds3', name: 'PostgreSQL', desc: '强大的开源对象关系型数据库', iconColor: 'bg-indigo-50', iconComponent: IconPostgreSQL },
  { id: 'ds4', name: 'SQL Server', desc: '微软企业级关系型数据库', iconColor: 'bg-red-50', iconComponent: IconSQLServer },
  { id: 'ds5', name: '达梦', desc: '国产自主知识产权数据库', iconColor: 'bg-red-50', iconComponent: IconDM },
  { id: 'ds6', name: 'OceanBase', desc: '蚂蚁集团分布式关系型数据库', iconColor: 'bg-blue-50', iconComponent: IconOceanBase },
  { id: 'ds7', name: 'TimescaleDB', desc: '基于PostgreSQL的时序数据库', iconColor: 'bg-orange-50', iconComponent: IconTimescale },
  { id: 'ds8', name: 'PostGIS', desc: 'PostgreSQL的空间数据扩展', iconColor: 'bg-green-50', iconComponent: IconPostGIS },
  { id: 'ds9', name: 'MinIO', desc: '高性能开放对象存储', iconColor: 'bg-red-50', iconComponent: IconMinIO },
  { id: 'ds10', name: 'Hive', desc: '基于Hadoop的数据仓库', iconColor: 'bg-yellow-50', iconComponent: IconHive },
  { id: 'ds11', name: 'DataSpace', desc: '科研数据空间管理平台', iconColor: 'bg-purple-50', iconComponent: IconDataSpace },
  { id: 'ds12', name: 'REST API', desc: '标准RESTful接口数据源', iconColor: 'bg-red-500', iconComponent: IconRestAPI },
  { id: 'ds13', name: '自动气象站', desc: '气象观测数据实时采集', iconColor: 'bg-cyan-50', iconComponent: IconWeather },
  { id: 'ds14', name: '科学装置', desc: '大型科学装置数据接入', iconColor: 'bg-purple-50', iconComponent: IconScience },
  { id: 'ds15', name: 'Kafka', desc: '分布式流处理消息队列', iconColor: 'bg-gray-100', iconComponent: IconKafka },
  { id: 'ds16', name: 'RabbitMQ', desc: '开源消息队列中间件', iconColor: 'bg-orange-50', iconComponent: IconRabbitMQ },
  { id: 'ds17', name: 'Milvus', desc: '开源向量数据库', iconColor: 'bg-cyan-50', iconComponent: IconMilvus },
  { id: 'ds18', name: 'FAISS', desc: 'Facebook高效向量检索库', iconColor: 'bg-blue-50', iconComponent: IconFAISS },
  { id: 'ds19', name: 'RAG知识库', desc: '检索增强生成知识库', iconColor: 'bg-emerald-50', iconComponent: IconRAG },
];

// 新建连接中的默认数据
const DATA_SOURCES = [
  { id: 'mysql', name: 'MySQL', icon: IconMySQL, color: 'bg-blue-100' },
  { id: 'mariadb', name: 'MariaDB', icon: IconMariaDB, color: 'bg-red-100' },
  { id: 'postgresql', name: 'PostgreSQL', icon: IconPostgreSQL, color: 'bg-blue-50' },
  { id: 'sqlserver', name: 'SQL Server', icon: IconSQLServer, color: 'bg-red-50' },
  { id: 'dameng', name: '达梦', icon: IconMariaDB, color: 'bg-red-100' },
  { id: 'oceanbase', name: 'OceanBase', icon: IconOceanBase, color: 'bg-blue-100' },
  { id: 'timescaledb', name: 'TimescaleDB', icon: IconMariaDB, color: 'bg-yellow-100' },
  { id: 'postgis', name: 'PostGIS', icon: IconPostGIS, color: 'bg-green-50' },
  { id: 'minio', name: 'MinIO', icon: IconMinIO, color: 'bg-red-50' },
  { id: 'hive', name: 'Hive', icon: IconHive, color: 'bg-yellow-100' },
  { id: 'dataspace', name: 'DataSpace', icon: IconDataSpace, color: 'bg-purple-100' },
  { id: 'restapi', name: 'REST API', icon: IconRestAPI, color: 'bg-orange-100' },
  { id: 'weather', name: '自动气象站', icon: IconPostgreSQL, color: 'bg-blue-50' },
  { id: 'science', name: '科学装置', icon: IconMySQL, color: 'bg-purple-50' },
  { id: 'kafka', name: 'Kafka', icon: IconKafka, color: 'bg-gray-100' },
  { id: 'rabbitmq', name: 'RabbitMQ', icon: IconRabbitMQ, color: 'bg-orange-100' },
  { id: 'milvus', name: 'Milvus', icon: IconMilvus, color: 'bg-blue-50' },
  { id: 'faiss', name: 'FAISS', icon: IconFAISS, color: 'bg-blue-100' },
  { id: 'rag', name: 'RAG知识库', icon: IconRAG, color: 'bg-green-100' },
];

// 弹框的表单字段
// 表单字段配置
const SOURCE_FORM_FIELDS: Record<string, { label: string; key: string; placeholder?: string }[]> = {
  mysql: [
    { label: '主机', key: 'host', placeholder: '例如：localhost' },
    { label: '端口', key: 'port', placeholder: '3306' },
    { label: '用户名', key: 'username' },
    { label: '密码', key: 'password', placeholder: '••••••••' },
    { label: '数据库', key: 'database' },
  ],
  postgresql: [
    { label: '主机', key: 'host' },
    { label: '端口', key: 'port', placeholder: '5432' },
    { label: '用户名', key: 'username' },
    { label: '密码', key: 'password' },
    { label: '数据库', key: 'database' },
  ],
  restapi: [
    { label: 'API 地址', key: 'url', placeholder: 'https://api.example.com/data' },
    { label: '认证 Token (可选)', key: 'token' },
  ],
  minio: [
    { label: 'Endpoint', key: 'endpoint', placeholder: 'http://minio:9000' },
    { label: 'Access Key', key: 'accessKey' },
    { label: 'Secret Key', key: 'secretKey' },
    { label: 'Bucket', key: 'bucket' },
  ],
  // 可为其他类型补充...
};
// --- 子组件 ---
const ConnectionCard = ({ item }: { item: ConnectionItem }) => (
  <div className="connection-card">
    <div>
      <div className="card-header">
        <div className={`icon-wrapper ${item.iconColor}`}>
          <item.iconComponent />
        </div>
        <div className="card-title-group">
          <h3 className="card-title" title={item.title}>{item.title}</h3>
          <span className="card-type">{item.type}</span>
        </div>
      </div>
      <div className="card-details">
        {item.details.map((d, i) => (
          <div key={i} className="detail-row">
            <span className="detail-label">{d.label}</span>
            <span className="detail-value">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
    <div className="card-actions">
      <button className="action-btn"
        onClick={() => {
          setSingleDeleteId(item.id);
          setIsBatchModalOpen(true);
        }}
      >测试</button>
      <button className="action-btn action-btn-edit">
        <Edit3 className="w-3 h-3" /> 编辑
      </button>
      <button className="action-btn-delete">
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  </div>
);

const DataSourceCard = ({ item }: { item: DataSourceItem }) => (
  <div className="datasource-card">
    <div className={`icon-wrapper ${item.iconColor}`}>
      <item.iconComponent />
    </div>
    <div className="datasource-info">
      <h4 className="datasource-name">{item.name}</h4>
      <p className="datasource-desc">{item.desc}</p>
    </div>
  </div>
);

// --- 主页面组件 ---
export default function DataConnectionsPage() {
const [showNewConnectionModal, setShowNewConnectionModal] = useState(false);
const [selectedSource, setSelectedSource] = useState<string | null>(null);
const [connectionConfig, setConnectionConfig] = useState<Record<string, string>>({});
// 删除弹框状态参数值
const [singleDeleteId, setSingleDeleteId] = useState<number | null>(null);
const handleOpenModal = () => setShowNewConnectionModal(true);
    const handleCloseModal = () => {
    setShowNewConnectionModal(false);
};
const handleSelectSource = (id: string) => {
  setSelectedSource(id);
  setConnectionConfig({}); // 重置表单内容
};


  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">数据连接</h1>
          <p className="page-subtitle">配置和管理外部数据库连接，支持多种数据库、存储、API和消息队列等数据源</p>
        </div>
        <button className="btn-primaryNew"
            onClick={handleOpenModal}
        >
          <Plus className="w-4 h-4" /> 新建连接
        </button>
      </div>

      {/* Section 1: My Connections */}
      <section className="page-section">
        <h2 className="section-title">
          <LinkIcon className="w-4 h-4 text-slate-500" /> 我的连接
        </h2>
        <div className="connections-grid">
          {connections.map(item => <ConnectionCard key={item.id} item={item} />)}
          {/* Add New Card */}
          <button className="add-new-card">
            <div className="add-new-icon-wrapper">
              <Plus className="w-5 h-5" />
            </div>
            <span className="add-new-text">新建连接</span>
          </button>
        </div>
      </section>

      {/* Section 2: Supported Data Sources */}
      <section className="page-section">
        <h2 className="section-title">
          <Database className="w-4 h-4 text-slate-500" /> 支持的数据源（{dataSources.length}种）
        </h2>
        <div className="datasources-grid">
          {dataSources.map(item => <DataSourceCard key={item.id} item={item} />)}
        </div>
      </section>



      {/* 新建数据连接弹框 */}
        {showNewConnectionModal && (
            <div className="modal-overlay">
            <div className="modal-container">
                {/* 弹窗头部 */}
                <div className="modal-header">
                <h2 className="modal-title">新建数据连接</h2>
                <button className="modal-close-btn" onClick={handleCloseModal}>
                    <X size={20} />
                </button>
                </div>

                {/* 弹窗内容 - 网格选择区 */}
                <div className="modal-body">
                <p className="modal-subtitle">选择数据源类型</p>
                <div className="source-grid">
                    {DATA_SOURCES.map((source) => (
                    <div 
                        key={source.id} 
                        className={`grid-item ${selectedSource === source.id ? 'grid-item-active' : ''}`}
                        onClick={() => handleSelectSource(source.id)}
                    >
                        <div className={`item-icon-wrapper ${source.color}`}>
                        <source.icon />
                        </div>
                        <span className="item-label">{source.name}</span>
                    </div>
                    ))}
                </div>
                {/* 单击某个数据链接后显示的内容 */}
                {selectedSource && (
                    <div className="form-section mt-6">
                        {SOURCE_FORM_FIELDS[selectedSource] ? (
                        <div className="form-fields">
                            {SOURCE_FORM_FIELDS[selectedSource].map((field) => (
                            <div key={field.key} className="form-field">
                                <label className="form-label">{field.label}</label>
                                <input
                                type={field.key === 'password' ? 'password' : 'text'}
                                className="form-input"
                                placeholder={field.placeholder || ''}
                                value={connectionConfig[field.key] || ''}
                                onChange={(e) =>
                                    setConnectionConfig((prev) => ({
                                    ...prev,
                                    [field.key]: e.target.value,
                                    }))
                                }
                                />
                            </div>
                            ))}
                        </div>
                        ) : (
                        <p className="text-slate-500 text-sm">该数据源暂无需额外配置</p>
                        )}
                    </div>
                )}
                </div>

                {/* 弹窗底部按钮 */}
                <div className="modal-footer">
                <button className="btn-text" onClick={handleCloseModal}>取消</button>
                <button className="btn-secondary">测试连接</button>
                <button className="btn-primary-gradient">保存连接</button>
                </div>
            </div>
            </div>
        )}
    </div>
  );
}