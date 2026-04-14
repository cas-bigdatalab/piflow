/**
 * 手动触发 document 事件的函数
 *
 * @param {string} eventName - 要触发的事件名称
 * @param {any} eventData - 事件的附加数据（可选）
 * @param {boolean} bubbles - 事件是否冒泡（默认为 true）
 * @param {boolean} cancelable - 事件是否可取消（默认为 true）
 *
 * @example
 * // 触发一个简单的自定义事件
 * triggerDocumentEvent('myCustomEvent');
 *
 * // 监听并响应自定义事件
 * document.addEventListener('myCustomEvent', () => {
 *   console.log('myCustomEvent was triggered!');
 * });
 * triggerDocumentEvent('myCustomEvent');
 *
 * @example
 * // 触发带有自定义数据的事件
 * triggerDocumentEvent('userAction', { userId: 123, action: 'click' });
 *
 * // 监听并使用自定义数据
 * document.addEventListener('userAction', (e: CustomEvent) => {
 *   console.log(`User ${e.detail.userId} performed ${e.detail.action}`);
 * });
 *
 * @example
 * // 触发不冒泡的事件
 * triggerDocumentEvent('nonBubblingEvent', {}, false);
 *
 * @example
 * // 触发不可取消的事件
 * triggerDocumentEvent('unCancelableEvent', {}, true, false);
 */
export function triggerDocumentEvent(
  eventName: string,
  eventData: any = {},
  bubbles: boolean = true,
  cancelable: boolean = true,
): void {
  const event = new CustomEvent(eventName, {
    bubbles,
    cancelable,
    detail: eventData,
  });
  document.dispatchEvent(event);
}
