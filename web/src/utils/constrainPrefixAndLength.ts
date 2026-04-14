/**
 * 约束字符串前缀和总长度的函数
 *
 * @description
 * 这个函数确保给定的字符串以指定的前缀开始，并且总长度不超过指定的最大长度。
 * 如果字符串不是以给定前缀开始，函数会添加这个前缀。
 * 如果结果字符串超过了最大长度，函数会截断字符串，但保证保留完整的前缀。
 *
 * @param {string} str - 要检查和可能修改的字符串
 * @param {string} prefix - 要确保存在的前缀
 * @param {number} maxLength - 字符串的最大长度（包括前缀）
 * @returns {string} 确保以指定前缀开始且不超过最大长度的字符串
 *
 * @example
 * // 添加前缀，不需要截断
 * constrainPrefixAndLength("Hello", "Say ", 20)
 * // 返回: "Say Hello"
 *
 * @example
 * // 已有前缀，需要截断
 * constrainPrefixAndLength("Prefix: This is a long sentence", "Prefix: ", 15)
 * // 返回: "Prefix: This i"
 *
 * @example
 * // 添加前缀并截断
 * constrainPrefixAndLength("This is a test", "Start: ", 12)
 * // 返回: "Start: This"
 *
 * @example
 * // 处理空字符串
 * constrainPrefixAndLength("", "Empty: ", 10)
 * // 返回: "Empty: "
 *
 * @example
 * // maxLength 小于 prefix 长度的情况
 * constrainPrefixAndLength("Test", "LongPrefix: ", 5)
 * // 返回: "LongPrefix: "
 */
export function constrainPrefixAndLength(str: string, prefix: string, maxLength: number = 99): string {
  // 确保 maxLength 不小于 prefix 的长度
  maxLength = Math.max(maxLength, prefix.length);

  // 如果字符串不是以前缀开始，添加前缀
  if (!str.startsWith(prefix)) {
    str = prefix + str;
  }

  // 如果字符串长度超过 maxLength，进行截断
  if (str.length > maxLength) {
    // 确保保留前缀
    const prefixLength = prefix.length;
    const remainingLength = maxLength - prefixLength;
    str = str.slice(0, prefixLength) + str.slice(prefixLength, prefixLength + remainingLength);
  }

  return str;
}
