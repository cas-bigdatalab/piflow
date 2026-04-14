import { arrayIncludes } from './arrayIncludes.ts';
import { get } from './get.ts';
import { isNumber, isValidDate } from './typeof2.ts';

/**
 * 定义可用的过滤类型
 */
export type FilterType = 'equal' | 'keyword' | 'greaterThan' | 'lessThan' | 'range' | 'in';

/**
 * 定义过滤选项的接口
 * @template T - 要过滤的对象类型
 */
export interface FilterOption<T> {
  key: keyof T | string; // 要过滤的属性名
  type: FilterType; // 过滤类型
  jointQuery?: (keyof T | string)[]; // 联合查询的属性名数组
}

/**
 * 定义过滤值的类型
 */
export type FilterValue = string | number | boolean | [number, number] | any[];

/**
 * 定义过滤参数的接口
 */
export interface FilterParams {
  [key: string]: FilterValue;
}

/**
 * 比较过滤值和数据值
 * @param {FilterType} filterType - 过滤类型
 * @param {FilterValue} filterValue - 过滤值
 * @param {any} dataValue - 数据值
 * @returns {boolean} 是否匹配
 */
function compareValues(filterType: FilterType, filterValue: FilterValue, dataValue: any): boolean {
  switch (filterType) {
    case 'equal':
      return dataValue === filterValue;
    case 'keyword':
      if (typeof dataValue === 'number' || typeof filterValue === 'number') {
        dataValue = dataValue.toString();
        filterValue = filterValue.toString();
      }
      return (
        typeof dataValue === 'string' &&
        typeof filterValue === 'string' &&
        dataValue.toLowerCase().includes(filterValue.toLowerCase())
      );
    case 'greaterThan':
      return isNumber(dataValue) && isNumber(filterValue) && dataValue > filterValue;
    case 'lessThan':
      return isNumber(dataValue) && isNumber(filterValue) && dataValue < filterValue;
    case 'range':
      if (Array.isArray(filterValue) && filterValue.length === 2) {
        if (isNumber(dataValue)) {
          return dataValue >= filterValue[0] && dataValue <= filterValue[1];
        } else if (isValidDate(filterValue[0]) && isValidDate(filterValue[1])) {
          if (isValidDate(dataValue)) {
            const dataValueToDate = new Date(dataValue);
            return dataValueToDate >= new Date(filterValue[0]) && dataValueToDate <= new Date(filterValue[1]);
          } else {
            return false;
          }
        } else {
          return dataValue >= filterValue[0] && dataValue <= filterValue[1];
        }
      } else {
        return false;
      }
    case 'in': {
      if (Array.isArray(dataValue)) {
        return arrayIncludes(dataValue, filterValue);
      } else {
        return Array.isArray(filterValue) && filterValue.includes(dataValue);
      }
    }
    default:
      return false;
  }
}

/**
 * 高级对象数组过滤函数
 * @template T - 要过滤的对象类型
 * @param {T[]} data - 要过滤的对象数组
 * @param {FilterParams} params - 过滤参数
 * @param {FilterOption<T>[]} opts - 过滤选项
 * @returns {T[]} 过滤后的对象数组
 *
 * @example
 * // 定义数据类型
 * interface Person {
 *   id: number
 *   name: string
 *   age: number
 *   department: {
 *     name: string
 *   }
 *   tags: string[]
 * }
 *
 * // 示例数据
 * const people: Person[] = [
 *   { id: 1, name: '张三', age: 30, department: { name: '技术部' }, tags: ['开发', '前端'] },
 *   { id: 2, name: '李四', age: 25, department: { name: '市场部' }, tags: ['设计', 'UI'] },
 *   { id: 3, name: '王五', age: 35, department: { name: '技术部' }, tags: ['开发', '后端'] },
 *   { id: 4, name: '赵六', age: 28, department: { name: '人事部' }, tags: ['招聘', 'HR'] },
 * ]
 *
 * // 定义过滤选项
 * const filterOptions: FilterOption<Person>[] = [
 *   { key: 'name', type: 'keyword' },
 *   { key: 'age', type: 'range' },
 *   { key: 'department.name', type: 'equal' },
 *   { key: 'tags', type: 'in' }
 * ]
 *
 * // 定义过滤参数
 * const filterParams: FilterParams = {
 *   name: '张',
 *   age: [25, 35],
 *   'department.name': '技术部',
 *   tags: ['开发']
 * }
 *
 * // 执行过滤
 * const filteredPeople = filterObjectArray(people, filterParams, filterOptions)
 * console.log(filteredPeople)
 * // 输出: [{ id: 1, name: '张三', age: 30, department: { name: '技术部' }, tags: ['开发', '前端'] }]
 */
export function filterObjectArray<T = Record<string, any>>(
  data: T[],
  params: FilterParams,
  opts: FilterOption<T>[],
): T[] {
  return data.filter((item) => {
    return opts.every((option) => {
      const filterValue = params[option.key as string];
      if (filterValue === void 0) return true; // 如果没有提供过滤值，则不过滤

      if (option.jointQuery) {
        // 如果有联合查询，只要有一个匹配就返回true
        return option.jointQuery.some((key) => {
          const dataValue = get(item, key as string);
          return compareValues(option.type, filterValue, dataValue);
        });
      } else {
        const dataValue = get(item, option.key as string);
        return compareValues(option.type, filterValue, dataValue);
      }
    });
  });
}
