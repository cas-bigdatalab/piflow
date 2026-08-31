import React from 'react';
import { useEffect,useState  } from 'react';
import { X, Download, Edit3, Save, FileText, Folder, ChevronRight, ChevronDown, Maximize2 } from 'lucide-react';
import { getSkillInfo,getSkillFile,saveSkillFile,downloadSkillPackage } from "../lib/api";
// 模拟各文件内容
const FILE_CONTENTS = {
  'skill.md': `---
title: "URL 链接过滤算子"
summary: "过滤文本中的 URL 链接，支持白名单域名"
version: "1.0.0"
---

# URL 链接过滤算子

识别并过滤文本中的 URL 链接。支持配置白名单域名，仅保留白名单内的链接，其余 URL 予以移除。

## 使用场景
- 清洗爬取的网页文本
- 移除用户生成内容中的外链

## 参数
- whitelist: 白名单域名列表 (可选)
- mode: 过滤模式 remove / replace`,
  
  'skill.json': `{
  "name": "url-filter-operator",
  "version": "1.0.0",
  "description": "过滤文本中的 URL 链接",
  "parameters": {
    "whitelist": {
      "type": "array",
      "default": []
    },
    "mode": {
      "type": "string",
      "enum": ["remove", "replace"],
      "default": "remove"
    }
  }
}`,
  
  'filter.py': `import re

def filter_urls(text: str, whitelist: list = None, mode: str = "remove") -> str:
    """
    过滤文本中的 URL 链接
    """
    if whitelist is None:
        whitelist = []
    
    # 匹配 URL 的正则（简化版）
    url_pattern = r'https?://[\\w\\-\\.]+'
    
    def replace_url(match):
        url = match.group(0)
        domain = re.findall(r'https?://([\\w\\-\\.]+)', url)
        if domain and domain[0] in whitelist:
            return url
        return "" if mode == "remove" else "[URL]"
    
    return re.sub(url_pattern, replace_url, text)
`
};

// 文件树结构（保持不变）
const FILE_TREE = [
  {
    id: 'root', name: 'url-filter-operator', type: 'folder', isOpen: true,
    children: [
      { id: 'f1', name: 'skill.md', type: 'file' },
      { id: 'f2', name: 'skill.json', type: 'file' },
      { id: 'd1', name: 'scripts', type: 'folder', isOpen: true, children: [{ id: 'f3', name: 'filter.py', type: 'file' }] },
      { id: 'd2', name: 'assets', type: 'folder', children: [{ id: 'f4', name: 'icon.svg', type: 'file' }] },
    ]
  }
];

// 扁平化文件映射（用于快速查找）
const FILE_PATH_MAP: Record<string, string> = {
  'skill.md': 'skill.md',
  'skill.json': 'skill.json',
  'filter.py': 'scripts/filter.py',
  'icon.svg': 'assets/icon.svg'
};
interface PreviewDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    previewData: Record<string, any> | null;// 或更具体的类型
}
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
  file_path?: string;  // 算子根目录路径，用于拼接各文件的完整 path
}

interface RenderTreeOptions {
  node: any;
  depth?: number;
  activeFile: string;
  onFileClick: (fileName: string) => void;
}

