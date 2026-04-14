import { formatDate } from './formatDate.ts';
import type { DateInput } from './formatDate.ts';

export type TimeUnit = 'milliseconds' | 'seconds' | 'minutes' | 'hours' | 'days';

export interface Interval {
  value: number;
  unit: TimeUnit;
}

/**
 * 将时间间隔转换为毫秒
 * @param interval Interval - 时间间隔对象
 * @returns number - 毫秒数
 */
function intervalToMs(interval: Interval): number {
  const msMultipliers: Record<TimeUnit, number> = {
    milliseconds: 1,
    seconds: 1000,
    minutes: 60 * 1000,
    hours: 60 * 60 * 1000,
    days: 24 * 60 * 60 * 1000,
  };
  return interval.value * msMultipliers[interval.unit];
}

/**
 * 将时间区间按指定间隔分割
 * @param {DateInput} startTime - 开始时间
 * @param {DateInput} endTime - 结束时间
 * @param {Interval} interval - 分割间隔
 * @param {string | undefined} format - 可选的日期格式化字符串
 * @returns {(Date[] | string[])} - 分割后的时间点数组（如果提供了格式，则返回格式化的字符串数组）
 *
 * @example
 * // 1. 基本用法：按小时分割时间区间
 * const start = new Date('2023-05-01T09:00:00');
 * const end = new Date('2023-05-01T17:00:00');
 * const interval = { value: 2, unit: 'hours' };
 *
 * const result1 = splitTimeInterval(start, end, interval);
 * console.log(result1);
 * // 输出: [
 * //   2023-05-01T09:00:00.000Z,
 * //   2023-05-01T11:00:00.000Z,
 * //   2023-05-01T13:00:00.000Z,
 * //   2023-05-01T15:00:00.000Z,
 * //   2023-05-01T17:00:00.000Z
 * // ]
 *
 * // 2. 使用格式化选项
 * const result2 = splitTimeInterval(start, end, interval, 'YYYY-MM-DD HH:mm');
 * console.log(result2);
 * // 输出: [
 * //   '2023-05-01 09:00',
 * //   '2023-05-01 11:00',
 * //   '2023-05-01 13:00',
 * //   '2023-05-01 15:00',
 * //   '2023-05-01 17:00'
 * // ]
 *
 * // 3. 使用分钟作为间隔单位
 * const shortInterval = { value: 30, unit: 'minutes' };
 * const result3 = splitTimeInterval(
 *   '2023-05-01T14:00:00',
 *   '2023-05-01T16:00:00',
 *   shortInterval,
 *   'HH:mm'
 * );
 * console.log(result3);
 * // 输出: ['14:00', '14:30', '15:00', '15:30', '16:00']
 *
 * // 4. 处理跨天的时间区间
 * const overnight = splitTimeInterval(
 *   '2023-05-01T22:00:00',
 *   '2023-05-02T02:00:00',
 *   { value: 1, unit: 'hours' },
 *   'MM-DD HH:mm'
 * );
 * console.log(overnight);
 * // 输出: [
 * //   '05-01 22:00',
 * //   '05-01 23:00',
 * //   '05-02 00:00',
 * //   '05-02 01:00',
 * //   '05-02 02:00'
 * // ]
 *
 * // 5. 使用自定义格式
 * const customFormat = splitTimeInterval(
 *   '2023-05-01T09:00:00',
 *   '2023-05-01T13:00:00',
 *   { value: 2, unit: 'hours' },
 *   'dddd, MMMM D, YYYY h:mm A'
 * );
 * console.log(customFormat);
 * // 输出: [
 * //   'Monday, May 1, 2023 9:00 AM',
 * //   'Monday, May 1, 2023 11:00 AM',
 * //   'Monday, May 1, 2023 1:00 PM'
 * // ]
 */
export function splitTimeInterval(
  startTime: DateInput,
  endTime: DateInput,
  interval: Interval,
  format?: string,
): Date[] | string[] {
  const start = new Date(startTime);
  const end = new Date(endTime);

  const totalDuration = end.getTime() - start.getTime();
  const intervalMs = intervalToMs(interval);
  const splitCount = Math.floor(totalDuration / intervalMs);

  const splitPoints: Date[] = [start];

  for (let i = 1; i <= splitCount; i++) {
    const pointTime = new Date(start.getTime() + i * intervalMs);
    splitPoints.push(pointTime);
  }

  if (splitPoints[splitPoints.length - 1].getTime() !== end.getTime()) {
    splitPoints.push(end);
  }

  return format ? splitPoints.map((date) => formatDate(date, format)) : splitPoints;
}
