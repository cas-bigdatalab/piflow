/**
 * @method request
 * @description 请求函数封装
 */

import Axios from "axios";
import { message, notification } from "antd";
import { throttle, isObject } from "@/utils";
import type { AxiosInstance, AxiosRequestConfig } from "axios";
const baseURL = "/api/";

export enum ContentTypeMap {
  urlencoded = "application/x-www-form-urlencoded",
  formdata = "multipart/form-data",
  json = "application/json;charset=utf-8",
}

// 登录过期提示
const LoginExpired = throttle(() => {
  notification.error({
    message: "系统提示",
    description: "登录凭证已过期，请重新登录。",
  });
}, 1000);

export const HandleStrategy = {
  [ContentTypeMap.urlencoded]: (config: AxiosRequestConfig) => {
    if (isObject(config.data)) {
      // 处理空值，data中如果有值为 undefined/null 的，会被变为字符串传输至后端，所以需要手动处理
      config.data = Object.entries(config.data).reduce((acc, [key, value]) => {
        if (value !== void 0 && value !== null) {
          acc[key] = value;
        }
        return acc;
      }, {} as any);
    }
  },
  [ContentTypeMap.formdata]: (config: AxiosRequestConfig) => {
    if (isObject(config.data)) {
      // 处理空值，data中如果有值为 undefined/null 的，会被变为字符串传输至后端，所以需要手动处理
      config.data = Object.entries(config.data).reduce((acc, [key, value]) => {
        if (value !== void 0 && value !== null) {
          acc[key] = value;
        }
        return acc;
      }, {} as any);
      // @ts-ignore
      config._data = config.data;
    }
  },
  [ContentTypeMap.json]: () => {},
};

export const CreateService = (
  opts: {
    baseURL?: string;
    timeout?: number;
    ContentType?: string;
    useToken?: boolean;
  } = {},
): AxiosInstance => {
  const service = Axios.create({
    baseURL: opts.baseURL ?? baseURL, // 默认地址
    timeout: opts.timeout || 60 * 1000, // 响应超时
    headers: {
      ["Content-Type"]: opts.ContentType || ContentTypeMap.json, // 请求头格式
    },
  });

  // request拦截器
  service.interceptors.request.use(
    (config) => {
      // 每种请求类型数据处理策略
      const type = config.headers!["Content-Type"] as ContentTypeMap;
      HandleStrategy[type] && HandleStrategy[type](config);

      return config;
    },
    (error) => {
      Promise.reject(error);
    },
  );

  // response拦截器
  // service.interceptors.response.use(
  //   (res) => {
  //     // 请求结束
  //     switch (res.data?.code) {
  //       case 401:
  //       case 403: {
  //         LoginExpired();
  //         break;
  //       }
  //       case 500: {
  //         notification.error({
  //           message: "错误码 500",
  //           description: "请求服务发生错误。",
  //         });
  //       }
  //     }
  //     if (res.data?.code === 1000) {
  //       message.error(res.data.message);
  //     }

  //     return res;
  //   },
  //   (error) => {
  //     switch (error.status) {
  //       case 401:
  //       case 403: {
  //         LoginExpired();
  //         break;
  //       }
  //       case 500:
  //         {
  //           notification.error({
  //             message: "错误码 500",
  //             description: "请求服务发生错误。",
  //           });
  //         }
  //         break;
  //       default:
  //         notification.error({
  //           message: "系统提示",
  //           description: "请求发生错误。",
  //         });
  //     }
  //     return Promise.reject(error.response);
  //   },
  // );

  return service;
};

export const requestJson = CreateService();

export const requestFormData = CreateService({
  ContentType: ContentTypeMap.formdata,
});

export const requestUrlencoded = CreateService({
  ContentType: ContentTypeMap.urlencoded,
});
