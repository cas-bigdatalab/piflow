/**
 * 在字符串的开头填充指定的字符，直到字符串达到指定的长度
 * @param {string | number} str - 要填充的原始字符串或数字
 * @param {number} targetLength - 目标长度
 * @param {string} padString - 用于填充的字符串，默认为空格
 * @returns {string} - 填充后的字符串
 *
 * @example
 * // 使用示例
 * console.log(padStart('123', 5));        // 输出: "  123"
 * console.log(padStart('123', 5, '0'));   // 输出: "00123"
 * console.log(padStart('123', 3));        // 输出: "123"
 * console.log(padStart(123, 5, '0'));     // 输出: "00123"
 * console.log(padStart('123', 6, 'ab'));  // 输出: "aba123"
 */
export function padStart(str: string | number, targetLength: number, padString: string = ' '): string {
  str = str.toString();
  // 如果目标长度小于或等于原字符串长度，直接返回原字符串
  if (targetLength <= str.length) {
    return str;
  }

  // 计算需要填充的长度
  const padLength = targetLength - str.length;

  // 创建填充字符串
  let padding = '';
  while (padding.length < padLength) {
    padding += padString;
  }

  // 如果填充字符串过长，截取所需的部分
  padding = padding.slice(0, padLength);

  // 返回填充后的字符串
  return padding + str;
}

/**
 * 在字符串的末尾填充指定的字符，直到字符串达到指定的长度
 * @param str string | number - 要填充的原始字符串或数字
 * @param targetLength number - 目标长度
 * @param padString string - 用于填充的字符串，默认为空格
 * @returns string - 填充后的字符串
 *
 * @example
 * // 使用示例
 * console.log(padEnd('123', 5));        // 输出: "123  "
 * console.log(padEnd('123', 5, '0'));   // 输出: "12300"
 * console.log(padEnd('123', 3));        // 输出: "123"
 * console.log(padEnd(123, 5, '0'));     // 输出: "12300"
 * console.log(padEnd('123', 6, 'ab'));  // 输出: "123aba"
 */
export function padEnd(str: string | number, targetLength: number, padString: string = ' '): string {
  str = str.toString();
  // 如果目标长度小于或等于原字符串长度，直接返回原字符串
  if (targetLength <= str.length) {
    return str;
  }

  // 计算需要填充的长度
  const padLength = targetLength - str.length;

  // 创建填充字符串
  let padding = '';
  while (padding.length < padLength) {
    padding += padString;
  }

  // 如果填充字符串过长，截取所需的部分
  padding = padding.slice(0, padLength);

  // 返回填充后的字符串
  return str + padding;
}

/**
 * 填充类型枚举
 */
enum PadType {
  Start = 'start',
  End = 'end',
  Both = 'both',
}

/**
 * 在字符串的指定位置填充字符，直到字符串达到指定的长度
 * @param str string | number - 要填充的原始字符串或数字
 * @param targetLength number - 目标长度
 * @param padString string - 用于填充的字符串，默认为空格
 * @param padType PadType - 填充类型，可以是 'start'、'end' 或 'both'，默认为 'both'
 * @returns string - 填充后的字符串
 *
 * @example
 * // 使用示例
 *
 * // 1. 默认填充（两端填充）
 * console.log(pad('hello', 10));           // 输出: "  hello   "
 * console.log(pad('hello', 10, '-'));      // 输出: "--hello---"
 *
 * // 2. 开头填充
 * console.log(pad('hello', 10, ' ', PadType.Start));  // 输出: "     hello"
 * console.log(pad('hello', 10, '0', PadType.Start));  // 输出: "00000hello"
 *
 * // 3. 末尾填充
 * console.log(pad('hello', 10, ' ', PadType.End));    // 输出: "hello     "
 * console.log(pad('hello', 10, '0', PadType.End));    // 输出: "hello00000"
 *
 * // 4. 处理数字
 * console.log(pad(42, 5, '0', PadType.Start));        // 输出: "00042"
 *
 * // 5. 目标长度小于或等于原字符串长度
 * console.log(pad('hello', 3));                       // 输出: "hello"
 *
 * // 6. 使用多字符填充字符串
 * console.log(pad('hi', 10, 'ab', PadType.Both));     // 输出: "abahiababa"
 *
 * // 7. 处理空字符串
 * console.log(pad('', 5, '-'));                       // 输出: "--—--"
 */
export function pad(
  str: string | number,
  targetLength: number,
  padString: string = ' ',
  padType: PadType = PadType.Both,
): string {
  str = str.toString();

  if (targetLength <= str.length) {
    return str;
  }

  const padLength = targetLength - str.length;

  switch (padType) {
    case PadType.Start:
      return padStart(str, targetLength, padString);
    case PadType.End:
      return padEnd(str, targetLength, padString);
    case PadType.Both:
    default: {
      const padStartLength = Math.floor(padLength / 2);
      return padEnd(padStart(str, str.length + padStartLength, padString), targetLength, padString);
    }
  }
}
