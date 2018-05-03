package cn.piflow

import java.util.Date
import java.util.concurrent.atomic.AtomicInteger

import cn.piflow.util.FormatUtils

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

/**
  * Created by bluejoe on 2018/5/2.
  */

trait Chain {
  def addProcess(name: String, process: Process, comment: String = null): String;

  def scheduleAt(time: Date);

  def scheduleAfter(processId: String, predecessors: String*);
}

trait Execution {
  def awaitComplete();
}

trait Runner {
  def run(chain: Chain, starts: String*): Execution;

  def run(chain: Chain): Execution;
}

trait ProcessContext {

}

trait Process {
  def run(pc: ProcessContext);
}


class ChainImpl extends Chain {
  val graph = new FlowGraph[ProcessInfo, String]();

  case class ProcessInfo(name: String, process: Process, comment: String) {
  }

  def getProcessInfo(id: String): ProcessInfo = graph.getNodeValue(id.toInt).asInstanceOf[ProcessInfo];

  def addProcess(name: String, process: Process, comment: String = null) = {
    val id = graph.createNode(new ProcessInfo(name, process, comment));
    "" + id;
  }

  def scheduleAfter(processId: String, predecessors: String*) = {
    predecessors.foreach { (predecessor) =>
      graph.link(predecessor.toInt, processId.toInt, "run after");
    }
  }

  def getSuccessorNodes(nodeId: String): Seq[String] = {
    graph.getSuccessorEdges(nodeId.toInt).map("" + _.to);
  }

  def getPredecessorNodes(nodeId: String): Seq[String] = {
    graph.getPredecessorEdges(nodeId.toInt).map("" + _.from);
  }
}

class RunnerImpl extends Runner {
  def run(chain: Chain, starts: String*): Execution = {
    new ExecutionImpl(chain.asInstanceOf[ChainImpl], starts);
  }

  def run(chain: Chain): Execution = {
    new ExecutionImpl(chain.asInstanceOf[ChainImpl], Seq());
  }
}

class ExecutionImpl(chain: ChainImpl, starts: Seq[String]) extends Execution {
  def awaitComplete() = {
    if (!starts.isEmpty) {
      val todo = ArrayBuffer[String]();
      val completed = ArrayBuffer[String]();
      todo ++= starts;
      while (!todo.isEmpty) {
        val one = todo.head;
        //are all predecessor processes done?
        val pns = chain.getPredecessorNodes(one);
        val readyToRun = pns.filter(!completed.contains(_)).isEmpty;
        if (readyToRun) {
          val pi = chain.getProcessInfo(one);
          pi.process.run(null);

          completed += one;
          todo.remove(0);
          todo ++= chain.getSuccessorNodes(one);
        }
      }
    }
    //TODO: timer triggers
  }
}

class FlowGraph[NodeValue, EdgeValue] {
  private val nodeMap = MMap[Int, NodeValue]();
  private val edges = ArrayBuffer[GraphEdge]();
  private val nodeIdSerial = new AtomicInteger(0);

  class GraphEdge(val from: Int, val to: Int, val label: EdgeValue) {
    def valueFrom() = nodeMap(from);

    def valueTo() = nodeMap(to);
  }

  def createNode(value: NodeValue): Int = {
    val nid = nodeIdSerial.incrementAndGet();
    nodeMap(nid) = value;
    nid;
  }

  def getNodeValue(nodeId: Int) = nodeMap(nodeId);

  def getSuccessorEdges(nodeId: Int): Seq[GraphEdge] = {
    edges.filter(_.from == nodeId);
  }

  def getPredecessorEdges(nodeId: Int): Seq[GraphEdge] = {
    edges.filter(_.to == nodeId);
  }

  def link(from: Int, to: Int,
           label: EdgeValue): FlowGraph[NodeValue, EdgeValue] = {
    edges += new GraphEdge(from, to, label);
    this;
  }

  def show() {
    val data = edges
      .map { edge: GraphEdge ⇒
        val startNodeId = edge.from;
        val endNodeId = edge.to;
        Seq[Any](edge.from -> edge.to,
          s"$startNodeId->$endNodeId",
          edge.valueFrom(),
          edge.valueTo(),
          edge.label)
      }.sortBy(_.apply(0).asInstanceOf[(Int, Int)]).map(_.drop(1));

    FormatUtils.printTable(Seq("", "from", "to", "label"), data);
  }
}