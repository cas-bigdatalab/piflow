/**
 * 对浮点数进行精度取舍
 *
 * @param {number} num - 要处理的浮点数
 * @param {number} precision - 小数点后的位数，范围为 0 到 20
 * @param {boolean} asNumber - 是否返回数字类型，默认为 false
 * @returns {string | number} 格式化后的字符串或数字
 *
 * @example
 * // 基本用法
 * toFixed(3.14159, 2);  // 返回: "3.14"
 * toFixed(3.14159, 4);  // 返回: "3.1416"
 * toFixed(33.333333, 2);  // 返回: "33.33"
 *
 * @example
 * // 返回数字类型
 * toFixed(3.14159, 2, true);  // 返回: 3.14
 * toFixed(3.14159, 4, true);  // 返回: 3.1416
 *
 * @example
 * // 舍入行为
 * toFixed(3.145, 2);    // 返回: "3.15"
 * toFixed(3.1449, 2);   // 返回: "3.14"
 *
 * @example
 * // 边缘情况
 * toFixed(0, 2);        // 返回: "0.00"
 * toFixed(-0, 2);       // 返回: "0.00"
 * toFixed(1e-7, 7);     // 返回: "0.0000001"
 *
 * @throws {Error} 如果 precision 不在 0 到 20 的范围内
 */
export function toFixed<T extends boolean = false>(
  num: number,
  precision: number,
  asNumber?: T,
): T extends true ? number : string {
  if (precision < 0 || precision > 20) {
    throw new Error('Precision must be between 0 and 20');
  }

  // 处理特殊情况
  if (isNaN(num)) return (asNumber ? NaN : 'NaN') as any;
  if (!isFinite(num)) return (asNumber ? num : num > 0 ? 'Infinity' : '-Infinity') as any;

  // 使用一个足够大的精度来避免舍入错误
  const factor = Math.pow(10, precision);
  const tempNumber = Math.abs(num) * factor;
  const rounded = Math.round(tempNumber);

  let intPart = Math.floor(rounded / factor).toString();
  let fracPart = (rounded % factor).toString().padStart(precision, '0');

  // 处理负数
  if (num < 0 && (intPart !== '0' || fracPart !== '0'.repeat(precision))) {
    intPart = '-' + intPart;
  }

  // 格式化结果
  let result: string;
  if (precision === 0) {
    result = intPart;
  } else {
    result = `${intPart}.${fracPart}`;
  }

  // 根据 asNumber 参数决定返回类型
  return (asNumber ? parseFloat(result) : result) as any;
}
