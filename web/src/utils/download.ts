import { message } from "antd";
import { get } from "./get";

/**
 * 下载文件（通过接口获取文件Blob对象下载）
 * @param {Blob} file 文件blob对象
 * @param {string} fileName 文件名称
 */
export function downloadByBlob(file: Blob, fileName = '下载文件') {
  const a = document.createElement('a');
  a.style.display = 'none';
  a.style.position = 'fixed';
  a.style.top = '0px';
  a.style.left = '0px';
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(a.href);
  document.body.removeChild(a);
}

/**
 * 下载文件（通过文件地址直接下载）
 * @param {string} fileUrl 文件路径
 */
export function downloadByUrl(fileUrl: string) {
  const iframe = document.createElement('iframe');
  iframe.style.display = 'none';
  iframe.src = fileUrl;
  document.body.appendChild(iframe);
  iframe.onload = function () {
    document.body.removeChild(iframe);
  };
}

/**
 * 通过请求headers信息获取文件名
 * @param {object} headers 响应头
 * @param {string} defaultFileName 默认文件名称
 * @returns {string} 文件名称
 */
export function getFileNameByHeaders(headers: Record<string, any>, defaultFileName = 'download') {
  if (headers['content-disposition'] && new RegExp('utf-8', 'i').test(headers['content-disposition'])) {
    return decodeURI(headers['content-disposition'].split(';')[1].split("UTF-8''")[1]);
  } else {
    return defaultFileName;
  }
}

/**
 * 下载文件
 * @param {Blob|string} file 文件Blob或文件url
 * @param {string} fileName 文件名称
 */
export function download(file: Blob | string, fileName = '下载文件') {
  if (file instanceof Blob) {
    downloadByBlob(file, fileName);
  } else if (typeof file === 'string') {
    downloadByUrl(file);
  } else {
    throw new Error('下载文件参数不合法。');
  }
}

/**
 * 将blob 解析为 JSON
 * @param {Blob} file 文件Blob
 */
export function parseBlobAsJSON(blob: Blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const json = JSON.parse(reader.result as any);
        resolve(json);
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('解析 Blob 失败', error);
        reject(new Error('解析 Blob 失败'));
      }
    };
    reader.onerror = () => reject(new Error('读取 Blob 失败'));
    reader.readAsText(blob);
  });
}

type Option = {
  /**
   * 下载文件的名称，默认为 'download'
   */
  fileName?: string;
  /**
   * 密级（传入则文件名称按格式自动拼接密级）
   */
  secLv?: string;
};

export async function BusinessDownload(
  // 请求函数，用于获取下载文件
  request: (...args: any[]) => Promise<any>,
  // 请求函数的参数
  args: any[],
  option: Option = {},
) {
  let { fileName = 'download' } = option;

  try {
    // 调用请求函数获取响应
    const res = await request(...args);
    /* 
      如果返回二进制流  响应头中 content-type  为 application/octet-stream
      反之 说明请求被拦截，返回了错误信息
      因为前端设置了响应头为  blob 所以不能直接拿到错误码和错误信息 使用parseBlobAsJSON 解析为json
    */
    if (res.headers['content-type'].includes('application/json')) {
      // 解析错误信息
      const resData = await parseBlobAsJSON(res.data);
      message.error(get(resData, 'msg', '下载失败。'));
      return;
    }

    // 从响应中获取文件数据
    const file = get<Blob>(res, 'data');
    // 创建 Blob 对象
    const blob = new Blob([file]);
    // 根据响应头获取文件名，如果没有则使用默认文件名，并根据密级拼接
    fileName = getFileNameByHeaders(res.headers, fileName);
    downloadByBlob(blob, fileName);
  } catch (error) {
    // 捕获并打印错误信息
    // eslint-disable-next-line no-console
    console.error('ModalConfirmDownload Error', error);
    // 显示错误消息
    message.error('下载失败。');
  }
}




export async function ViewPdfBlob(
  // 请求函数，用于获取下载文件
  request: (...args: any[]) => Promise<any>,
  // 请求函数的参数
  args: any[],
  option: Option = {},
) {

  try {
    const res = await request(...args);
    if (res.headers['content-type'].includes('application/json')) {
      // 解析错误信息
      // @ts-ignore
      const resData = await parseBlobAsJSON(res.data);
      message.error(get(resData, 'msg', '文件下载失败。'));
      return;
    }

    var binaryData = [];
    binaryData.push(res.data);
    // 记得一定要设置application的类型
    let url = window.URL.createObjectURL(
      // @ts-ignore
      new Blob(binaryData, {
        type: 'application/pdf;charset=utf-8',
      }),
    );
    if (url != null && url != undefined && url) {
      // 新页面打开
      window.open(url, '_blank');
    }
  } catch (err) {
    message.error('预览失败，请稍后重试！');
  }

}