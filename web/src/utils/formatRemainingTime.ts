import { MS_DAY, MS_HOUR, MS_MINUTE, MS_MONTH, MS_SECOND, MS_YEAR } from './formatDate.ts';
import { padStart } from './pad.ts';

/**
 * 时间单位配置接口
 */
interface TimeUnitConfig {
  showYear?: boolean;
  showMonth?: boolean;
  showDay?: boolean;
  showHour?: boolean;
  showMinute?: boolean;
  showSecond?: boolean;
  showMillisecond?: boolean;
}

/**
 * 时间单位名称接口
 */
interface TimeUnitNames {
  year?: string;
  month?: string;
  day?: string;
  hour?: string;
  minute?: string;
  second?: string;
  millisecond?: string;
}

/**
 * 时间单位原始数据接口
 */
interface TimeUnitData {
  years: number;
  months: number;
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  milliseconds: number;
}

/**
 * 格式化结果接口
 */
interface FormattedResult {
  formatted: string;
  rawData: TimeUnitData;
}

function padZero(num: number, len = 2): string {
  if (num <= 0) return '0';
  return padStart(num, len, '0');
}

/**
 * 将毫秒数格式化为剩余时间字符串
 *
 * @description
 * 这个函数接受一个毫秒数，并将其转换为格式化的时间字符串。
 * 可以通过配置选项控制显示哪些时间单位，以及自定义每个单位的名称。
 *
 * @param {number} ms - 要格式化的毫秒数
 * @param {TimeUnitConfig} config - 时间单位配置选项，控制显示哪些单位
 * @param {TimeUnitNames} unitNames - 时间单位名称配置，自定义每个单位的显示名称
 * @returns {FormattedResult} 包含格式化字符串和原始数据的对象
 *
 * @example
 * // 基本用法
 * const result = formatRemainingTime(1231232131);
 * console.log(result.formatted);
 * // 输出: "14日06小时32秒131毫秒"
 *
 * @example
 * // 自定义配置，只显示天、小时和分钟
 * const config = { showYear: false, showMonth: false, showSecond: false, showMillisecond: false };
 * const result = formatRemainingTime(1231232131, config);
 * console.log(result.formatted);
 * // 输出: "14日06小时"
 *
 * @example
 * // 自定义单位名称
 * const unitNames = { day: 'd', hour: 'h', minute: 'm', second: 's' };
 * const result = formatRemainingTime(1231232131, {}, unitNames);
 * console.log(result.formatted);
 * // 输出: "14d06h32s131毫秒"
 *
 * @example
 * // 获取原始数据
 * const result = formatRemainingTime(1231232131);
 * console.log(result.rawData);
 * // 输出: { years: 0, months: 0, days: 14, hours: 6, minutes: 0, seconds: 32, milliseconds: 131 }
 *
 * @example
 * // 处理大数值（1年）
 * const result = formatRemainingTime(31536000000);
 * console.log(result.formatted);
 * // 输出: "01年"
 *
 * @example
 * // 处理小数值
 * const result = formatRemainingTime(1500);
 * console.log(result.formatted);
 * // 输出: "01秒500毫秒"
 */
export function formatRemainingTime(
  ms: number,
  config: TimeUnitConfig = {},
  unitNames: TimeUnitNames = {},
): FormattedResult {
  const {
    showYear = true,
    showMonth = true,
    showDay = true,
    showHour = true,
    showMinute = true,
    showSecond = true,
    showMillisecond = true,
  } = config;

  const {
    year = '年',
    month = '月',
    day = '日',
    hour = '小时',
    minute = '分钟',
    second = '秒',
    millisecond = '毫秒',
  } = unitNames;

  let remainingMs = Math.max(0, ms);

  const items = [
    { name: year, key: 'years', value: 0, str: '', show: showYear, ms: MS_YEAR },
    { name: month, key: 'months', value: 0, str: '', show: showMonth, ms: MS_MONTH },
    { name: day, key: 'days', value: 0, str: '', show: showDay, ms: MS_DAY },
    { name: hour, key: 'hours', value: 0, str: '', show: showHour, ms: MS_HOUR },
    { name: minute, key: 'minutes', value: 0, str: '', show: showMinute, ms: MS_MINUTE },
    { name: second, key: 'seconds', value: 0, str: '', show: showSecond, ms: MS_SECOND },
    { name: millisecond, key: 'milliseconds', str: '', value: 0, show: showMillisecond, ms: 1 },
  ];

  const rawData = {} as TimeUnitData;
  const parts: string[] = [];

  for (const item of items) {
    if (item.show) {
      item.value = Math.floor(remainingMs / item.ms);
      remainingMs %= item.ms;
      item.str = padZero(item.value, item.ms === 1 ? 3 : 2) + item.name;

      if (item.value > 0) {
        parts.push(item.str);
      }
    }
    rawData[item.key as keyof TimeUnitData] = item.value;
  }

  const formatted = parts.join('') || `0${second}`;

  return { formatted, rawData };
}
