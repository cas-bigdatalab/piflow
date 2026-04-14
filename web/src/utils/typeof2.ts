/**
 * 判定准确的数据类型并实现类型收窄
 * @param {unknown} value - 要判定类型的值
 * @returns 数据类型的字符串表示
 *
 * @example
 * // 基本类型
 * typeof2(42);  // 返回: "number"
 * typeof2("hello");  // 返回: "string"
 * typeof2(true);  // 返回: "boolean"
 *
 * @example
 * // 特殊类型
 * typeof2(null);  // 返回: "null"
 * typeof2(undefined);  // 返回: "undefined"
 * typeof2(Symbol("sym"));  // 返回: "symbol"
 *
 * @example
 * // 对象类型
 * typeof2({});  // 返回: "object"
 * typeof2([]);  // 返回: "array"
 * typeof2(new Date());  // 返回: "date"
 * typeof2(/regex/);  // 返回: "regexp"
 *
 * @example
 * // 函数
 * typeof2(function() {});  // 返回: "function"
 * typeof2(() => {});  // 返回: "function"
 * typeof2(async function() {});  // 返回: "asyncfunction"
 *
 * @example
 * // 特殊数字
 * typeof2(NaN);  // 返回: "nan"
 * typeof2(Infinity);  // 返回: "infinity"
 *
 * @example
 * // 类型收窄
 * const value: unknown = [1, 2, 3];
 * if (typeof2(value) === "array") {
 *   // 在这个块中，TypeScript 知道 value 是一个数组
 *   console.log(value.length);
 * }
 */
export function typeof2(value: unknown): string {
  if (value === null) return 'null';
  if (value === void 0) return 'undefined';
  if (typeof value === 'number') {
    if (Number.isNaN(value)) return 'nan';
    if (!Number.isFinite(value)) return 'infinity';
  }

  const type = Object.prototype.toString.call(value).slice(8, -1).toLowerCase();

  switch (type) {
    case 'number':
    case 'string':
    case 'boolean':
    case 'symbol':
    case 'bigint':
      return type;
    case 'function':
      return value.constructor.name === 'AsyncFunction' ? 'asyncfunction' : 'function';
    case 'array':
      return 'array';
    case 'date':
      return 'date';
    case 'regexp':
      return 'regexp';
    case 'map':
      return 'map';
    case 'set':
      return 'set';
    case 'weakmap':
      return 'weakmap';
    case 'weakset':
      return 'weakset';
    default:
      if (typeof value === 'object' && value instanceof Error) {
        return 'error';
      }
      if (typeof window !== 'undefined' && value instanceof Element) {
        return 'element';
      }
      return 'object';
  }
}

// 类型谓词函数
// ... (保留原有的 typeof2 函数及其注释)

/**
 * 判断值是否为数字类型
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是数字类型则返回 true，否则返回 false
 *
 * @example
 * console.log(isNumber(42)); // 输出: true
 * console.log(isNumber('42')); // 输出: false
 * console.log(isNumber(NaN)); // 输出: true
 *
 * const value: unknown = 3.14;
 * if (isNumber(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个数字
 *   console.log(value.toFixed(2));
 * }
 */
export function isNumber(value: unknown): value is number {
  return typeof2(value) === 'number';
}

/**
 * 判断值是否为字符串类型
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是字符串类型则返回 true，否则返回 false
 *
 * @example
 * console.log(isString('hello')); // 输出: true
 * console.log(isString(42)); // 输出: false
 *
 * const value: unknown = 'TypeScript';
 * if (isString(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个字符串
 *   console.log(value.toUpperCase());
 * }
 */
export function isString(value: unknown): value is string {
  return typeof2(value) === 'string';
}

/**
 * 判断值是否为布尔类型
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是布尔类型则返回 true，否则返回 false
 *
 * @example
 * console.log(isBoolean(true)); // 输出: true
 * console.log(isBoolean(false)); // 输出: true
 * console.log(isBoolean('true')); // 输出: false
 *
 * const value: unknown = false;
 * if (isBoolean(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个布尔值
 *   console.log(value ? 'Yes' : 'No');
 * }
 */
export function isBoolean(value: unknown): value is boolean {
  return typeof2(value) === 'boolean';
}

/**
 * 判断值是否为 null
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 null 则返回 true，否则返回 false
 *
 * @example
 * console.log(isNull(null)); // 输出: true
 * console.log(isNull(undefined)); // 输出: false
 * console.log(isNull(0)); // 输出: false
 *
 * const value: unknown = null;
 * if (isNull(value)) {
 *   console.log('Value is null');
 * } else {
 *   console.log('Value is not null');
 * }
 */
