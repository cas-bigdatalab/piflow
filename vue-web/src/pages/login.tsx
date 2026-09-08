// login.tsx
import React, { useState } from 'react';
import { Eye, EyeOff, Cloud, Scan, Mail } from 'lucide-react';
import './LoginPage.css';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [activeTab, setActiveTab] = useState('email');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Login attempt with:', { email, password });
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-card">
        {/* 左侧品牌展示区 */}
        <div className="brand-section">
          {/* 背景网格 */}
          <div className="brand-grid"></div>
          
          {/* 光晕 */}
          <div className="brand-glow"></div>

          <div className="brand-content">
            {/* Logo */}
            <div className="brand-logo-wrapper">
              <div className="brand-logo-container">
                <svg width="72" height="72" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="40" cy="40" r="34" stroke="#10b981" strokeWidth="3" opacity="0.3"/>
                  <circle cx="40" cy="40" r="34" stroke="#10b981" strokeWidth="3" 
                    strokeDasharray="4 4" opacity="0.6"/>
                  <path d="M40 18 C 18 18, 18 62, 40 62" stroke="#10b981" strokeWidth="3.5" strokeLinecap="round"/>
                  <path d="M40 18 C 62 18, 62 62, 40 62" stroke="#3b82f6" strokeWidth="3.5" strokeLinecap="round"/>
                  <text x="40" y="48" fontSize="28" fill="white" textAnchor="middle" 
                    fontFamily="'Times New Roman', serif" fontWeight="600">π</text>
                </svg>
              </div>
            </div>

            {/* 标题 */}
            <h1 className="brand-title">π<span>Flow</span></h1>

            {/* 副标题 */}
            <p className="brand-subtitle">
              面向科学数据加工的<br/>
              <span className="highlight">智能工作流</span>平台
            </p>

            {/* 装饰分隔线 */}
            <div className="brand-divider"></div>

            {/* 描述 */}
            <p className="brand-desc">
              以智能工作流重构科学数据加工流程，<br/>
              让科研数据处理更<strong>智能</strong>、更<strong>高效</strong>、更<strong>易复用</strong>
            </p>

            {/* 底部装饰点 */}
            <div className="brand-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        {/* 右侧登录表单区 */}
        <div className="form-section">
          <div className="form-header">
            <h2 className="welcome-title">欢迎回来</h2>
            <p className="welcome-subtitle">登录 πFlow 开始你的数据加工之旅</p>
          </div>

          {/* 登录方式切换标签 */}
          <div className="tabs-container">
            <nav className="tabs-nav">
              <button
                onClick={() => setActiveTab('email')}
                className={`tab-btn ${activeTab === 'email' ? 'active' : ''}`}
              >
                邮箱登录
              </button>
              <button
                onClick={() => setActiveTab('cloud')}
                className={`tab-btn ${activeTab === 'cloud' ? 'active' : ''}`}
              >
                科技云账号
              </button>
            </nav>
          </div>

          {/* 邮箱登录表单 */}
          {activeTab === 'email' && (
            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-group">
                <label htmlFor="email-address" className="form-label">邮箱地址</label>
                <input
                  id="email-address"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="请输入邮箱地址"
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">密码</label>
                <div className="password-input-wrapper">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                    className="form-input password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="password-toggle-btn"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="form-options">
                <label className="remember-me">
                  <input id="remember-me" name="remember-me" type="checkbox" className="checkbox-input" />
                  <span className="checkbox-label">记住登录</span>
                </label>
                <a href="#" className="forgot-password">忘记密码?</a>
              </div>

              <button type="submit" className="submit-btn">登 录</button>
            </form>
          )}

          {/* 科技云账号登录视图 */}
          {activeTab === 'cloud' && (
            <div className="cloud-login-view fade-in">
              <div className="cloud-intro">
                <div className="cloud-icon-large"><Cloud size={28} color="white" /></div>
                <h3>科技云账号登录</h3>
                <p>使用中国科技云统一认证账号<br/>快速安全登录 πFlow</p>
              </div>

              <div className="qr-placeholder">
                <Scan size={40} color="#ccc" />
                <span>扫码登录</span>
              </div>
              <p className="qr-tip">打开科技云App，扫描二维码确认登录</p>

              <button className="btn-primary-green full-width">
                <Cloud size={16} />
                跳转科技云认证页面
              </button>

              <div className="divider">
                <span className="divider-text">其他登录方式</span>
              </div>

              <button 
                className="btn-outline full-width"
                onClick={() => setActiveTab('email')}
              >
                <Mail size={16} />
                邮箱密码登录
              </button>
            </div>
          )}

          {/* 其他登录方式分隔线 */}
          <div className="divider">
            <span className="divider-text">其他登录方式</span>
          </div>

          {/* 科技云账号一键登录按钮 */}
          <button type="button" className="cloud-login-btn">
            <svg className="cloud-icon" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path d="M5.5 16a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.977A4.5 4.5 0 1113.5 16h-8z"></path>
            </svg>
            科技云账号登录
          </button>

          {/* 注册链接 */}
          <p className="register-link">
            还没有账号？ <a href="#" className="register-text">立即注册</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;