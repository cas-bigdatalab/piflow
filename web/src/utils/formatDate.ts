import { padStart } from "./pad.ts";

export const MS_SECOND = 1000;
export const MS_MINUTE = MS_SECOND * 60;
export const MS_HOUR = MS_MINUTE * 60;
export const MS_DAY = MS_HOUR * 24;
export const MS_WEEK = MS_DAY * 7;
export const MS_MONTH = MS_DAY * 30;
export const MS_QUATER = MS_MONTH * 3;
export const MS_YEAR = MS_DAY * 365;

/**
 * 定义可接受的日期输入类型
 * Date: JavaScript 日期对象
 * string: 日期字符串（如 ISO 8601 格式）
 * number: 时间戳（毫秒）
 */
export type DateInput = Date | string | number;

/**
 * 将输入转换为 Date 对象
 *
 * @param {DateInput} time - 输入的时间（Date 对象、毫秒数或日期字符串）
 * @returns {Date} 转换后的 Date 对象
 * @throws {Error} 如果输入无法转换为有效的 Date 对象
 */
export function toDate(time: DateInput): Date {
  if (time instanceof Date) {
    return time;
  }
  if (typeof time === "number") {
    return new Date(time);
  }
  const date = new Date(time);
  if (isNaN(date.getTime())) {
    throw new Error("Invalid date input");
  }
  return date;
}

/**
 * 格式化日期函数
 *
 * @param {DateInput} input - 要格式化的日期（可以是 Date 对象、日期字符串或时间戳）
 * @param {string} format - 指定的输出格式
 * @returns {string} 格式化后的日期字符串
 * @throws 如果输入的日期无效，则抛出错误
 *
 * 格式选项：
 * - YYYY: 四位年份
 * - MM: 两位月份（01-12）
 * - DD: 两位日期（01-31）
 * - HH: 两位小时（00-23）
 * - mm: 两位分钟（00-59）
 * - ss: 两位秒（00-59）
 * - SSS: 三位毫秒（000-999）
 * - Q: 季度（1-4）
 * - WW: 两位周数（01-53）
 *
 * @example
 * // 格式化当前日期
 * const now = new Date();
 * console.log(formatDate(now, 'YYYY-MM-DD HH:mm:ss'));
 * // 输出: 2023-05-16 10:30:45 (假设当前时间)
 *
 * @example
 * // 格式化日期，包含季度和周数
 * const date = new Date('2023-05-15T14:30:45.123');
 * console.log(formatDate(date, 'YYYY年第Q季第WW周 MM月DD日'));
 * // 输出: 2023年第2季第20周 05月15日
 *
 * @example
 * // 解析和格式化日期字符串
 * const dateString = '2023-12-31T23:59:59';
 * console.log(formatDate(dateString, 'YYYY年MM月DD日 HH时mm分ss秒 (第Q季)'));
 * // 输出: 2023年12月31日 23时59分59秒 (第4季)
 *
 * @example
 * // 格式化时间戳
 * const timestamp = 1684159845123;
 * console.log(formatDate(timestamp, 'YYYY/MM/DD HH:mm:ss.SSS (第WW周)'));
 * // 输出: 2023/05/15 14:30:45.123 (第20周)
 *
 * @example
 * // 错误处理
 * try {
 *   console.log(formatDate('Invalid input', 'YYYY-MM-DD'));
 * } catch (error) {
 *   console.error('Error:', error.message);
 * }
 * // 输出: Error: Invalid date input
 */
export function formatDate(
  input?: DateInput,
  format = "YYYY-MM-DD HH:mm:ss",
): string {
  // 将输入转换为 Date 对象
  const date = toDate(input || new Date());

  const padZreo = (num: number, len = 2): string => padStart(num, len, "0");

  // 获取季度
  const getQuarter = (d: Date): number => Math.floor(d.getMonth() / 3) + 1;

  // 获取周数
  const getWeek = (d: Date): number => {
    const firstDayOfYear = new Date(d.getFullYear(), 0, 1);
    const pastDaysOfYear = (d.getTime() - firstDayOfYear.getTime()) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
  };

  // 定义格式化选项
  const formats: { [key: string]: string } = {
    YYYY: date.getFullYear().toString(), // 四位年份
    MM: padZreo(date.getMonth() + 1), // 两位月份（01-12）
    DD: padZreo(date.getDate()), // 两位日期（01-31）
    HH: padZreo(date.getHours()), // 两位小时（00-23）
    mm: padZreo(date.getMinutes()), // 两位分钟（00-59）
    ss: padZreo(date.getSeconds()), // 两位秒（00-59）
    SSS: padZreo(date.getMilliseconds(), 3), // 三位毫秒（000-999）
    Q: getQuarter(date).toString(), // 季度（1-4）
    WW: padZreo(getWeek(date)), // 两位周数（01-53）
  };

  // 使用正则表达式替换格式字符串中的占位符
  return format.replace(
    /YYYY|MM|DD|HH|mm|ss|SSS|Q|WW/g,
    (match) => formats[match],
  );
}

