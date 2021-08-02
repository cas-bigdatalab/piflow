package cn.piflow.conf.bean

import cn.piflow._

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class DataCenterTaskPlan {

  var name = ""
  var uuid = ""

  var edges = List[PathBean]();
  val stops = MMap[String, StopBean]();

  val incomingEdges = MMap[String, ArrayBuffer[PathBean]]()
  val outgoingEdges = MMap[String, ArrayBuffer[PathBean]]()

  def init(flow: FlowBean) = {
    this.edges = flow.paths
    flow.stops.foreach{s =>
      this.stops(s.name) = s
    }
    edges.foreach { edge =>
      incomingEdges.getOrElseUpdate(edge.to, ArrayBuffer[PathBean]()) += edge;
      outgoingEdges.getOrElseUpdate(edge.from, ArrayBuffer[PathBean]()) += edge;
    }
  }

  def visit(flow: FlowBean/*, op: (String) => T*/): Unit = {

    init(flow)
    val ends = stops.keys.filterNot(outgoingEdges.contains(_));
    val visited = MMap[String, Boolean]();
    ends.foreach {
      _visitStop(flow, _, /*op,*/ visited);
    }
  }

  /*def _visitStop[T](flow: FlowBean, stopName: String, /*op: (String) => T, */visited: MMap[String, T]): T = {
    if (!visited.contains(stopName)) {

      //executes dependent processes
      val inputs =
        if (incomingEdges.contains(stopName)) {
          //all incoming edges
          val edges = incomingEdges(stopName);
          edges.map { edge =>
            edge ->
              _visitStop(flow, edge.from, /*op, */visited);
          }.toMap
        }
        else {
          Map[PathBean, T]();
        }

      //val ret = op(flow,stopName);
      val ret = setDataCenter(stopName)
      visited(stopName) = ret;
      ret;
    }
    else {
      visited(stopName);
    }
  }*/

  def _visitStop(flow: FlowBean, stopName: String,visited: MMap[String, Boolean]): Boolean = {
    if (!visited.contains(stopName)) {

      if (incomingEdges.contains(stopName)) {
        //all incoming edges
        val edges = incomingEdges(stopName);
        edges.foreach { edge =>
          edge ->
            _visitStop(flow, edge.from, /*op, */visited);
        }
      }

      //val ret = op(flow,stopName);
      val ret = setDataCenter(stopName)
      visited(stopName) = ret;
      ret;
    }
    else {
      visited(stopName);
    }
  }

  def setDataCenter(stopName: String) : Boolean = {

    val stop = stops.getOrElse(stopName,None).asInstanceOf[StopBean]
    if(stop.dataCenter == ""){

      val inEdges = incomingEdges(stopName)
      val outEdges = outgoingEdges(stopName)

      val fromDataCenterMap = MMap[String, Int]()
      val toDataCenterMap = MMap[String, Int]()

      inEdges.foreach{edge => {
        val fromStop = edge.from
        val fromStopDataCenter = stops(fromStop).dataCenter

        val dcCount = fromDataCenterMap.getOrElse(fromStopDataCenter,0)
        fromDataCenterMap(fromStopDataCenter) = dcCount + 1
      }}

      outEdges.foreach{edge => {
        val toStop = edge.to
        val toStopDataCenter = stops(toStop).dataCenter

        val dcCount = toDataCenterMap.getOrElse(toStopDataCenter,0)
        toDataCenterMap(toStopDataCenter) = dcCount + 1
      }}

      if(fromDataCenterMap.keySet.size == 0){
        false
      }
      else if (fromDataCenterMap.keySet.size == 1){

        stop.dataCenter = fromDataCenterMap.keySet.take(0).asInstanceOf[String]

      }else{
        val intersect = fromDataCenterMap.keySet.intersect(toDataCenterMap.keySet)
        if(intersect.size > 0){
          stop.dataCenter = intersect.iterator.next()
        }else{
          stop.dataCenter = fromDataCenterMap.keySet.iterator.next()
        }
      }
    }
    true
  }
}
object DataCenterTaskPlan{
  def apply(): DataCenterTaskPlan = {
    val plan = new DataCenterTaskPlan()
    //plan.initEdges()
    plan
  }
}


