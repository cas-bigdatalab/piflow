/**
 * 安全地获取对象的嵌套属性值
 *
 * @template T - 对象类型
 * @param {T} obj - 要查询的对象
 * @param {string | (string | number)[]} path - 属性路径，可以是字符串（用点号或方括号分隔）或字符串数组
 * @param {T} defaultValue - 如果路径不存在，返回的默认值
 * @param {T} emptyValue - 如果路径存在但值为这些值之一，返回默认值
 * @returns {T} 找到的值或默认值
 *
 * @example
 * const obj = { a: { b: { c: 3 } }, d: [{ e: 5 }] };
 * get(obj, 'a.b.c');  // 返回: 3
 * get(obj, 'a.b.c.d', 'default');  // 返回: 'default'
 * get(obj, 'd[0].e');  // 返回: 5
 * get(obj, ['d', '0', 'e']);  // 返回: 5
 */
export function get<T>(obj: any, path: string | (string | number)[], defaultValue?: T, emptyValue = [void 0, null]): T {
  const normalizedPath = normalizePath(path);
  const result = getValueByPath(obj, normalizedPath);
  return (emptyValue.includes(result) ? defaultValue : result) as T;
}

/**
 * 将路径字符串转换为路径数组
 * @param path 路径字符串或数组
 * @returns 路径数组
 */
function normalizePath(path: string | (string | number)[]): (string | number)[] {
  if (Array.isArray(path)) {
    return path;
  }

  // 处理混合语法（点号、方括号、混合）
  return path
    .replace(/(\w+)$$(\d+)$$/g, (_, key, index) => {
      if (index) return `${key}[${index}]`;
      return key;
    })
    .split(/[[\].]+/) // 分割任意分隔符
    .filter((part) => part !== ''); // 移除空字符串
}

/**
 * 从对象中获取指定路径的值
 * @param obj 要查询的对象
 * @param path 属性路径数组
 * @returns 找到的值或 undefined
 */
function getValueByPath(obj: any, path: (string | number)[]): any {
  let current = obj;
  for (const key of path) {
    if (current === null || current === void 0) {
      return void 0;
    }
    current = current[key];
  }
  return current;
}
