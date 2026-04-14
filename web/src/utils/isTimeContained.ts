import { toDate } from './formatDate.ts';
import type { DateInput } from './formatDate.ts';

/**
 * 表示时间范围的接口
 */
interface TimeRange {
  start: DateInput;
  end: DateInput;
}

/**
 * 判断一个时间点或时间区间是否被另一个时间区间包含
 *
 * @param {DateInput | TimeRange} inner - 内部时间点或时间区间
 * @param {TimeRange} outer - 外部时间区间
 * @returns {boolean} 如果内部时间点或时间区间完全被外部时间区间包含，则返回 true；否则返回 false
 *
 * @description
 * 这个函数检查 inner（可以是时间点或时间区间）是否被 outer 时间区间包含。
 * - 如果 inner 是一个时间点（Date、毫秒数或日期字符串），则检查这个时间点是否在 outer 区间内。
 * - 如果 inner 是一个 TimeRange 对象（时间区间），则检查这个区间是否完全被 outer 区间包含。
 *
 * @example
 * const outerRange = { start: '2023-01-01', end: '2023-01-04' };
 *
 * // 检查时间点（Date 对象）
 * console.log(isTimeContained(new Date('2023-01-02'), outerRange));  // 输出: true
 *
 * // 检查时间点（毫秒数）
 * console.log(isTimeContained(new Date('2023-01-02').getTime(), outerRange));  // 输出: true
 *
 * // 检查时间点（日期字符串）
 * console.log(isTimeContained('2023-01-02', outerRange));  // 输出: true
 *
 * // 检查时间区间
 * const innerRange = { start: '2023-01-02', end: '2023-01-03' };
 * console.log(isTimeContained(innerRange, outerRange));  // 输出: true
 *
 * const notContainedRange = { start: '2023-01-01', end: '2023-01-05' };
 * console.log(isTimeContained(notContainedRange, outerRange));  // 输出: false
 */
export function isTimeContained(inner: DateInput | TimeRange, outer: TimeRange): boolean {
  try {
    const outerStart = toDate(outer.start);
    const outerEnd = toDate(outer.end);

    if (typeof inner === 'object' && 'start' in inner && 'end' in inner) {
      // inner 是时间区间
      const innerStart = toDate(inner.start);
      const innerEnd = toDate(inner.end);
      return innerStart >= outerStart && innerEnd <= outerEnd;
    } else {
      // inner 是单个时间点
      const innerDate = toDate(inner as DateInput);
      return innerDate >= outerStart && innerDate <= outerEnd;
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Error in isTimeContained:', error);
    return false;
  }
}
