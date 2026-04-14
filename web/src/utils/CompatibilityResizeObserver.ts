type Size = { width: number; height: number };
type ResizeCallback = (size: Size) => void;

interface CompatibilityResizeObserverOptions {
  debounceTime?: number; // 防抖时间，单位为毫秒
  observeParent?: boolean; // 是否观察父元素的变化，默认为 true
}

/**
 * CompatibilityResizeObserver 类实现了一个兼容性良好的元素尺寸变化观察器。
 * 它支持现代浏览器的 ResizeObserver，并为不支持 ResizeObserver 的浏览器提供了降级方案（MutationObserver + requestAnimationFrame）。
 * 它还支持防抖功能，以避免频繁触发回调。
 *
 * @template Size 定义了尺寸的类型，包含 width 和 height
 * @template ResizeCallback 定义了尺寸变化时的回调函数类型
 * @template CompatibilityResizeObserverOptions 定义了配置选项的类型
 *
 * @example
 * // 创建 CompatibilityResizeObserver 实例
 * const target = document.getElementById('element');
 * const observer = new CompatibilityResizeObserver(
 *   target,
 *   (size) => console.log('Size changed:', size),
 *   { debounceTime: 100 }
 * );
 *
 * // 当不再需要监听时调用 dispose 方法
 * observer.dispose();
 */
export class CompatibilityResizeObserver {
  private element: Element; // 被观察的目标元素
  private callback: ResizeCallback; // 尺寸变化时的回调函数
  private options: CompatibilityResizeObserverOptions; // 配置选项

  private resizeObserver: ResizeObserver | null = null; // ResizeObserver 实例
  private resizeObserverParent: ResizeObserver | null = null; // 父元素的 ResizeObserver 实例
  private mutationObserver: MutationObserver | null = null; // MutationObserver 实例（降级方案）
  private rafId: number | null = null; // requestAnimationFrame 的 ID
  private debounceTimeout: ReturnType<typeof setTimeout> | null = null; // 防抖定时器
  private lastSize: Size = { width: 0, height: 0 }; // 上一次记录的尺寸

  /**
   * 构造函数，初始化 CompatibilityResizeObserver 实例
   *
   * @param element 被观察的目标元素
   * @param callback 当尺寸变化时调用的回调函数
   * @param options 配置选项，包括防抖时间和是否观察父元素
   *
   * @example
   * const target = document.getElementById('element');
   * const observer = new CompatibilityResizeObserver(
   *   target,
   *   (size) => console.log('Size changed:', size),
   *   { debounceTime: 100 }
   * );
   */
  constructor(element: Element, callback: ResizeCallback, options: CompatibilityResizeObserverOptions = {}) {
    this.element = element;
    this.callback = callback;
    this.options = {
      debounceTime: 0,
      observeParent: true,
      ...options,
    };

    this.initialize();
  }

  /**
   * 初始化观察器，根据浏览器支持情况选择 ResizeObserver 或降级方案
   */
  private initialize() {
    this.updateSize(); // 初始尺寸测量

    if (typeof ResizeObserver !== 'undefined') {
      this.setupResizeObservers(); // 使用 ResizeObserver
    } else {
      this.setupFallbackObservers(); // 使用降级方案
    }
  }

  /**
   * 更新尺寸信息，并在尺寸变化时调用回调函数
   */
  private updateSize = () => {
    const rect = this.element.getBoundingClientRect();
    const newSize = { width: rect.width, height: rect.height };

    // 只有当尺寸发生变化时才调用回调函数
    if (newSize.width !== this.lastSize.width || newSize.height !== this.lastSize.height) {
      this.lastSize = newSize;
      this.callback(newSize);
    }
  };

  /**
   * 防抖版本的更新尺寸函数，避免频繁触发回调
   */
  private debouncedUpdateSize = () => {
    if (this.debounceTimeout) clearTimeout(this.debounceTimeout);
    this.debounceTimeout = setTimeout(this.updateSize, this.options.debounceTime);
  };

  /**
   * 设置 ResizeObserver，用于现代浏览器
   */
  private setupResizeObservers() {
    this.resizeObserver = new ResizeObserver(this.debouncedUpdateSize);
    this.resizeObserver.observe(this.element);

    // 如果配置了观察父元素，则设置父元素的 ResizeObserver
    if (this.options.observeParent) {
      const parent = this.element.parentElement;
      if (parent) {
        this.resizeObserverParent = new ResizeObserver(this.debouncedUpdateSize);
        this.resizeObserverParent.observe(parent);
      }
    }
  }

  /**
   * 设置降级方案，用于不支持 ResizeObserver 的浏览器
   */
  private setupFallbackObservers() {
    // 使用 MutationObserver 监听目标元素的属性、子元素等变化
    this.mutationObserver = new MutationObserver(this.debouncedUpdateSize);
    this.mutationObserver.observe(this.element, {
      attributes: true, // 监听属性变化
      childList: true, // 监听子元素变化
      subtree: true, // 监听子树变化
      characterData: true, // 监听文本内容变化
    });

    // 监听窗口的 resize 事件
    window.addEventListener('resize', this.debouncedUpdateSize);
    // 启动 requestAnimationFrame 定期检查尺寸变化
    this.startRAFMonitoring();
  }

  /**
   * 启动 requestAnimationFrame 循环，定期检查尺寸变化
   */
  private startRAFMonitoring() {
    const check = () => {
      this.debouncedUpdateSize();
      this.rafId = requestAnimationFrame(check);
    };
    this.rafId = requestAnimationFrame(check);
  }

  /**
   * 清理所有观察器和监听器，释放资源
   *
   * @example
   * const observer = new CompatibilityResizeObserver(...);
   * observer.dispose(); // 清理资源
   */
  dispose() {
    this.resizeObserver?.disconnect(); // 断开 ResizeObserver
    this.resizeObserverParent?.disconnect(); // 断开父元素的 ResizeObserver
    this.mutationObserver?.disconnect(); // 断开 MutationObserver

    if (this.rafId) cancelAnimationFrame(this.rafId); // 取消 requestAnimationFrame
    if (this.debounceTimeout) clearTimeout(this.debounceTimeout); // 清除防抖定时器

    window.removeEventListener('resize', this.debouncedUpdateSize); // 移除窗口 resize 事件监听
  }
}
