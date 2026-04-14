import { useRef, useEffect, useCallback } from "react";

/**
 * 用于判断当前组件是否还在挂载状态的hook
 * @returns () => boolean - 调用该函数返回组件是否仍在挂载状态
 */
export default function useMounted() {
  const mountedRef = useRef(true);

  useEffect(() => {
    // 组件挂载时设置为true
    mountedRef.current = true;

    // 组件卸载时设置为false
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // 返回一个稳定的函数，用于检查组件是否仍在挂载状态
  return useCallback(() => mountedRef.current, []);
}
