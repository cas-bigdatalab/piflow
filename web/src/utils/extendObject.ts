export type Extender<T> = {
  [K in keyof T]?: T[K] | ((value: T[K]) => T[K]);
};

/**
 * 扩展对象的指定属性
 *
 * @template T - 对象类型
 * @param {T} obj T - 要扩展的对象
 * @param {Extender<T>} extender - 扩展规则
 * @returns {T} 扩展后的新对象
 *
 * @example
 * // 使用示例
 *
 * // 定义一个用户对象
 * const user = {
 *   name: 'Alice',
 *   age: 30,
 *   email: 'alice@example.com',
 *   settings: {
 *     notifications: true,
 *     theme: 'light'
 *   }
 * };
 *
 * // 定义扩展规则
 * const extender = {
 *   name: 'Bob',  // 直接替换值
 *   age: (age: number) => age + 1,  // 使用函数修改值
 *   email: (email: string) => email.toLowerCase(),  // 使用函数修改值
 *   settings: {  // 部分修改嵌套对象
 *     theme: 'dark'
 *   }
 * };
 *
 * // 扩展对象
 * const extendedUser = extendObject(user, extender);
 *
 * console.log(extendedUser);
 * // 输出:
 * // {
 * //   name: 'Bob',
 * //   age: 31,
 * //   email: 'alice@example.com',
 * //   settings: {
 * //     notifications: true,
 * //     theme: 'dark'
 * //   }
 * // }
 *
 * // 原对象保持不变
 * console.log(user);
 * // 输出:
 * // {
 * //   name: 'Alice',
 * //   age: 30,
 * //   email: 'alice@example.com',
 * //   settings: {
 * //     notifications: true,
 * //     theme: 'light'
 * //   }
 * // }
 */
export function extendObject<T extends object>(obj: T, extender: Extender<T>): T {
  const result = { ...obj };

  for (const key in extender) {
    if (Reflect.has(extender, key)) {
      const extenderValue = extender[key];
      if (typeof extenderValue === 'function') {
        result[key] = extenderValue(obj[key]);
      } else {
        result[key] = extenderValue as T[typeof key];
      }
    }
  }

  return result;
}
