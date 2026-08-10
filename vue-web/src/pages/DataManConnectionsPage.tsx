import React from 'react';
import { Database, Globe, HardDrive, Activity, Cloud, Layers, BookOpen, CloudRain, Server, 
    Plus, Trash2, Edit3, Link as LinkIcon,X
} from 'lucide-react';
import { useState,useEffect } from 'react';
import './DataManConnectionsPage.css';
import { listDataspace,listDataspaceDirecory,detailFiled,detailCreate,detail,validate,deleteSource,validateById,detailUpdate} from "../lib/api";
// --- 类型定义 ---
interface ConnectionItem {
  app_id: string;
  auth_code: string;
  base_url: string;
  created_at: string;
  ftp_link: string;
  ftp_password: string;
  ftp_user: string;
  logo: string;
  root_path: string;
  source_id: string
  space_id: string;
  space_name: string;
  updated_at: string;
  webdav_link: string;
  database_name:string;
  name: string;
  type_code: string;
}

interface DataSourceItem {
  id: string;
  typeName: string;       // 原 name
  description: string;    // 原 desc
  logo: string | null;  // 原 iconComponent —— 注意：这里假设后端返回的是组件或可渲染内容
  type_code: string;
}

// 根据类型掉接口的字段
interface FieldConfig {
  label: string;
  name: string;  
  placeholder?: string;
  type?: string; // 可选，用于指定 input 类型
}


// --- LogoUpload 组件 ---
interface LogoUploadProps {
  value: string | File | undefined;
  onChange: (file: File | undefined) => void;
}

const LogoUpload: React.FC<LogoUploadProps> = ({ value, onChange }) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 校验文件类型
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      alert('仅支持 JPG/PNG 格式的图片！');
      return;
    }

    // 校验文件大小（2MB）
    if (file.size > 2 * 1024 * 1024) {
      alert('图片大小不能超过 2MB！');
      return;
    }

    onChange(file);
  };
const handleDelete = (e: React.MouseEvent) => {
  e.stopPropagation();
  onChange(undefined);
  if (fileInputRef.current) {
    fileInputRef.current.value = '';
  }
};
const getPreviewSrc = () => {
  if (value instanceof File) {
    return URL.createObjectURL(value);
  } else if (typeof value === 'string' && value) {
    return value;
  }
  return null;
};

