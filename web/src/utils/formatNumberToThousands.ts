/**
 * 将数字转换为带有千分位分隔符的字符串
 * @param {number} num - 要格式化的数字
 * @returns {string} 格式化后的字符串
 *
 * @example
 * // 基本用法
 * formatNumberToThousands(1000);  // 返回 "1,000"
 * formatNumberToThousands(1000000);  // 返回 "1,000,000"
 *
 * @example
 * // 处理小数
 * formatNumberToThousands(1234.56);  // 返回 "1,234.56"
 *
 * @example
 * // 处理负数
 * formatNumberToThousands(-1000000);  // 返回 "-1,000,000"
 *
 * @example
 * // 处理大数字
 * formatNumberToThousands(1234567890);  // 返回 "1,234,567,890"
 */
export function formatNumberToThousands(num: number): string {
  // 将数字转换为字符串
  const numStr = num.toString();

  // 使用正则表达式添加千分位分隔符
  return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