/**
 * 获取指定分钟数之前到现在的时间范围
 *
 * @param {number} min - 要回溯的分钟数
 * @returns 包含开始时间和结束时间的数组 [startTime, endTime]
 *
 * @example
 * // 获取 5 分钟前到现在的时间范围
 * const [startTime, endTime] = getMinutesTimeRange(5);
 * console.log(startTime, endTime);
 * // 输出类似：2023-05-16T10:25:00.000Z 2023-05-16T10:30:00.000Z
 *
 * @example
 * // 获取 1 小时前到现在的时间范围
 * const [start, end] = getMinutesTimeRange(60);
 * console.log(start.toISOString(), end.toISOString());
 * // 输出类似：2023-05-16T09:30:00.000Z 2023-05-16T10:30:00.000Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间
 * const [start, end] = getMinutesTimeRange(30);
 * console.log(`开始时间：${start.toLocaleString()}`);
 * console.log(`结束时间：${end.toLocaleString()}`);
 * // 输出类似：
 * // 开始时间：2023/5/16 18:00:00
 * // 结束时间：2023/5/16 18:30:00
 */
export function getMinutesTimeRange(min: number): [Date, Date] {
  const endTime = new Date(); // 当前时间
  const startTime = new Date(endTime.getTime() - min * 60000); // min 分钟前的时间

  return [startTime, endTime];
}

/**
 * 获取指定天数之前到现在（或昨天）的时间范围
 *
 * @param {number} day - 要回溯的天数
 * @param {boolean} includeToday - 是否包括今天，默认为 true
 * @returns 包含开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59
 *
 * @example
 * // 获取 5 天前到今天的时间范围
 * const [startTime, endTime] = getDateRange(5);
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 输出类似：2023-05-11T00:00:00.000Z 2023-05-15T23:59:59.999Z
 *
 * @example
 * // 获取 5 天前到昨天的时间范围（不包括今天）
 * const [start, end] = getDateRange(5, false);
 * console.log(start.toISOString(), end.toISOString());
 * // 输出类似：2023-05-10T00:00:00.000Z 2023-05-14T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getDateRange(3, false);
 * console.log(`开始时间：${start.toLocaleString()}`);
 * console.log(`结束时间：${end.toLocaleString()}`);
 * // 输出类似：
 * // 开始时间：2023/5/12 00:00:00
 * // 结束时间：2023/5/14 23:59:59
 */
export function getDateRange(
  day: number,
  includeToday: boolean = true,
): [Date, Date] {
  const now = new Date();

  // 根据 includeToday 参数设置结束日期
  const endDate = includeToday
    ? now
    : new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);

  // 设置结束时间为结束日期的23:59:59.999
  const endTime = new Date(
    endDate.getFullYear(),
    endDate.getMonth(),
    endDate.getDate(),
    23,
    59,
    59,
    999,
  );

  // 设置开始时间为 (day - 1) 天前的00:00:00，如果不包括今天则额外减去一天
  const startTime = new Date(
    endDate.getFullYear(),
    endDate.getMonth(),
    endDate.getDate() - day + (includeToday ? 1 : 0),
    0,
    0,
    0,
    0,
  );

  return [startTime, endTime];
}

/**
 * 获取今天的日期范围
 *
 * @returns {[Date, Date]} 包含今天开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取今天的日期范围
 * const [startTime, endTime] = getTodayDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 输出类似：2023-05-16T00:00:00.000Z 2023-05-16T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getTodayDateRange();
 * console.log(`今天开始时间：${start.toLocaleString()}`);
 * console.log(`今天结束时间：${end.toLocaleString()}`);
 * // 输出类似：
 * // 今天开始时间：2023/5/16 00:00:00
 * // 今天结束时间：2023/5/16 23:59:59
 */