const previewSrc = getPreviewSrc();
  return (
    <div className="logo-upload-area">
      <input
        type="file"
        accept=".png,.jpg,.jpeg"
        className="hidden"
        ref={fileInputRef}
        onChange={handleFileChange}
      />
      <div
        className={`upload-placeholder relative border-2 border-dashed rounded-lg p-4 cursor-pointer flex items-center justify-center min-h-[120px] transition-colors ${
          previewSrc ? 'border-transparent' : 'hover:border-blue-400'
        }`}
        onClick={handleUploadClick}
        style={{ background: previewSrc ? '#f8fafc' : 'transparent' }}
      >
        {previewSrc ? (
          <>
            <img
              src={previewSrc}
              alt="Logo 预览"
              className="max-w-full max-h-full object-contain"
              style={{ maxHeight: '160px' }}
            />
            <button
              type="button"
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center shadow-md text-xs z-10"
              onClick={handleDelete}
            >
              ×
            </button>
          </>
        ) : (
          <div className="flex flex-col items-center text-slate-500">
            <Plus className="w-6 h-6 mb-2 text-slate-400" />
            <span className="text-sm">点击上传 Logo</span>
            <span className="text-xs mt-1 text-slate-400">(JPG/PNG, ≤2MB)</span>
          </div>
        )}
      </div>
    </div>
  );
};
export default function DataManConnectionsPage(){

// 数据源类型列表数组赋值
const [dataSources, setDataSources] = useState<DataSourceItem[]>([]);
// 数据源类型列表实例数组赋值
const [dataSourcesDirectory, setDataSourcesDirectory] = useState<DataSourceItem[]>([]);
//记录source_id
const [dataSourceId,setSourceId] = useState("");
//记录数据源类型
const [typeCode,setTypeCode]  = useState("");
// 数据源类型所返回的字段
const [detailFileds,setDetailFiled] = useState<FieldConfig[]>([]);
//编辑数据源类型所返回的字段
const [editFields,setEditFields] = useState<FieldConfig[]>([]);
const fileInputRef = React.useRef<HTMLInputElement>(null);
// 数据源类型列表
useEffect(() => {
  const fetchDataSources = async () => {
    try {
      const res = await listDataspace(); // 假设返回 DataSourceItem[]
      console.log(res);
      setDataSources(res.result.items);
    } catch (error) {
      console.error('Failed to fetch data sources:', error);
      // 可选：设置默认值或错误提示
    }
  };
  fetchDataSources();
}, []);
// 数据源类型实例列表
useEffect(() => {
  const fetchDataDirectorySources = async () => {
    try {
      const res = await listDataspaceDirecory(); // 假设返回 DataSourceItem[]
      console.log(res);
      setDataSourcesDirectory(res.result.items);
    } catch (error) {
      console.error('Failed to fetch data sources:', error);
      // 可选：设置默认值或错误提示
    }
  };
  fetchDataDirectorySources();
}, []);
//封装一个刷新方法
const refreshDataSourcesDirectory = async () => {
  try {
    const res = await listDataspaceDirecory();
    setDataSourcesDirectory(res.result.items);
  } catch (error) {
    console.error('Failed to refresh data sources directory:', error);
  }
};
//图片转为base64
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
  });
};
//保存数据连接
const handleSaveConnection = async (show:boolean) => {
  // 将图片logo文件转为base64传给后台
  let configToSend = { ...connectionConfig };
  if (configToSend.logo instanceof File) {
    try {
      configToSend.logo = await fileToBase64(configToSend.logo);
    } catch (err) {
      alert('Logo 文件读取失败');
      return;
    }
  }
  //true为保存链接，false为修改链接,一个编辑一个新增
  if (show){
    try {
      const res = await detailCreate(configToSend);
      if (res.code === 200 || res.success) {
        alert('连接保存成功！');
        handleCloseModal();
        await refreshDataSourcesDirectory();
      } else {
        alert('保存失败：' + (res.message || '未知错误'));
      }
    } catch (error) {
      console.error('保存连接失败:', error);
      alert('网络请求失败，请重试');
    }
  } else {
    try {
      // 调用接口
      console.log(connectionConfig)
      let connectionConfigNew = {
        source_id: connectionConfig.source_id,
        base_url: connectionConfig.base_url,
        app_id: connectionConfig.app_id,
        auth_code: connectionConfig.auth_code,
        space_name: connectionConfig.space_name,
        ftp_user: connectionConfig.ftp_user,
        ftp_password: connectionConfig.ftp_password,
        logo:  configToSend.logo,
        name:connectionConfig.name

      }
      const res = await detailUpdate(connectionConfigNew);
      if (res.code === 200 || res.success) {
        alert('连接修改成功！');
        handleCloseModal();
        await refreshDataSourcesDirectory();
      } else {
        alert('修改失败：' + (res.message || '未知错误'));
      }
    } catch (error) {
      console.error('修改连接失败:', error);
      alert('网络请求失败，请重试');
    }
  }
};
//实例详情接口
const hanldeDetail = async (item:any) => {
  setShowEditConnectionModal(true); //打开编辑弹框 
  setSourceId(item.source_id); //测试连接调用详情接口时候进行使用
  setTypeCode(item.type_code); //测试连接需要使用数据源类型来进行封装参数
  //调用详情接口前，先调用字段详情接口
  try {
    const res = await detailFiled(item.type_code);
    //编辑和新增时调用字段详情接口分开
    setEditFields(res.result.catalog.init_fields || [])
  } catch (error) {
    console.error('Failed to fetch data sources:', error);
  }
  try {
    const res = await detail(item.source_id);
    if (res.code === 200 || res.success) {
      const sourceData = res.result.source;
      setConnectionConfig({
        ...sourceData,
        auth_code: '',
        ftp_password: '',
      });
    } else {
      alert('保存失败：' + (res.message || '未知错误'));
    }
  } catch (error) {
    console.error('保存连接失败:', error);
    alert('网络请求失败，请重试');
  }
};

