package cn.piflow.conf

import scala.reflect.runtime.{universe => ru}
sealed class StopGroup
case object CommonGroup extends StopGroup
case object CsvGroup extends StopGroup
case object HiveGroup extends StopGroup
case object JdbcGroup extends StopGroup
case object JsonGroup extends StopGroup
case object XmlGroup extends StopGroup
case object HttpGroup extends StopGroup
case object FtpGroup extends StopGroup
case object ScriptGroup extends StopGroup
case object FileGroup extends StopGroup
case object CleanGroup extends StopGroup
case object RedisGroup extends StopGroup
case object KafkaGroup extends StopGroup
case object ESGroup extends StopGroup
case object HdfsGroup extends StopGroup
case object MicroorganismGroup extends StopGroup
case object ExcelGroup extends StopGroup




object StopGroup{
  def findAllGroup(): List[String] ={
    var groupList : List[String] = List()
    val tpe = ru.typeOf[StopGroup]
    val clazz = tpe.typeSymbol.asClass
    clazz.knownDirectSubclasses.foreach(x => {
      val subObjectArray = x.toString.split(" ")
      groupList = subObjectArray(1) :: groupList})
    groupList
  }
}




