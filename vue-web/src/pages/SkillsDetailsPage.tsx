import React, { useState,useEffect  } from 'react';
import { useParams, useNavigate,useSearchParams,useLocation  } from 'react-router-dom';
import { 
  ArrowLeft, Download, Trash2, Star, 
  Clock, User, Code, Layers, FileText, Folder, File, Terminal
} from 'lucide-react';
import { getSkillInfo,downloadSkillPackage } from "../lib/api";
import './SkillsDetailsPage.css';
interface OperatorParam {
  name: string;
  type: string;
  required?: boolean;
  default?: string | number | null;
  desc: string;
}

// 扩展 MOCK_DATA 包含完整信息
const MOCK_DATA: OperatorData = {
  skill_name: '',
  name_zh: '',
  englishName: '',
  version: '',
  category: '',
  author: '李明',
  language: '',
  license: '',
  env: '',
  downloads: 0,
  rating: 0,
  description: '',
  logic: [
    '',
    '',
    '',
    ''
  ],
  inputs: [
    {
      name: '',
      type: '',
      required: true,
      default: null,
      desc: '待处理的原始文本数据'
    },
    {
      name: 'min_ratio',
      type: 'float',
      required: false,
      default: '0.0',
      desc: '字母/数字比例下限阈值'
    },
    {
      name: 'max_ratio',
      type: 'float',
      required: false,
      default: '1.0',
      desc: '字母/数字比例上限阈值'
    },
    {
      name: 'granularity',
      type: 'str',
      required: false,
      default: '"char"',
      desc: '统计粒度：char（字符级）或 word（词级）'
    },
    {
      name: 'language',
      type: 'str',
      required: false,
      default: '"mixed"',
      desc: '文本语言：zh / en / mixed'
    }
  ],
  outputs: [
    {
      name: 'filtered_text',
      type: 'str',
      desc: '过滤后保留的文本数据'
    },
    {
      name: 'ratio_score',
      type: 'float',
      desc: '计算出的字母/数字比例值'
    },
    {
      name: 'is_kept',
      type: 'bool',
      desc: '是否在阈值范围内被保留'
    }
  ],
  skillJson: {
    name: 'alphabet-num-ratio-filter',
    label: '字母数字比例过滤器算子',
    version: '1.0.0',
    description: '过滤文本中字母/数字比例不在指定范围内的样本',
    author: '李明',
    tags: ['过滤', '文本', '比例筛选'],
    inputs: [
      { name: 'input_text', type: 'str', required: true },
      { name: 'min_ratio', type: 'float', required: false, default: 0.0 },
      { name: 'max_ratio', type: 'float', required: false, default: 1.0 }
    ],
    outputs: [
      { name: 'filtered_text', type: 'str' },
      { name: 'ratio_score', type: 'float' },
      { name: 'is_kept', type: 'bool' }
    ]
  },
  fileStructure: [
    'alphabet-num-ratio-filter/',
    '├── skill.md — 算子功能描述与使用说明',
    '├── skill.json — 算子配置清单',
    '├── scripts/',
    '│   ├── main.py — 算子执行入口脚本',
    '│   └── requirements.txt — Python 依赖清单',
    '└── assets/',
    '    └── icon.svg — 算子图标（64×64px）'
  ]
};
interface OperatorData {
  id: string;
  name_zh: string;
  englishName: string;
  version: string;
  category: string;
  author: string;
  language: string;
  license: string;
  env: string;
  downloads: number;
  rating: number;
  description: string;
  logic: string[];
  inputs: OperatorParam[];
  outputs: OperatorParam[];
  skillJson: any;
  file_tree: FileNode; // 替代原来的 fileStructure: string[]
}

interface FileNode {
  name: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  description?: string; // 对应 "— 说明文字"
}


// 相关算子数据
const RELATED_OPERATORS = [
  {
    id: 'avg-line-length-filter',
    name: '平均行长度过滤器算子',
    category: '过滤与筛选',
    author: '王芳'
  },
  {
    id: 'char-repeat-ratio-filter',
    name: '字符重复比例过滤器算子',
    category: '过滤与筛选',
    author: '张伟'
  },
  {
    id: 'sensitive-word-filter',
    name: '敏感词过滤器算子',
    category: '过滤与筛选',
    author: '刘洋'
  }
];



