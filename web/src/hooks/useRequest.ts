import { get, isEmpty } from "@/utils";
import { useState, useEffect, useCallback, useRef } from "react";

// 定义请求选项接口
export interface RequestOptions<TData, TParams extends FT.Object> {
  /**
   * 是否手动触发请求
   */
  manual?: boolean;
  /**
   * 默认请求参数
   */
  defaultParams?: TParams;
  /**
   * 重试次数
   */
  retryCount?: number;
  /**
   * 重试间隔（毫秒）
   */
  retryInterval?: number;
  /**
   * 防抖等待时间（毫秒）
   */
  debounceWait?: number;
  /**
   * 节流等待时间（毫秒）
   */
  throttleWait?: number;
  /**
   * 轮询间隔（毫秒）
   */
  pollingInterval?: number;
  /**
   * 默认数据（请求失败时使用）
   */
  defaultData?: TData;
  /**
   * 数据路径（从响应中提取数据）
   */
  dataPath?: string;
  /**
   * 请求成功回调
   * @param {TData} data
   * @param {TParams} params
   * @returns
   */
  onSuccess?: (data: TData, params: TParams) => void;
  /**
   * 请求失败回调
   * @param {Error} error
   * @param {TParams} params
   * @returns
   */
  onError?: (error: Error, params: TParams) => void;
  /**
   * 结果格式化函数
   * @param data
   * @returns
   */
  format?: (data: any) => TData; // 结果格式化函数
}

// useRequest Hook 主函数
export function useRequest<TData, TParams extends object = FT.Object>(
  requestFn: (params: TParams) => Promise<any>,
  options: RequestOptions<TData, TParams> = {},
) {
  const {
    manual = false,
    defaultParams = {} as TParams,
    onSuccess,
    onError,
    retryCount = 0,
    retryInterval = 1000,
    debounceWait = 0,
    throttleWait = 0,
    pollingInterval = 0,
    defaultData,
    dataPath = "data.data",
    format,
  } = options;
  // 状态管理
  const [data, setData] = useState<TData>(defaultData as TData);
  const [error, setError] = useState<Error | undefined>(void 0);
  const [loading, setLoading] = useState<boolean>(false);

  // 引用管理
  const requestCount = useRef(0);
  const timer = useRef<NodeJS.Timeout | null>(null);
  const cancelRequest = useRef<(() => void) | null>(null);

  // 核心请求函数
  const run = useCallback(
    async (params: TParams): Promise<TData> => {
      const theParams = isEmpty(params) ? defaultParams : params;
      setLoading(true);
      setError(void 0);
      requestCount.current += 1;
      const currentCount = requestCount.current;

      // 内部重试函数
      const retryRequest = async (retryTimes: number): Promise<TData> => {
        try {
          const result = await requestFn(theParams);
          if (currentCount === requestCount.current) {
            let finalData: TData;
            // 使用 dataPath 从响应中提取数据
            if (dataPath) {
              finalData = get(result, dataPath);
            } else {
              finalData = result;
            }
            // 使用 format 格式化数据
            if (format) {
              finalData = format(finalData);
            }
            setData(finalData);
            setLoading(false);
            onSuccess?.(finalData, theParams);
            return finalData;
          }
          throw new Error("请求被取消");
        } catch (err) {
          if (retryTimes > 0 && currentCount === requestCount.current) {
            // 重试逻辑
            await new Promise((resolve) => setTimeout(resolve, retryInterval));
            return retryRequest(retryTimes - 1);
          }
          if (currentCount === requestCount.current) {
            setError(err as Error);
            setLoading(false);
            onError?.(err as Error, theParams);
            // 使用默认数据（如果提供）
            if (defaultData !== void 0) {
              setData(defaultData);
              return defaultData;
            }
          }
          throw err;
        }
      };

      return retryRequest(retryCount);
    },
    [
      requestFn,
      onSuccess,
      onError,
      retryCount,
      retryInterval,
      dataPath,
      format,
      defaultData,
    ],
  );

  // 防抖处理
  const debouncedRun = useCallback(
    (params: TParams) => {
      if (timer.current) {
        clearTimeout(timer.current);
      }
      timer.current = setTimeout(() => {
        run(params);
      }, debounceWait);
    },
    [run, debounceWait],
  );

  // 节流处理
  const throttledRun = useCallback(
    (params: TParams) => {
      if (!timer.current) {
        run(params);
        timer.current = setTimeout(() => {
          timer.current = null;
        }, throttleWait);
      }
    },
    [run, throttleWait],
  );

  // 取消请求
  const cancel = useCallback(() => {
    requestCount.current += 1;
    setLoading(false);
    if (timer.current) {
      clearTimeout(timer.current);
    }
    cancelRequest.current?.();
  }, []);

  // 自动执行（非手动模式）
  useEffect(() => {
    if (!manual) {
      run(defaultParams);
    }
  }, []);

  // 轮询处理
  useEffect(() => {
    if (pollingInterval > 0) {
      const pollingTimer = setInterval(() => {
        run(defaultParams);
      }, pollingInterval);

      return () => {
        clearInterval(pollingTimer);
      };
    }
  }, [pollingInterval, run]);

  // 根据配置选择适当的执行方式
  const runRequest = useCallback(
    (params = {} as TParams) => {
      if (debounceWait > 0) {
        debouncedRun(params);
      } else if (throttleWait > 0) {
        throttledRun(params);
      } else {
        return run(params);
      }
      return Promise.resolve(void 0 as TData);
    },
    [run, debouncedRun, throttledRun, debounceWait, throttleWait],
  );

  // 仅在请求未执行时执行请求
  const runRequestOnce = useCallback(
    (params: TParams) => {
      if (requestCount.current > 0) {
        return Promise.resolve(data);
      } else {
        return runRequest(params);
      }
    },
    [runRequest, data],
  );

  // 清理函数
  const clean = useCallback(() => {
    cancel();
    setData(defaultData as TData);
    setError(void 0);
    setLoading(false);
    requestCount.current = 0;
  }, [cancel]);

  return {
    data,
    requestCount: requestCount.current,
    loading,
    error,
    run: runRequest,
    runOnce: runRequestOnce,
    cancel,
    clean,
    setData,
  } as const;
}