const PreviewDrawer = ({ isOpen, onClose, previewData }: PreviewDrawerProps) => {
  const [isDrawerFullscreen, setIsDrawerFullscreen] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [activeFile, setActiveFile] = React.useState('skill.md');
  const [data, setData] = useState<OperatorData | null>(null);
  const [filePath, setFilePath] = useState('');
  //代码content内容
  const [codeContent, setCodeContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [originalCodeContent, setOriginalCodeContent] = useState('');
  // 👇 新增
  const updateFileContent = (newContent: string) => {
    setCodeContent(newContent);
  };
  console.log('Received previewData:', previewData);
//   调用详情接口将文件结构的内容获取出来


  useEffect(() => {
    const fetchSkill = async () => {
      try {
        // 确保 previewData 存在且有 skill_id
        if (!previewData?.skill_id) {
          setLoading(false);
          return;
        }

        const response = await getSkillInfo(previewData.skill_id, true, true);
        
        if (response?.code === 200 && response.result) {
          setData(response.result); 
          setFilePath(response.result.file_path)
        }
      } catch (err) {
        console.error('接口请求失败:', err);
      } finally {
        setLoading(false); 
      }
    };

    fetchSkill();
  }, [previewData?.skill_id]); // 使用可选链避免 null 访问

 const handleSaveToMySpace = async () => {
  if (!previewData?.skill_id || !activeFile || !codeContent) {
    console.warn('缺少必要参数，无法保存');
    return;
  }

    if (!filePath) {
      console.error('未找到文件路径映射:', activeFile);
      return;
    }

    try {
      setLoading(true);
      const res = await saveSkillFile(previewData.skill_id, filePath, codeContent);
      
      if (res?.code === 200) {
        // 保存成功，更新原始内容以清除“未保存”状态
        setOriginalCodeContent(codeContent);
        alert('✅ 保存成功！');
      } else {
        throw new Error(res?.message || '保存失败');
      }
    } catch (err) {
      console.error('保存失败:', err);
      alert('❌ 保存失败，请重试');
    } finally {
      setLoading(false);
    }
  };
  const toggleDrawerFullscreen = () => {
    setIsDrawerFullscreen(!isDrawerFullscreen);
  };

  const handleFileSelect  = async (fileName: string, fullPath: string) => {
    setActiveFile(fileName);

    if (!previewData?.skill_id || !fullPath) {
      setCodeContent('');
      setOriginalCodeContent('');
      return;
    }

    // 记录当前选中文件的完整路径，供保存等操作复用
    setFilePath(fullPath);

    try {
      setLoading(true);
      const res = await getSkillFile(previewData.skill_id, fullPath);
      
      if (res?.code === 200 && res.result) {
        const content = res.result.content || '';
        setCodeContent(content);
        console.log("接口返回内容值",res.result.content)
        setOriginalCodeContent(content); // 保存原始内容
      } else {
        setCodeContent('');
        setOriginalCodeContent('');
      }
    } catch (err) {
      console.error('接口请求失败:', err);
      setCodeContent('');
      setOriginalCodeContent('');
    } finally {
      setLoading(false);
    }
  };

  

  if (!isOpen) return null;

  const fileExt = activeFile.split('.').pop() || '';
  // const currentContent = fileContents[activeFile] || '// 文件内容为空';

  const hasUnsavedChanges = isEditing && codeContent !== originalCodeContent;
  

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/30 z-40 transition-opacity" 
        onClick={onClose}
      />
      
      <div className={`fixed inset-y-0 right-0 bg-white shadow-2xl z-50 flex flex-col ${isDrawerFullscreen ? 'w-full' : 'w-[900px]'}`}>
        
        <div className="h-14 border-b flex items-center justify-between px-4 bg-white">
          <div className="flex items-center gap-4">
            <h2 className="font-bold text-gray-800">预览算子</h2>
            <span className="text-sm text-gray-500">URL 链接过滤算子</span>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsEditing(!isEditing)}
              className="p-2 hover:bg-gray-100 rounded"
              title={isEditing ? "完成编辑" : "编辑代码"}
            >
              <Edit3 size={16} />
            </button>
            <button onClick={toggleDrawerFullscreen} className="p-2 hover:bg-gray-100 rounded">
              <Maximize2 size={16} />
            </button>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded">
              <X size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* 左侧：文件树 —— 支持点击 */}
          <div className="w-64 border-r bg-gray-50 p-4 overflow-y-auto">
            <div className="text-xs font-bold text-gray-400 mb-3 uppercase">算子文件夹</div>
            {data?.file_tree ? (
              renderPreviewFileTree(
                data.file_tree,
                0,                     // depth
                activeFile,            // 当前激活的文件名
                handleFileSelect,      // 文件点击回调
                // 拼接路径的根锚点：取 file_path 的父目录，
                // 使文件树顶层节点（算子文件夹）重新拼回，得到与后端一致的完整路径，
                // 例如 skills/generated/xxx/scripts/run.py
                (data.file_path || filePath).replace(/\/[^/]*$/, '')
              )
            ) : (
              <div className="text-sm text-gray-500 italic">加载中...</div>
            )}
          </div>

          {/* 右侧：代码区域 */}
          <div className="flex-1 flex flex-col bg-[#1e1e2e] text-gray-300">
            {/* Tab 栏 */}
            <div className="flex items-center justify-between bg-[#181825] border-b border-gray-700">
              <div className="flex">
                {[activeFile].map((tab) => (
                  <div 
                    key={tab} 
                    className={`px-4 py-2 text-sm cursor-pointer border-t-2 ${
                      tab === activeFile 
                        ? 'bg-[#1e1e2e] border-blue-500 text-white' 
                        : 'border-transparent hover:bg-[#1e1e2e]'
                    }`}
                    onClick={() => handleFileSelect(tab, filePath)}
                  >
                    {tab}
                  </div>
                ))}
              </div>
            </div>

            {/* 状态提示栏 */}
            <div className="px-6 py-2 bg-[#181825] text-xs text-gray-400 border-b border-gray-700">
              {hasUnsavedChanges 
                ? `1 个文件已修改 · ${fileExt}` 
                : `就绪 · 无未保存修改`}
            </div>

            {/* 代码内容 */}
            {isEditing ? (
              <textarea
                value={codeContent}
                onChange={(e) => updateFileContent(e.target.value)}
                className="flex-1 p-6 font-mono text-sm bg-[#1e1e2e] text-gray-300 border-none outline-none resize-none w-full h-full"
                spellCheck="false"
              />
            ) : (
              <div className="flex-1 p-6 overflow-auto font-mono text-sm leading-relaxed">
                <pre className="whitespace-pre-wrap">{codeContent}</pre>
              </div>
            )}
          </div>
        </div>

        <div className="h-16 border-t bg-white px-6 flex items-center justify-between">
          <div className="flex gap-3">
            <button 
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded border border-transparent"
              onClick={() => setIsEditing(!isEditing)}
            >
              <Edit3 size={16} /> {isEditing ? '完成编辑' : '继续修改'}
            </button>
            <button className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded border border-gray-200"
              onClick={async () => {
                if (!previewData?.skill_id) {
                  alert('无效的算子 ID');
                  return;
                }
                try {
                    await downloadSkillPackage(previewData?.skill_id);
                } catch (err) {
                  console.error('下载失败:', err);
                  alert('下载失败，请稍后重试');
                }
              }}
            >
              <Download size={16} /> 下载为 zip 
            </button> 
          </div>
          <button className="flex items-center gap-2 px-5 py-2 text-sm text-white bg-green-600 hover:bg-green-700 rounded shadow-sm"
           onClick={handleSaveToMySpace} // ← 绑定保存函数
          >
            <Save size={16} /> 保存到我的空间
          </button>
        </div>
      </div>
    </>
  );
};




