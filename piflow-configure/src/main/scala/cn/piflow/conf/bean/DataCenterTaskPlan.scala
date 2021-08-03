package cn.piflow.conf.bean

import java.util.UUID

import cn.piflow._

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class DataCenterTaskPlan {

  var name = ""
  var uuid = ""

  var flowBean: FlowBean = _

  var edges = List[PathBean]();
  val stops = MMap[String, StopBean]();

  val incomingEdges = MMap[String, ArrayBuffer[PathBean]]()
  val outgoingEdges = MMap[String, ArrayBuffer[PathBean]]()

  def init(flowBean: FlowBean) = {
    this.flowBean = flowBean
    this.edges = flowBean.paths
    flowBean.stops.foreach{s =>
      this.stops(s.name) = s
    }
    edges.foreach { edge =>
      incomingEdges.getOrElseUpdate(edge.to, ArrayBuffer[PathBean]()) += edge;
      outgoingEdges.getOrElseUpdate(edge.from, ArrayBuffer[PathBean]()) += edge;
    }
  }

  def plan() : DataCenterGroupBean = {
    initDataCenter(flowBean)
    constructDataCenterGroupBean(flowBean)
  }

  def initDataCenter(flow: FlowBean): Unit = {

    init(flow)
    val ends = stops.keys.filterNot(outgoingEdges.contains(_));
    val visited = MMap[String, Boolean]();
    ends.foreach {
      _visitStop(flow, _, visited);
    }
  }

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

  def constructDataCenterGroupBean(flow: FlowBean): DataCenterGroupBean = {

    //DataCenterGroupBean()
    var newStop = List[StopBean]()
    var newPath = List[PathBean]()
    var removePath = List[PathBean]()
    var flowCount = 1
    flow.paths.foreach(path => {

      val from = path.from
      val to = path.to

      if(stops(from).dataCenter != stops(to).dataCenter){
        //flowoutport
        val flowOutportDataCenter = stops(from).dataCenter
        val flowOutportName = "FlowOutportWriter_" + flowCount
        val flowOutportWriter = getFlowOutportWriter(flowOutportDataCenter, flow.name, flowOutportName)
        val flowOutportPathBean = PathBean(from, path.outport, "", flowOutportName)

        //flow inport
        val flowInportDataCenter = stops(to).dataCenter
        val flowInportName = "FlowInportReader_" + flowCount
        val flowInportReader = getFlowInportReader(flowInportDataCenter, flow.name, flowInportName)
        val flowInportPathBean = PathBean(flowInportName, "", path.inport, to)

        //add new stop
        newStop = flowOutportWriter +: newStop
        newStop = flowInportReader +: newStop

        //add new path
        newPath = flowOutportPathBean +: newPath
        newPath = flowInportPathBean +: newPath

        //remove path
        removePath = path +: removePath
        flowCount = flowCount + 1
      }
    })

    flow.stops = flow.stops.union(newStop)
    flow.paths = flow.paths.diff(removePath)
    flow.paths = flow.paths.union(newPath)


    //TODO
    null
  }

  private def getFlowOutportWriter(dataCenter:String, flowName:String, stopName:String) : StopBean = {
    val map = Map[String, Any]("uuid" -> UUID.randomUUID.toString,
      "name" -> stopName,
      "bundle" -> "cn.piflow.bundle.FlowPort.FlowOutportWriter",
      "properties" -> Map[String,String](),
      "dataCenter" -> dataCenter
    )
    StopBean(flowName, map)

  }

  private def getFlowInportReader(dataCenter:String, flowName:String, stopName:String) : StopBean = {
    val map = Map[String, Any]("uuid" -> UUID.randomUUID.toString,
      "name" -> stopName,
      "bundle" -> "cn.piflow.bundle.FlowPort.FlowInportReader",
      "properties" -> Map[String,String]("dataSource" -> ""),
      "dataCenter" -> dataCenter
    )
    StopBean(flowName, map)

  }
}
object DataCenterTaskPlan{
  def apply(flowBean: FlowBean): DataCenterTaskPlan = {
    val plan = new DataCenterTaskPlan()
    plan.init(flowBean)
    plan
  }
}


