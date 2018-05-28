package cn.piflow

import scala.collection.mutable.{Map => MMap}

trait Context {
  def get(key: String): Any;

  def get[T]()(implicit m: Manifest[T]): T = {
    get(m.runtimeClass.getName).asInstanceOf[T];
  }

  def put(key: String, value: Any): this.type;

  def put[T](value: T)(implicit m: Manifest[T]): this.type =
    put(m.runtimeClass.getName, value);
}

class CascadeContext(parent: Context = null) extends Context {
  val map = MMap[String, Any]();

  override def get(key: String): Any = {
    if (map.contains(key)) {
      map(key);
    }
    else {
      if (parent != null)
        parent.get(key);
      else
        null;
    }
  };

  override def put(key: String, value: Any): this.type = {
    map(key) = value;
    this;
  }
}
