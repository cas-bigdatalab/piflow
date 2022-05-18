package cn.piflow.util

import java.net.InetAddress
import java.sql.{Connection, DriverManager, ResultSet}
import java.text.SimpleDateFormat
import java.util.Date

import cn.piflow.util
import net.liftweb.json.compactRender
import net.liftweb.json.JsonDSL._
import org.apache.spark.sql.execution.streaming.state
import org.h2.tools.Server
import cn.piflow.util.ScheduleState

import scala.util.control.Breaks.{break, breakable}

object H2Util {

  val QUERY_TIME = 3000
  //val CREATE_PROJECT_TABLE = "create table if not exists project (id varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_GROUP_TABLE = "create table if not exists flowGroup (id varchar(255), parentId varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255), childCount int)"
  val CREATE_FLOW_TABLE = "create table if not exists flow (id varchar(255), groupId varchar(255), pid varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_STOP_TABLE = "create table if not exists stop (flowId varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_THOUGHPUT_TABLE = "create table if not exists thoughput (flowId varchar(255), stopName varchar(255), portName varchar(255), count long)"
  val CREATE_FLAG_TABLE = "create table if not exists configFlag(id bigint auto_increment, item varchar(255), flag int, createTime varchar(255))"
  val CREATE_SCHEDULE_TABLE = "create table if not exists schedule(id bigint auto_increment, scheduleId varchar(255), scheduleEntryId varchar(255), scheduleEntryType varchar(255))"
  val CREATE_PLUGIN_TABLE = "create table if not exists plugin (id varchar(255), name varchar(255), state varchar(255), createTime varchar(255), updateTime varchar(255))"
  val CREATE_FLOW_DATASIZE_TABLE = "create table if not exists flow_datasize (appId varchar(255), datasize varchar(255),createTime varchar(255))"
  val serverIP = ServerIpUtil.getServerIp() + ":" + PropertyUtil.getPropertyValue("h2.port")
  val CONNECTION_URL = "jdbc:h2:tcp://" +  serverIP + "/~/piflow;AUTO_SERVER=true"
  var connection : Connection= null

  try{

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    //statement.executeUpdate(CREATE_PROJECT_TABLE)
    statement.executeUpdate(CREATE_GROUP_TABLE)
    statement.executeUpdate(CREATE_FLOW_TABLE)
    statement.executeUpdate(CREATE_STOP_TABLE)
    statement.executeUpdate(CREATE_THOUGHPUT_TABLE)
    statement.executeUpdate(CREATE_FLAG_TABLE)
    statement.executeUpdate(CREATE_SCHEDULE_TABLE)
    statement.executeUpdate(CREATE_PLUGIN_TABLE)
    statement.executeUpdate(CREATE_FLOW_DATASIZE_TABLE)
    statement.close()
  }catch {
    case ex => println(ex)
  }

  def getConnectionInstance() : Connection = {
    if(connection == null){
      Class.forName("org.h2.Driver")
      println(CONNECTION_URL)
      connection = DriverManager.getConnection(CONNECTION_URL)
    }
    connection
  }

  def cleanDatabase() = {

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort",PropertyUtil.getPropertyValue("h2.port")).start()
    try{

      val statement = getConnectionInstance().createStatement()
      statement.setQueryTimeout(QUERY_TIME)
      statement.executeUpdate("drop table if exists flowGroup")
      statement.executeUpdate("drop table if exists flow")
      statement.executeUpdate("drop table if exists stop")
      statement.executeUpdate("drop table if exists thoughput")
      statement.executeUpdate("drop table if exists flag")
      statement.executeUpdate("drop table if exists schedule")
      statement.executeUpdate("drop table if exists plugin")
      statement.executeUpdate("drop table if exists flow_datasize")
      statement.close()

    } catch{
        case ex => println(ex)
    }finally {
      h2Server.shutdown()
    }

  }

  /*def updateToVersion6() = {
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
  }*/

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
  def updateFlowDataCenter(appId:String, dataCenter:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flow set dataCenter='" + dataCenter + "' where id='" + appId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  /*def updateFlowProjectId(appId:String, ProjectId:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flow set projectId='" + ProjectId + "' where id='" + appId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }*/

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
      flowInfoMap += ("dataCenter" -> flowRS.getString("dataCenter"))
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

  //Group related api
  def addGroup(groupId:String, name:String, childCount: Int)={
    val startTime = new Date().toString
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into flowGroup(id, name, childCount) values('" + groupId +  "','" + name + "','" + childCount + "')")
    statement.close()
  }
  def updateGroupState(groupId:String, state:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set state='" + state + "' where id='" + groupId + "'"

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
  def updateGroupStartTime(groupId:String, startTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set startTime='" + startTime + "' where id='" + groupId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateGroupFinishedTime(groupId:String, endTime:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set endTime='" + endTime + "' where id='" + groupId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }
  def updateGroupParent(groupId:String, parentId:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update flowGroup set parentId='" + parentId + "' where id='" + groupId + "'"
    //println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def getGroupState(groupId:String) : String = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    var groupState = ""

    val groupRS : ResultSet = statement.executeQuery("select state from flowGroup where id='" + groupId +"'")
    if (groupRS.next()){

      groupState = groupRS.getString("state")
    }
    return groupState
  }

  def isGroupChildError( groupId : String) : Boolean = {

    if(getGroupChildByStatus(groupId, GroupState.FAILED).size > 0 || getGroupChildByStatus(groupId, GroupState.KILLED).size > 0)
      return true
    else if(getFlowChildByStatus(groupId, FlowState.FAILED).size > 0 || getFlowChildByStatus(groupId, FlowState.KILLED).size > 0)
      return true
    else
      return false
  }

  def isGroupChildRunning( groupId : String) : Boolean = {

    if(getGroupChildByStatus(groupId, GroupState.STARTED).size > 0 )
      return true
    else if(getFlowChildByStatus(groupId, FlowState.STARTED).size > 0 )
      return true
    else
      return false
  }

  def getGroupChildByStatus(groupId: String, status : String) : List[String] = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    var failedList = List[String]()

    //group children state
    val groupRS : ResultSet = statement.executeQuery("select * from flowGroup where parentId='" + groupId +"'")
    breakable{
      while (groupRS.next()){
        val groupName = groupRS.getString("name")
        val groupState = groupRS.getString("state")
        if(groupState == status){
          failedList = groupName +: failedList
        }
      }
    }
    groupRS.close()
    statement.close()
    return failedList
  }
  def getFlowChildByStatus(groupId: String, status : String) : List[String] = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    var failedList = List[String]()

    //flow children state
    val rs : ResultSet = statement.executeQuery("select * from flow where groupId='" + groupId +"'")
    breakable{
      while(rs.next()){
        val flowName = rs.getString("name")
        val flowState = rs.getString("state")
        if(flowState == status){
          failedList = flowName +: failedList
        }
      }
    }

    rs.close()
    statement.close()
    return failedList
  }

  def getFlowGroupInfo(groupId:String) : String = {

    val flowGroupInfoMap = getGroupInfoMap(groupId)
    JsonUtil.format(JsonUtil.toJson(flowGroupInfoMap))

  }

  //TODO need to get group
  def getGroupInfoMap(groupId:String) : Map[String, Any] = {
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

    var groupList:List[Map[String, Any]] = List()
    val childGroupRS : ResultSet = statement.executeQuery("select * from flowGroup where parentId='" + groupId +"'")
    while (childGroupRS.next()){
      val childGroupId = childGroupRS.getString("id")
      val childGroupMapInfo = getGroupInfoMap(childGroupId)
      groupList = childGroupMapInfo +: groupList
    }
    childGroupRS.close()
    flowGroupInfoMap += ("groups" -> groupList)

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

  def getGroupProgressPercent(groupId:String) : String = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var childCount = 0;

    var completedGroupCount = 0
    var completedFlowCount = 0

    val groupRSALL : ResultSet = statement.executeQuery("select * from flowGroup where id='" + groupId +"'")
    var groupState = ""
    while (groupRSALL.next()){
      groupState = groupRSALL.getString("state")
      childCount = groupRSALL.getInt("childCount")
    }
    groupRSALL.close()

    if(groupState.equals(FlowState.COMPLETED)){
      statement.close()
      return "100"
    }else{

      val completedGroupRS : ResultSet = statement.executeQuery("select count(*) as completedGroupCount from flowGroup where parentId='" + groupId +"' and state='" + GroupState.COMPLETED+ "'")
      while(completedGroupRS.next()){
        completedGroupCount = completedGroupRS.getInt("completedGroupCount")
        println("completedGroupCount:" + completedGroupCount)
      }
      completedGroupRS.close()


      val completedFlowRS : ResultSet = statement.executeQuery("select count(*) as completedFlowCount from flow where GroupId='" + groupId +"' and state='" + FlowState.COMPLETED + "'")
      while(completedFlowRS.next()){
        completedFlowCount = completedFlowRS.getInt("completedFlowCount")
        println("completedFlowCount:" + completedFlowCount)
      }
      completedFlowRS.close()

      statement.close()

      val progress:Double = (completedFlowCount.asInstanceOf[Double] + completedGroupCount.asInstanceOf[Double])/ childCount * 100
      return progress.toString
    }

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

  def addScheduleInstance(scheduleId : String, cronExpression : String, startDate : String, endDate : String, state : String): Unit ={
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val time = new Date().toString
    statement.executeUpdate("insert into scheduleInstance(id, cronExpression, startDate, endDate, state, createTime, updateTime) values('" + scheduleId +  "','" + cronExpression + "','" + startDate + "','" + endDate + "','" + state + "','" + time + "','" + time + "')")
    statement.close()
  }

  def updateScheduleInstanceStatus(scheduleId : String, state : String)  = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val time = new Date().toString
    val updateSql = "update scheduleInstance set state='" + state + "', updateTime='" + time + "' where id='" + scheduleId + "'"
    println(updateSql)
    statement.executeUpdate(updateSql)
    statement.close()
  }

  def getNeedStopSchedule(): List[String] = {
    var resultList : List[String]= List()
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val nowDate: String = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date())
    val updateSql = "select id from scheduleInstance where state = '" + ScheduleState.STARTED  + "' and endDate != '' and endDate <= '" + nowDate + "'"
    println(updateSql)

    val scheduleRS : ResultSet = statement.executeQuery(updateSql)
    while (scheduleRS.next()){

      val id = scheduleRS.getString("id")
      resultList = id +: resultList

    }
    statement.close()
    resultList
  }

  def addScheduleEntry(scheduleId : String, scheduleEntryId : String, scheduleEntryType : String): Unit ={
    val createTime = new Date().toString
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into schedule(scheduleId, scheduleEntryId, scheduleEntryType) values('" + scheduleId +  "','" + scheduleEntryId + "','" + scheduleEntryType +"')")
    statement.close()
  }

  def getScheduleInfo(scheduleId: String) : String = {

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var scheduleInfoMap = Map[String, Any]()
    //get flow basic info
    val scheduleInstanceRS : ResultSet = statement.executeQuery("select * from scheduleInstance where id='" + scheduleId +"'")
    while (scheduleInstanceRS.next()){

      scheduleInfoMap += ("id" -> scheduleInstanceRS.getString("id"))
      scheduleInfoMap += ("cronExpression" -> scheduleInstanceRS.getString("cronExpression"))
      scheduleInfoMap += ("startDate" -> scheduleInstanceRS.getString("startDate"))
      scheduleInfoMap += ("endDate" -> scheduleInstanceRS.getString("endDate"))
      scheduleInfoMap += ("state" -> scheduleInstanceRS.getString("state"))
      scheduleInfoMap += ("createTime" -> scheduleInstanceRS.getString("createTime"))
      scheduleInfoMap += ("updateTime" -> scheduleInstanceRS.getString("updateTime"))
    }
    scheduleInstanceRS.close()

    var scheduleEntryList : List[Map[String, String]] = List()
    val scheduleRS : ResultSet = statement.executeQuery("select * from schedule where scheduleId='" + scheduleId +"'")
    while (scheduleRS.next()){

      var scheduleEntryMap = Map[String, String]()
      scheduleEntryMap += ("scheduleEntryId" -> scheduleRS.getString("scheduleEntryId"))
      scheduleEntryMap += ("scheduleEntryType" -> scheduleRS.getString("scheduleEntryType"))

      scheduleEntryList = scheduleEntryMap +: scheduleEntryList
    }

    scheduleInfoMap += ("entryList" -> scheduleEntryList)
    var scheduleJson = JsonUtil.format(JsonUtil.toJson(Map("schedule" -> scheduleInfoMap)))
    scheduleJson

  }

  def getStartedSchedule() : List[String] ={

    var scheduleList = List[String]()
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var scheduleInfoMap = Map[String, Any]()
    //get flow basic info
    val scheduleInstanceRS : ResultSet = statement.executeQuery("select * from scheduleInstance where state='" + ScheduleState.STARTED +"'")
    while (scheduleInstanceRS.next()){

      scheduleList = scheduleInstanceRS.getString("id") +: scheduleList
    }
    scheduleInstanceRS.close()
    scheduleList
  }

  def addPlugin(name:String)={

    var id = ""
    var state = ""
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val rs : ResultSet = statement.executeQuery("select * from plugin where name='" + name +"'")
    if(!rs.isBeforeFirst){
      id = IdGenerator.uuid()
      val time = new Date().toString
      statement.executeUpdate("insert into plugin(id, name, state, createTime, updateTime) values('" + id + "','" + name + "','" + PluginState.ON + "','" + time + "','" + time  + "')")
      state = PluginState.ON
    }else{

      breakable{
        while(rs.next()){
          id = rs.getString("id")
          state = rs.getString("state")
          val time = new Date().toString
          if(state == PluginState.OFF){
            val updateSql = "update plugin set state='" + PluginState.ON + "'," + "updateTime='" + time +"' where name='" + name + "'"
            statement.executeUpdate(updateSql)
            state = PluginState.ON
            break
          }
        }

      }
    }
    rs.close()
    statement.close()
    id
  }

  def removePlugin(name:String)={

    var state = ""
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val rs : ResultSet = statement.executeQuery("select * from plugin where name='" + name +"'")
    if(!rs.isBeforeFirst){
      state = PluginState.NONE
    }else{

      breakable{
        while(rs.next()){
          state = rs.getString("state")
          val time = new Date().toString
          if(state == PluginState.ON){
            val updateSql = "update plugin set state='" + PluginState.OFF + "'," + "updateTime='" + time +"' where name='" + name + "'"
            statement.executeUpdate(updateSql)
            state = PluginState.OFF
            break
          }
        }
      }
    }
    rs.close()
    statement.close()
    state
  }

  def getPluginInfo(pluginId : String) : String ={

    val pluginMap = getPluginInfoMap(pluginId)
    JsonUtil.format(JsonUtil.toJson(pluginMap))
  }

  def getPluginInfoMap(pluginId : String) : Map[String, String] ={

    var pluginMap = Map[String, String]()
    val statement = getConnectionInstance().createStatement()
    val rs : ResultSet = statement.executeQuery("select * from plugin where id='" + pluginId + "'")
    while(rs.next()){

      val path = PropertyUtil.getClassPath() + "/" + rs.getString("name")
      pluginMap += ("id" -> rs.getString("id"))
      pluginMap += ("name" -> rs.getString("name"))
      pluginMap += ("path" -> path)
      pluginMap += ("state" -> rs.getString("state"))
      pluginMap += ("createTime" -> rs.getString("createTime"))
      pluginMap += ("updateTime" -> rs.getString("updateTime"))
    }
    rs.close()
    statement.close()
    pluginMap
  }

  def getPluginOn() : List[String] ={

    var pluginList = List[String]()
    val statement = getConnectionInstance().createStatement()
    val rs : ResultSet = statement.executeQuery("select * from plugin where state='" + PluginState.ON + "'")
    while(rs.next()){
      pluginList = rs.getString("name") +: pluginList
    }
    rs.close()
    statement.close()
    pluginList
  }


  def addSparkJar(sparkJarName:String)={

    var id = ""
    var state = ""
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val rs : ResultSet = statement.executeQuery("select * from sparkJar where name='" + sparkJarName +"'")
    if(!rs.isBeforeFirst){
      id = IdGenerator.uuid()
      val time = new Date().toString
      statement.executeUpdate("insert into sparkJar(id, name, state, createTime, updateTime) values('" + id + "','" + sparkJarName + "','" + PluginState.ON + "','" + time + "','" + time  + "')")
      state = SparkJarState.ON
    }else{

      breakable{
        while(rs.next()){
          id = rs.getString("id")
          state = rs.getString("state")
          val time = new Date().toString
          if(state == SparkJarState.OFF){
            val updateSql = "update sparkJar set state='" + SparkJarState.ON + "'," + "updateTime='" + time +"' where name='" + sparkJarName + "'"
            statement.executeUpdate(updateSql)
            state = SparkJarState.ON
            break
          }
        }

      }
    }
    rs.close()
    statement.close()
    id
  }

  def removeSparkJar(sparkJarId:String) : String={

    var state = ""
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val rs : ResultSet = statement.executeQuery("select * from sparkJar where id='" + sparkJarId +"'")
    if(!rs.isBeforeFirst){
      state = SparkJarState.NONE
    }else{

      breakable{
        while(rs.next()){
          state = rs.getString("state")
          val time = new Date().toString
          if(state == SparkJarState.ON){
            val updateSql = "update sparkJar set state='" + SparkJarState.OFF + "'," + "updateTime='" + time +"' where id='" + sparkJarId + "'"
            statement.executeUpdate(updateSql)
            state = SparkJarState.OFF
            break
          }
        }
      }
    }
    rs.close()
    statement.close()
    state
  }

  def getSparkJarInfo(sparkJarId : String) : String ={

    val sparkJarMap = getSparkJarInfoMap(sparkJarId)
    JsonUtil.format(JsonUtil.toJson(sparkJarMap))
  }

  def getSparkJarInfoMap(sparkJarId : String) : Map[String, String] ={

    var sparkJarMap = Map[String, String]()
    val statement = getConnectionInstance().createStatement()
    val rs : ResultSet = statement.executeQuery("select * from sparkJar where id='" + sparkJarId + "'")
    while(rs.next()){

      val path = PropertyUtil.getSpartJarPath() + "/" + rs.getString("name")
      sparkJarMap += ("id" -> rs.getString("id"))
      sparkJarMap += ("name" -> rs.getString("name"))
      sparkJarMap += ("path" -> path)
      sparkJarMap += ("state" -> rs.getString("state"))
      sparkJarMap += ("createTime" -> rs.getString("createTime"))
      sparkJarMap += ("updateTime" -> rs.getString("updateTime"))
    }
    rs.close()
    statement.close()
    sparkJarMap
  }

  def getSparkJarOn() : List[String] ={

    var pluginList = List[String]()
    val statement = getConnectionInstance().createStatement()
    val rs : ResultSet = statement.executeQuery("select * from sparkJar where state='" + SparkJarState.ON + "'")
    while(rs.next()){
      pluginList = rs.getString("name") +: pluginList
    }
    rs.close()
    statement.close()
    pluginList
  }

  def addFlowDataSize(appId:String, datasize:String, date:String)={
    val startTime = new Date().toString
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into flow_datasize(appId, datasize, createTime) values('" + appId + "','" + datasize + "','" + date + "')")
    statement.close()
  }
  def getFlowDataSize(appId:String):String = {
    var datasize :String=null
    val statement = getConnectionInstance().createStatement()
    val rs : ResultSet = statement.executeQuery("select * from flow_datasize where appId='" + appId + "'")
    while(rs.next()){
      datasize = rs.getString("datasize")
    }
    rs.close()
    statement.close()
    datasize
  }



  //datacenter's task plan related API
  def addTaskPlanGroup(groupId:String,groupName:String,groupDataCenter:String) = {

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into taskplan_group(id, groupName, groupDataCenter) values('" + groupId +  "','" + groupName + "','" + groupDataCenter + "')")
    statement.close()

  }
  def addTaskPlanFlow(id:String, groupId:String,flowName:String,flowDataCenter:String) = {

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into taskplan_flow(id, groupId, flowName, flowDataCenter) values('" + id +  "','" + groupId +  "','" + flowName + "','" + flowDataCenter + "')")
    statement.close()
  }

  def addTaskPlanCondition(id:String,groupId:String,upstreamFlowName:String,flowOutport:String,flowInport:String,downstreamFlowName:String) = {

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into taskplan_condition(id, groupId, upstreamFlowName, flowOutport, flowInport, downstreamFlowName) values('" + id +  "','" + groupId +  "','" + upstreamFlowName + "','" + flowOutport + "','" + flowInport + "','" + downstreamFlowName  + "')")
    statement.close()
  }

  def addTaskPlanStop(id:String,flowId:String,stopName:String,stopDataCenter:String) ={

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into taskplan_stop(id, flowId, stopName, stopDataCenter) values('" + id +  "','" + flowId +  "','" + stopName + "','" + stopDataCenter + "')")
    statement.close()

  }
  def addTaskPlanPath(id:String,flowId:String,fromStop:String,outport:String,inport:String,toStop:String)= {

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("insert into taskplan_path(id, flowId, fromStop, outport, inport, toStop) values('" + id +  "','" + flowId +  "','" + fromStop + "','" + outport + "','" + inport + "','" + toStop  + "')")
    statement.close()

  }

  def updateTaskPlanFlowDataCenter(groupId:String, flowName:String, flowDataCenter:String) = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    val updateSql = "update taskplan_flow set flowDataCenter='" + flowDataCenter + "' where groupId='" + groupId + "' and flowName='" + flowName + "'"
    println(updateSql)

    statement.executeUpdate(updateSql)
    statement.close()
  }
  def getTaskPlan(groupId:String) : String = {
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)


