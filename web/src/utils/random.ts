/**
 * 生成指定范围内的随机数
 * @param {number} min - 最小值（包含）
 * @param {number} max - 最大值（包含）
 * @param {boolean} floating - 是否返回浮点数，默认为 false
 * @returns {number} 生成的随机数
 *
 * @example
 * // 生成 1 到 10 之间的整数
 * random(1, 10);  // 可能返回: 5
 *
 * @example
 * // 生成 0 到 1 之间的浮点数
 * random(0, 1, true);  // 可能返回: 0.7564321
 *
 * @example
 * // 生成 -10 到 10 之间的整数
 * random(-10, 10);  // 可能返回: -3
 *
 * @example
 * // 生成 1.5 到 2.5 之间的浮点数
 * random(1.5, 2.5, true);  // 可能返回: 2.1234567
 */
export function random(min: number, max: number, floating: boolean = false): number {
  if (min > max) {
    [min, max] = [max, min]; // 交换 min 和 max
  }

  const range = max - min;
  let result: number;

  if (floating || !Number.isInteger(min) || !Number.isInteger(max)) {
    // 生成浮点数
    result = Math.random() * range + min;
  } else {
    // 生成整数
    result = Math.floor(Math.random() * (range + 1)) + min;
  }

  return floating ? result : Math.floor(result);
}

/**
 * 生成指定范围内的多个随机数
 * @param {number} min 最小值（包含）
 * @param {number} max 最大值（包含）
 * @param {number} count 生成随机数的数量
 * @param {boolean} floating 是否返回浮点数，默认为 false
 * @returns {number[]} 生成的随机数数组
 *
 * @example
 * // 生成 5 个 1 到 10 之间的整数
 * randomMultiple(1, 10, 5);  // 可能返回: [5, 8, 2, 10, 3]
 *
 * @example
 * // 生成 3 个 0 到 1 之间的浮点数
 * randomMultiple(0, 1, 3, true);  // 可能返回: [0.7564321, 0.2345678, 0.9876543]
 *
 * @example
 * // 生成 4 个 -10 到 10 之间的整数
 * randomMultiple(-10, 10, 4);  // 可能返回: [-3, 7, -1, 10]
 *
 * @example
 * // 生成 2 个 1.5 到 2.5 之间的浮点数
 * randomMultiple(1.5, 2.5, 2, true);  // 可能返回: [2.1234567, 1.8901234]
 */
export function randomMultiple(min: number, max: number, count: number, floating: boolean = false): number[] {
  return Array.from({ length: count }, () => random(min, max, floating));
}
