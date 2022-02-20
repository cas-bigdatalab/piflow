package com.piflow.sql.datasource

import cn.piflow.conf.bean.StopBean
import cn.piflow.conf.util.MapUtil

object RegisterDataSource {

  //TODO: need to optimize
  val personPropertisMap:Map[String, String] = Map("hiveQL" -> "select * from test.student limit 10")
  val personMap : Map[String, Any] = Map(
    "dataCenter" -> "http://10.0.90.155:8002",
    "name" -> "SelectHiveQL-A",
    "bundle" -> "cn.piflow.bundle.hive.SelectHiveQL",
    "uuid" -> "223232",
    "properties" -> personPropertisMap)
  val personDataSource = StopBean("test", personMap)


  val scorePropertisMap:Map[String, String] = Map("hiveQL" -> "select * from test.score")
  val scoreMap : Map[String, Any] = Map(
    "dataCenter" -> "http://10.0.82.42:8002",
    "name" -> "SelectHiveQL-B",
    "bundle" -> "cn.piflow.bundle.hive.SelectHiveQL",
    "uuid" -> "223232",
    "properties" -> scorePropertisMap)
  val scoreDataSource = StopBean("test", scoreMap)


  val dataSourceMap : Map[String, StopBean] = Map(
    "Persons" -> personDataSource,
    "Scores" -> scoreDataSource
  )

  def getDataSourceStopBean(key:String) : StopBean = {
    MapUtil.get(dataSourceMap, key).asInstanceOf[StopBean]
  }
}