export function getTodayDateRange(): [Date, Date] {
  const now = new Date();

  // 设置开始时间为今天的00:00:00.000
  const startTime = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
    0,
    0,
    0,
    0,
  );

  // 设置结束时间为今天的23:59:59.999
  const endTime = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
    23,
    59,
    59,
    999,
  );

  return [startTime, endTime];
}

/**
 * 获取昨天的日期范围
 *
 * @returns {[Date, Date]} 包含昨天开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取昨天的日期范围
 * const [startTime, endTime] = getYesterdayDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 输出类似：2023-05-15T00:00:00.000Z 2023-05-15T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getYesterdayDateRange();
 * console.log(`昨天开始时间：${start.toLocaleString()}`);
 * console.log(`昨天结束时间：${end.toLocaleString()}`);
 * // 输出类似：
 * // 昨天开始时间：2023/5/15 00:00:00
 * // 昨天结束时间：2023/5/15 23:59:59
 */
export function getYesterdayDateRange(): [Date, Date] {
  const now = new Date();
  const yesterday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() - 1,
  );

  // 设置开始时间为昨天的00:00:00.000
  const startTime = new Date(
    yesterday.getFullYear(),
    yesterday.getMonth(),
    yesterday.getDate(),
    0,
    0,
    0,
    0,
  );

  // 设置结束时间为昨天的23:59:59.999
  const endTime = new Date(
    yesterday.getFullYear(),
    yesterday.getMonth(),
    yesterday.getDate(),
    23,
    59,
    59,
    999,
  );

  return [startTime, endTime];
}

/**
 * 获取本周的日期范围
 *
 * @param {number} startOfWeek - 一周的开始日期，0 表示周日，1 表示周一，以此类推。默认为 1（周一）
 * @returns {[Date, Date]} 包含本周开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取本周的日期范围（默认周一为一周的开始）
 * const [startTime, endTime] = getCurrentWeekDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 输出类似：2023-05-15T00:00:00.000Z 2023-05-21T23:59:59.999Z
 *
 * @example
 * // 获取本周的日期范围（周日为一周的开始）
 * const [start, end] = getCurrentWeekDateRange(0);
 * console.log(`本周开始时间：${start.toLocaleString()}`);
 * console.log(`本周结束时间：${end.toLocaleString()}`);
 * // 输出类似：
 * // 本周开始时间：2023/5/14 00:00:00
 * // 本周结束时间：2023/5/20 23:59:59
 */
export function getCurrentWeekDateRange(startOfWeek: number = 1): [Date, Date] {
  const now = new Date();
  const currentDay = now.getDay();
  const diff =
    currentDay >= startOfWeek
      ? currentDay - startOfWeek
      : 7 - startOfWeek + currentDay;

  // 设置开始时间为本周开始的00:00:00.000
  const startTime = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() - diff,
    0,
    0,
    0,
    0,
  );

  // 设置结束时间为本周结束的23:59:59.999
  const endTime = new Date(
    startTime.getFullYear(),
    startTime.getMonth(),
    startTime.getDate() + 6,
    23,
    59,
    59,
    999,
  );

  return [startTime, endTime];
}

/**
 * 获取上周的日期范围
 *
 * @param {number} startOfWeek - 一周的开始日期，0 表示周日，1 表示周一，以此类推。默认为 1（周一）
 * @returns {[Date, Date]} 包含上周开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取上周的日期范围（默认周一为一周的开始）
 * const [startTime, endTime] = getLastWeekDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 输出类似：2023-05-08T00:00:00.000Z 2023-05-14T23:59:59.999Z
 *
 * @example
 * // 获取上周的日期范围（周日为一周的开始）
 * const [start, end] = getLastWeekDateRange(0);
 * console.log(`上周开始时间：${start.toLocaleString()}`);
 * console.log(`上周结束时间：${end.toLocaleString()}`);
 * // 输出类似：
 * // 上周开始时间：2023/5/7 00:00:00
 * // 上周结束时间：2023/5/13 23:59:59
 */
export function getLastWeekDateRange(startOfWeek: number = 1): [Date, Date] {
  const now = new Date();
  const currentDay = now.getDay();
  const diff =
    (currentDay >= startOfWeek
      ? currentDay - startOfWeek
      : 7 - startOfWeek + currentDay) + 7;

  // 设置开始时间为上周开始的00:00:00.000
  const startTime = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() - diff,
    0,
    0,
    0,
    0,
  );

  // 设置结束时间为上周结束的23:59:59.999
  const endTime = new Date(
    startTime.getFullYear(),
    startTime.getMonth(),
    startTime.getDate() + 6,
    23,
    59,
    59,
    999,
  );

  return [startTime, endTime];
}

