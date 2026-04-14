export type Formatter<T, R> = {
  [K in keyof R]: ((obj: T) => R[K]) | keyof T;
};

/**
 * 格式化对象
 *
 * @template T - 源对象类型
 * @template R - 目标对象类型
 * @param {T} obj - 要格式化的对象
 * @param {Formatter<T, R>} format - 格式化规则
 * @returns {R} 格式化后的新对象
 *
 * @example
 * // 基本用法
 * const user = { name: 'John Doe', age: 30, email: 'john@example.com' };
 * const format = {
 *   fullName: 'name',
 *   userAge: 'age',
 *   contact: (u) => u.email
 * };
 * const result = formatObject(user, format);
 * // 结果: { fullName: 'John Doe', userAge: 30, contact: 'john@example.com' }
 *
 * @example
 * // 使用函数进行复杂转换
 * const product = { name: 'Laptop', price: 1000, inStock: true };
 * const format = {
 *   productName: 'name',
 *   formattedPrice: (p) => `$${p.price.toFixed(2)}`,
 *   availability: (p) => p.inStock ? 'In Stock' : 'Out of Stock'
 * };
 * const result = formatObject(product, format);
 * // 结果: { productName: 'Laptop', formattedPrice: '$1000.00', availability: 'In Stock' }
 *
 * @example
 * // 组合多个字段
 * const order = { id: '12345', date: '2023-05-20', customerName: 'Alice', total: 150 };
 * const format = {
 *   orderInfo: (o) => `Order ${o.id} placed on ${o.date}`,
 *   customer: 'customerName',
 *   totalAmount: (o) => `$${o.total}`
 * };
 * const result = formatObject(order, format);
 * // 结果: { orderInfo: 'Order 12345 placed on 2023-05-20', customer: 'Alice', totalAmount: '$150' }
 */
export function formatObject<T extends object, R extends object>(obj: T, format: Formatter<T, R>): R {
  const result = {} as R;

  for (const key in format) {
    const formatter = format[key];
    if (typeof formatter === 'function') {
      result[key] = formatter(obj);
    } else if (typeof formatter === 'string') {
      result[key] = obj[formatter as keyof T] as any;
    }
  }

  return result;
}
