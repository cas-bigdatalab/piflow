import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';


import { uploadPackage } from "../lib/api";
import './SkillsCreatePage.css';
const AddOperatorPage = () => {
  const navigate = useNavigate();
  
  // 核心状态：控制当前处于哪个步骤 (1: 选择方式, 2: 上传包, 3: 完成)
  const [currentStep, setCurrentStep] = useState(1);
  
  // 侧边栏面板状态
  const [showSpecPanel, setShowSpecPanel] = useState(false);
  
  // 模拟上传的文件状态
  const [uploadedFile, setUploadedFile] = useState(null);
  // 处理文件上传逻辑（模拟）
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };
  //处理算子上传接口
  // 上传 zip 文件到后端接口
const handleZipFileUpload = async (file: File) => {

  try {
    const response = await uploadPackage(file)
    if (response.code === 200) {
      alert('算子包上成功');
      setCurrentStep(3); // 👈 关键：跳转到第三步
      setUploadedFile(null); // 可选：清空文件状态
    }
  } catch (error) {
    console.error('上传出错:', error);
    alert('算子包上传失败，请检查文件格式或网络');
  }
};

  // 渲染步骤条组件
  const renderStepper = () => {
    return (
      <div className="og-stepper max-w-5xl mx-auto px-4 mb-8">
        {/* 步骤 1: 选择方式 */}
        <div className={`og-step ${currentStep > 1 ? 'completed' : ''} ${currentStep === 1 ? 'active' : ''}`}>
          <span className="og-step-circle">1</span>
          <span className="og-step-label">选择方式</span>
        </div>
        <div className="og-step-line"></div>

        {/* 步骤 2: 上传包 */}
        <div className={`og-step ${currentStep > 2 ? 'completed' : ''} ${currentStep === 2 ? 'active' : ''}`}>
          <span className="og-step-circle">2</span>
          <span className="og-step-label">上传包</span>
        </div>
        <div className="og-step-line"></div>

        {/* 步骤 3: 完成 */}
        <div className={`og-step ${currentStep > 3 ? 'completed' : ''} ${currentStep === 3 ? 'active' : ''}`}>
          <span className="og-step-circle">3</span>
          <span className="og-step-label">完成</span>
        </div>
      </div>
    );
  };

  return (
    <div className="page-dom">
      {/* 顶部返回导航 */}
      <div className="mb-6">
        <button 
          onClick={() => navigate('/skills')}
          className="text-slate-500 hover:text-slate-800 flex items-center text-sm transition-colors"
        >
          <span className="mr-1">←</span> 返回算子库
        </button>
      </div>

      {/* 页面标题 */}
      <h1 className="text-2xl font-bold text-slate-900 mb-8">添加算子</h1>

      {/* 步骤条区域 */}
      {renderStepper()}

      {/* 主要内容卡片区域 */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-8 max-w-5xl mx-auto min-h-[500px]">
        
        {/* ================= 步骤 1: 选择方式 ================= */}
        {currentStep === 1 && (
          <div className="animate-fade-in">
            <div className="mb-8">
              <h2 className="text-lg font-bold text-slate-900 mb-2">选择添加方式</h2>
              <p className="text-slate-500 text-sm">
                你可以直接上传已开发好的算子压缩包，也可以通过算子生成器对话创建一个新算子。
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 选项 A: 上传算子包 */}
              <div 
                className="group border border-slate-200 rounded-xl p-6 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer bg-white"
                onClick={() => setCurrentStep(2)} // 点击进入下一步
              >
                <div className="mb-4">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M24 4L6 14V34L24 44L42 34V14L24 4Z" fill="#E7DCCF" stroke="#A89F91" strokeWidth="2" strokeLinejoin="round"/>
                    <path d="M6 14L24 24L42 14" stroke="#A89F91" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M24 44V24" stroke="#A89F91" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <rect x="10" y="20" width="6" height="8" rx="1" fill="#EF4444" transform="rotate(-15 10 20)" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
                  上传算子包
                </h3>
                <p className="text-slate-500 text-sm leading-relaxed">
                  已有算子 zip 包？直接上传导入，自动解析 skill.md 与 skill.json。
                </p>
              </div>

              {/* 选项 B: 算子生成器 */}
              <div 
                className="group border border-slate-200 rounded-xl p-6 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer bg-white"
                onClick={() => navigate('/skill/generator')}
              >
                <div className="mb-4">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M24 4C12.9543 4 4 12.9543 4 24C4 29.35 6.1 34.2 9.5 37.8L6 44L13.5 41C16.6 42.3 20.1 43 24 43C35.0457 43 44 34.0457 44 24C44 12.9543 35.0457 4 24 4Z" fill="white" stroke="#1E293B" strokeWidth="2" strokeLinejoin="round"/>
                    <circle cx="16" cy="24" r="2" fill="#1E293B"/>
                    <circle cx="24" cy="24" r="2" fill="#1E293B"/>
                    <circle cx="32" cy="24" r="2" fill="#1E293B"/>
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
                  算子生成器
                </h3>
                <p className="text-slate-500 text-sm leading-relaxed">
                  没有现成算子？通过对话描述需求，生成器自动生成符合标准的算子文件夹结构。
                </p>
              </div>
            </div>

            {/* 底部辅助链接 */}
            <div className="mt-10 pt-6 border-t border-slate-100 text-center text-sm text-slate-500">
              首次开发？{' '}
              <button 
                onClick={() => setShowSpecPanel(true)} 
                className="text-blue-600 hover:underline hover:text-blue-700 font-medium"
              >
                查看算子开发规范
              </button>
              {' '}或{' '}
              <a href="#" className="text-blue-600 hover:underline hover:text-blue-700 font-medium">
                下载示例算子
              </a>
            </div>
          </div>
        )}

        {/* ================= 步骤 2: 上传包 ================= */}
        {currentStep === 2 && (
          <div className="animate-fade-in">
             <div className="mb-8">
              <h2 className="text-lg font-bold text-slate-900 mb-2">上传算子包</h2>
              <p className="text-slate-500 text-sm">
                支持 .zip 格式，包内须包含 skill.md 与 skill.json 文件。
              </p>
            </div>

            {/* 拖拽上传区域 */}
            <div className="border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors h-64 flex flex-col items-center justify-center cursor-pointer relative group">
              <input 
                type="file" 
                accept=".zip" 
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              
              {/* 图标 */}
              <div className="mb-4 transform group-hover:scale-110 transition-transform">
                 <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M32 48V16M32 16L20 28M32 16L44 28" stroke="#3B82F6" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M12 40V48C12 50.2091 13.7909 52 16 52H48C50.2091 52 52 50.2091 52 48V40" stroke="#1E293B" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>
                 </svg>
              </div>
              
              <p className="text-slate-900 font-medium text-lg">点击或拖拽上传算子包</p>
              <p className="text-slate-500 text-sm mt-2">支持 .zip 格式</p>

              {uploadedFile && (
                <div className="absolute bottom-4 bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-medium flex items-center">
                  <span className="mr-1">✓</span> 已选择: {uploadedFile.name}
                </div>
              )}
            </div>

            {/* 底部操作按钮 */}
            <div className="mt-10 flex justify-between items-center">
               <button 
                 onClick={() => setCurrentStep(1)}
                 className="text-slate-500 hover:text-slate-800 font-medium flex items-center px-4 py-2 rounded-lg hover:bg-slate-100 transition-colors"
               >
                 ← 上一步
               </button>

               {/* <button 
                 disabled={!uploadedFile}
                 onClick={() => setCurrentStep(3)}
                 className={`px-6 py-2.5 rounded-lg font-medium text-white shadow-sm transition-all
                   ${uploadedFile 
                     ? 'bg-emerald-500 hover:bg-emerald-600 hover:shadow-md cursor-pointer' 
                     : 'bg-slate-300 cursor-not-allowed'}
                 `}
               >
                 预览算子 →
               </button> */}

              <button 
                disabled={!uploadedFile}
                onClick={() => uploadedFile && handleZipFileUpload(uploadedFile)}
                className={`px-6 py-2.5 rounded-lg font-medium text-white shadow-sm transition-all
                  ${uploadedFile 
                    ? 'bg-emerald-500 hover:bg-emerald-600 hover:shadow-md cursor-pointer' 
                    : 'bg-slate-300 cursor-not-allowed'}
                `}
              >
                上传算子 →
              </button>
            </div>
          </div>
        )}

        {/* ================= 步骤 3: 完成 (占位) ================= */}
        {currentStep === 3 && (
           <div className="text-center py-20 animate-fade-in">
             <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
             </div>
             <h2 className="text-2xl font-bold text-slate-900 mb-2">上传成功！</h2>
             <p className="text-slate-500 mb-8">算子包已解析完成，即将跳转到详情页。</p>
             <button onClick={() => navigate('/skills')} className="bg-slate-900 text-white px-6 py-2 rounded-lg hover:bg-slate-800">
               返回算子库
             </button>
           </div>
        )}

      </div>

      {/* 侧边栏：算子开发规范 (保持不变) */}
      {showSpecPanel && (
        <>
          <div 
            className="fixed inset-0 bg-black bg-opacity-30 z-40"
            onClick={() => setShowSpecPanel(false)}
          />
          <div className="fixed top-0 right-0 w-full max-w-[540px] h-screen bg-white shadow-lg z-50 overflow-y-auto animate-slide-in-right">
            <div className="flex justify-between items-center mb-6 border-b p-6 sticky top-0 bg-white z-10">
              <h2 className="text-xl font-semibold">📖 算子开发规范</h2>
              <button onClick={() => setShowSpecPanel(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <div className="space-y-4 p-6 pb-20">
              <p className="text-sm text-slate-600">算子本质上是一个标准文件夹...</p>
              {/* 此处省略具体规范内容，保持原样即可 */}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AddOperatorPage;