//删除接口

const handleDelte = async (item:any) => {
  try {
    const res = await deleteSource(item.source_id);
    if (res.code === 200 || res.success) {
     alert('删除成功!');
     await listDataspaceDirecory();
    } else {
     alert('删除失败!');
    }
  } catch (error) {
    console.error('保存连接失败:', error);
    alert('网络请求失败，请重试');
  }
};

//测试接口(分为两个测试接口，一个是保存后测试，一个是未保存后的测试)
const handleValidate = async (source_id:string,show:boolean,type_code:string) => {
  if (show){ //为true，是保存后的测试，直接使用source_id进行接口测试
    try {
      const res = await validateById(source_id);
      if (res.code === 200 || res.success) {
        alert('连接测试成功!');
      } else {
        alert('连接测试失败');
      }
    } catch (error) {
      console.error('连接测试失败:', error);
      alert('连接测试失败，请重试');
    }
  } else {
    // 调用详情接口
    let payload: Record<string, any> = {};
    try {
      const res = await detail(source_id);
      if (res.code === 200 || res.success) {
        payload = res.result.source;
      } else {
        alert('保存失败：' + (res.message || '未知错误'));
      }
    } catch (error) {
      console.error('保存连接失败:', error);
      alert('网络请求失败，请重试');
    }
    
    let payloadNew: Record<string, any> = {};
    if (type_code === "dataspace"){
      payloadNew = {
        "base_url": payload.base_url,
        "app_id":payload.app_id,
        "auth_code": payload.auth_code,
        "space_name": payload.space_name,
        "ftp_user": payload.ftp_user,
        "ftp_password":payload.ftp_password,
        "name":payload.name
      }
    }
    try {
      const res = await validate(payloadNew);
      if (res.code === 200 || res.success) {
        alert('连接测试成功!');
      } else {
        alert('连接测试失败');
      }
    } catch (error) {
      console.error('连接测试失败:', error);
      alert('连接测试失败，请重试');
    }
  }
};

// --- 子组件 ---
const ConnectionCard = ({ item }: { item: ConnectionItem }) => (
  <div className="connection-card">
    <div>
      <div className="card-header">
        <div className="icon-wrapper-rounded">
          <img 
            src={item.logo} 
            alt={item.name} 
            className="logo-image" 
          />
        </div>
        <div className="card-title-group">
          <h3 className="card-title" title={item.name}>{item.name}</h3>
          <span className="card-type">{item.type_code}</span>
        </div>
      </div>
      <div className="card-details">
        <div className="detail-row">
          <span className="detail-label">地址</span>
          <span className="detail-value">{item.base_url}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">库</span>
          <span className="detail-value">{item.database_name}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">创建</span>
          <span className="detail-value">{item.created_at?.slice(0, 10)}</span>
        </div>
      </div>
    </div>
    <div className="card-actions">
      <button className="action-btn"
        onClick={() => {
          handleValidate(item.source_id,true,item.type_code)
        }}
      >测试</button>
      <button className="action-btn action-btn-edit"
        onClick={() => {
          hanldeDetail(item);
        }}
      >
        <Edit3 className="w-3 h-3" /> 编辑
      </button>
      <button className="action-btn-delete" 
        onClick={() => {
          handleDelte(item)
        }}>
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  </div>
);

