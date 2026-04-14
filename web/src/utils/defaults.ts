import { deepClone } from './deepClone.ts';
import { isObject } from './typeof2.ts';

/**
 * 确保赋予默认值的属性在最终结果中一定存在
 */
type Defaults<T, U> = T & {
  [K in keyof U]: K extends keyof T ? (T[K] extends object ? Defaults<T[K], U[K]> : T[K]) : U[K];
};

function isPlainObject(value: unknown): value is Record<string, any> {
  if (!isObject(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === null || prototype === Object.prototype;
}

/**
 * 将默认值应用到给定对象，包括深层嵌套对象
 *
 * @template T 目标对象的类型
 * @template U 默认值对象的类型
 * @param {T} object 要应用默认值的对象
 * @param {U} sources 包含默认值的对象
 * @returns {Defaults<T, U>} 合并后的新对象，确保默认值属性一定存在
 *
 * @example
 * // 基本用法
 * defaults({ a: 1 }, { a: 0, b: 0 });
 * // 返回: { a: 1, b: 0 }
 *
 * @example
 * // 使用 undefined 值
 * defaults({ a: undefined, b: 2 }, { a: 0, b: 0, c: 0 });
 * // 返回: { a: 0, b: 2, c: 0 }
 *
 * @example
 * // 深层对象
 * defaults({ user: { name: 'John' } }, { user: { name: 'Guest', age: 18 }, settings: { theme: 'dark' } });
 * // 返回: { user: { name: 'John', age: 18 }, settings: { theme: 'dark' } }
 *
 * @example
 * // 数组处理
 * defaults({ fruits: ['apple'] }, { fruits: ['banana', 'orange'], vegetables: ['carrot'] });
 * // 返回: { fruits: ['apple'], vegetables: ['carrot'] }
 */
export function defaults<T = Record<string, any>, U = Record<string, any>>(
  object?: T,
  ...sources: U[]
): Defaults<T, U> {
  object = object || ({} as T);

  function merge(target: any, source: any): any {
    const result = deepClone(target);

    Object.keys(source).forEach((key) => {
      const srcValue = source[key];
      if (isPlainObject(srcValue) && isPlainObject(result[key])) {
        result[key] = merge(result[key], srcValue);
      } else if (result[key] === void 0) {
        result[key] = deepClone(srcValue);
      }
    });

    return result;
  }

  return sources.reduce(
    (acc, source) => {
      return source !== null ? merge(acc, source) : acc;
    },
    deepClone(object as any),
  ) as Defaults<T, U>;
}
