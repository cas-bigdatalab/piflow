type TreeNode<T> = T & {
  [key: string]: any;
};

type MatchFunction<T> = (node: TreeNode<T>) => boolean;

interface SearchOptions {
  childrenKey?: string; // 子节点的键名，默认为 'children'
  prefix?: string; // 扩展属性的前缀，默认为 '__'
}

/**
 * 在树结构中查找满足条件的节点，并返回包含这些节点及其祖先的完整树结构。每个节点会添加额外的元数据，如是否匹配、原始索引和层级
 *
 * @param tree - 树结构的根节点数组。
 * @param predicate - 匹配函数，用于判断节点是否满足条件。
 * @param options - 配置选项，包括子节点的键名和扩展属性的前缀。
 * @returns 返回一个新的树结构，包含所有匹配节点及其祖先。
 *
 * @example
 * const tree = [
 *   {
 *     id: 1,
 *     name: 'Node 1',
 *     children: [
 *       { id: 2, name: 'Node 1.1', children: [] },
 *       { id: 3, name: 'Node 1.2', children: [] },
 *     ],
 *   },
 *   {
 *     id: 4,
 *     name: 'Node 2',
 *     children: [
 *       { id: 5, name: 'Node 2.1', children: [] },
 *     ],
 *   },
 * ];
 *
 * const result = findNodesAndAncestorsInTree(tree, (node) => node.id === 5);
 * console.log(result);
 * // 输出:
 * // [
 * //   {
 * //     id: 4,
 * //     name: 'Node 2',
 * //     __isMatch: false,
 * //     __originalIndex: 1,
 * //     __level: 0,
 * //     children: [
 * //       {
 * //         id: 5,
 * //         name: 'Node 2.1',
 * //         __isMatch: true,
 * //         __originalIndex: 0,
 * //         __level: 1,
 * //         children: [],
 * //       },
 * //     ],
 * //   },
 * // ]
 */
export function findNodesAndAncestorsInTree<T>(
  tree: TreeNode<T>[],
  predicate: MatchFunction<T>,
  options: SearchOptions = {},
): TreeNode<T>[] {
  const { childrenKey = 'children', prefix = '__' } = options;

  // 用于存储所有匹配节点及其祖先的树结构
  const resultTree: TreeNode<T>[] = [];

  // 用于缓存已经处理过的节点，避免重复遍历
  const nodeCache = new Map<TreeNode<T>, TreeNode<T>>();

  /**
   * 递归搜索函数，遍历树结构并查找匹配节点。
   *
   * @param node - 当前节点。
   * @param index - 当前节点在父节点的子节点数组中的索引。
   * @param level - 当前节点的层级。
   * @param parentPath - 当前节点的祖先路径。
   * @returns 返回当前节点或其子节点是否存在匹配项。
   */
  function search(node: TreeNode<T>, index: number, level: number, parentPath: TreeNode<T>[]): boolean {
    // 检查当前节点是否匹配条件
    const isMatch = predicate(node);

    // 创建扩展节点，添加额外的元数据
    const extendedNode: TreeNode<T> = {
      ...node,
      [`${prefix}isMatch`]: isMatch, // 标记当前节点是否匹配
      [`${prefix}originalIndex`]: index, // 记录当前节点在父节点中的原始索引
      [`${prefix}level`]: level, // 记录当前节点的层级
    };

    // 将当前节点添加到路径中
    const newPath = [...parentPath, extendedNode];

    // 如果节点匹配，将其路径整合到结果树中
    if (isMatch) {
      integratePathIntoResultTree(newPath);
    }

    // 如果当前节点有子节点，递归搜索每个子节点
    let hasMatchInChildren = false;
    if (node[childrenKey] && Array.isArray(node[childrenKey])) {
      for (let i = 0; i < node[childrenKey].length; i++) {
        if (search(node[childrenKey][i], i, level + 1, newPath)) {
          hasMatchInChildren = true;
        }
      }
    }

    // 返回当前节点或其子节点是否存在匹配项
    return isMatch || hasMatchInChildren;
  }

  /**
   * 将路径整合到结果树中的辅助函数。
   *
   * @param path - 当前匹配节点的完整路径（包括其祖先）。
   */
  function integratePathIntoResultTree(path: TreeNode<T>[]): void {
    let currentLevel = resultTree;

    // 遍历路径中的每个节点，将其整合到结果树中
    for (const currentNode of path) {
      const cachedNode: any = nodeCache.get(currentNode);

      if (cachedNode) {
        // 如果节点已经存在，复用缓存中的节点
        if (!cachedNode[childrenKey]) {
          // 如果子节点不存在，初始化为空数组
          cachedNode[childrenKey] = [];
        }
        currentLevel = cachedNode[childrenKey];
      } else {
        // 如果节点不存在，创建新节点并缓存
        const newNode = { ...currentNode, [childrenKey]: [] };
        currentLevel.push(newNode);
        nodeCache.set(currentNode, newNode);
        currentLevel = newNode[childrenKey];
      }
    }
  }

  // 开始搜索树的每个顶级节点
  for (let i = 0; i < tree.length; i++) {
    search(tree[i], i, 0, []);
  }

  return resultTree;
}
