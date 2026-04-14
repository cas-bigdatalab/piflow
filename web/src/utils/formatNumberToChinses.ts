/**
 * 将数字转换为中文表示
 *
 * @param {number} num - 要转换的数字
 * @param {boolean} [uppercase=false] - 是否使用大写数字（如壹、贰、叁等）
 * @returns {string} 数字的中文表示
 *
 * @description
 * 这个函数可以将数字转换为中文表示，支持整数和小数。
 * 可以处理的范围从0到万亿级别的数字，小数部分保留到分（两位小数）。
 * 可以选择使用大写数字（壹、贰、叁等）或小写数字（一、二、三等）。
 *
 * @example
 * // 基本用法（小写）
 * console.log(formatNumberToChinses(0));  // 输出: 零
 * console.log(formatNumberToChinses(10));  // 输出: 十
 * console.log(formatNumberToChinses(100));  // 输出: 一百
 *
 * // 使用大写数字
 * console.log(formatNumberToChinses(0, true));  // 输出: 零
 * console.log(formatNumberToChinses(10, true));  // 输出: 壹拾
 * console.log(formatNumberToChinses(100, true));  // 输出: 壹佰
 *
 * // 处理大数
 * console.log(formatNumberToChinses(1234567890));  // 输出: 十二亿三千四百五十六万七千八百九十
 * console.log(formatNumberToChinses(1234567890, true));  // 输出: 壹拾贰亿叁仟肆佰伍拾陆万柒仟捌佰玖拾
 *
 * // 处理小数
 * console.log(formatNumberToChinses(1.23));  // 输出: 一点二三
 * console.log(formatNumberToChinses(1.23, true));  // 输出: 壹点贰叁
 *
 * @note
 * - 对于小数，函数会四舍五入到两位小数
 * - 函数会自动处理数字中的零，确保输出符合中文读法习惯
 * - 当使用大写数字时，"两"会被替换为"贰"
 */
export function formatNumberToChinses(num: number, uppercase: boolean = false): string {
  // 中文数字数组（小写和大写）
  const chineseNums = [
    ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'],
    ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'],
  ];
  // 中文单位数组（小写和大写）
  const chineseUnits = [
    ['', '十', '百', '千', '万', '十', '百', '千', '亿', '十', '百', '千', '万'],
    ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿', '拾', '佰', '仟', '万'],
  ];

  const nums = chineseNums[uppercase ? 1 : 0];
  const units = chineseUnits[uppercase ? 1 : 0];

  // 处理 0 的特殊情况
  if (num === 0) return nums[0];

  // 分离整数部分和小数部分
  const integerPart = Math.floor(num);
  const decimalPart = Math.round((num - integerPart) * 100) / 100;

  let result = '';

  // 处理整数部分
  if (integerPart > 0) {
    let temp = '';
    let unitPos = 0;
    let strNum = integerPart.toString();

    // 从个位开始处理每一位数字
    for (let i = strNum.length - 1; i >= 0; i--) {
      const n = parseInt(strNum[i]);
      if (n !== 0) {
        // 当前位不为0，加上数字和单位
        temp = nums[n] + units[unitPos] + temp;
      } else {
        // 当前位为0，需要特殊处理
        if (unitPos % 4 === 0) {
          // 在万位或亿位上，即使是0也要加上单位
          temp = units[unitPos] + temp;
        }
        if (temp[0] !== nums[0]) {
          // 避免多个连续的零
          temp = nums[0] + temp;
        }
      }
      unitPos++;
    }
    // 去掉末尾的零
    result = temp.replace(/零+$/, '');

    // 处理十到十九的特殊情况
    if (result.startsWith('一十')) {
      result = result.substring(1);
    }
  }

  // 处理小数部分
  if (decimalPart > 0) {
    result += '点';
    const decimalStr = decimalPart.toString().split('.')[1];
    for (let i = 0; i < decimalStr.length; i++) {
      result += nums[parseInt(decimalStr[i])];
    }
  }

  return result;
}
