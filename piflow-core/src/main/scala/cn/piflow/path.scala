package cn.piflow

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

trait PathHead {
  def via(ports: (String, String)): PathVia;

  def to(stopTo: String): Path;
}

trait Path extends PathHead {
  def toEdges(): Seq[Edge];

  def addEdge(edge: Edge): Path;
}

trait PathVia {
  def to(stopTo: String): Path;
}

class PathImpl() extends Path {
  val edges = ArrayBuffer[Edge]();

  override def toEdges(): Seq[Edge] = edges.toSeq;

  override def addEdge(edge: Edge): Path = {
    edges += edge;
    this;
  }

  val thisPath = this;

  override def via(ports: (String, String)): PathVia = new PathVia() {
    override def to(stopTo: String): Path = {
      edges += new Edge(edges.last.stopTo, stopTo, ports._1, ports._2);
      thisPath;
    }
  }

  override def to(stopTo: String): Path = {
    edges += new Edge(edges.last.stopTo, stopTo, "", "");
    this;
  }
}

case class Edge(stopFrom: String, stopTo: String, outport: String, inport: String) {
  override def toString() = {
    s"[$stopFrom]-($outport)-($inport)-[$stopTo]";
  }
}

object Path {
  def from(stopFrom: String): PathHead = {
    new PathHead() {
      override def via(ports: (String, String)): PathVia = new PathVia() {
        override def to(stopTo: String): Path = {
          val path = new PathImpl();
          path.addEdge(new Edge(stopFrom, stopTo, ports._1, ports._2));
          path;
        }
      }

      override def to(stopTo: String): Path = {
        val path = new PathImpl();
        path.addEdge(new Edge(stopFrom, stopTo, "", ""));
        path;
      }
    };
  }

  def of(path: (Any, String)): Path = {
    val pi = new PathImpl();

    def _addEdges(path: (Any, String)): Unit = {
      val value1 = path._1;

      //String->String
      if (value1.isInstanceOf[String]) {
        pi.addEdge(new Edge(value1.asInstanceOf[String], path._2, "", ""));
      }

      //(String->String)->String
      else if (value1.isInstanceOf[(Any, String)]) {
        val tuple = value1.asInstanceOf[(Any, String)];
        _addEdges(tuple);
        pi.addEdge(new Edge(tuple._2, path._2, "", ""));
      }

      else {
        throw new InvalidPathException(value1);
      }
    }

    _addEdges(path);
    pi;
  }
}