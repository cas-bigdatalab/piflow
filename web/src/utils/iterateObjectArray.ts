/**
 * 表示可能包含子项的对象
 */
interface TreeNode {
  [key: string]: any;
  children?: TreeNode[];
}

/**
 * 遍历对象数组（包括树结构）并对每项执行自定义操作
 *
 * @template T - 树节点的类型
 * @template R - 操作后的结果类型
 * @param {T[]} arr - 要遍历的对象数组
 * @param {(item: T, index: number, array: T[], parent: T) => R} operation - 对每个对象执行的操作函数
 * @param {keyof T} childrenKey - 子节点的键名，默认为 'children'
 * @returns {R[]} 操作后的新数组
 *
 * @example
 * // 使用示例
 *
 * // 定义一个树结构
 * const tree = [
 *   {
 *     id: 1,
 *     name: '部门A',
 *     children: [
 *       { id: 2, name: '小组A-1' },
 *       {
 *         id: 3,
 *         name: '小组A-2',
 *         children: [
 *           { id: 4, name: '成员A-2-1' }
 *         ]
 *       }
 *     ]
 *   },
 *   {
 *     id: 5,
 *     name: '部门B',
 *     children: [
 *       { id: 6, name: '小组B-1' }
 *     ]
 *   }
 * ];
 *
 * // 定义操作函数：为每个节点添加 level 属性
 * const addLevel = (node: TreeNode, index: number, array: TreeNode[], level = 0) => ({
 *   ...node,
 *   level,
 *   children: node.children
 *     ? iterateObjectArray(node.children, (child, childIndex, childArray) =>
 *         addLevel(child, childIndex, childArray, level + 1)
 *       )
 *     : undefined
 * });
 *
 * // 遍历树结构并添加 level 属性
 * const treeWithLevels = iterateObjectArray(tree, (node, index, array) => addLevel(node, index, array));
 *
 * console.log(JSON.stringify(treeWithLevels, null, 2));
 * // 输出:
 * // [
 * //   {
 * //     "id": 1,
 * //     "name": "部门A",
 * //     "level": 0,
 * //     "children": [
 * //       {
 * //         "id": 2,
 * //         "name": "小组A-1",
 * //         "level": 1
 * //       },
 * //       {
 * //         "id": 3,
 * //         "name": "小组A-2",
 * //         "level": 1,
 * //         "children": [
 * //           {
 * //             "id": 4,
 * //             "name": "成员A-2-1",
 * //             "level": 2
 * //           }
 * //         ]
 * //       }
 * //     ]
 * //   },
 * //   {
 * //     "id": 5,
 * //     "name": "部门B",
 * //     "level": 0,
 * //     "children": [
 * //       {
 * //         "id": 6,
 * //         "name": "小组B-1",
 * //         "level": 1
 * //       }
 * //     ]
 * //   }
 * // ]
 *
 * // 使用自定义的子节点键名
 * const customTree = [
 *   {
 *     id: 1,
 *     name: '根节点',
 *     subItems: [
 *       { id: 2, name: '子项A' },
 *       { id: 3, name: '子项B' }
 *     ]
 *   }
 * ];
 *
 * const customTreeWithLevels = iterateObjectArray(
 *   customTree,
 *   (node, index, array) => addLevel(node, index, array),
 *   'subItems'
 * );
 *
 * console.log(JSON.stringify(customTreeWithLevels, null, 2));
 * // 输出:
 * // [
 * //   {
 * //     "id": 1,
 * //     "name": "根节点",
 * //     "level": 0,
 * //     "subItems": [
 * //       {
 * //         "id": 2,
 * //         "name": "子项A",
 * //         "level": 1
 * //       },
 * //       {
 * //         "id": 3,
 * //         "name": "子项B",
 * //         "level": 1
 * //       }
 * //     ]
 * //   }
 * // ]
 */
export function iterateObjectArray<T extends TreeNode, R = T>(
  arr: T[],
  operation: (item: T, index: number, array: T[], parent?: T) => R,
  childrenKey: keyof T = 'children',
  parent?: T,
): R[] {
  if (!Array.isArray(arr)) {
    throw new Error('Input must be an array');
  }

  if (typeof operation !== 'function') {
    throw new Error('Operation must be a function');
  }

  return arr.map((item, index, array) => {
    const result = operation(item, index, array, parent);
    if (Array.isArray(item[childrenKey])) {
      return {
        ...result,
        [childrenKey]: iterateObjectArray(item[childrenKey], operation, childrenKey, item),
      };
    }
    return result;
  });
}
