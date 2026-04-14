interface TreeNode {
  [key: string]: any;
}

/**
 * 使用深度优先搜索（DFS）查找树中目标节点的路径
 *
 * @param tree - 树的根节点数组
 * @param match - 匹配函数，用于判断当前节点是否为目标节点
 * @param getChildren - 获取子节点的函数，用于获取当前节点的子节点数组
 * @returns 返回从根节点到目标节点的路径数组，如果未找到目标节点则返回空数组
 *
 * @example
 * const tree = [
 *   {
 *     id: 1,
 *     children: [
 *       { id: 2, children: [{ id: 4 }] },
 *       { id: 3 }
 *     ]
 *   }
 * ];
 * const targetNode = { id: 4 };
 * const path = findNodePath(tree, node => node.id === targetNode.id);
 * console.log(path); // 输出: [{ id: 1 }, { id: 2 }, { id: 4 }]
 *
 * @example
 * // 自定义字段名称
 * const customTree = [
 *   {
 *     nodeId: 'a',
 *     subNodes: [
 *       { nodeId: 'b', subNodes: [{ nodeId: 'c' }] }
 *     ]
 *   }
 * ];
 * const customTarget = { nodeId: 'c' };
 * const customPath = findNodePath(customTree, node => node.nodeId === customTarget.nodeId, node => node.subNodes);
 * console.log(customPath); // 输出: [{ nodeId: 'a' }, { nodeId: 'b' }, { nodeId: 'c' }]
 */
export function findNodePath<T extends TreeNode>(
  tree: T[],
  match: (node: T) => boolean,
  getChildren = (node: T) => node.children as T[] | undefined,
): T[] {
  const path: T[] = [];

  function dfs(nodes: T[], parentPath: T[]): boolean {
    for (const node of nodes) {
      const currentPath = [...parentPath, node];

      if (match(node)) {
        path.push(...currentPath);
        return true;
      }

      const children = getChildren(node) || [];
      if (children && children.length > 0) {
        if (dfs(children, currentPath)) {
          return true;
        }
      }
    }
    return false;
  }

  dfs(tree, []);
  return path;
}
