import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import './LoginPage.css'; // 引入独立的 CSS 文件

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
        
        {/* --- 左侧品牌展示区 --- */}
        <div className="brand-section">
          <div className="brand-logo-container">
            {/* SVG Logo */}
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="40" cy="40" r="36" stroke="#00D2A0" strokeWidth="4"/>
              <path d="M40 20 C 20 20, 20 60, 40 60" stroke="#00D2A0" strokeWidth="4" strokeLinecap="round"/>
              <path d="M40 20 C 60 20, 60 60, 40 60" stroke="#00BFFF" strokeWidth="4" strokeLinecap="round"/>
              <text x="40" y="48" fontSize="28" fill="white" textAnchor="middle" fontFamily="serif">π</text>
            </svg>
          </div>
          <h1 className="brand-title">π Flow</h1>
          <p className="brand-subtitle">面向科学数据加工的<br/>智能工作流平台</p>
          <p className="brand-desc">
            以智能工作流重构科学数据加工流程，<br/>让科研数据处理更智能、更高效、更易复用
          </p>
        </div>

        {/* --- 右侧登录表单区 --- */}
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
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <div className="form-options">
                <div className="remember-me">
                  <input id="remember-me" name="remember-me" type="checkbox" className="checkbox-input" />
                  <label htmlFor="remember-me" className="checkbox-label">记住登录</label>
                </div>
                <a href="#" className="forgot-password">忘记密码?</a>
              </div>

              <button type="submit" className="submit-btn">登 录</button>
            </form>
          )}

          {/* 科技云账号登录提示 */}
          {activeTab === 'cloud' && (
            <div className="cloud-login-placeholder">
              <p>科技云账号登录功能正在开发中...</p>
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