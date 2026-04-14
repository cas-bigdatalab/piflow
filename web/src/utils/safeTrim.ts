import { typeof2 } from "./typeof2";

/**
 * 安全地去除字符串两端的空白字符
 * @param {unknown} value - 要处理的值
 * @returns {string} 处理后的字符串，如果输入不是字符串则返回空字符串
 *
 * @example
 * // 基本用法
 * safeTrim("  Hello, World!  ");  // 返回: "Hello, World!"
 *
 * @example
 * // 处理非字符串输入
 * safeTrim(null);  // 返回: ""
 * safeTrim(undefined);  // 返回: ""
 * safeTrim(123);  // 返回: ""
 *
 * @example
 * // 处理只包含空白字符的字符串
 * safeTrim("   \t\n  ");  // 返回: ""
 *
 * @example
 * // 处理空字符串
 * safeTrim("");  // 返回: ""
 */
export function safeTrim(value: unknown): string {
  // 检查输入是否为字符串
  if (typeof value !== 'string') {
    return '';
  }

  // 使用正则表达式去除前后的空白字符
  // 这包括空格、制表符、换行符等
  return value.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');
}

/**
 * @method trimDeep
 * @description 去除任意对象中字符的首尾空格
 * @param data 任意对象
 * @returns 去除首尾空格后的字符
 */
export function trimDeep(data: any) {
  const type = typeof2(data)
  if (['object', 'array'].includes(type)) {
    for (const key in data) {
      data[key] = trimDeep(data[key])
    }
    return data
  } else if (type === 'string') {
    return safeTrim(data)
  } else {
    return data
  }
}

