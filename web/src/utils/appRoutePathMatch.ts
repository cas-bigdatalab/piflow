import { match } from 'path-to-regexp';

/**
 * 匹配路由路径和当前路径名
 * @param {string} routePath - 路由路径
 * @param {string} pathname - 当前路径名
 * @returns {boolean} 是否匹配
 */
export function appRoutePathMatch(routePath: string, pathname: string) {
  return !!match(routePath, { decode: decodeURIComponent })(pathname);
}
