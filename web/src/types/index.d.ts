import type { AxiosPromise } from "axios";
declare global {
  namespace FT {
    // 任意方法
    type Function = (...args: any[]) => any;

    // 对象
    type Object<T = any> = Record<string, T>;

    type Key = string | number | bigint;

    type StringKeyNumberValue = Record<string, number>;
    type StringKeyStringValue = Record<string, string>;
    type StringKeyNumberArrayValue = Record<string, number[]>;
    type StringKeyAnyArrayValue = Record<string, Object[]>;

    // Form
    type FormMode = "add" | "edit" | "view";
    type FormProps = {
      // 开启
      onOpen?: () => void;
      // 关闭
      onClose?: () => void;
      // 打开状态变更
      onOpenChange?: () => void;
      // 提交前，返回false将中断后续执行
      onBeforeSubmit?: (
        data?: Record<string, any>,
      ) => boolean | Promise<boolean>;
      // 提交后
      onSubmit?: (data?: any) => void;
      columns?: ProColumns<FT.Object<any>, string>[] | undefined;
    };
    // 表单实例，均为可选属性，具体使用时根据表单组件声明自行判断
    type FormInstance = {
      // 打开表单（添加模式）
      add?: (...args: any[]) => void;
      // 打开表单（编辑模式）
      edit?: (...args: any[]) => void;
      // 打开表单（查看模式）
      view?: (...args: any[]) => void;
      // 关闭表单
      close?: () => void;
      // 手动提交表单
      submit?: (...args: any[]) => void | Promise<void>;
    };

    // 匹配方法
    type MatchFunc<T = any> = (item: T) => boolean;

    // 请求
    type Response<T = any, E = FT.Object> = {
      code: number;
      msg: string;
      data?: T;
      rows?: T;
      total?: number;
    } & E;
    type Request<T = any, E = FT.Object> = (
      ...args: any[]
    ) => AxiosPromise<Response<T, E>>;

    type RoutePageProps = {
      route: FT.Route;
    };
  }
}