const DataSourceCard = ({ item }: { item: DataSourceItem }) => {
  return (
    <div className="datasource-card"
      onClick={handleOpenModal}
    >
      <div className="icon-wrapper bg-gray-100" > {/* 可根据需要动态设置背景色 */}
         {item.logo ? (
          <img 
            src={item.logo} 
            alt={item.typeName} 
            className="w-full h-full object-contain" 
            onError={(e) => {
              // 可选：加载失败时回退到默认图标
              e.currentTarget.style.display = 'none';
              // 或替换为默认图标
            }}
          />
        ) : (
          <Database className="icon-base text-gray-400" />
        )}
      </div>
      <div className="datasource-info">
        <h4 className="datasource-name">{item.type_name}</h4>
        <p className="datasource-desc">{item.description}</p>
      </div>
    </div>
  );
};

// --- 主页面组件 ---
const [showNewConnectionModal, setShowNewConnectionModal] = useState(false);
//编辑数据连接
const [showEditConnectionModal, setShowEditConnectionModal] = useState(false);
const [selectedSource, setSelectedSource] = useState<string | null>(null);
// 替换原来的 connectionConfig 类型
const [connectionConfig, setConnectionConfig] = useState<Record<string, string | File | undefined>>({});

// 删除弹框状态参数值
const [singleDeleteId, setSingleDeleteId] = useState<number | null>(null);
const handleOpenModal = () => setShowNewConnectionModal(true);
    const handleCloseModal = () => {
      setShowNewConnectionModal(false);
      setShowEditConnectionModal(false);
      setSelectedSource(null);         // 清空选中的数据源类型
      setConnectionConfig({});         // 清空表单输入内容
      setDetailFiled([]);
  };