export function isNull(value: unknown): value is null {
  return typeof2(value) === 'null';
}

/**
 * 判断值是否为 undefined
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 undefined 则返回 true，否则返回 false
 *
 * @example
 * console.log(isUndefined(undefined)); // 输出: true
 * console.log(isUndefined(null)); // 输出: false
 * console.log(isUndefined(void 0)); // 输出: true
 *
 * let value: unknown;
 * if (isUndefined(value)) {
 *   console.log('Value is undefined');
 * } else {
 *   console.log('Value is defined');
 * }
 */
export function isUndefined(value: unknown): value is undefined {
  return typeof2(value) === 'undefined';
}

/**
 * 判断值是否为 Error 对象
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 Error 对象则返回 true，否则返回 false
 *
 * @example
 * console.log(isError(new Error('Test error'))); // 输出: true
 * console.log(isError(new TypeError('Type error'))); // 输出: true
 * console.log(isError({ message: 'Not an error' })); // 输出: false
 *
 * const value: unknown = new Error('Something went wrong');
 * if (isError(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个 Error 对象
 *   console.log(value.message);
 * }
 */
export function isError(value: unknown): value is Error {
  return typeof2(value) === 'error';
}

/**
 * 判断值是否为 Symbol 类型
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 Symbol 类型则返回 true，否则返回 false
 *
 * @example
 * console.log(isSymbol(Symbol('test'))); // 输出: true
 * console.log(isSymbol(Symbol.for('test'))); // 输出: true
 * console.log(isSymbol('symbol')); // 输出: false
 *
 * const value: unknown = Symbol('unique');
 * if (isSymbol(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个 Symbol
 *   console.log(value.description);
 * }
 */
export function isSymbol(value: unknown): value is symbol {
  return typeof2(value) === 'symbol';
}

/**
 * 判断值是否为 BigInt 类型
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 BigInt 类型则返回 true，否则返回 false
 *
 * @example
 * console.log(isBigInt(BigInt(9007199254740991))); // 输出: true
 * console.log(isBigInt(1234567890123456789n)); // 输出: true
 * console.log(isBigInt(123)); // 输出: false
 *
 * const value: unknown = BigInt(Number.MAX_SAFE_INTEGER) + BigInt(1);
 * if (isBigInt(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个 BigInt
 *   console.log(value.toString());
 * }
 */
export function isBigInt(value: unknown): value is bigint {
  return typeof2(value) === 'bigint';
}

/**
 * 判断值是否为正则表达式对象
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是正则表达式对象则返回 true，否则返回 false
 *
 * @example
 * console.log(isRegExp(/test/)); // 输出: true
 * console.log(isRegExp(new RegExp('test'))); // 输出: true
 * console.log(isRegExp('/test/')); // 输出: false
 *
 * const value: unknown = /^[a-z]+$/i;
 * if (isRegExp(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个正则表达式对象
 *   console.log(value.test('Hello'));
 * }
 */
export function isRegExp(value: unknown): value is RegExp {
  return typeof2(value) === 'regexp';
}

/**
 * 判断值是否为数组
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是数组则返回 true，否则返回 false
 *
 * @example
 * console.log(isArray([1, 2, 3])); // 输出: true
 * console.log(isArray(new Array(3))); // 输出: true
 * console.log(isArray({ length: 3 })); // 输出: false
 *
 * const value: unknown = ['a', 'b', 'c'];
 * if (isArray(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个数组
 *   console.log(value.length);
 * }
 */
export function isArray(value: unknown): value is unknown[] {
  return typeof2(value) === 'array';
}

/**
 * 判断值是否为对象（不包括数组和 null）
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是对象则返回 true，否则返回 false
 *
 * @example
 * console.log(isObject({})); // 输出: true
 * console.log(isObject(new Object())); // 输出: true
 * console.log(isObject(null)); // 输出: false
 * console.log(isObject([])); // 输出: false
 *
 * const value: unknown = { name: 'John', age: 30 };
 * if (isObject(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个对象
 *   console.log(Object.keys(value));
 * }
 */
export function isObject(value: unknown): value is Record<string, any> {
  return typeof2(value) === 'object';
}

