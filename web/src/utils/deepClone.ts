type DeepCloneable = { [key: string]: any } | any[] | Date | RegExp | null | undefined;

/**
 * 深拷贝函数，可以处理循环引用的对象
 *
 * @template T - 要深拷贝的对象类型
 * @param {T} obj - 要深拷贝的对象
 * @returns {T} 深拷贝后的对象
 */
export function deepClone<T extends DeepCloneable>(obj: T): T {
  const cloneInternal = (value: any, visited = new WeakMap<object, any>()): any => {
    // 处理基本类型和 null
    if (value === null || typeof value !== 'object') {
      return value;
    }

    // 处理已访问过的对象（循环引用）
    if (visited.has(value)) {
      return visited.get(value);
    }

    // 处理日期对象
    if (value instanceof Date) {
      return new Date(value.getTime());
    }

    // 处理正则表达式
    if (value instanceof RegExp) {
      return new RegExp(value.source, value.flags);
    }

    // 创建新的数组或对象
    const clonedValue: any = Array.isArray(value) ? [] : {};

    // 将新对象添加到已访问的 Map 中
    visited.set(value, clonedValue);

    // 递归克隆所有属性
    Object.entries(value).forEach(([key, val]) => {
      clonedValue[key] = cloneInternal(val, visited);
    });

    return clonedValue;
  };

  return cloneInternal(obj);
}