/**
 * 获取本月的日期范围
 *
 * @returns {[Date, Date]} 包含本月开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取本月的日期范围
 * const [startTime, endTime] = getCurrentMonthDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 输出类似：2023-05-01T00:00:00.000Z 2023-05-31T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getCurrentMonthDateRange();
 * console.log(`本月开始时间：${start.toLocaleString()}`);
 * console.log(`本月结束时间：${end.toLocaleString()}`);
 * // 输出类似：
 * // 本月开始时间：2023/5/1 00:00:00
 * // 本月结束时间：2023/5/31 23:59:59
 */
export function getCurrentMonthDateRange(): [Date, Date] {
  const now = new Date();

  // 设置开始时间为本月1日的00:00:00.000
  const startTime = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, 0);

  // 设置结束时间为下月1日的00:00:00.000，然后减去1毫秒
  const endTime = new Date(
    now.getFullYear(),
    now.getMonth() + 1,
    1,
    0,
    0,
    0,
    0,
  );
  endTime.setMilliseconds(-1);

  return [startTime, endTime];
}

/**
 * 获取上月的日期范围
 *
 * @returns {[Date, Date]} 包含上月开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取上月的日期范围
 * const [startTime, endTime] = getLastMonthDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 如果当前是2024年1月，输出类似：2023-12-01T00:00:00.000Z 2023-12-31T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getLastMonthDateRange();
 * console.log(`上月开始时间：${start.toLocaleString()}`);
 * console.log(`上月结束时间：${end.toLocaleString()}`);
 * // 如果当前是2024年1月，输出类似：
 * // 上月开始时间：2023/12/1 00:00:00
 * // 上月结束时间：2023/12/31 23:59:59
 */
export function getLastMonthDateRange(): [Date, Date] {
  const now = new Date();

  // 设置开始时间为上月1日的00:00:00.000
  const startTime = new Date(
    now.getFullYear(),
    now.getMonth() - 1,
    1,
    0,
    0,
    0,
    0,
  );

  // 设置结束时间为本月1日的00:00:00.000，然后减去1毫秒
  const endTime = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, -1);

  return [startTime, endTime];
}

/**
 * 获取本季度的日期范围
 *
 * @returns {[Date, Date]} 包含本季度开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取本季度的日期范围
 * const [startTime, endTime] = getCurrentQuarterDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 如果当前是2023年5月，输出类似：2023-04-01T00:00:00.000Z 2023-06-30T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getCurrentQuarterDateRange();
 * console.log(`本季度开始时间：${start.toLocaleString()}`);
 * console.log(`本季度结束时间：${end.toLocaleString()}`);
 * // 如果当前是2023年5月，输出类似：
 * // 本季度开始时间：2023/4/1 00:00:00
 * // 本季度结束时间：2023/6/30 23:59:59
 */
export function getCurrentQuarterDateRange(): [Date, Date] {
  const now = new Date();
  const currentMonth = now.getMonth();
  const currentYear = now.getFullYear();

  // 确定当前季度的开始月份
  const quarterStartMonth = Math.floor(currentMonth / 3) * 3;

  // 设置开始时间为本季度第一天的00:00:00.000
  const startTime = new Date(currentYear, quarterStartMonth, 1, 0, 0, 0, 0);

  // 设置结束时间为下一个季度第一天的00:00:00.000，然后减去1毫秒
  const endTime = new Date(currentYear, quarterStartMonth + 3, 1, 0, 0, 0, -1);

  return [startTime, endTime];
}

/**
 * 获取上季度的日期范围
 *
 * @returns {[Date, Date]} 包含上季度开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取上季度的日期范围
 * const [startTime, endTime] = getLastQuarterDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 如果当前是2024年2月（第一季度），输出类似：2023-10-01T00:00:00.000Z 2023-12-31T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getLastQuarterDateRange();
 * console.log(`上季度开始时间：${start.toLocaleString()}`);
 * console.log(`上季度结束时间：${end.toLocaleString()}`);
 * // 如果当前是2024年2月（第一季度），输出类似：
 * // 上季度开始时间：2023/10/1 00:00:00
 * // 上季度结束时间：2023/12/31 23:59:59
 */
