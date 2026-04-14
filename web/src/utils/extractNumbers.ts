/**
 * 从字符串中提取数字
 *
 * @param {string} input - 输入的字符串
 * @returns {number[]} 提取出的数字数组
 *
 * @example
 * // 提取整数和小数
 * const numbers = extractNumbers("The price is $19.99 and quantity is 2");
 * console.log(numbers);
 * // 输出: [19.99, 2]
 *
 * @example
 * // 处理负数和科学记数法
 * const scientificNumbers = extractNumbers("Temperature is -5°C and pressure is 1.2e-5 Pa");
 * console.log(scientificNumbers);
 * // 输出: [-5, 1.2e-5]
 *
 * @example
 * // 处理没有数字的情况
 * const noNumbers = extractNumbers("There are no numbers here");
 * console.log(noNumbers);
 * // 输出: []
 */
export function extractNumbers(input: string): number[] {
  // 使用正则表达式匹配数字，包括整数、小数、负数和科学记数法
  const numberRegex = /-?\d+(?:\.\d+)?(?:e[+-]?\d+)?/g;
  const matches = input.match(numberRegex);

  // 如果没有匹配到数字，返回空数组
  if (!matches) {
    return [];
  }

  // 将匹配到的字符串转换为数字
  return matches.map(Number);
}
