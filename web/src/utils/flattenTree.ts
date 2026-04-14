/**
 * 将树结构数组数据全部一维化的函数
 *
 * @template T - 树节点的类型
 * @param {T[]} tree - 要一维化的树结构数组
 * @param {string} [childrenKey='children'] - 子节点的键名，默认为 'children'
 * @returns {T[]} 一维化后的数组
 *
 * @example
 * // 使用示例
 *
 * // 定义一个树结构
 * const tree = [
 *   {
 *     id: '1',
 *     name: '部门A',
 *     children: [
 *       {
 *         id: '1-1',
 *         name: '小组A-1',
 *         children: [
 *           { id: '1-1-1', name: '成员A-1-1' },
 *           { id: '1-1-2', name: '成员A-1-2' }
 *         ]
 *       },
 *       {
 *         id: '1-2',
 *         name: '小组A-2',
 *         children: [
 *           { id: '1-2-1', name: '成员A-2-1' }
 *         ]
 *       }
 *     ]
 *   },
 *   {
 *     id: '2',
 *     name: '部门B',
 *     children: [
 *       { id: '2-1', name: '小组B-1' },
 *       { id: '2-2', name: '小组B-2' }
 *     ]
 *   }
 * ];
 *
 * // 一维化树结构
 * const flattenedTree = flattenTree(tree);
 *
 * console.log(flattenedTree);
 * // 输出:
 * // [
 * //   { id: '1', name: '部门A', children: [...] },
 * //   { id: '1-1', name: '小组A-1', children: [...] },
 * //   { id: '1-1-1', name: '成员A-1-1' },
 * //   { id: '1-1-2', name: '成员A-1-2' },
 * //   { id: '1-2', name: '小组A-2', children: [...] },
 * //   { id: '1-2-1', name: '成员A-2-1' },
 * //   { id: '2', name: '部门B', children: [...] },
 * //   { id: '2-1', name: '小组B-1' },
 * //   { id: '2-2', name: '小组B-2' }
 * // ]
 *
 * // 使用自定义的子节点键名
 * const customTree = [
 *   {
 *     id: '1',
 *     name: '根节点',
 *     subNodes: [
 *       { id: '1-1', name: '子节点A' },
 *       { id: '1-2', name: '子节点B' }
 *     ]
 *   }
 * ];
 *
 * const flattenedCustomTree = flattenTree(customTree, 'subNodes');
 * console.log(flattenedCustomTree);
 * // 输出:
 * // [
 * //   { id: '1', name: '根节点', subNodes: [...] },
 * //   { id: '1-1', name: '子节点A' },
 * //   { id: '1-2', name: '子节点B' }
 * // ]
 */
export function flattenTree<T extends object>(tree: T[], childrenKey: string = 'children'): T[] {
  // 用于存储结果的数组
  const result: T[] = [];

  // 递归函数，用于遍历树结构
  function traverse(node: T) {
    // 将当前节点添加到结果数组中
    // 这里我们使用类型断言来确保 T 类型的兼容性
    result.push(node as T);

    // 如果当前节点有子节点，则递归遍历子节点
    const children = node[childrenKey as keyof T] as T[] | undefined;
    if (Array.isArray(children)) {
      children.forEach(traverse);
    }
  }

  // 遍历树的每个顶级节点
  tree.forEach(traverse);

  return result;
}