    var flowGroupInfoMap = Map[String, Any]()

    val flowGroupRS : ResultSet = statement.executeQuery("select * from taskplan_group where id='" + groupId +"'")
    while (flowGroupRS.next()){

      flowGroupInfoMap += ("id" -> flowGroupRS.getString("id"))
      flowGroupInfoMap += ("name" -> flowGroupRS.getString("groupName"))
      flowGroupInfoMap += ("dataCenter" -> flowGroupRS.getString("groupDataCenter"))
    }
    flowGroupRS.close()

    flowGroupInfoMap += ("flows" -> getTaskPlanFlowInfoMap(groupId))
    flowGroupInfoMap += ("conditions" -> getTaskPlanConditionsList(groupId))

    statement.close()

    val taskPlanMap = Map[String, Any]("group" -> flowGroupInfoMap)
    JsonUtil.format(JsonUtil.toJson(taskPlanMap))

  }

  private def getTaskPlanFlowInfoMap(groupId:String) = {

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var taskPlanFlowInfoMap = Map[String, Any]()
    var flowInfoList:List[Map[String, Any]] = List()
    var flowIdList:List[String] = List()
    //get flow basic info
    val flowRS : ResultSet = statement.executeQuery("select * from taskplan_flow where groupId='group_9f497ee5-56a1-42e5-8555-fa427ab49c34'")
    while (flowRS.next()){
      flowIdList = flowRS.getString("id") +: flowIdList
    }
    flowRS.close()
    statement.close()

    flowIdList.foreach{ id => {
      val statement = getConnectionInstance().createStatement()
      statement.setQueryTimeout(QUERY_TIME)

      val flowRS : ResultSet = statement.executeQuery("select * from taskplan_flow where id='" + id + "'")
      if(flowRS.next()){
        var flowInfoMap = Map[String, Any]()
        val flowId = flowRS.getString("id")
        flowInfoMap += ("name" -> flowRS.getString("flowName"))
        flowInfoMap += ("dataCenter") -> flowRS.getString("flowDataCenter")

        //get flow stops info
        var stopList:List[Map[String, Any]] = List()
        val stopRS : ResultSet = statement.executeQuery("select * from taskplan_stop where flowId='" + flowId +"'")
        while(stopRS.next()){
          var stopMap = Map[String, Any]()
          stopMap += ("name" -> stopRS.getString("stopName"))
          stopMap += ("dataCenter" -> stopRS.getString("stopDataCenter"))
          stopList = Map("stop" -> stopMap) +: stopList
        }
        stopRS.close()
        flowInfoMap += ("stops" -> stopList)

        //get flow path info
        var pathList:List[Map[String, Any]] = List()
        val pathRS : ResultSet = statement.executeQuery("select * from taskplan_path where flowId='" + flowId +"'")
        while(pathRS.next()){
          var pathMap = Map[String, Any]()
          pathMap += ("fromStop" -> pathRS.getString("fromStop"))
          pathMap += ("outport" -> pathRS.getString("outport"))
          pathMap += ("inport" -> pathRS.getString("inport"))
          pathMap += ("toStop" -> pathRS.getString("toStop"))
          pathList = Map("path" -> pathMap) +: stopList
        }
        pathRS.close()
        flowInfoMap += ("paths" -> pathList)

        flowInfoList = Map("flow" -> flowInfoMap) +: flowInfoList
      }
      flowRS.close()
      statement.close()
    }}

    flowInfoList
  }
  private def getTaskPlanConditionsList(groupId:String) = {

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    //var taskPlanConditionInfoMap = Map[String, Any]()

    //get condition info
    var conditionList:List[Map[String, Any]] = List()
    val conditionRS : ResultSet = statement.executeQuery("select * from taskplan_condition where groupId='" + groupId +"'")
    while (conditionRS.next()){

      var conditionMap = Map[String, Any]()
      conditionMap += ("upstreamFlowName" -> conditionRS.getString("upstreamFlowName"))
      conditionMap += ("flowOutport" -> conditionRS.getString("flowOutport"))
      conditionMap += ("flowInport" -> conditionRS.getString("flowInport"))
      conditionMap += ("downstreamFlowName" -> conditionRS.getString("downstreamFlowName"))
      conditionList = Map("condition" -> conditionMap) +: conditionList
    }
    conditionRS.close()

    conditionList

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
    /*val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)

    var taskPlanFlowInfoMap = Map[String, Any]()
    var flowInfoList:List[Map[String, Any]] = List()
    var flowIdList:List[String] = List()
    //get flow basic info
    val flowRS : ResultSet = statement.executeQuery("select * from taskplan_flow where groupId='group_9f497ee5-56a1-42e5-8555-fa427ab49c34'")
    while (flowRS.next()){
      flowIdList = flowRS.getString("id") +: flowIdList
    }
    flowRS.close()
    statement.close()

    flowIdList.foreach{ id => {
      val statement = getConnectionInstance().createStatement()
      statement.setQueryTimeout(QUERY_TIME)

      val flowRS : ResultSet = statement.executeQuery("select * from taskplan_flow where id='" + id + "'")
      if(flowRS.next()){
        var flowInfoMap = Map[String, Any]()
        val flowId = flowRS.getString("id")
        flowInfoMap += ("name" -> flowRS.getString("flowName"))
        flowInfoMap += ("dataCenter") -> flowRS.getString("flowDataCenter")

        //get flow stops info
        var stopList:List[Map[String, Any]] = List()
        val stopRS : ResultSet = statement.executeQuery("select * from taskplan_stop where flowId='" + flowId +"'")
        while(stopRS.next()){
          var stopMap = Map[String, Any]()
          stopMap += ("name" -> stopRS.getString("stopName"))
          stopMap += ("dataCenter" -> stopRS.getString("stopDataCenter"))
          stopList = Map("stop" -> stopMap) +: stopList
        }
        stopRS.close()
        flowInfoMap += ("stops" -> stopList)

        //get flow path info
        var pathList:List[Map[String, Any]] = List()
        val pathRS : ResultSet = statement.executeQuery("select * from taskplan_path where flowId='" + flowId +"'")
        while(pathRS.next()){
          var pathMap = Map[String, Any]()
          pathMap += ("fromStop" -> pathRS.getString("fromStop"))
          pathMap += ("outport" -> pathRS.getString("outport"))
          pathMap += ("inport" -> pathRS.getString("inport"))
          pathMap += ("toStop" -> pathRS.getString("toStop"))
          pathList = Map("path" -> pathMap) +: stopList
        }
        pathRS.close()
        flowInfoMap += ("paths" -> pathList)

        flowInfoList = Map("flow" -> flowInfoMap) +: flowInfoList
      }
      flowRS.close()
      statement.close()
    }}

    flowInfoList*/
    val str = getTaskPlan("group_9f497ee5-56a1-42e5-8555-fa427ab49c34")
    println(str)
  }

}
