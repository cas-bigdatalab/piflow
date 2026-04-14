/**
 * 将对象数组转换为树形结构
 *
 * @template T - 数组元素的类型
 * @param {T[]} items - 要转换的对象数组
 * @param {keyof T} idKey - 用作节点唯一标识的属性名
 * @param {keyof T} parentKey - 用作父节点标识的属性名
 * @param {keyof T} childrenKey - 用作子节点数组的属性名
 * @returns {T[]} 树形结构的根节点数组
 *
 * @example
 * // 使用示例
 * const items = [
 *   { id: '1', name: '部门A', parentId: null },
 *   { id: '2', name: '部门B', parentId: '1' },
 *   { id: '3', name: '部门C', parentId: '1' },
 *   { id: '4', name: '小组1', parentId: '2' },
 *   { id: '5', name: '小组2', parentId: '2' },
 *   { id: '6', name: '小组3', parentId: '3' },
 * ];
 *
 * const tree = arrayToTree(items, 'id', 'parentId');
 *
 * console.log(JSON.stringify(tree, null, 2));
 * // 输出:
 * // [
 * //   {
 * //     "id": "1",
 * //     "name": "部门A",
 * //     "parentId": null,
 * //     "children": [
 * //       {
 * //         "id": "2",
 * //         "name": "部门B",
 * //         "parentId": "1",
 * //         "children": [
 * //           {
 * //             "id": "4",
 * //             "name": "小组1",
 * //             "parentId": "2",
 * //             "children": []
 * //           },
 * //           {
 * //             "id": "5",
 * //             "name": "小组2",
 * //             "parentId": "2",
 * //             "children": []
 * //           }
 * //         ]
 * //       },
 * //       {
 * //         "id": "3",
 * //         "name": "部门C",
 * //         "parentId": "1",
 * //         "children": [
 * //           {
 * //             "id": "6",
 * //             "name": "小组3",
 * //             "parentId": "3",
 * //             "children": []
 * //           }
 * //         ]
 * //       }
 * //     ]
 * //   }
 * // ]
 *
 * // 使用自定义的子节点属性名
 * const treeWithCustomChildrenKey = arrayToTree(items, 'id', 'parentId', 'subItems');
 * console.log(treeWithCustomChildrenKey[0].subItems); // 输出部门A的子部门数组
 */
export function arrayToTree<T extends object>(
  items: T[],
  idKey: keyof T,
  parentKey: keyof T,
  childrenKey: keyof T = 'children' as keyof T,
): T[] {
  const nodes: { [key: string]: T } = {};

  // 首先，创建所有节点的映射
  items.forEach((item) => {
    const id = item[idKey] as string;
    nodes[id] = { ...item, [childrenKey]: [] } as T;
  });

  // 然后，构建树结构
  const roots: T[] = [];
  items.forEach((item) => {
    const id = item[idKey] as string;
    const parentId = item[parentKey] as string | null;

    if (parentId && nodes[parentId]) {
      (nodes[parentId][childrenKey as keyof T] as T[]).push(nodes[id]);
    } else {
      roots.push(nodes[id]);
    }
  });

  return roots;
}
