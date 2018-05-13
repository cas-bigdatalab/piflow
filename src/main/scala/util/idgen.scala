package cn.piflow.util

import java.util.concurrent.atomic.AtomicInteger

import scala.collection.mutable.{Map => MMap}

trait IdGenerator {
  def generateId(): Int;
}

object IdGenerator {
  val map = MMap[String, IdGenerator]();

  def getNextId[T](implicit manifest: Manifest[T]) = map.getOrElseUpdate(manifest.runtimeClass.getName,
    new IdGenerator() {
      val ai = new AtomicInteger();

      def generateId(): Int = ai.incrementAndGet();
    })
}
