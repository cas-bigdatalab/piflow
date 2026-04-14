/**
 * 定义差异结果的类型
 */
export type DiffResult = {
  added: Array<{ key: string; value: any }>;
  deleted: Array<{ key: string; value: any }>;
  modified: Array<{ key: string; oldValue: any; newValue: any }>;
};

/**
 * 定义主键配置的类型
 */
export type KeyConfig = {
  [path: string]: (item: any) => string | number;
};

/**
 * 比较两个对象，返回它们之间的差异
 * @param {object} oldObj - 旧对象
 * @param {object} newObj - 新对象
 * @param {KeyConfig} keyConfig - 对象数组的主键配置
 * @param {boolean} detectArrayOrder - 是否检测数组顺序变化
 * @returns {DiffResult} 包含新增、删除和修改字段的对象，使用路径表示
 * @example
 * 使用示例
 *
 * // 基本类型比较
 * const oldObj = { a: 1, b: 'hello', c: true };
 * const newObj = { a: 2, b: 'hello', d: false };
 * const result = compareObjects(oldObj, newObj);
 * // result: {
 * //   added: [{ key: 'd', value: false }],
 * //   deleted: [{ key: 'c', value: true }],
 * //   modified: [{ key: 'a', oldValue: 1, newValue: 2 }]
 * // }
 *
 * // 嵌套对象比较
 * const oldObj = { a: { b: { c: 1 } } };
 * const newObj = { a: { b: { c: 2, d: 3 } } };
 * const result = compareObjects(oldObj, newObj);
 * // result: {
 * //   added: [{ key: 'a.b.d', value: 3 }],
 * //   deleted: [],
 * //   modified: [{ key: 'a.b.c', oldValue: 1, newValue: 2 }]
 * // }
 *
 * // 数组比较（检测顺序）
 * const oldObj = { arr: [1, 2, 3] };
 * const newObj = { arr: [3, 2, 1, 4] };
 * const result = compareObjects(oldObj, newObj, {}, true);
 * // result: {
 * //   added: [{ key: 'arr[3]', value: 4 }],
 * //   deleted: [],
 * //   modified: [
 * //     { key: 'arr[0]', oldValue: 1, newValue: 3 },
 * //     { key: 'arr[2]', oldValue: 3, newValue: 1 }
 * //   ]
 * // }
 *
 * // 对象数组比较（使用 keyConfig）
 * const oldObj = { users: [{ id: 1, name: '张三' }, { id: 2, name: '李四' }] };
 * const newObj = { users: [{ id: 1, name: '张三', age: 30 }, { id: 3, name: '王五' }] };
 * const keyConfig = { users: (item) => item.id };
 * const result = compareObjects(oldObj, newObj, keyConfig);
 * // result: {
 * //   added: [
 * //     { key: 'users[0].age', value: 30 },
 * //     { key: 'users[1]', value: { id: 3, name: '王五' } }
 * //   ],
 * //   deleted: [{ key: 'users[1]', value: { id: 2, name: '李四' } }],
 * //   modified: []
 * // }
 *
 * // 处理 undefined 和 null
 * const oldObj = { a: undefined, b: null, c: 1 };
 * const newObj = { a: null, b: undefined, d: 1 };
 * const result = compareObjects(oldObj, newObj);
 * // result: {
 * //   added: [{ key: 'd', value: 1 }],
 * //   deleted: [{ key: 'c', value: 1 }],
 * //   modified: [
 * //     { key: 'a', oldValue: undefined, newValue: null },
 * //     { key: 'b', oldValue: null, newValue: undefined }
 * //   ]
 * // }
 */
