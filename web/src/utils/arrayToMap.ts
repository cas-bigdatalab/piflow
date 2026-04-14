/**
 * 将对象数组转换为Map，使用指定的属性作为键
 *
 * @template T - 数组元素的类型
 * @template K - 用作Map键的属性类型
 * @param {T} arr - 要转换的对象数组
 * @param {K} key - 用作Map键的属性名
 * @returns {Map<T[K], T>} 转换后的Map
 *
 * @example
 * const users = [
 *   { id: 1, name: 'Alice', age: 30 },
 *   { id: 2, name: 'Bob', age: 25 },
 *   { id: 3, name: 'Charlie', age: 35 }
 * ];
 *
 * const userMap = arrayToMap(users, 'id');
 * console.log(userMap.get(2)); // 输出: { id: 2, name: 'Bob', age: 25 }
 *
 * // 使用不同的键
 * const userMapByName = arrayToMap(users, 'name');
 * console.log(userMapByName.get('Alice')); // 输出: { id: 1, name: 'Alice', age: 30 }
 */
export function arrayToMap<T extends object, K extends keyof T>(arr: T[], key: K): Map<T[K], T> {
  return arr.reduce((map, obj) => {
    const mapKey = obj[key];
    if (mapKey !== void 0 && mapKey !== null) {
      map.set(mapKey, obj);
    }
    return map;
  }, new Map<T[K], T>());
}
