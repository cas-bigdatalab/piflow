/**
 * 安全地将 JavaScript 对象转换为 JSON 字符串
 *
 * @template T - 要转换的对象类型
 * @param {T} value - 要转换为 JSON 字符串的值
 * @param {string} defaultValue - 转换失败时返回的默认字符串
 * @returns {string} JSON 字符串或默认值
 *
 * @example
 *
 * // 1. 转换简单对象
 * const simpleObject = { name: "Alice", age: 30, city: "New York" };
 * const stringifiedSimple = jsonStringify(simpleObject, "{}");
 * console.log(stringifiedSimple);
 * // 输出: '{"name":"Alice","age":30,"city":"New York"}'
 *
 * // 2. 转换包含循环引用的对象（会失败并返回默认值）
 * const circularObject: any = { name: "Bob" };
 * circularObject.self = circularObject;
 * const stringifiedCircular = jsonStringify(circularObject, '{"error":"Circular reference"}');
 * console.log(stringifiedCircular);
 * // 输出: '{"error":"Circular reference"}'
 * // 控制台会输出错误信息：JSON stringification failed: TypeError: Converting circular structure to JSON
 *
 * // 3. 转换数组
 * const array = [1, 2, 3, 4, 5];
 * const stringifiedArray = jsonStringify(array, "[]");
 * console.log(stringifiedArray);
 * // 输出: '[1,2,3,4,5]'
 *
 * // 4. 转换嵌套对象
 * const nestedObject = {
 *   person: { name: "David", age: 40 },
 *   hobbies: ["reading", "cycling"]
 * };
 * const stringifiedNested = jsonStringify(nestedObject, "{}");
 * console.log(stringifiedNested);
 * // 输出: '{"person":{"name":"David","age":40},"hobbies":["reading","cycling"]}'
 *
 * // 5. 转换包含特殊值的对象
 * const specialObject = {
 *   nullValue: null,
 *   undefinedValue: undefined,
 *   date: new Date("2023-05-20T12:00:00Z"),
 *   regex: /test/g
 * };
 * const stringifiedSpecial = jsonStringify(specialObject, "{}");
 * console.log(stringifiedSpecial);
 * // 输出类似: '{"nullValue":null,"date":"2023-05-20T12:00:00.000Z","regex":{}}'
 * // 注意：undefined 值和函数会被忽略，正则表达式会被转换为空对象
 */
export function jsonStringify<T>(value: T, defaultValue: string): string {
  try {
    const result = JSON.stringify(value, (key, val) => {
      if (val !== val) {
        // 处理 NaN
        return 'NaN';
      }
      if (typeof val === 'number' && !isFinite(val)) {
        // 处理 Infinity 和 -Infinity
        return val.toString();
      }
      return val;
    });

    if (result === void 0) {
      // 处理 JSON.stringify 返回 undefined 的情况（例如，当值为 undefined 或函数时）
      return defaultValue;
    }

    return result;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('JSON stringification failed:', error);
    return defaultValue;
  }
}
