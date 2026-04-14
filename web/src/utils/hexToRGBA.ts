/**
 * 将16进制颜色值转换为RGB或RGBA格式
 * @param {string} hex - 16进制颜色值，格式为 "#RRGGBB" 或 "#RGB"
 * @param {number} opacity - 可选的不透明度值，范围为 0 到 1
 * @returns {string} RGB 或 RGBA 格式的颜色字符串
 *
 * @example
 * // 基本用法 - 转换为 RGB
 * hexToRGBA('#FF0000');
 * // 返回: "rgb(255, 0, 0)"
 *
 * @example
 * // 使用不透明度 - 转换为 RGBA
 * hexToRGBA('#00FF00', 0.5);
 * // 返回: "rgba(0, 255, 0, 0.5)"
 *
 * @example
 * // 使用简写的十六进制颜色
 * hexToRGBA('#F0F', 0.8);
 * // 返回: "rgba(255, 0, 255, 0.8)"
 *
 * @throws {Error} 如果提供的十六进制颜色格式无效
 */
export function hexToRGBA(hex: string, opacity?: number): string {
  // 移除可能存在的 # 前缀
  hex = hex.replace(/^#/, '');

  // 检查十六进制颜色格式是否有效
  if (!/^([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
    throw new Error('Invalid hex color format');
  }

  // 如果是简写形式（如 #RGB），转换为完整形式（#RRGGBB）
  if (hex.length === 3) {
    hex = hex
      .split('')
      .map((char) => char + char)
      .join('');
  }

  // 将十六进制值转换为 RGB 值
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // 如果提供了不透明度，返回 RGBA 格式
  if (opacity !== void 0) {
    // 确保 opacity 在 0 到 1 之间
    const validOpacity = Math.max(0, Math.min(1, opacity));
    return `rgba(${r}, ${g}, ${b}, ${validOpacity})`;
  }

  // 否则返回 RGB 格式
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * 将 RGBA 或 RGB 格式的颜色值转换为 16 进制颜色值
 * @param {string} color - RGBA 或 RGB 格式的颜色值字符串
 * @returns {string} 16进制格式的颜色值字符串
 *
 * @example
 * // RGB 格式
 * rgbaToHex('rgb(255, 0, 0)');  // 返回: "#FF0000"
 *
 * @example
 * // RGBA 格式
 * rgbaToHex('rgba(0, 255, 0, 0.5)');  // 返回: "#00FF0080"
 *
 * @example
 * // 带有空格的格式
 * rgbaToHex('rgba(0, 0, 255, 1)');  // 返回: "#0000FF"
 *
 * @example
 * // 百分比透明度
 * rgbaToHex('rgba(128, 128, 128, 50%)');  // 返回: "#80808080"
 *
 * @throws {Error} 如果输入的颜色格式不正确
 */
export function rgbaToHex(color: string): string {
  // 匹配 RGB 或 RGBA 格式
  const rgbaRegex = /^rgba?$$(\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d*(?:\.\d+)?%?))?$$$/;
  const match = color.match(rgbaRegex);

  if (!match) {
    throw new Error('Invalid color format');
  }

  // 提取 RGB 值
  const r = parseInt(match[1]);
  const g = parseInt(match[2]);
  const b = parseInt(match[3]);

  // 处理 Alpha 值
  let a: number | undefined;
  if (match[4] !== void 0) {
    if (match[4].endsWith('%')) {
      // 处理百分比透明度
      a = Math.round(parseFloat(match[4]) * 2.55);
    } else {
      a = Math.round(parseFloat(match[4]) * 255);
    }
  }

  // 转换为 16 进制
  const toHex = (value: number): string => {
    const hex = value.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };

  let result = `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  if (a !== void 0) {
    result += toHex(a);
  }

  return result.toUpperCase();
}


/**
 * 获取线性渐变区域的样式
 * @param color - 渐变颜色
 * @param startOpacity - 起始不透明度，默认为0.7
 * @param endOpacity - 结束不透明度，默认为0
 * @returns 线性渐变区域的样式对象
 */
export const getLinearGradientAreaStyle = (color: string, startOpacity = 0.7, endOpacity = 0) => {
  return {
    color: {
      type: 'linear',
      x: 0,
      y: 0,
      x2: 0,
      y2: 1,
      colorStops: [
        { offset: 0, color: hexToRGBA(color, startOpacity) },
        { offset: 1, color: hexToRGBA(color, endOpacity) }
      ]
    }
  }
}
