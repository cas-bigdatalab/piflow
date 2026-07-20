// src/pages/LoginPage.tsx
import React, { useState } from 'react';
import styles from './LoginPage.module.css';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log({ username, password, rememberMe });
    // TODO: 调用登录 API
  };

  return (
    <div className={styles.container}>
      {/* 左侧插画区 */}
      <div className={styles.illustration}></div>

      {/* 右侧表单区 */}
      <div className={styles.formContainer}>
        <div className={styles.logo}>YourLogo</div>
        <h2 className={styles.title}>欢迎登录</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          {/* 用户名 */}
          <div className={styles.inputGroup}>
            <span className={styles.inputIcon}>👤</span>
            <input
              type="text"
              placeholder="请输入用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={styles.input}
            />
          </div>

          {/* 密码 */}
          <div className={styles.inputGroup}>
            <span className={styles.inputIcon}>🔒</span>
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="请输入密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles.input}
            />
            <button
              type="button"
              className={styles.togglePassword}
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>

          {/* 记住我 + 忘记密码 */}
          <div className={styles.footerOptions}>
            <label className={styles.rememberMe}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              记住我
            </label>
            <a href="#" className={styles.forgotPassword}>
              忘记密码？
            </a>
          </div>

          {/* 登录按钮 */}
          <button type="submit" className={styles.loginButton}>
            登录
          </button>

          {/* 其他登录方式 */}
          <div className={styles.otherLogin}>
            <span>其他方式登录</span>
            <div className={styles.socialIcons}>
              <span>微信</span>
              <span>钉钉</span>
              <span>企业微信</span>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
