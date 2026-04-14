/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本内容
 * @returns {boolean} 返回是否复制成功
 *
 * @example
 * const text = 'Hello, world!';
 * const isCopied = await copyToClipboard(text);
 * console.log(isCopied ? '复制成功' : '复制失败');
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (typeof document === 'undefined' || typeof navigator === 'undefined') {
    throw new Error('document or navigator is not defined');
  }

  if (!text) return false;

  // 现代 API 优先
  if (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      // eslint-disable-next-line no-console
      console.warn('现代 API 失败:', error);
    }
  }

  // 降级使用旧方法（HTTP 兼容）
  return fallbackCopy(text);
}

/**
 * 旧版 execCommand 方案（兼容性备用）
 * @param text 要复制的文本
 * @returns 返回是否复制成功
 */
function fallbackCopy(text: string): boolean {
  // 创建临时 textarea 元素
  const textarea = document.createElement('textarea');
  textarea.value = text;

  // 防止页面滚动和样式影响
  textarea.style.position = 'fixed';
  textarea.style.top = '-128px';
  textarea.style.left = '-128px';
  textarea.style.opacity = '0';
  textarea.style.pointerEvents = 'none';

  document.body.appendChild(textarea);

  try {
    // 选中文本
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length); // 兼容移动端

    // 执行复制命令
    const successful = document.execCommand('copy');
    return successful;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('旧版复制方法失败:', err);
    return false;
  } finally {
    // 清理临时元素
    document.body.removeChild(textarea);
  }
}
