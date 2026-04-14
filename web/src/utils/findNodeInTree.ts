/**
 * 在树形数组中查找指定节点
 *
 * @template T - 节点类型
 * @param {T[]} tree - 树形数组，可以是任意满足树形结构的数组数据
 * @param {(node: T) => boolean} predicate - 用于匹配节点的断言函数
 * @param {(node: T) => T[] | undefined} [getChildren] - 函数，用于获取节点的子节点数组，默认使用 'children' 属性
 * @returns {T | null} 返回匹配的节点，如果未找到则返回 null
 *
 * @description
 * 这个函数使用深度优先搜索（DFS）遍历树形数组，查找满足指定条件的节点。
 * 它可以处理任意深度和结构的嵌套数组，并且可以根据自定义的断言函数来匹配节点。
 * 默认情况下，函数会查找节点的 'children' 属性作为子节点数组。
 * 用户可以通过提供 getChildren 函数来自定义如何从节点中获取子节点数组。
 *
 * @example
 * const tree = [
 *   { id: 1, name: 'Root', children: [
 *     { id: 2, name: 'Child 1' },
 *     { id: 3, name: 'Child 2', children: [
 *       { id: 4, name: 'Grandchild' }
 *     ]}
 *   ]}
 * ];
 *
 * const node = findNodeInTree(tree, node => node.id === 4);
 * console.log(node); // { id: 4, name: 'Grandchild' }
 *
 * @example
 * const treeWithDifferentStructure = [
 *   { value: 1, subItems: [
 *     { value: 2 },
 *     { value: 3, subItems: [{ value: 4 }] }
 *   ]}
 * ];
 *
 * const nodeInDifferentStructure = findNodeInTree(
 *   treeWithDifferentStructure,
 *   node => node.value === 4,
 *   node => node.subItems
 * );
 * console.log(nodeInDifferentStructure); // { value: 4 }
 */
export function findNodeInTree<T extends Record<string, any>>(
  tree: T[],
  predicate: (node: T) => boolean,
  getChildren: (node: T) => T[] | undefined = (node) => node.children,
): T | null {
  for (const node of tree) {
    if (predicate(node)) {
      return node;
    }
    const children = getChildren(node);
    if (Array.isArray(children)) {
      const found = findNodeInTree(children, predicate, getChildren);
      if (found) {
        return found;
      }
    }
  }
  return null;
}
