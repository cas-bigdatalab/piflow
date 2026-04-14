/**
 * 判断值是否为空
 * @param {unknown} value - 要判断的值，可以是任意类型
 * @returns {boolean} 如果值为 undefined、null、空数组或空对象则返回 true，否则返回 false
 *
 * @example
 * // 基本用法
 * isEmpty(null);        // 返回: true
 * isEmpty(undefined);   // 返回: true
 * isEmpty([]);          // 返回: true
 * isEmpty({});          // 返回: true
 *
 * @example
 * // 非空值
 * isEmpty(0);           // 返回: false
 * isEmpty('');          // 返回: false
 * isEmpty(false);       // 返回: false
 * isEmpty([1, 2, 3]);   // 返回: false
 * isEmpty({ a: 1 });    // 返回: false
 *
 * @example
 * // 特殊情况
 * isEmpty(new Set());   // 返回: true
 * isEmpty(new Map());   // 返回: true
 */
export function isEmpty(value: unknown): boolean {
  if (value === null || value === void 0) {
    return true;
  }

  if (Array.isArray(value) || typeof value === 'string') {
    return value.length === 0;
  }

  if (value instanceof Set || value instanceof Map) {
    return value.size === 0;
  }

  if (typeof value === 'object') {
    return Object.keys(value as object).length === 0;
  }

  return false;
}
