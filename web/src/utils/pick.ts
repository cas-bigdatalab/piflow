/**
 * 从对象中选取指定的字段并返回一个新的对象
 *
 * @template T - 源对象的类型
 * @template K - 要选取的字段的类型
 * @param {T} obj - 源对象
 * @param {K[]} keys - 要选取的字段数组
 * @returns {Pick<T, K>} 包含选取字段的新对象
 *
 * @example
 * // 基本用法
 * const obj = { a: 1, b: 2, c: 3 };
 * pick(obj, ['a', 'c']); // 返回: { a: 1, c: 3 }
 *
 * @example
 * // 使用接口
 * interface Person {
 *   name: string;
 *   age: number;
 *   address: string;
 * }
 * const person: Person = { name: 'Alice', age: 30, address: '123 Main St' };
 * pick(person, ['name', 'age']); // 返回: { name: 'Alice', age: 30 }
 *
 * @example
 * // 处理不存在的键
 * pick(obj, ['a', 'd']); // 返回: { a: 1 }
 */
export function pick<T extends object, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
  return keys.reduce(
    (result, key) => {
      if (key in obj) {
        result[key] = obj[key];
      }
      return result;
    },
    {} as Pick<T, K>,
  );
}
