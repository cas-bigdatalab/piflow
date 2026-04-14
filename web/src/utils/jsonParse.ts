/**
 * 安全地解析 JSON 字符串
 *
 * @template T - 解析后的对象类型
 * @param {string} jsonString - 要解析的 JSON 字符串
 * @param {T} defaultValue - 解析失败时返回的默认值
 * @returns {T} 解析后的对象或默认值
 *
 * @example
 * // 使用示例
 *
 * // 1. 解析有效的 JSON 字符串
 * const validJson = '{"name": "Alice", "age": 30, "city": "New York"}';
 * const parsedValidJson = jsonParse(validJson, {});
 * console.log(parsedValidJson);
 * // 输出: { name: "Alice", age: 30, city: "New York" }
 *
 * // 2. 解析无效的 JSON 字符串，使用默认值
 * const invalidJson = '{"name": "Bob", "age": 25,}'; // 注意多余的逗号
 * const parsedInvalidJson = jsonParse(invalidJson, { name: "Unknown", age: 0, city: "Unknown" });
 * console.log(parsedInvalidJson);
 * // 输出: { name: "Unknown", age: 0, city: "Unknown" }
 * // 控制台会输出错误信息：JSON parsing failed: SyntaxError: Unexpected token } in JSON at position 26
 *
 * // 3. 使用特定类型
 * interface User {
 *   name: string;
 *   age: number;
 *   email?: string;
 * }
 *
 * const userJson = '{"name": "Charlie", "age": 35, "email": "charlie@example.com"}';
 * const defaultUser: User = { name: "Unknown", age: 0 };
 * const parsedUser = jsonParse<User>(userJson, defaultUser);
 * console.log(parsedUser);
 * // 输出: { name: "Charlie", age: 35, email: "charlie@example.com" }
 *
 * // 4. 解析数组
 * const arrayJson = '[1, 2, 3, 4, 5]';
 * const parsedArray = jsonParse<number[]>(arrayJson, []);
 * console.log(parsedArray);
 * // 输出: [1, 2, 3, 4, 5]
 *
 * // 5. 解析嵌套对象
 * const nestedJson = '{"person": {"name": "David", "age": 40}, "hobbies": ["reading", "cycling"]}';
 * const parsedNested = jsonParse(nestedJson, {});
 * console.log(parsedNested);
 * // 输出: { person: { name: "David", age: 40 }, hobbies: ["reading", "cycling"] }
 */
export function jsonParse<T>(jsonString: string, defaultValue: T): T {
  try {
    const result = JSON.parse(jsonString);
    return result as T;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('JSON parsing failed:', error);
    return defaultValue;
  }
}