export default function SkillsDetailsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // ✅ 全部从 searchParams 获取
  const id = searchParams.get('id');
  const skillNameFromUrl = searchParams.get('name') || '未知算子';
  
  const [activeTab, setActiveTab] = useState('overview');
  const [isEnabled, setIsEnabled] = useState(true);
  const [data, setData] = useState<OperatorData | null>(null);
  const [loading, setLoading] = useState(true);
  //调用详情接口
  useEffect(() => {
    const fetchSkill = async () => {
      setLoading(true);
      try {
        const response = await getSkillInfo(id, true, true);
        
        if (response?.code === 200 && response.result) {
          setData(response.result); // ✅ 成功时设置真实数据
        } else {
          setData(MOCK_DATA); // ⚠️ 失败时回退到 mock（不是 null！）
        }
      } catch (err) {
        console.error('接口请求失败:', err);
        setData(MOCK_DATA); // ⚠️ 异常时也用 mock 保证页面可展示
      } finally {
        setLoading(false); // ✅ 只关闭 loading，不碰 data
      }
    };

    if (id) {
      fetchSkill();
    } else {
      setData(MOCK_DATA); // 无 id 时直接用 mock
      setLoading(false);
    }
  }, [id]);
  
  
  console.log("打印出接口所返回内容值",data)


  // 格式化 JSON 字符串用于显示
  const formatJson = (obj: any): string => {
    return JSON.stringify(obj, null, 2);
  };

  return (
    <div className="min-h-screen bg-[#f7f8fa] pb-20">
      {/* 1. 顶部面包屑导航 */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center text-sm text-gray-600 sticky top-0 z-10">
        <button onClick={() => navigate(-1)} className="flex items-center hover:text-blue-600 transition-colors mr-4">
          <ArrowLeft size={16} className="mr-1" /> 返回
        </button>
        <span className="mx-2 text-gray-400">/</span>
        <span className="hover:text-gray-900 cursor-pointer">算子库</span>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900 font-medium truncate">{data?.name_zh}</span>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 3. 主体内容：自定义 75% / 20% 布局 */}
        <div className="grid grid-cols-1 lg:grid-cols-[75%,20%] gap-6">
          
          {/* === 左侧主要内容 (75%) === */}
          <div className="space-y-6">
            {/* 2. 头部概览区域 */}
            <div className="flex gap-5 detail-card">
              <div className="w-16 h-16 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 shrink-0">
                <Layers size={32} />
              </div>
              
              <div>
                <h1 className="detail-card-title">{data?.name_zh}</h1>
                <div className="detail-card-slug">
                  <code className="px-2 py-0.5 text-gray-600 text-xs rounded font-mono">
                    {data?.skill_name}
                  </code>
                </div>
                <div className="detail-card-tags">
                  <span className="tag-pill">
                    {data?.skill_type}
                  </span>
                  <span className="text-gray-400 text-xs">v{data?.version}</span>
                </div>
                {/* <div className="detail-card-status">
                  <span className={`text-sm ${isEnabled ? 'text-gray-900' : 'text-gray-400'}`}>
                    {isEnabled ? '已启用' : '已停用'}
                  </span>
                  <button 
                    onClick={() => setIsEnabled(!isEnabled)}
                    className={`w-11 h-6 rounded-full relative transition-colors duration-200 ease-in-out focus:outline-none ${isEnabled ? 'bg-green-500' : 'bg-gray-200'}`}
                  >
                    <span className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full shadow transform transition-transform duration-200 ease-in-out ${isEnabled ? 'translate-x-5' : 'translate-x-0'}`} />
                  </button>
                </div> */}
                <p className="detail-card-desc">
                  {data?.description.split('。')[0]}。
                </p>

                <div className="flex items-center gap-6 text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center text-[10px] text-gray-600 font-bold">
                      {/* {data?.author.slice(0, 1)} */}
                      {'李'}
                    </div>
                    {/* {data?.author} */}
                      {'李明'}
                  </div>
                  <div className="flex items-center gap-1"><Clock size={12}/> 发布于 {data?.create_time}</div>
                  <div className="flex items-center gap-1"><Clock size={12}/> 最后更新 {data?.update_time}</div>
                  {/* <div className="flex items-center gap-1"><Download size={12}/> 下载 {data?.downloads.toLocaleString()}</div> */}
                </div>
              </div>
            </div>

            {/* <div className="flex flex-col items-end gap-4">
              <div className="flex items-center gap-2">
                  <span className={`text-sm ${isEnabled ? 'text-gray-900' : 'text-gray-400'}`}>
                    {isEnabled ? '已启用' : '已停用'}
                  </span>
                  <button 
                    onClick={() => setIsEnabled(!isEnabled)}
                    className={`w-11 h-6 rounded-full relative transition-colors duration-200 ease-in-out focus:outline-none ${isEnabled ? 'bg-green-500' : 'bg-gray-200'}`}
                  >
                    <span className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full shadow transform transition-transform duration-200 ease-in-out ${isEnabled ? 'translate-x-5' : 'translate-x-0'}`} />
                  </button>
              </div>
              
              <div className="flex gap-2">
                <button className="flex items-center gap-1 px-4 py-2 bg-white border border-green-600 text-green-600 rounded-md text-sm hover:bg-green-50 transition-colors">
                  <Download size={16} /> 同步
                </button>
                <button className="flex items-center gap-1 px-4 py-2 bg-white border border-red-200 text-red-600 rounded-md text-sm hover:bg-red-50 transition-colors">
                  <Trash2 size={16} /> 移除
                </button>
              </div>
            </div> */}

            {/* Tab 区域 */}
            <div className="space-y-6">
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                  {['overview', 'params', 'json', 'structure'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`
                        whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                        ${activeTab === tab 
                          ? 'border-blue-500 text-blue-600' 
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                      `}
                    >
                      {tab === 'overview' && '概述'}
                      {tab === 'params' && '参数配置'}
                      {tab === 'json' && 'skill.json'}
                      {tab === 'structure' && '文件结构'}
                    </button>
                  ))}
                </nav>
              </div>

              {activeTab === 'overview' && (
                <div className="prose prose-slate max-w-none">
                  <h3 className="text-lg font-bold text-gray-900 mb-3">{data?.name_zh}</h3>
                  <p className="text-gray-600 mb-6 leading-relaxed">
                    {data?.description}
                  </p>

                  {/* <div className="bg-white rounded-lg border border-gray-200 p-6">
                    <h4 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <Code size={18} className="text-blue-500"/> 功能描述
                    </h4>
                    <p className="text-gray-600 text-sm mb-4">
                      过滤文本中字母/数字比例不在指定范围内的样本。适用于清理乱码文本、筛选混合语言内容等场景。
                    </p>
                    
                    <h5 className="text-sm font-medium text-gray-900 mb-2">核心逻辑：</h5>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-2 ml-2">
                      {data?.logic.map((item, idx) => (
                        <li key={idx}>
                          {item.split(/(\b[a-z_]+\b)/g).map((part, i) => 
                            ['min_ratio', 'max_ratio'].includes(part) ? (
                              <code key={i} className="bg-gray-100 text-pink-600 px-1 py-0.5 rounded text-xs font-mono border border-gray-200 mx-1">{part}</code>
                            ) : part
                          )}
                        </li>
                      ))}
                    </ul>
                  </div> */}
                  {/* 新增：适用场景 */}
                    {/* <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                      <h4 className="text-base font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <FileText size={18} className="text-green-500"/> 适用场景
                      </h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 ml-2">
                        <li>清理包含大量乱码或无效字符的文本数据</li>
                        <li>筛选中英文混合内容中字母/数字比例异常的样本</li>
                        <li>预处理阶段过滤低质量文本（如爬虫噪声）</li>
                      </ul>
                    </div> */}

                    {/* 新增：使用示例 */}
                    {/* <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                      <h4 className="text-base font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <Terminal size={18} className="text-purple-500"/> 使用示例
                      </h4>
                      <div className="bg-gray-900 rounded p-3 overflow-x-auto text-xs text-gray-200 font-mono">
                        {`{
                          "operator": "alphabet-num-ratio-filter",
                          "params": {
                            "min_ratio": 0.3,
                            "max_ratio": 0.9,
                            "granularity": "char",
                            "language": "mixed"
                          }
                        }`}
                      </div>
                    </div> */}

                    {/* 新增：注意事项 */}
                    {/* <div className="bg-white rounded-lg border border-gray-200 p-6">
                      <h4 className="text-base font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        ⚠️ 注意事项
                      </h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 ml-2">
                        <li>若文本中无字母和数字（如纯标点），默认视为 <code className="bg-gray-100 px-1 rounded text-xs">ratio = 0</code>，可能被过滤</li>
                        <li><code>granularity="word"</code> 模式下，需确保分词逻辑与语言匹配</li>
                      </ul>
                    </div> */}
                </div>
              )}

              {activeTab === 'params' && (
                <div className="prose prose-slate max-w-none">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">输入参数</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">参数名</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">必填</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">默认值</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">说明</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {data?.input_params.params.map((param, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-3 whitespace-nowrap">
                              <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">{param.name}</code>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">{param.type}</code>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              {param.required ? (
                                <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded-full">必填</span>
                              ) : (
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">可选</span>
                              )}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              {param.default !== null && param.default !== undefined ? (
                                <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">
                                  {typeof param.default === 'string' && param.default.startsWith('"') ? param.default : String(param.default)}
                                </code>
                              ) : (
                                <span className="text-gray-400">—</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">{param.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <h2 className="text-xl font-bold text-gray-900 mt-8 mb-4">输出参数</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">参数名</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">说明</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {data?.output_params.params.map((param, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-3 whitespace-nowrap">
                              <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">{param.name}</code>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">{param.type}</code>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">{param.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeTab === 'json' && (
                <div className="prose prose-slate max-w-none">
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-sm text-gray-200">
                      <code>{formatJson(data?.skill_json)}</code>
                    </pre>
                  </div>
                </div>
              )}

              {activeTab === 'structure' && (
                <div className="prose prose-slate max-w-none">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">文件结构</h2>
                  <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm">
                   {data?.file_tree ? (
                    <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm">
                      {renderFileTree(data.file_tree)}
                    </div>
                  ) : (
                    <div className="text-gray-400 text-sm p-4">无文件结构信息</div>
                  )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* === 右侧信息栏 (20%) - sticky === */}
          <div className="space-y-6">
            <div className="sticky top-6 space-y-6">
              {/* 卡片 1: 基本信息 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-50 bg-gray-50/50">
                  <h3 className="font-semibold text-gray-900 text-sm">基本信息</h3>
                </div>
                <div className="p-5 space-y-4">
                  <InfoRow label="分类" value={data?.skill_type} />
                  <InfoRow label="版本" value={data?.version} />
                  <InfoRow label="作者" value={data?.author} icon={<User size={14}/>} />
                  <InfoRow label="语言" value={data?.language} />
                  <InfoRow label="许可" value={data?.license} />
                  <InfoRow label="环境" value={data?.env} />
                </div>
              </div>

              {/* 卡片 2: 使用统计 */}
              {/* <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-50 bg-gray-50/50">
                  <h3 className="font-semibold text-gray-900 text-sm">使用统计</h3>
                </div>
                <div className="p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">下载量</span>
                  
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">评分</span>
                    <div className="flex items-center gap-1">
                      <span className="text-sm font-bold text-gray-900">{data?.rating}</span>
                      <Star size={14} className="fill-yellow-400 text-yellow-400" />
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">启用</span>
                    <span className="text-sm font-medium text-gray-900">893</span>
                  </div>
                </div>
              </div> */}

              {/* 卡片 3: 相关算子 */}
              {/* <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-50 bg-gray-50/50">
                  <h3 className="font-semibold text-gray-900 text-sm">相关算子</h3>
                </div>
                <div className="p-2">
                  {RELATED_OPERATORS.map((op, i) => (
                    <div 
                      key={i} 
                      className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors group"
                      onClick={() => navigate(`/skills/${op.id}`)}
                    >
                      <div className="w-8 h-8 bg-blue-50 rounded flex items-center justify-center text-blue-500 shrink-0">
                        <Layers size={16} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate group-hover:text-blue-600">{op.name}</div>
                        <div className="text-xs text-gray-500 truncate">{op.category}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div> */}

              {/* 底部下载按钮 */}
              <button 
                className="w-full py-2.5 bg-white border border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors flex items-center justify-center gap-2 shadow-sm"
                onClick={async () => {
                  if (!id) {
                    alert('无效的算子 ID');
                    return;
                  }
                  try {
                      await downloadSkillPackage(id);
                  } catch (err) {
                    console.error('下载失败:', err);
                    alert('下载失败，请稍后重试');
                  }
                }}
              >
                <Download size={18} /> 下载算子包
              </button>
              <p className="text-xs text-center text-gray-400">包含完整文件结构，可直接本地部署</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// 辅助组件：信息行
function InfoRow({ label, value, icon }: { label: string, value: string, icon?: React.ReactNode }) {
  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-gray-500 flex items-center gap-1.5">{icon}{label}</span>
      <span className="text-gray-900 font-medium text-right truncate max-w-[60%]" title={value}>{value}</span>
    </div>
  );
}

// 递归渲染文件树
const renderFileTree = (node: any, depth = 0) => {
  const isDir = node.type === 'directory';
  const hasChildren = node.children && node.children.length > 0;
  const indent = depth * 16; // 每层缩进 16px

  return (
    <div key={node.name} style={{ paddingLeft: `${indent}px` }} className="mb-1">
      <div className="flex items-start gap-2">
        {isDir ? (
          <Folder size={14} className="text-blue-500 mt-0.5 flex-shrink-0" />
        ) : (
          <File size={14} className="text-gray-500 mt-0.5 flex-shrink-0" />
        )}
        <span className={`font-mono text-sm ${isDir ? 'text-blue-600 font-medium' : 'text-gray-700'}`}>
          {node.name}
        </span>
        {node.description && (
          <span className="text-gray-400 text-sm">— {node.description}</span>
        )}
      </div>
      {hasChildren && (
        <div className="mt-1">
          {node.children.map((child: any) => renderFileTree(child, depth + 1))}
        </div>
      )}
    </div>
  );
};