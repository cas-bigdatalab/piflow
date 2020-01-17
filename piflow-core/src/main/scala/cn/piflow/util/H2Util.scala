package cn.piflow.util

import java.net.InetAddress
import java.sql.{Connection, DriverManager, ResultSet}
import java.util.Date

import net.liftweb.json.compactRender
import net.liftweb.json.JsonDSL._
import org.h2.tools.Server

object H2Util {

  val QUERY_TIME = 300
  val CREATE_PROJECT_TABLE = "create table if not exists project (id varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_GROUP_TABLE = "create table if not exists flowGroup (id varchar(255), projectId varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255), flowCount int)"
  val CREATE_FLOW_TABLE = "create table if not exists flow (id varchar(255), groupId varchar(255), projectId varchar(255), pid varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_STOP_TABLE = "create table if not exists stop (flowId varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_THOUGHPUT_TABLE = "create table if not exists thoughput (flowId varchar(255), stopName varchar(255), portName varchar(255), count long)"
  val CREATE_FLAG_TABLE = "create table if not exists configFlag(id bigint auto_increment, item varchar(255), flag int, createTime varchar(255))"
  val serverIP = PropertyUtil.getPropertyValue("server.ip") + ":" + PropertyUtil.getPropertyValue("h2.port")
  //val ip = InetAddress.getLocalHost.getHostAddress
  //val serverIP = ip + ":" + PropertyUtil.getPropertyValue("h2.port")
  //print("getHostAddress:" +  ip  + " in H2Util!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
  val CONNECTION_URL = "jdbc:h2:tcp://" +  serverIP + "/~/piflow;AUTO_SERVER=true"
  var connection : Connection= null

  try{

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate(CREATE_PROJECT_TABLE)
    statement.executeUpdate(CREATE_GROUP_TABLE)
    statement.executeUpdate(CREATE_FLOW_TABLE)
    statement.executeUpdate(CREATE_STOP_TABLE)
    statement.executeUpdate(CREATE_THOUGHPUT_TABLE)
    statement.executeUpdate(CREATE_FLAG_TABLE)
    statement.close()
  }catch {
    case ex => println(ex)
  }

  def getConnectionInstance() : Connection = {
    if(connection == null){
      Class.forName("org.h2.Driver")
      connection = DriverManager.getConnection(CONNECTION_URL)
    }
    connection
  }

  def cleanDatabase() = {

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort",PropertyUtil.getPropertyValue("h2.port")).start()
    try{

      val statement = getConnectionInstance().createStatement()
      statement.setQueryTimeout(QUERY_TIME)
      statement.executeUpdate("drop table if exists project")
      statement.executeUpdate("drop table if exists flowGroup")
      statement.executeUpdate("drop table if exists flow")
      statement.executeUpdate("drop table if exists stop")
      statement.executeUpdate("drop table if exists thoughput")
      statement.executeUpdate("drop table if exists flag")
      statement.close()

    } catch{
        case ex => println(ex)
    }finally {
      h2Server.shutdown()
    }

  }

  def updateToVersion6() = {
    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort",PropertyUtil.getPropertyValue("h2.port")).start()
    try{

      val ALTER_COLUMN = "alter table flowgroup add flowCount Int;"
      val statement = getConnectionInstance().createStatement()
      statement.setQueryTimeout(QUERY_TIME)
      statement.executeUpdate(CREATE_PROJECT_TABLE)
      statement.executeUpdate(CREATE_GROUP_TABLE)
      statement.executeUpdate(CREATE_THOUGHPUT_TABLE)
      statement.executeUpdate(ALTER_COLUMN)
      statement.close()

    } catch{
      case ex => println(ex)
    }finally {
      h2Server.shutdown()
    }
  }

  def addFlow(appId:String,pId:String, name:String)={
    val startTime = new Date().toString
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into flow(id, pid, name) values('" + appId + "','" + pId + "','" + name + "')")
    statement.close()
  }
  def updateFlowState(appId:String, state:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flow set state='" + state + "' where id='" + appId + "'"
    println(updateSql)
    //update related stop stop when flow state is KILLED
    if(state.equals(FlowState.KILLED)){
      val startedStopList = getStartedStop(appId)
      startedStopList.foreach(stopName => {
        updateStopState(appId,stopName,StopState.KILLED)
        updateStopFinishedTime(appId, stopName, new Date().toString)
      })
    }
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateFlowStartTime(appId:String, startTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flow set startTime='" + startTime + "' where id='" + appId + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateFlowFinishedTime(appId:String, endTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flow set endTime='" + endTime + "' where id='" + appId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def updateFlowGroupId(appId:String, groupId:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flow set groupId='" + groupId + "' where id='" + appId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def updateFlowProjectId(appId:String, ProjectId:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flow set projectId='" + ProjectId + "' where id='" + appId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def getFlowState(appId: String): String = {
    var state = ""
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val rs : ResultSet = statement.executeQuery("select * from flow where id='" + appId +"'")
    while(rs.next()){
      state = rs.getString("state")
      //println("id:" + rs.getString("id") + "\tname:" + rs.getString("name") + "\tstate:" + rs.getString("state"))
    }
    rs.close()
    statement.close()
    state
  }

  def getFlowProcessId(appId:String) : String = {
    var pid = ""
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val rs : ResultSet = statement.executeQuery("select pid from flow where id='" + appId +"'")
    while(rs.next()){
      pid = rs.getString("pid")
    }
    rs.close()
    statement.close()
    pid
  }

  def getFlowInfo(appId:String) : String = {
    /*val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    var flowInfo = ""

    val flowRS : ResultSet = statement.executeQuery("select * from flow where id='" + appId +"'")
    while (flowRS.next()){
      val progress = getFlowProgressPercent(appId:String)
      flowInfo = "{\"flow\":{\"id\":\"" + flowRS.getString("id") +
        "\",\"pid\":\"" +  flowRS.getString("pid") +
        "\",\"name\":\"" +  flowRS.getString("name") +
        "\",\"state\":\"" +  flowRS.getString("state") +
        "\",\"startTime\":\"" +  flowRS.getString("startTime") +
        "\",\"endTime\":\"" + flowRS.getString("endTime") +
        "\",\"progress\":\"" + progress +
        "\",\"stops\":["
    }
    flowRS.close()

    var stopList:List[String] = List()
    val rs : ResultSet = statement.executeQuery("select * from stop where flowId='" + appId +"'")
    while(rs.next()){
      val stopStr = "{\"stop\":{\"name\":\"" + rs.getString("name") +
        "\",\"state\":\"" +  rs.getString("state") +
        "\",\"startTime\":\"" + rs.getString("startTime") +
        "\",\"endTime\":\"" + rs.getString("endTime") + "\"}}"
      //println(stopStr)
      stopList = stopStr.toString +: stopList
    }
    rs.close()

    statement.close()
    if (!flowInfo.equals(""))
      flowInfo += stopList.mkString(",") + "]}}"

    flowInfo*/
    val flowInfoMap = getFlowInfoMap(appId)
    JsonUtil.format(JsonUtil.toJson(flowInfoMap))
  }

  def getFlowInfoMap(appId:String) : Map[String, Any] = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var flowInfoMap = Map[String, Any]()

    //get flow basic info
    val flowRS : ResultSet = statement.executeQuery("select * from flow where id='" + appId +"'")
    while (flowRS.next()){
      val progress = getFlowProgressPercent(appId:String)
      flowInfoMap += ("id" -> flowRS.getString("id"))
      flowInfoMap += ("pid" -> flowRS.getString("pid"))
      flowInfoMap += ("name" -> flowRS.getString("name"))
      flowInfoMap += ("state" -> flowRS.getString("state"))
      flowInfoMap += ("startTime" -> flowRS.getString("startTime"))
      flowInfoMap += ("endTime" -> flowRS.getString("endTime"))
      flowInfoMap += ("progress" -> progress)
    }
    flowRS.close()

    //get flow stops info
    var stopList:List[Map[String, Any]] = List()
    val rs : ResultSet = statement.executeQuery("select * from stop where flowId='" + appId +"'")
    while(rs.next()){
      var stopMap = Map[String, Any]()
      stopMap += ("name" -> rs.getString("name"))
      stopMap += ("state" -> rs.getString("state"))
      stopMap += ("startTime" -> rs.getString("startTime"))
      stopMap += ("endTime" -> rs.getString("endTime"))

      stopList = Map("stop" -> stopMap) +: stopList

    }
    rs.close()

    statement.close()

    //add flow stops info to flowInfoMap
    flowInfoMap += ("stops" -> stopList)

    Map[String, Any]("flow" -> flowInfoMap)
  }

  def getFlowProgressPercent(appId:String) : String = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var stopCount = 0
    var completedStopCount = 0
    val totalRS : ResultSet = statement.executeQuery("select count(*) as stopCount from stop where flowId='" + appId + "'")
    while(totalRS.next()){
      stopCount = totalRS.getInt("stopCount")
      //println("stopCount:" + stopCount)
    }
    totalRS.close()

    val completedRS : ResultSet = statement.executeQuery("select count(*) as completedStopCount from stop where flowId='" + appId +"' and state='" + StopState.COMPLETED + "'")
    while(completedRS.next()){
      completedStopCount = completedRS.getInt("completedStopCount")
      //println("completedStopCount:" + completedStopCount)
    }
    completedRS.close()

    val flowRS : ResultSet = statement.executeQuery("select * from flow where id='" + appId +"'")
    var flowState = ""
    while (flowRS.next()){
      flowState = flowRS.getString("state")
    }
    flowRS.close()

    statement.close()

    val progress:Double = completedStopCount.asInstanceOf[Double] / stopCount * 100
    if(flowState.equals(FlowState.COMPLETED)){
      "100"
    }else{
      progress.toString
    }
  }

  def getFlowProgress(appId:String) : String = {

    val progress = getFlowProgressPercent(appId)
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val flowRS : ResultSet = statement.executeQuery("select * from flow where id='" + appId +"'")
    var id = ""
    var name = ""
    var state = ""
    while (flowRS.next()){
      id = flowRS.getString("id")
      name =  flowRS.getString("name")
      state = flowRS.getString("state")
    }

    flowRS.close()
    val json =
      ("FlowInfo" ->
        ("appId" -> id)~
          ("name" -> name) ~
          ("state" -> state) ~
          ("progress" -> progress.toString))
    val flowProgress = compactRender(json)
    flowProgress
  }

  //Stop related API
  def addStop(appId:String,name:String)={
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into stop(flowId, name) values('" + appId + "','" + name + "')")
    statement.close()
  }
  def updateStopState(appId:String, name:String, state:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update stop set state='" + state + "' where flowId='" + appId + "' and name='" + name + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def updateStopStartTime(appId:String, name:String, startTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update stop set startTime='" + startTime + "' where flowId='" + appId + "' and name='" + name + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def updateStopFinishedTime(appId:String, name:String, endTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update stop set endTime='" + endTime + "' where flowId='" + appId + "' and name='" + name + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def getStartedStop(appId:String) : List[String] = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var stopList:List[String] = List()
    val rs : ResultSet = statement.executeQuery("select * from stop where flowId='" + appId +"' and state = '" + StopState.STARTED + "'")
    while(rs.next()){

      stopList = rs.getString("name") +: stopList
    }
    rs.close()
    statement.close()
    stopList
  }

  // Throughput related API
  def addThroughput(appId:String, stopName:String, portName:String, count:Long) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into thoughput(flowId, stopName, portName, count) values('" + appId + "','" + stopName + "','" + portName + "','" + count + "')")
    statement.close()
  }
  def getThroughput(appId:String, stopName:String, portName:String) = {
    var count = ""
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val rs : ResultSet = statement.executeQuery("select count from thoughput where flowId='" + appId +"' and stopName = '" + stopName + "' and portName = '" + portName + "'")
    while(rs.next()){
      count = rs.getString("count")
    }
    rs.close()
    statement.close()
    count
  }
  def updateThroughput(appId:String, stopName:String, portName:String, count:Long) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update thoughput set count='" + count + "' where flowId='" + appId + "' and stopName='" + stopName + "' and portName='" + portName + "'"
    statement.executeUpdate(updateSql)
    statement.close()
  }

  //flowGroup related api
  def addFlowGroup(flowGroupId:String,name:String, flowCount:Int)={
    val startTime = new Date().toString
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into flowGroup(id, name, flowCount) values('" + flowGroupId +  "','" + name + "','" + flowCount +"')")
    statement.close()
  }
  def updateFlowGroupState(flowGroupId:String, state:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set state='" + state + "' where id='" + flowGroupId + "'"

    //update related stop stop when flow state is KILLED
    /*if(state.equals(FlowState.KILLED)){
      val startedStopList = getStartedStop(appId)
      startedStopList.foreach(stopName => {
        updateStopState(appId,stopName,StopState.KILLED)
        updateStopFinishedTime(appId, stopName, new Date().toString)
      })
    }*/
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateFlowGroupStartTime(flowGroupId:String, startTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set startTime='" + startTime + "' where id='" + flowGroupId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateFlowGroupFinishedTime(flowGroupId:String, endTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set endTime='" + endTime + "' where id='" + flowGroupId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateFlowGroupProject(flowGroupId:String, projectId:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set projectId='" + projectId + "' where id='" + flowGroupId + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def getFlowGroupState(flowGroupId:String) : String = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    var flowGroupState = ""

    val flowGroupRS : ResultSet = statement.executeQuery("select state from flowGroup where id='" + flowGroupId +"'")
    if (flowGroupRS.next()){

      flowGroupState = flowGroupRS.getString("state")
    }
    return flowGroupState
  }

  def getFlowGroupInfo(groupId:String) : String = {

    val flowGroupInfoMap = getFlowGroupInfoMap(groupId)
    JsonUtil.format(JsonUtil.toJson(flowGroupInfoMap))

  }

  def getFlowGroupInfoMap(groupId:String) : Map[String, Any] = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)


    var flowGroupInfoMap = Map[String, Any]()

    val flowGroupRS : ResultSet = statement.executeQuery("select * from flowGroup where id='" + groupId +"'")
    while (flowGroupRS.next()){

      flowGroupInfoMap += ("id" -> flowGroupRS.getString("id"))
      flowGroupInfoMap += ("name" -> flowGroupRS.getString("name"))
      flowGroupInfoMap += ("state" -> flowGroupRS.getString("state"))
      flowGroupInfoMap += ("startTime" -> flowGroupRS.getString("startTime"))
      flowGroupInfoMap += ("endTime" -> flowGroupRS.getString("endTime"))
    }
    flowGroupRS.close()

    var flowList:List[Map[String, Any]] = List()
    val flowRS : ResultSet = statement.executeQuery("select * from flow where groupId='" + groupId +"'")
    while (flowRS.next()){
      val appId = flowRS.getString("id")
      flowList = getFlowInfoMap(appId) +: flowList
    }
    flowRS.close()
    flowGroupInfoMap += ("flows" -> flowList)

    statement.close()

    Map[String, Any]("group" -> flowGroupInfoMap)
  }

  def getFlowGroupProgressPercent(groupId:String) : String = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var flowCount = 0;
    var completedFlowCount = 0
    val totalRS : ResultSet = statement.executeQuery("select flowCount from flowGroup where Id='" + groupId + "'")
    while(totalRS.next()){
      flowCount = totalRS.getInt("flowCount")
      println("flowCount:" + flowCount)
    }
    totalRS.close()

    val completedRS : ResultSet = statement.executeQuery("select count(*) as completedFlowCount from flow where GroupId='" + groupId +"' and state='" + FlowState.COMPLETED + "'")
    while(completedRS.next()){
      completedFlowCount = completedRS.getInt("completedFlowCount")
      println("completedFlowCount:" + completedFlowCount)
    }
    completedRS.close()

    val flowGroupRS : ResultSet = statement.executeQuery("select * from flowGroup where id='" + groupId +"'")
    var flowGroupState = ""
    while (flowGroupRS.next()){
      flowGroupState = flowGroupRS.getString("state")
    }
    flowGroupRS.close()

    statement.close()

    val progress:Double = completedFlowCount.asInstanceOf[Double] / flowCount * 100
    if(flowGroupState.equals(FlowState.COMPLETED)){
      "100"
    }else{
      progress.toString
    }
  }

  //project related api
  def addProject(projectId:String,name:String)={
    val startTime = new Date().toString
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into project(id, name) values('" + projectId +  "','" + name + "')")
    statement.close()
  }
  def updateProjectState(projectId:String, state:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update project set state='" + state + "' where id='" + projectId + "'"

    //update related stop stop when flow state is KILLED
    /*if(state.equals(FlowState.KILLED)){
      val startedStopList = getStartedStop(appId)
      startedStopList.foreach(stopName => {
        updateStopState(appId,stopName,StopState.KILLED)
        updateStopFinishedTime(appId, stopName, new Date().toString)
      })
    }*/
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateProjectStartTime(projectId:String, startTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update project set startTime='" + startTime + "' where id='" + projectId + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateProjectFinishedTime(projectId:String, endTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update project set endTime='" + endTime + "' where id='" + projectId + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def getProjectInfo(projectId:String) : String = {

    val projectInfoMap = getProjectInfoMap(projectId)
    JsonUtil.format(JsonUtil.toJson(projectInfoMap))

  }

  def getProjectInfoMap(projectId:String) : Map[String, Any] = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)


    var projectInfoMap = Map[String, Any]()

    val projectRS : ResultSet = statement.executeQuery("select * from project where id='" + projectId +"'")
    while (projectRS.next()){

      projectInfoMap += ("id" -> projectRS.getString("id"))
      projectInfoMap += ("name" -> projectRS.getString("name"))
      projectInfoMap += ("state" -> projectRS.getString("state"))
      projectInfoMap += ("startTime" -> projectRS.getString("startTime"))
      projectInfoMap += ("endTime" -> projectRS.getString("endTime"))
    }
    projectRS.close()

    //get flowGroups info
    var flowGroupList:List[Map[String, Any]] = List()
    val flowGroupRS : ResultSet = statement.executeQuery("select * from flowGroup where projectId='" + projectId +"'")
    while (flowGroupRS.next()){
      val flowGroupId = flowGroupRS.getString("id")
      flowGroupList = getFlowGroupInfoMap(flowGroupId) +: flowGroupList
    }
    flowGroupRS.close()
    projectInfoMap += ("groups" -> flowGroupList)

    //get flow info
    var flowList:List[Map[String, Any]] = List()
    val flowRS : ResultSet = statement.executeQuery("select * from flow where projectId='" + projectId +"'")
    while (flowRS.next()){
      val appId = flowRS.getString("id")
      flowList = getFlowInfoMap(appId) +: flowList
    }
    flowRS.close()
    projectInfoMap += ("flows" -> flowList)

    statement.close()

    Map[String, Any]("project" -> projectInfoMap)
  }

  def addFlag(item:String, flag:Int) : Unit = {
    val createTime = new Date().toString
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into configFlag(item, flag, createTime) values('" + item +  "','" + flag + "','" + createTime +"')")
    statement.close()
  }

  def getFlag(item : String) : Int = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    var flag = 0

    val flowGroupRS : ResultSet = statement.executeQuery("select flag from configFlag where item='" + item +"'")
    if (flowGroupRS.next()){

      flag = flowGroupRS.getInt("flag")
    }
    return flag
  }


  def main(args: Array[String]): Unit = {

    /*try{

      val appId = "111"
      addFlow(appId,"xjzhu")
      updateFlowState(appId,"running")
      val state2 = getFlowState(appId)

      val stop1 = "stop1"
      val stop2 = "stop2"
      addStop(appId, stop1)
      updateStopState(appId,stop1,StopState.COMPLETED)
      addStop(appId, stop2)
      updateStopState(appId,stop2,StopState.STARTED)


      val process = getFlowProgress(appId)
      println("appId=" + appId + "'s process is " + process + "%")

    }catch {
      case ex => println(ex)
    }*/
    if (args.size != 1){
      println("Error args!!! Please enter Clean or UpdateToVersion6")
    }
    val operation =  args(0)
    if(operation == "Clean"){
      cleanDatabase()
    }else if( operation == "UpdateToVersion6"){
      updateToVersion6()
    }else{
      println("Error args!!! Please enter Clean or UpdateToVersion6")
    }

    //println(getFlowGroupInfo("group_9b41bab2-7c3a-46ec-b716-93b636545e5e"))

    //val flowInfoMap = getFlowInfoMap("application_1544066083705_0864")
    //val flowJsonObject = JsonUtil.toJson(flowInfoMap)
    //println(JsonUtil.format(flowJsonObject))
  }

}
