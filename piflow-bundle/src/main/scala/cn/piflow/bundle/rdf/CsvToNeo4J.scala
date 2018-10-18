package cn.piflow.bundle.rdf

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum}
import cn.piflow.conf.bean.PropertyDescriptor

class CsvToNeo4J extends ConfigurableStop{
  override val authorEmail: String = "sha0w@cnic.cn"
  override val description: String = "this stop use linux shell & neo4j-import command to lead CSV file data create/into a database"
  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)

  override def setProperties(map: Map[String, Any]): Unit = ???

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = ???

  override def initialize(ctx: ProcessContext): Unit = ???

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = ???
}
