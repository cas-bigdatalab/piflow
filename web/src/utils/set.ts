type NestedObject = { [key: string]: any };

/**
 * 在嵌套对象或数组中设置值
 *
 * @param {NestedObject} obj - 要修改的对象。
 * @param {string} path - 要设置的属性的路径，使用点号表示法或方括号表示法。
 *               例如: 'a.b.c' 或 'a[0].b.c'。
 * @param {any} value - 要设置的值。
 * @returns {NestedObject} 修改后的对象。
 *
 * @throws {Error} 当尝试在数组上设置对象属性时抛出错误。
 *
 * @example
 * // 设置嵌套对象属性
 * set({}, 'a.b.c', 1) // 返回 { a: { b: { c: 1 } } }
 *
 * @example
 * // 设置嵌套数组元素
 * set({}, 'a[0].b.c', 2) // 返回 { a: [{ b: { c: 2 } }] }
 *
 * @example
 * // 混合对象和数组
 * const obj = {};
 * set(obj, 'x.y[0].z', 3);
 * set(obj, 'x.y[1].w', 4);
 * // obj 现在是 { x: { y: [{ z: 3 }, { w: 4 }] } }
 */
export function set(obj: NestedObject, path: string, value: any): NestedObject {
  const keys = path.match(/[^.[\]]+/g) || [];
  let current: NestedObject = obj;

  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    const nextKey = keys[i + 1];
    const isNextKeyArrayIndex = /^\d+$/.test(nextKey);

    if (!(key in current)) {
      current[key] = isNextKeyArrayIndex ? [] : {};
    }

    if (Array.isArray(current[key]) && !isNextKeyArrayIndex) {
      throw new Error(`Cannot set object property '${nextKey}' on array at path '${keys.slice(0, i + 1).join('.')}'`);
    }

    if (!Array.isArray(current[key]) && isNextKeyArrayIndex) {
      current[key] = [];
    }

    current = current[key];
  }

  const lastKey = keys[keys.length - 1];
  current[lastKey] = value;

  return obj;
}