export function getLastQuarterDateRange(): [Date, Date] {
  const now = new Date();
  const currentMonth = now.getMonth();
  const currentYear = now.getFullYear();

  let lastQuarterStartMonth: number;
  let lastQuarterStartYear: number;

  if (currentMonth < 3) {
    // 如果当前是第一季度（1-3月），上一季度是去年的第四季度
    lastQuarterStartMonth = 9; // 10月
    lastQuarterStartYear = currentYear - 1;
  } else {
    // 其他情况，上一季度在本年内
    lastQuarterStartMonth = Math.floor((currentMonth - 3) / 3) * 3;
    lastQuarterStartYear = currentYear;
  }

  // 设置开始时间为上季度第一天的00:00:00.000
  const startTime = new Date(
    lastQuarterStartYear,
    lastQuarterStartMonth,
    1,
    0,
    0,
    0,
    0,
  );

  // 设置结束时间为上季度最后一天的23:59:59.999
  const endTime = new Date(
    lastQuarterStartYear,
    lastQuarterStartMonth + 3,
    1,
    0,
    0,
    0,
    -1,
  );

  return [startTime, endTime];
}

/**
 * 获取今年的日期范围
 *
 * @returns {[Date, Date]} 包含今年开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取今年的日期范围
 * const [startTime, endTime] = getCurrentYearDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 如果当前是2023年，输出类似：2023-01-01T00:00:00.000Z 2023-12-31T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getCurrentYearDateRange();
 * console.log(`今年开始时间：${start.toLocaleString()}`);
 * console.log(`今年结束时间：${end.toLocaleString()}`);
 * // 如果当前是2023年，输出类似：
 * // 今年开始时间：2023/1/1 00:00:00
 * // 今年结束时间：2023/12/31 23:59:59
 */
export function getCurrentYearDateRange(): [Date, Date] {
  const now = new Date();
  const currentYear = now.getFullYear();

  // 设置开始时间为今年1月1日的00:00:00.000
  const startTime = new Date(currentYear, 0, 1, 0, 0, 0, 0);

  // 设置结束时间为今年12月31日的23:59:59.999
  const endTime = new Date(currentYear, 11, 31, 23, 59, 59, 999);

  return [startTime, endTime];
}

/**
 * 获取去年的日期范围
 *
 * @returns {[Date, Date]} 包含去年开始时间和结束时间的数组 [startTime, endTime]
 *          开始时间的时分秒为00:00:00，结束时间时分秒为23:59:59.999
 *
 * @example
 * // 获取去年的日期范围
 * const [startTime, endTime] = getLastYearDateRange();
 * console.log(startTime.toISOString(), endTime.toISOString());
 * // 如果当前是2023年，输出类似：2022-01-01T00:00:00.000Z 2022-12-31T23:59:59.999Z
 *
 * @example
 * // 使用解构赋值获取开始和结束时间，并格式化输出
 * const [start, end] = getLastYearDateRange();
 * console.log(`去年开始时间：${start.toLocaleString()}`);
 * console.log(`去年结束时间：${end.toLocaleString()}`);
 * // 如果当前是2023年，输出类似：
 * // 去年开始时间：2022/1/1 00:00:00
 * // 去年结束时间：2022/12/31 23:59:59
 */
export function getLastYearDateRange(): [Date, Date] {
  const now = new Date();
  const lastYear = now.getFullYear() - 1;

  // 设置开始时间为去年1月1日的00:00:00.000
  const startTime = new Date(lastYear, 0, 1, 0, 0, 0, 0);

  // 设置结束时间为去年12月31日的23:59:59.999
  const endTime = new Date(lastYear, 11, 31, 23, 59, 59, 999);

  return [startTime, endTime];
}

/**
 * 获取给定日期格式的当前日除去天的毫秒数
 *
 * @param {DateInput} input - 日期格式
 * @returns {number} 当前日除去天的毫秒数
 *
 * @example
 * // 获取当前日期时间的毫秒数（从午夜开始）
 * const ms = getHourMilliseconds();
 * console.log(ms);
 * // 输出类似：43200000 （如果当前时间是中午12点）
 */
export function getHourMilliseconds(input?: DateInput): number {
  // 将输入转换为 Date 对象
  const date = new Date(input ?? Date.now());
  const midnight = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
    0,
    0,
    0,
  );
  return date.getTime() - midnight.getTime();
}
