/**
 * 发送聊天消息
 */

import { requestFormData, requestJson } from "@/utils/request";

export const sendMessage: FT.Request = (data: FT.Object) =>
  requestJson({
    url: "/chat",
    method: "POST",
    data,
  });

export const getHistory: FT.Request = (data: FT.Object) =>
  requestJson({
    url: "/threads/getTitles",
    method: "POST",
    data,
  });

export const deleteThread: FT.Request = (data: FT.Object) =>
  requestJson({
    url: "/thread/delete",
    method: "POST",
    data,
  });

export const getThreadMessages: FT.Request = (data: FT.Object) =>
  requestJson({
    url: "/thread/messages",
    method: "POST",
    data,
  });

export const uploadFile: FT.Request = (data: FT.Object) =>
  requestFormData({
    url: "/workspace/upload",
    method: "POST",
    data,
  });

export const getSkills: FT.Request = (params: FT.Object) =>
  requestJson({
    url: "/skills/list",
    method: "GET",
    params,
  });
