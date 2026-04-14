type DeepMerge<T, U> = T extends object
  ? U extends object
    ? {
        [K in keyof T | keyof U]: K extends keyof T
          ? K extends keyof U
            ? DeepMerge<T[K], U[K]>
            : T[K]
          : K extends keyof U
            ? U[K]
            : never;
      }
    : U
  : U;

/**
 * 深度合并两个对象
 *
 * @template T - 对象的类型，必须是 Record<string, any> 的子类型
 * @param {T} obj1 - 要合并的第一个对象
 * @param {T} obj2 - 要合并的第二个对象
 * @returns {T} 合并后的新对象
 *
 * @example
 * const obj1 = { a: 1, b: { c: 2 } };
 * const obj2 = { b: { d: 3 }, e: 4 };
 * const mergedObj = deepMerge(obj1, obj2);
 * // mergedObj 现在是 { a: 1, b: { c: 2, d: 3 }, e: 4 }
 */
export function deepMerge<T extends object, U extends object>(obj1: T, obj2: U): DeepMerge<T, U> {
  const result: any = { ...obj1 };

  // 遍历 obj2 中的每个键
  for (const key in obj2) {
    if (Reflect.has(obj2, key)) {
      if (obj2[key] instanceof Date || Array.isArray(obj2[key])) {
        result[key] = obj2[key];
      } else if (typeof obj2[key] === 'object' && obj2[key] !== null) {
        // 如果 result 对象中已经存在相同的键，并且该键对应的值也是一个对象
        if (typeof result[key] === 'object' && result[key] !== null) {
          // 递归调用 deepMerge 函数，将 result 中的对应对象与 obj2 中的对应对象进行深度合并
          result[key] = deepMerge(result[key], obj2[key]);
        }
        // 如果 result 对象中不存在相同的键，或者该键对应的值不是一个对象
        else {
          // 将 obj2 中的嵌套对象合并到 result 中，使用空对象作为初始值
          result[key] = deepMerge({}, obj2[key]);
        }
      }
      // 如果 obj2 的键对应的值不是一个对象（即它是一个基本类型值）
      else {
        result[key] = obj2[key];
      }
    }
  }

  // 返回合并后的新对象
  return result;
}
