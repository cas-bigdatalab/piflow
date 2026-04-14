/**
 * 检查数组是否包含指定的元素或元素数组
 *
 * @template T - 数组元素的类型
 * @param {T} array - 要检查的目标数组
 * @param {T | T[]} element - 要检查的单个元素或元素数组
 * @returns {boolean} 如果数组包含指定的元素（或所有指定的元素），则返回 true；否则返回 false
 *
 * @example
 * // 检查单个元素
 * arrayIncludes([1, 2, 3, 4, 5], 3); // 返回 true
 * arrayIncludes([1, 2, 3, 4, 5], 6); // 返回 false
 *
 * @example
 * // 检查多个元素
 * arrayIncludes([1, 2, 3, 4, 5], [2, 4]); // 返回 true
 * arrayIncludes([1, 2, 3, 4, 5], [2, 6]); // 返回 false
 *
 * @example
 * // 使用字符串数组
 * arrayIncludes(['apple', 'banana', 'orange'], 'banana'); // 返回 true
 * arrayIncludes(['apple', 'banana', 'orange'], ['apple', 'grape']); // 返回 false
 *
 * @example
 * // 使用大型数组（内部会使用 Set 来优化性能）
 * const largeArray = Array.from({ length: 10000 }, (_, i) => i);
 * arrayIncludes(largeArray, 9999); // 返回 true
 * arrayIncludes(largeArray, [1000, 5000, 9000]); // 返回 true
 */
export function arrayIncludes<T>(array: T[], element: T | T[]): boolean {
  // 对于小数组，直接使用 includes 可能更快
  if (array.length < 100) {
    if (Array.isArray(element)) {
      return element.every((item) => array.includes(item));
    } else {
      return array.includes(element);
    }
  }

  // 对于大数组，使用 Set 来提高效率
  const set = new Set(array);

  if (Array.isArray(element)) {
    return element.every((item) => set.has(item));
  } else {
    return set.has(element);
  }
}
