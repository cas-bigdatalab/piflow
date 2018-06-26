package cn.piflow.element

import java.io.File

import cn.piflow._

import scala.collection.mutable.{Map => MMap}

object FlowElement {
  def fromFile(file: File): FlowElement = {
    null;
  }

  def saveFile(flowElement: FlowElement, file: File): Unit = {
  }
}

class FlowElement {
  def build(): Flow = {
    null;
  }
}

trait FlowElementManager {
  def list(): Seq[(String, FlowElement)];

  def get(name: String): Option[FlowElement];

  def add(name: String, flowJson: FlowElement): Unit;

  def delete(name: String): Unit;
}

class InMemoryFlowElementManager extends FlowElementManager {
  val items = MMap[String, FlowElement]();

  override def list(): Seq[(String, FlowElement)] = items.toSeq;

  override def get(name: String): Option[FlowElement] = items.get(name);

  override def delete(name: String) = items - name;

  override def add(name: String, flowJson: FlowElement) {
    items(name) = flowJson;
  }
}

class SqlFlowElementManager /* extends FlowJsonManager */ {

}

class FileSystemFlowElementManager {

}