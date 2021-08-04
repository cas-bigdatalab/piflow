package cn.piflow.conf.bean

import java.util.UUID

import scala.collection.mutable.{ArrayBuffer, Map => MMap}


class DataCenterFlowBean{


  var flowBean : FlowBean = _

  var edges = List[PathBean]();
  val stops = MMap[String, StopBean]();

  val incomingEdges = MMap[String, ArrayBuffer[PathBean]]()
  val outgoingEdges = MMap[String, ArrayBuffer[PathBean]]()


  def initFlowBean(map : Map[String, Any]) = {
    this.flowBean = FlowBean(map)
  }

  def initParams(flowBean: FlowBean) = {
    this.flowBean = flowBean
    this.edges = flowBean.paths
    flowBean.stops.foreach{s =>
      s.flowName = ""
      this.stops(s.name) = s
    }
    edges.foreach { edge =>
      incomingEdges.getOrElseUpdate(edge.to, ArrayBuffer[PathBean]()) += edge;
      outgoingEdges.getOrElseUpdate(edge.from, ArrayBuffer[PathBean]()) += edge;
    }
  }
  //create Flow by FlowBean
  def constructDataCenterGroupBean() : DataCenterGroupBean= {

    val flowCount = DataCenterTaskPlan(this.flowBean).plan()
    initParams(this.flowBean)
    constructDataCenterGroupBean(this.flowBean, flowCount)
  }

  def constructDataCenterGroupBean(flow: FlowBean, flowCount:Int) : DataCenterGroupBean = {

    val ends = stops.keySet.filterNot(outgoingEdges.contains(_));
    val visited = MMap[String, String]();
    for(i <- 1 to flowCount){
      val flowName = "flow_" + i
      val iteratorStop = ends.diff(visited.keySet).iterator.next()
      _visitStop(flow, iteratorStop, visited, flowName)
    }


    var flowBeanList = List[GroupEntryBean]()
    for(i <- 1 to flowCount){

      //construct flowBean
      val flowName = "flow_" + i
      val flowBean = getFlowBean("",flowName )
      var stopBeanList =  List[StopBean]()
      var pathBeanList = List[PathBean]()
      visited.foreach{m => {
        val tempStopName = m._1
        val tempFlowName = m._2
        if(tempFlowName == flowName){
          stopBeanList = stops(tempStopName) +: stopBeanList
          if(outgoingEdges.contains(tempStopName))
            pathBeanList = outgoingEdges(tempStopName).toList ::: pathBeanList
        }
      }}
      flowBean.stops = stopBeanList
      flowBean.paths = pathBeanList
      flowBean.dataCenter = stopBeanList(0).dataCenter

      //DataCenterGroupBean
      flowBeanList = flowBean +: flowBeanList
      //conditions
      //path
    }

    null
  }

  def _visitStop(flow: FlowBean, stopName: String,visited: MMap[String, String], flowName:String): String = {

    if (!visited.contains(stopName)) {

      visited(stopName) = flowName

      if (incomingEdges.contains(stopName)) {
        //all incoming edges
        val edges = incomingEdges(stopName);
        edges.foreach { edge =>
          if(!visited.contains(edge.from))
            _visitStop(flow, edge.from, visited,flowName);
        }
      }

      if (outgoingEdges.contains(stopName)) {
        //all outgoing edges
        val edges = outgoingEdges(stopName);
        edges.foreach { edge =>
          if(!visited.contains(edge.to))
            _visitStop(flow, edge.to, visited,flowName);
        }
      }

      flowName
    }
    else {
      visited(stopName);
    }
  }

  private def  getFlowBean(dataCenter:String, flowName:String) : FlowBean = {
    val map = Map[String, Any]("uuid" -> UUID.randomUUID.toString,
      "name" -> flowName,
      "dataCenter" -> dataCenter,
      "stops" -> List[Map[String,Any]](),
      "paths" -> List[Map[String,Any]]()

    )
    FlowBean(Map[String, Any]("flow" -> map))
  }


}

object DataCenterFlowBean{
  def apply(map : Map[String, Any]): DataCenterFlowBean = {
    val dcFlowBean = new DataCenterFlowBean()
    dcFlowBean.initFlowBean(map)
    dcFlowBean
  }
}


