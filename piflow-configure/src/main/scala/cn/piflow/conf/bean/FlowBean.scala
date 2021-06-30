package cn.piflow.conf.bean

import cn.piflow.conf.util.{MapUtil, ScalaExecutorUtil}
import cn.piflow.util.JsonUtil
import cn.piflow.{FlowImpl, GroupEntry, Path}
import net.liftweb.json.JsonDSL._
import net.liftweb.json._

import scala.util.matching.Regex
import scala.collection.mutable.{Map => MMap}



class FlowBean extends GroupEntryBean{
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

  //flow environment variable
  var environmentVariable : Map[String, Any] = _

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

    this.environmentVariable = flowMap.getOrElse("environmentVariable", Map()).asInstanceOf[Map[String, Any]]

    //construct StopBean List
    val stopsList = MapUtil.get(flowMap,"stops").asInstanceOf[List[Map[String, Any]]]

    //replace environment variable
    if(this.environmentVariable.keySet.size != 0){
      val pattern = new Regex("\\$\\{+[^\\}]*\\}")
      stopsList.foreach( stopMap => {
        val stopMutableMap = MMap(stopMap.toSeq: _*)
        var stopPropertiesMap = MapUtil.get(stopMutableMap, "properties").asInstanceOf[MMap[String, Any]]
        stopPropertiesMap.keySet.foreach{ key => {

          var value = MapUtil.get(stopPropertiesMap,key).asInstanceOf[String]

          val it = (pattern findAllIn value)
          while (it.hasNext){
            val item = it.next()
            val newValue = value.replace(item,MapUtil.get(environmentVariable,item).asInstanceOf[String])
            stopPropertiesMap(key) = newValue
            println(key + " -> " + newValue)
          }
        }}
        stopMutableMap("properties") = stopPropertiesMap.toMap
        val stop = StopBean(this.name, stopMutableMap.toMap)
        this.stops =   stop +: this.stops
      })
    }else{//no environment variables
      stopsList.foreach( stopMap => {
        val stop = StopBean(this.name, stopMap)
        this.stops =   stop +: this.stops
      })
    }


    //construct PathBean List
    val pathsList = MapUtil.get(flowMap,"paths").asInstanceOf[List[Map[String, Any]]]
    pathsList.foreach( pathMap => {
      val path = PathBean(pathMap.asInstanceOf[Map[String, Any]])
      this.paths = path +: this.paths
    })

  }

  //create Flow by FlowBean
  def constructFlow(buildScalaJar : Boolean = true)= {

    if(buildScalaJar == true)
      ScalaExecutorUtil.buildScalaExcutorJar(this)

    val flow = new FlowImpl();

    flow.setFlowJson(this.flowJson)
    flow.setFlowName(this.name)
    flow.setUUID(uuid)
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
