/**
 * 在树结构中查找匹配的节点并返回它们及其子树
 *
 * @template T - 树节点的类型
 * @param {T[]} data - 要搜索的树结构
 * @param {(node: T) => boolean} predicate - 用于判断节点是否匹配的函数
 * @param {string} [childrenKey='children'] - 用于子节点的键名
 * @returns {T[]} 匹配节点及其子树的数组
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
 * // 定义匹配函数：查找名称中包含 "A" 的节点
 * const matchFn = (node: { name: string }) => node.name.includes('A');
 *
 * // 过滤树结构
 * const filteredTree = filterTreeWithSubtrees(tree, matchFn);
 *
 * console.log(JSON.stringify(filteredTree, null, 2));
 * // 输出:
 * // [
 * //   {
 * //     "id": "1",
 * //     "name": "部门A",
 * //     "children": [
 * //       {
 * //         "id": "1-1",
 * //         "name": "小组A-1",
 * //         "children": [
 * //           {
 * //             "id": "1-1-1",
 * //             "name": "成员A-1-1",
 * //             "children": []
 * //           },
 * //           {
 * //             "id": "1-1-2",
 * //             "name": "成员A-1-2",
 * //             "children": []
 * //           }
 * //         ]
 * //       },
 * //       {
 * //         "id": "1-2",
 * //         "name": "小组A-2",
 * //         "children": [
 * //           {
 * //             "id": "1-2-1",
 * //             "name": "成员A-2-1",
 * //             "children": []
 * //           }
 * //         ]
 * //       }
 * //     ]
 * //   }
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
 * const filteredCustomTree = filterTreeWithSubtrees(customTree, matchFn, 'subNodes');
 * console.log(JSON.stringify(filteredCustomTree, null, 2));
 * // 输出:
 * // [
 * //   {
 * //     "id": "1-1",
 * //     "name": "子节点A",
 * //     "subNodes": []
 * //   }
 * // ]
 */
export function filterTreeWithSubtrees<T extends object>(
  data: T[],
  predicate: (node: T) => boolean,
  childrenKey: string = 'children',
): T[] {
  // 内部递归函数，用于遍历树结构
  const traverse = (nodes: T[]): T[] => {
    return nodes.reduce<T[]>((acc, node) => {
      // 如果当前节点匹配条件
      if (predicate(node)) {
        // 获取子节点（如果存在）
        const children = node[childrenKey as keyof T] as T[] | undefined;
        // 将匹配的节点添加到结果数组中，同时递归处理其子节点
        acc.push({
          ...node, // 复制节点的所有属性
          [childrenKey]: Array.isArray(children) ? traverse(children) : [], // 递归处理子节点
        });
      }
      return acc;
    }, []);
  };

  // 开始遍历整个树结构
  return traverse(data);
}