/**
 * 判断值是否为 Date 对象
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 Date 对象则返回 true，否则返回 false
 *
 * @example
 * console.log(isDate(new Date())); // 输出: true
 * console.log(isDate(Date.now())); // 输出: false
 * console.log(isDate('2023-05-17')); // 输出: false
 *
 * const value: unknown = new Date('2023-05-17');
 * if (isDate(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个 Date 对象
 *   console.log(value.toISOString());
 * }
 */
export function isDate(value: unknown): value is Date {
  return typeof2(value) === 'date';
}

/**
 * 判断值是否为异步函数
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是异步函数则返回 true，否则返回 false
 *
 * @example
 * console.log(isAsyncFunction(async function() {})); // 输出: true
 * console.log(isAsyncFunction(async () => {})); // 输出: true
 * console.log(isAsyncFunction(function() {})); // 输出: false
 *
 * const value: unknown = async () => { await Promise.resolve(); };
 * if (isAsyncFunction(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个异步函数
 *   value().then(() => console.log('Async function completed'));
 * }
 */
export function isAsyncFunction(value: unknown): value is (...args: any[]) => Promise<unknown> {
  return typeof2(value) === 'asyncfunction';
}

/**
 * 判断值是否为函数（包括异步函数）
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是函数则返回 true，否则返回 false
 *
 * @example
 * console.log(isFunction(function() {})); // 输出: true
 * console.log(isFunction(() => {})); // 输出: true
 * console.log(isFunction(async () => {})); // 输出: true
 * console.log(isFunction(class {})); // 输出: true
 * console.log(isFunction({})); // 输出: false
 *
 * const value: unknown = (x: number, y: number) => x + y;
 * if (isFunction(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个函数
 *   console.log(value(2, 3));
 * }
 */
export function isFunction(value: unknown): value is (...args: any[]) => unknown {
  return typeof2(value) === 'function' || typeof2(value) === 'asyncfunction';
}

/**
 * 判断值是否为 DOM 元素
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 DOM 元素则返回 true，否则返回 false
 *
 * @example
 * // 在浏览器环境中：
 * console.log(isElement(document.body)); // 输出: true
 * console.log(isElement(document.createElement('div'))); // 输出: true
 * console.log(isElement({})); // 输出: false
 *
 * const value: unknown = document.getElementById('myElement');
 * if (isElement(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个 DOM 元素
 *   console.log(value.tagName);
 * }
 */
export function isElement(value: unknown): value is Element {
  return typeof2(value) === 'element';
}

/**
 * 判断值是否为 Map 对象
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 Map 对象则返回 true，否则返回 false
 *
 * @example
 * console.log(isMap(new Map())); // 输出: true
 * console.log(isMap(new WeakMap())); // 输出: false
 * console.log(isMap({})); // 输出: false
 *
 * const value: unknown = new Map([['key', 'value']]);
 * if (isMap(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个 Map 对象
 *   console.log(value.get('key'));
 * }
 */
export function isMap(value: unknown): value is Map<unknown, unknown> {
  return typeof2(value) === 'map';
}

/**
 * 判断值是否为 Set 对象
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是 Set 对象则返回 true，否则返回 false
 *
 * @example
 * console.log(isSet(new Set())); // 输出: true
 * console.log(isSet(new WeakSet())); // 输出: false
 * console.log(isSet([])); // 输出: false
 *
 * const value: unknown = new Set([1, 2, 3]);
 * if (isSet(value)) {
 *   // 在这个块中，TypeScript 知道 value 是一个 Set 对象
 *   console.log(value.has(2));
 * }
 */
export function isSet(value: unknown): value is Set<unknown> {
  return typeof2(value) === 'set';
}

/**
 * 判断值是否为有效的 Date 对象
 * @param {unknown} value - 要判断的值
 * @returns {boolean} - 如果值是有效的 Date 对象则返回 true，否则返回 false
 *
 * @example
 * console.log(isValidDate(new Date())); // 输出: true
 * console.log(isValidDate(new Date('2023-05-17'))); // 输出: true
 * console.log(isValidDate(new Date('invalid date'))); // 输出: false
 * console.log(isValidDate('2023-05-17')); // 输出: true
 * console.log(isValidDate('invalid date')); // 输出: false
 *
 * const value: unknown = '2023-05-17T12:00:00Z';
 * if (isValidDate(value)) {
 *   // 在这个块中，TypeScript 知道 value 可以被转换为有效的 Date 对象
 *   const date = new Date(value);
 *   console.log(date.toISOString());
 * }
 */
export function isValidDate(value: unknown): value is Date {
  const date = new Date(value as any);
  return isDate(date) && !isNaN(date.getTime());
}