// 新增：用于 PreviewDrawer 的可点击文件树渲染
const renderPreviewFileTree = (
  node: any,
  depth: number = 0,
  activeFile: string,
  onFileClick: (fileName: string, fullPath: string) => void,
  parentPath: string = ''
) => {
  const isDir = node.type === 'directory';
  const hasChildren = node.children && node.children.length > 0;
  const indent = depth * 12 + 8;

  // 计算当前节点的完整路径：
  // 1) 后端若直接返回 node.path 则优先使用，最贴合服务端预期；
  // 2) 否则根据树层级拼接（父路径 / 当前节点名）。
  const currentPath =
    node.path ||
    (parentPath ? `${parentPath}/${node.name}` : node.name);

  return (
    <div key={currentPath} className="space-y-1">
      <div
        className={`flex items-center py-1.5 px-2 rounded cursor-pointer text-sm ${
          node.name === activeFile
            ? 'bg-blue-50 text-blue-600 font-medium'
            : 'text-gray-600 hover:bg-gray-200'
        }`}
        style={{ paddingLeft: `${indent}px` }}
        onClick={() => {
          if (!isDir) {
            onFileClick(node.name, currentPath); // ✅ 传入当前文件的完整路径
          }
        }}
      >
        {isDir ? (
          <Folder size={14} className="mr-2 text-yellow-500" />
        ) : (
          <FileText size={14} className="mr-2 text-gray-400" />
        )}
        <span>{node.name}</span>
      </div>

      {hasChildren && (
        <div>
          {node.children.map((child: any) =>
            renderPreviewFileTree(child, depth + 1, activeFile, onFileClick, currentPath)
          )}
        </div>
      )}
    </div>
  );
};

export default PreviewDrawer;