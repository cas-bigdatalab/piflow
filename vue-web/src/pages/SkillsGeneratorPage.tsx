import React, { useState, useRef, useEffect } from 'react';
import './SkillsGeneratorPage.css'; // 引入样式文件

import { useNavigate } from 'react-router-dom';
import { generatingSkill,streamMessages } from "../lib/api";
import { shortId } from "../lib/ids"; 
// 引入下面新建的抽屉组件
import PreviewDrawer from './PreviewDrawer'; 



const OperatorGenerator = () => {
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState('');
  // 页面级 thread_id：仅在组件挂载（进入/刷新页面）时生成一次，
  // 同一页面内的连续对话始终复用同一个 thread_id，刷新或重新进入才会变化。
  const threadIdRef = useRef<string>('');
  if (!threadIdRef.current) {
    threadIdRef.current = `t_${shortId()}`;
  }
  useEffect(() => {
    setThreadId(threadIdRef.current);
  }, []);
  const [previewData, setPreviewData] = useState(null); // 👈 新增这行
  //预览算子抽屉弹框
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const initialAssistantMessage = {
    id: 'msg_welcome',
    role: 'assistant' as const,
    content: `你好！我是算子生成器 👻\n\n请描述你想要创建的算子功能，我会帮你生成标准的算子文件夹结构。\n\n例如：“帮我做一个过滤文本中 URL 链接的算子，支持白名单域名”`,
  }; 

  const [messages, setMessages] = useState([
    initialAssistantMessage
  ]);
  const chatAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages]);
  //预览算子
  const handleZipFileUpload = async () => {
    setThreadId('t_76dc5eeef63448fd'); //先默认写死
    const res = await generatingSkill('t_76dc5eeef63448fd')
    console.log('测试出的内容为————————',res)
    setPreviewData(res.result); 
    if (res.result){
      setIsDrawerOpen(true);
      //打开抽屉弹框并将skill_id内容传输
    }
  };
  const handleSend = async () => {
    if (!inputValue.trim()) return;

    setIsLoading(true); // 启动加载状态

    const userMessage = {
      id: 'msg_' + Date.now(),
      role: 'user' as const,
      content: inputValue.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);

    const userId = localStorage.getItem('userId') || 'u_default';
    // 复用页面级 thread_id，保证同一页面内连续对话使用同一会话
    const advisorSessionId = threadIdRef.current;

    try {
      const res = await streamMessages(userId, advisorSessionId, inputValue.trim());
      
      let aiContent = "✅ 算子生成完成！";
      if (typeof res === 'object' && res !== null) {
        if ('content' in res && typeof res.content === 'string') {
          aiContent = res.content;
        } else if ('attachments' in res && Array.isArray(res.attachments)) {
          aiContent += `（共 ${res.attachments.length} 个文件）`;
        }
      }

      const aiMessage = { id: 'msg_' + Date.now(), role: 'assistant' as const, content: aiContent };
      console.log('请求成功:', res);
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err: any) {
      console.error('请求失败:', err);
      const errorMsg = {
        id: 'msg_' + Date.now(),
        role: 'assistant' as const,
        content: `❌ 调用失败: ${err.message || '未知错误'}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false); // 确保无论成功失败都恢复状态
    }

    setInputValue('');
  };

  return (
    <div className="og-container">
      {/* 顶部导航 */}
      <header className="og-header">
        <button
          className="og-back-link"
          onClick={() => navigate('/skills?tab=' + encodeURIComponent('我的空间'))}
        >← 返回算子库</button>
        <h1 className="og-page-title">添加算子</h1>
      </header>

      {/* 步骤条 */}
      <div className="og-stepper">
        <div className="og-step completed">
          <span className="og-step-circle">1</span>
          <span className="og-step-label">选择方式</span>
        </div>
        <div className="og-step-line"></div>
        <div className="og-step active">
          <span className="og-step-circle">2</span>
          <span className="og-step-label">算子生成器</span>
        </div>
        <div className="og-step-line"></div>
        <div className="og-step">
          <span className="og-step-circle">3</span>
          <span className="og-step-label">完成</span>
        </div>
      </div>

      {/* 主内容卡片 */}
      <main className="og-card">
        <div className="og-card-header">
          <div>
            <h2 className="og-card-title">算子生成器</h2>
            <p className="og-card-subtitle">描述算子功能需求，生成器帮你构建标准算子文件夹结构</p>
          </div>
          <button className="og-back-small"
           onClick={() => navigate('/skill/create')}
          >← 返回</button>
        </div>

        {/* 聊天/展示区域 */}
        <div className="og-chat-area" ref={chatAreaRef}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`og-message-row ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              <div className={`og-avatar ${msg.role === 'user' ? 'user' : 'assistant'}`}>
                {msg.role === 'user' ? 'ME' : 'OP'}
              </div>
              <div className={`og-message-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`}>
                {/* 支持多段落 */}
                {msg.content.split('\n\n').map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* 底部操作栏 */}
        <div className="og-action-area">
          {/* 快捷标签 */}
          {/* <div className="og-chips-container">
            <button className="og-chip">+ 增加参数校验</button>
            <button className="og-chip">+ 支持正则模式</button>
          </div> */}

          {/* 输入框行 */}
          <div className="og-input-row">
            <input
              type="text"
              className="og-input"
              placeholder="描述算子功能需求..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSend()}
              disabled={isLoading} // ← 禁用状态
            />
            <button 
              className="og-btn-send" 
              onClick={handleSend}
              disabled={isLoading} // 可选：防止重复点击
            >
              {isLoading ? '生成中…' : '发送'}
            </button>
          </div>

          {/* 底部次要按钮 */}
          <div className="og-footer-actions">
            <button className="og-btn-preview"
            onClick={ handleZipFileUpload}
            > 预览算子</button>
          </div>
        </div>
      </main>
       <PreviewDrawer 
        isOpen={isDrawerOpen} 
        onClose={() => setIsDrawerOpen(false)}
        previewData={previewData} // 👈 新增 props
      />
    </div>
  );
};

export default OperatorGenerator;