/**
 * 判定两个值是否深度相等
 * @param {unknown} a 第一个要比较的值
 * @param {unknown} b 第二个要比较的值
 * @returns {boolean} 如果两个值深度相等则返回 true，否则返回 false
 *
 * @example
 * // 基本类型比较
 * deepEqual(1, 1);                  // 返回: true
 * deepEqual('hello', 'hello');      // 返回: true
 * deepEqual(true, true);            // 返回: true
 * deepEqual(null, null);            // 返回: true
 * deepEqual(undefined, undefined);  // 返回: true
 *
 * @example
 * // 数组比较
 * deepEqual([1, 2, 3], [1, 2, 3]);              // 返回: true
 * deepEqual([1, [2, 3]], [1, [2, 3]]);          // 返回: true
 * deepEqual([1, 2, 3], [1, 2, 4]);              // 返回: false
 *
 * @example
 * // 对象比较
 * deepEqual({a: 1, b: 2}, {a: 1, b: 2});        // 返回: true
 * deepEqual({a: 1, b: {c: 2}}, {a: 1, b: {c: 2}}); // 返回: true
 * deepEqual({a: 1, b: 2}, {b: 2, a: 1});        // 返回: true
 * deepEqual({a: 1, b: 2}, {a: 1, b: 3});        // 返回: false
 *
 * @example
 * // 特殊情况
 * deepEqual(NaN, NaN);                          // 返回: true
 * deepEqual(new Date(2023, 0, 1), new Date(2023, 0, 1)); // 返回: true
 * deepEqual(/abc/, /abc/);                      // 返回: true
 * deepEqual(() => {}, () => {});                // 返回: false (函数比较)
 */
export function deepEqual(a: unknown, b: unknown): boolean {
  // 处理基本类型和引用相等
  if (a === b) return true;

  // 处理 null 和 undefined
  if (a === null || b === null || a === void 0 || b === void 0) return false;

  // 处理 NaN
  if (Number.isNaN(a) && Number.isNaN(b)) return true;

  // 处理日期对象
  if (a instanceof Date && b instanceof Date) {
    return a.getTime() === b.getTime();
  }

  // 处理正则表达式
  if (a instanceof RegExp && b instanceof RegExp) {
    return a.toString() === b.toString();
  }

  // 处理函数（仅比较引用）
  if (typeof a === 'function' && typeof b === 'function') {
    return a === b;
  }

  // 处理对象和数组
  if (typeof a === 'object' && typeof b === 'object') {
    if (Array.isArray(a) && Array.isArray(b)) {
      if (a.length !== b.length) return false;
      for (let i = 0; i < a.length; i++) {
        if (!deepEqual(a[i], b[i])) return false;
      }
      return true;
    } else if (!Array.isArray(a) && !Array.isArray(b)) {
      const keysA = Object.keys(a as object);
      const keysB = Object.keys(b as object);
      if (keysA.length !== keysB.length) return false;
      for (const key of keysA) {
        if (!Object.prototype.hasOwnProperty.call(b, key)) return false;
        if (!deepEqual((a as any)[key], (b as any)[key])) return false;
      }
      return true;
    }
  }

  // 其他情况视为不相等
  return false;
}
