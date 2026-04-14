/**
 * 数据大小单位枚举
 */
enum DataSizeUnit {
  B = 'B',
  KB = 'KB',
  MB = 'MB',
  GB = 'GB',
  TB = 'TB',
  PB = 'PB',
  EB = 'EB',
  ZB = 'ZB',
  YB = 'YB',
}

/**
 * 格式化数据大小，将字节数转换为更易读的格式
 *
 * @param {number} bytes - 要格式化的字节数
 * @param {number} decimals - 小数点后的位数，默认为 2
 * @param {DataSizeUnit} targetUnit - 目标单位，如果指定，将强制使用此单位
 * @returns {string} 格式化后的字符串
 *
 * @example
 * // 自动选择合适的单位
 * console.log(formatDataSize(1536));
 * // 输出: 1.50 KB
 *
 * @example
 * // 指定格式化至 MB
 * console.log(formatDataSize(1536, 2, DataSizeUnit.MB));
 * // 输出: 0.00 MB
 *
 * @example
 * // 格式化大数据，指定单位为 GB
 * console.log(formatDataSize(1073741824, 2, DataSizeUnit.GB));
 * // 输出: 1.00 GB
 *
 * @example
 * // 使用 3 位小数
 * console.log(formatDataSize(1073741824, 3, DataSizeUnit.GB));
 * // 输出: 1.000 GB
 */
export function formatDataSize(bytes: number, decimals: number = 2, targetUnit?: DataSizeUnit): string {
  if (bytes === 0 || !bytes) return '0 B';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = Object.values(DataSizeUnit);

  let i = targetUnit ? sizes.indexOf(targetUnit) : Math.floor(Math.log(bytes) / Math.log(k));

  // 如果指定了目标单位，但字节数太大，我们仍然使用自动选择的单位
  if (targetUnit && bytes >= Math.pow(k, sizes.length)) {
    i = Math.floor(Math.log(bytes) / Math.log(k));
  }

  const convertedValue = bytes / Math.pow(k, i);
  return `${convertedValue.toFixed(dm)} ${sizes[i]}`;
}

type formatByteDataValue = {
  data: string,
  unit: string
}

export function formatByteData(bytes: number, decimals: number = 2, targetUnit?: DataSizeUnit): formatByteDataValue {
  if (bytes === 0) return {
    data: '0',
    unit: 'B'
  };

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = Object.values(DataSizeUnit);

  let i = targetUnit ? sizes.indexOf(targetUnit) : Math.floor(Math.log(bytes) / Math.log(k));
  const convertedValue = bytes / Math.pow(k, i);
  return {
    data: convertedValue.toFixed(dm),
    unit: sizes[i]
  }
}
