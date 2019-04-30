package cn.piflow.conf.bean

import cn.piflow.conf.util.{JsonUtil, MapUtil}
import cn.piflow.{FlowImpl, Path}
import net.liftweb.json.JsonDSL._
import net.liftweb.json._

import scala.util.parsing.json.JSONObject



class FlowBean {
  /*@BeanProperty*/
  var uuid : String = _
  var name : String = _
  var checkpoint : String = _
  var checkpointParentProcessId : String = _
  var runMode : String = _
  var showData : String = _

  var stops : List[StopBean] = List()
  var paths : List[PathBean] = List()

  //flow resource info
  var driverMem : String = _
  var executorNum : String = _
  var executorMem : String = _
  var executorCores : String = _

  //flow json string
  var flowJson: String = _

  def init(map : Map[String, Any]) = {

    val flowJsonOjb = JsonUtil.toJson(map)
    this.flowJson = JsonUtil.format(flowJsonOjb)

    val flowMap = MapUtil.get(map, "flow").asInstanceOf[Map[String, Any]]


    this.uuid = MapUtil.get(flowMap,"uuid").asInstanceOf[String]
    this.name = MapUtil.get(flowMap,"name").asInstanceOf[String]
    this.checkpoint = flowMap.getOrElse("checkpoint","").asInstanceOf[String]
    this.checkpointParentProcessId = flowMap.getOrElse("checkpointParentProcessId", "").asInstanceOf[String]
    this.runMode = flowMap.getOrElse("runMode","RUN").asInstanceOf[String]
    this.showData = flowMap.getOrElse("showData","0").asInstanceOf[String]

    this.driverMem = flowMap.getOrElse("driverMemory","1g").asInstanceOf[String]
    this.executorNum = flowMap.getOrElse("executorNumber","1").asInstanceOf[String]
    this.executorMem= flowMap.getOrElse("executorMemory","1g").asInstanceOf[String]
    this.executorCores = flowMap.getOrElse("executorCores","1").asInstanceOf[String]

    //construct StopBean List
    val stopsList = MapUtil.get(flowMap,"stops").asInstanceOf[List[Map[String, Any]]]
    stopsList.foreach( stopMap => {
      val stop = StopBean(stopMap.asInstanceOf[Map[String, Any]])
      this.stops =   stop +: this.stops
    })

    //construct PathBean List
    val pathsList = MapUtil.get(flowMap,"paths").asInstanceOf[List[Map[String, Any]]]
    pathsList.foreach( pathMap => {
      val path = PathBean(pathMap.asInstanceOf[Map[String, Any]])
      this.paths = path +: this.paths
    })

  }

  //create Flow by FlowBean
  def constructFlow()= {
    val flow = new FlowImpl();

    flow.setFlowJson(this.flowJson)
    flow.setFlowName(this.name)
    flow.setCheckpointParentProcessId(this.checkpointParentProcessId)
    flow.setRunMode(this.runMode)

    flow.setDriverMemory(this.driverMem)
    flow.setExecutorNum(this.executorNum)
    flow.setExecutorCores(this.executorCores)
    flow.setExecutorMem(this.executorMem)

    this.stops.foreach( stopBean => {
      flow.addStop(stopBean.name,stopBean.constructStop())
    })
    this.paths.foreach( pathBean => {
      flow.addPath(Path.from(pathBean.from).via(pathBean.outport, pathBean.inport).to(pathBean.to))
    })

    if(!this.checkpoint.equals("")){
      val checkpointList = this.checkpoint.split(",")
      checkpointList.foreach{checkpoint => flow.addCheckPoint(checkpoint)}
    }

    flow
  }

  def toJson():String = {
    val json =
      ("flow" ->
        ("uuid" -> this.uuid) ~
          ("name" -> this.name) ~
          ("stops" ->
            stops.map { stop =>(
              ("uuid" -> stop.uuid) ~
                ("name" -> stop.name)~
                ("bundle" -> stop.bundle) )}) ~
          ("paths" ->
            paths.map { path => (
              ("from" -> path.from) ~
                ("outport" -> path.outport) ~
                ("inport" -> path.inport) ~
                ("to" -> path.to)
              )}))
    val jsonString = compactRender(json)
    //println(jsonString)
    jsonString
  }

}

object FlowBean{
  def apply(map : Map[String, Any]): FlowBean = {
    val flowBean = new FlowBean()
    flowBean.init(map)
    flowBean
  }

}