const handleSelectSource = async (type_code: string) => {
  setSelectedSource(type_code);
  // 根据type_code数据源类型查询新增哪些字段
  try {
    const res = await detailFiled(type_code);
    console.log("根据类型查询出的数据源类型为—---------------------------",res);
    // 将接口返回的字段赋值给弹框中显示
    const fields: FieldConfig[] = (res.result.catalog.init_fields || []).map(field => ({
      label: field.label,
      name: field.name, // ← 关键：使用 name
      placeholder: field.placeholder,
      type: field.type
    }));
    setDetailFiled(res.result.catalog.init_fields || [])
  } catch (error) {
    console.error('Failed to fetch data sources:', error);
  }
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
          {dataSourcesDirectory.map(item => <ConnectionCard key={item.id} item={item} />)}
          <button className="add-new-card"
            onClick={handleOpenModal}>
            <div className="add-new-icon-wrapper"
            >
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
          {dataSources.map(item => <DataSourceCard item={item} />)}
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
                {dataSources.map((source) => (
                  <div
                    key={source.type_code}
                    className={`grid-item ${selectedSource === source.type_code ? 'grid-item-active' : ''}`}
                    onClick={() => handleSelectSource(source.type_code)}
                  >
                    <div className="item-icon-wrapper">
                        {source.logo ? (
                          <img 
                            src={source.logo} 
                            alt={source.type_name} 
                            className="w-full h-full object-contain" 
                          />
                        ) : (
                          <Database className="icon-base text-gray-400" />
                        )}
                    </div>
                    <span className="item-label">{source.type_name}</span>
                  </div>
                ))}
              </div>

              {/* 单击某个数据链接后显示的内容 */}
              {selectedSource && (
                <div className="form-section mt-6">
                  {detailFileds.length > 0 ? (
                    <div className="form-fields">
                      {detailFileds.map((field) => (
                        <div key={field.name} className="form-field">
                          <label className="form-label">{field.label}</label>
                          {field.label === 'Logo' ? (
                              // <div className="file-upload-wrapper">
                              //   <input
                              //     type="file"
                              //     accept=".png,.jpg,.jpeg"
                              //     className="form-input-file"
                              //     onChange={(e) => {
                              //       const file = e.target.files?.[0] || null;
                              //       setConnectionConfig((prev) => ({
                              //         ...prev,
                              //         [field.name]: file,
                              //       }));
                              //     }}
                              //   />
                              //   {/* 显示当前 logo：优先显示 File 名称，否则显示预览图（如果是 URL） */}
                              //   {(() => {
                              //     const currentLogo = connectionConfig[field.name];
                              //     if (currentLogo instanceof File) {
                              //       return <p className="file-name text-sm text-slate-500 mt-1">已选择: {currentLogo.name}</p>;
                              //     } else if (typeof currentLogo === 'string' && currentLogo) {
                              //       return (
                              //         <div className="mt-2">
                              //           <p className="text-sm text-slate-500 mb-1">当前 Logo：</p>
                              //           <img 
                              //             src={currentLogo} 
                              //             alt="当前 Logo" 
                              //             className="w-12 h-12 object-contain border rounded"
                              //           />
                              //         </div>
                              //       );
                              //     }
                              //     return null;
                              //   })()}
                              // </div>
                              // 换为ant封装好的图片上传组件
                              <LogoUpload
                                value={connectionConfig[field.name]}
                                onChange={(file) => {
                                  setConnectionConfig(prev => ({ ...prev, [field.name]: file }));
                                }}
                              />
                            ) : (
                            <input
                              type={field.type === 'password' ? 'password' : 'text'}
                              className="form-input"
                              placeholder={field.placeholder || `请输入${field.label}`}
                              value={typeof connectionConfig[field.name] === 'string' ? connectionConfig[field.name] : ''} 
                              onChange={(e) =>
                                setConnectionConfig((prev) => ({
                                  ...prev,
                                  [field.name]: e.target.value,
                                }))
                              }
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="form-fields">
                      <p className="text-slate-500 text-sm mb-4">该数据源暂无需额外配置</p>
                      {/* 如果确实需要默认字段，可保留；否则建议移除 */}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 弹窗底部按钮 */}
            <div className="modal-footer">
              <button className="btn-text" onClick={handleCloseModal}>取消</button>
              <button className="btn-secondary"
                onClick={() => {
                  handleValidate(dataSourceId,true,typeCode)
                }}
              >测试连接</button>
              <button className="btn-primary-gradient"
                onClick={() => {
                  handleSaveConnection(true)
                }}>保存连接</button>
            </div>
          </div>
        </div>
      )}
      {/* 编辑数据连接 */}
      {/* 编辑数据连接弹框 */}
      {showEditConnectionModal && (
        <div className="modal-overlay">
          <div className="modal-container">
            {/* 弹窗头部 */}
            <div className="modal-header">
              <h2 className="modal-title">编辑数据连接</h2>
              <button 
                className="modal-close-btn" 
                onClick={() => {
                  setShowEditConnectionModal(false);
                  setConnectionConfig({});
                  setEditFields([]);
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* 弹窗内容 - 表单区 */}
            <div className="modal-body">
              <div className="form-section mt-6">
                {editFields.length > 0 ? (
                  <div className="form-fields">
                    {editFields.map((field) => (
                      <div key={field.name} className="form-field">
                        <label className="form-label">{field.label}</label>
                        {field.label === 'Logo' ? (
                          <LogoUpload
                            value={connectionConfig[field.name]}
                            onChange={(file) => {
                              setConnectionConfig(prev => ({ ...prev, [field.name]: file }));
                            }}
                          />
                        ) : (
                          <input
                            type={field.type === 'password' ? 'password' : 'text'}
                            className="form-input"
                            placeholder={field.placeholder || `请输入${field.label}`}
                            value={typeof connectionConfig[field.name] === 'string' ? connectionConfig[field.name] : ''} 
                            onChange={(e) =>
                              setConnectionConfig((prev) => ({
                                ...prev,
                                [field.name]: e.target.value,
                              }))
                            }
                          />
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm">该数据源暂无需额外配置</p>
                )}
              </div>
            </div>

            {/* 弹窗底部按钮 */}
            <div className="modal-footer">
              {/* <button className="btn-text" onClick={handleCloseModal}>取消</button> */}
              <button className="btn-secondary"
                onClick={() => {
                  handleValidate(dataSourceId,false,typeCode)
                }}
              >测试连接</button>
              <button className="btn-primary-gradient"
                onClick={() => {
                  handleSaveConnection(false)
                }}
              >修改连接</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}