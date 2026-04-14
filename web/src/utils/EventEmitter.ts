/**
 * 表示一个事件监听器函数的类型。
 * @template T 事件数据的类型
 */
type Listener<T> = (data: T) => void;

/**
 * EventEmitter 类实现了一个类型安全的事件发射器。
 * 它允许你注册事件监听器，发射事件，以及管理事件监听器。
 *
 * @template EventMap 一个记录类型，定义了事件名称到事件数据类型的映射
 *
 * @example
 * // 定义事件映射
 * interface MyEvents {
 *   'user:login': { userId: string; timestamp: number };
 *   'user:logout': { userId: string; timestamp: number };
 *   'message': string;
 * }
 *
 * // 创建 EventEmitter 实例
 * const emitter = new EventEmitter<MyEvents>();
 *
 * // 添加事件监听器
 * emitter.on('user:login', ({ userId, timestamp }) => {
 *   console.log(`User ${userId} logged in at ${new Date(timestamp).toISOString()}`);
 * });
 *
 * // 发射事件
 * emitter.emit('user:login', { userId: 'user123', timestamp: Date.now() });
 */
export class EventEmitter<EventMap = Record<string, any>> {
  /**
   * 存储所有注册的事件监听器。
   * 键是事件名称，值是该事件的监听器数组。
   */
  private listeners: {
    [K in keyof EventMap]?: Listener<EventMap[K]>[];
  } = {};

  /**
   * 为指定的事件添加一个监听器。
   * @param event 要监听的事件名称
   * @param listener 当事件被触发时要调用的函数
   *
   * @example
   * emitter.on('user:login', ({ userId, timestamp }) => {
   *   console.log(`User ${userId} logged in at ${new Date(timestamp).toISOString()}`);
   * });
   */
  on<K extends keyof EventMap>(event: K, listener: Listener<EventMap[K]>): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]!.push(listener);
  }

  /**
   * 从指定的事件中移除一个监听器。
   * @param event 事件名称
   * @param listener 要移除的监听器函数
   *
   * @example
   * const loginListener = ({ userId, timestamp }) => {
   *   console.log(`User ${userId} logged in at ${new Date(timestamp).toISOString()}`);
   * };
   * emitter.on('user:login', loginListener);
   * // ... 之后
   * emitter.off('user:login', loginListener);
   */
  off<K extends keyof EventMap>(event: K, listener: Listener<EventMap[K]>): void {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event]!.filter((l) => l !== listener);
  }

  /**
   * 触发指定的事件，调用所有注册的监听器。
   * @param event 要触发的事件名称
   * @param data 要传递给监听器的数据
   *
   * @example
   * emitter.emit('user:login', { userId: 'user123', timestamp: Date.now() });
   */
  emit<K extends keyof EventMap>(event: K, data: EventMap[K]): void {
    if (!this.listeners[event]) return;
    this.listeners[event]!.forEach((listener) => listener(data));
  }

  /**
   * 为指定的事件添加一个只会触发一次的监听器。
   * 在事件被触发后，监听器会自动被移除。
   * @param event 要监听的事件名称
   * @param listener 当事件被触发时要调用的函数
   *
   * @example
   * emitter.once('message', (message) => {
   *   console.log(`Received message (once): ${message}`);
   * });
   */
  once<K extends keyof EventMap>(event: K, listener: Listener<EventMap[K]>): void {
    const onceListener: Listener<EventMap[K]> = (data) => {
      listener(data);
      this.off(event, onceListener);
    };
    this.on(event, onceListener);
  }

  /**
   * 清除所有注册的事件监听器。
   * 这个方法会重置 EventEmitter 实例到其初始状态。
   *
   * @example
   * emitter.clear();
   * // 所有之前注册的监听器现在都被移除了
   */
  clear(): void {
    this.listeners = {};
  }
}
