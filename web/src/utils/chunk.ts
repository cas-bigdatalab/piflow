/**
 * 将一维数组按指定大小分割成二维数组
 *
 * @template T - 数组元素的类型
 * @param {T[]} array - 要分割的原始数组
 * @param {number} size - 每个子数组的大小
 * @returns {T[][]} 分割后的二维数组
 *
 * @example
 * // 基本用法
 * chunk([1, 2, 3, 4, 5], 2);
 * // 返回: [[1, 2], [3, 4], [5]]
 *
 * @example
 * // 使用字符串数组
 * chunk(['a', 'b', 'c', 'd', 'e'], 3);
 * // 返回: [['a', 'b', 'c'], ['d', 'e']]
 *
 * @example
 * // 当 size 大于数组长度时
 * chunk([1, 2, 3], 5);
 * // 返回: [[1, 2, 3]]
 *
 * @example
 * // 使用空数组
 * chunk([], 2);
 * // 返回: []
 *
 * @throws {Error} 如果 size 不是正整数
 */
export function chunk<T>(array: T[], size: number): T[][] {
  if (size <= 0 || !Number.isInteger(size)) {
    throw new Error('Size must be a positive integer');
  }

  const chunkedArray: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunkedArray.push(array.slice(i, i + size));
  }

  return chunkedArray;
}
