/**
 * 创建一个节流函数
 *
 * @template T - 函数类型
 * @param {T} func - 要节流的函数
 * @param {number} wait - 节流时间间隔（毫秒）
 * @returns {(...args: Parameters<T>) => void} 节流后的函数
 */
export function throttle<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void {
  let previous = 0;

  return function (this: ThisParameterType<T>, ...args: Parameters<T>): void {
    const now = Date.now();
    const remaining = wait - (now - previous);

    if (remaining <= 0 || remaining > wait) {
      previous = now;
      func.apply(this, args);
    }
  };
}