export function compareObjects(
  oldObj: object,
  newObj: object,
  keyConfig: KeyConfig = {},
  detectArrayOrder: boolean = false,
): DiffResult {
  const result: DiffResult = {
    added: [],
    deleted: [],
    modified: [],
  };

  const processedPaths = new Set<string>();

  /**
   * 递归比较函数
   * @param oldValue - 旧值
   * @param newValue - 新值
   * @param path - 当前路径
   */
  function compare(oldValue: any, newValue: any, path: string): void {
    if (processedPaths.has(path)) return;
    processedPaths.add(path);

    // 这两个值都是undefined或null
    if (oldValue === newValue) return;

    // 一个值是undefined或null，但不能两者都是
    if ((oldValue === void 0 || oldValue === null) && newValue !== void 0 && newValue !== null) {
      result.added.push({ key: path, value: newValue });
      return;
    }
    if ((newValue === void 0 || newValue === null) && oldValue !== void 0 && oldValue !== null) {
      result.deleted.push({ key: path, value: oldValue });
      return;
    }

    // 这两个值都undefined，不为null，但类型不同
    if (typeof oldValue !== typeof newValue) {
      result.modified.push({ key: path, oldValue, newValue });
      return;
    }

    // 两个值都是对象（包括数组）
    if (typeof oldValue === 'object' && typeof newValue === 'object') {
      if (Array.isArray(oldValue) && Array.isArray(newValue)) {
        compareArrays(oldValue, newValue, path);
      } else {
        const oldKeys = Object.keys(oldValue);
        const newKeys = Object.keys(newValue);

        for (const key of newKeys) {
          const newPath = path ? `${path}.${key}` : key;
          if (!(key in oldValue)) {
            result.added.push({ key: newPath, value: newValue[key] });
          } else {
            compare(oldValue[key], newValue[key], newPath);
          }
        }

        for (const key of oldKeys) {
          if (!(key in newValue)) {
            const newPath = path ? `${path}.${key}` : key;
            result.deleted.push({ key: newPath, value: oldValue[key] });
          }
        }
      }
      return;
    }

    // 这两个值具有相同的基本类型，但不相等
    if (oldValue !== newValue) {
      result.modified.push({ key: path, oldValue, newValue });
    }
  }

  /**
   * 比较数组函数
   * @param oldArray - 旧数组
   * @param newArray - 新数组
   * @param path - 当前路径
   */
  function compareArrays(oldArray: any[], newArray: any[], path: string): void {
    const getKey = keyConfig[path];

    if (getKey) {
      compareObjectArrays(oldArray, newArray, path, getKey);
    } else {
      if (detectArrayOrder) {
        compareOrderedArrays(oldArray, newArray, path);
      } else {
        compareUnorderedArrays(oldArray, newArray, path);
      }
    }
  }

  /**
   * 比较有序数组
   * @param oldArray - 旧数组
   * @param newArray - 新数组
   * @param path - 当前路径
   */
  function compareOrderedArrays(oldArray: any[], newArray: any[], path: string): void {
    const maxLength = Math.max(oldArray.length, newArray.length);
    for (let i = 0; i < maxLength; i++) {
      if (i >= oldArray.length) {
        result.added.push({ key: `${path}[${i}]`, value: newArray[i] });
      } else if (i >= newArray.length) {
        result.deleted.push({ key: `${path}[${i}]`, value: oldArray[i] });
      } else if (JSON.stringify(oldArray[i]) !== JSON.stringify(newArray[i])) {
        compare(oldArray[i], newArray[i], `${path}[${i}]`);
      }
    }
  }

  /**
   * 比较无序数组
   * @param oldArray - 旧数组
   * @param newArray - 新数组
   * @param path - 当前路径
   */
  function compareUnorderedArrays(oldArray: any[], newArray: any[], path: string): void {
    const oldSet = new Set(oldArray.map((it) => JSON.stringify(it)));
    const newSet = new Set(newArray.map((it) => JSON.stringify(it)));

    newArray.forEach((item, index) => {
      const stringifiedItem = JSON.stringify(item);
      if (!oldSet.has(stringifiedItem)) {
        result.added.push({ key: `${path}[${index}]`, value: item });
      }
    });

    oldArray.forEach((item, index) => {
      const stringifiedItem = JSON.stringify(item);
      if (!newSet.has(stringifiedItem)) {
        result.deleted.push({ key: `${path}[${index}]`, value: item });
      }
    });
  }

  /**
   * 比较对象数组
   * @param oldArray - 旧数组
   * @param newArray - 新数组
   * @param path - 当前路径
   * @param getKey - 获取对象主键的函数
   */
  function compareObjectArrays(
    oldArray: any[],
    newArray: any[],
    path: string,
    getKey: (item: any) => string | number,
  ): void {
    const oldMap = new Map(oldArray.map((item) => [getKey(item), item]));
    const newMap = new Map(newArray.map((item) => [getKey(item), item]));

    newArray.forEach((item, index) => {
      const key = getKey(item);
      if (!oldMap.has(key)) {
        result.added.push({ key: `${path}[${index}]`, value: item });
      } else {
        const oldItem = oldMap.get(key);
        compare(oldItem, item, `${path}[${index}]`);
      }
    });

    oldArray.forEach((item, index) => {
      const key = getKey(item);
      if (!newMap.has(key)) {
        result.deleted.push({ key: `${path}[${index}]`, value: item });
      }
    });
  }

  compare(oldObj, newObj, '');
  return result;
}
