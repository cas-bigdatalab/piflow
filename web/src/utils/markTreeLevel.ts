type Option = {
  /**
   * 子节点的key
   */
  childrenKey?: string;
  /**
   * 层级的key
   */
  levelKey?: string;
  /**
   * 层级的起始值
   */
  startLevel?: number;
};

/**
 * 标记树的层级
 * @description 标记树的层级
 * @param {T[]} tree 树
 * @param {Option} option 选项
 * @param {string} option.childrenKey 子节点的key
 * @param {string} option.levelKey 层级的key
 * @param {number} option.startLevel 层级的起始值
 * @returns {T[]} 标记后的树
 *
 * @example
 * const tree = [
 *  { id: 1, name: '1', children: [{ id: 2, name: '2', children: [{ id: 3, name: '3' }] }] },
 *  { id: 4, name: '4', children: [{ id: 5, name: '5' }] },
 * ];
 * markTreeLevel(tree);
 * console.log(tree);
 */
export function markTreeLevel<T = Record<string, any>>(tree: T[], option: Option = {}) {
  const { childrenKey = 'children', levelKey = 'level', startLevel = 1 } = option;

  return tree.map((node: any) => {
    const newNode: any = {
      ...node,
      [levelKey]: startLevel,
    };
    if (newNode[childrenKey] && newNode[childrenKey].length > 0) {
      markTreeLevel(newNode[childrenKey], { childrenKey, levelKey, startLevel: startLevel + 1 });
    }
    return newNode;
  });
}
