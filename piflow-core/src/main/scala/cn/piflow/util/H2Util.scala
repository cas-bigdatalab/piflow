package cn.piflow.util

import java.sql.{Connection, DriverManager, ResultSet}
import java.util.Date

import net.liftweb.json.compactRender
import net.liftweb.json.JsonDSL._
import org.h2.tools.Server

object H2Util {

  val QUERY_TIME = 300
  val CREATE_FLOW_TABLE = "create table if not exists flow (id varchar(255), pid varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_STOP_TABLE = "create table if not exists stop (flowId varchar(255), name varchar(255), state varchar(255), startTime varchar(255), endTime varchar(255))"
  val CREATE_THOUGHPUT_TABLE = "create table if not exists thoughput (flowId varchar(255), stopName varchar(255), portName varchar(255), count long)"
  val serverIP = PropertyUtil.getPropertyValue("server.ip") + ":" + PropertyUtil.getPropertyValue("h2.port")
  val CONNECTION_URL = "jdbc:h2:tcp://" +  serverIP + "/~/piflow;AUTO_SERVER=true"
  var connection : Connection= null

  try{

    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate(CREATE_FLOW_TABLE)
    statement.executeUpdate(CREATE_STOP_TABLE)
    statement.executeUpdate(CREATE_THOUGHPUT_TABLE)
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
    val statement = getConnectionInstance().createStatement()
    statement.setQueryTimeout(QUERY_TIME)
    statement.executeUpdate("drop table if exists flow")
    statement.executeUpdate("drop table if exists stop")
    statement.executeUpdate("drop table if exists thoughput")
    statement.close()
    h2Server.shutdown()

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
    //println(updateSql)
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
    val statement = getConnectionInstance().createStatement()
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

    flowInfo
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
    cleanDatabase()
  }

}
