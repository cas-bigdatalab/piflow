/**
 * 切换数组中的元素
 *
 * @template T 数组元素的类型
 * @param {T[]} items - 目标数组
 * @param {T} targetItem - 要切换的目标元素
 * @param {(item: T, target: T) => boolean} predicate - 匹配函数，用于比较数组中的元素和目标元素
 * @returns {T[]} 返回新的数组，其中目标元素被切换（如果存在则移除，不存在则添加）
 *
 * @description
 * 这个函数接受一个数组、一个目标元素和一个匹配函数。
 * 如果数组中存在与目标元素匹配的元素（由匹配函数决定），则将其移除。
 * 如果数组中不存在匹配的元素，则将目标元素添加到数组中。
 * 这个函数不会修改原始数组，而是返回一个新的数组。
 *
 * @example
 * const numbers = [1, 2, 3, 4, 5];
 * const toggledNumbers = toggleArrayElement(numbers, 3, (a, b) => a === b);
 * console.log(toggledNumbers); // [1, 2, 4, 5]
 *
 * const toggledAgain = toggleArrayElement(toggledNumbers, 3, (a, b) => a === b);
 * console.log(toggledAgain); // [1, 2, 4, 5, 3]
 *
 * const objects = [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }];
 * const toggledObjects = toggleArrayElement(objects, { id: 2, name: 'Bob' }, (a, b) => a.id === b.id);
 * console.log(toggledObjects); // [{ id: 1, name: 'Alice' }]
 */
export function toggleArrayElement<T>(items: T[], targetItem: T, predicate: (item: T, target: T) => boolean): T[] {
  const index = items.findIndex((item) => predicate(item, targetItem));
  if (index !== -1) {
    // 如果找到匹配的元素，返回一个新数组，其中不包含该元素
    return [...items.slice(0, index), ...items.slice(index + 1)];
  } else {
    // 如果没有找到匹配的元素，返回一个新数组，其中包含原数组的所有元素和目标元素
    return [...items, targetItem];
  }
}
