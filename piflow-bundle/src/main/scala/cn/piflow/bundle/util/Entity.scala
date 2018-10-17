package cn.piflow.bundle.util


import org.apache.spark.sql.Row

import scala.collection.mutable.ListBuffer

class Entity( id : String, label : String, prop : Map[String, Any], schema : Seq[String]) extends Serializable
{
  def propSeq : Array[String] = {
    var ret : ListBuffer[String] = new ListBuffer[String]()
    ret +:= id
    for (name <- schema) {
      val value = {
        if (prop.contains(name))
          prop(name)
        else
          ""
      }
      value match {
        case _: String =>
          ret += value.asInstanceOf[String]
        case _: Array[String] =>
          var temp = value.asInstanceOf[Array[String]]
          val templist: ListBuffer[String] = ListBuffer()
          for (t <- temp) {
            templist.+=(t)
          }
          ret += templist.reduce((a,b) => a + ";" + b)
        case _ => ret += ""
      }
    }
    ret += label
    ret.toArray
  }

  override def toString: String = {
    this.propSeq.map(a =>"\"" + a + "\"").reduce((a,b) => a + "," + b)
  }

  def getEntityRow : Row = {
    Row(propSeq)
  }
}
object Entity{
  def main(args: Array[String]): Unit = {
    val m : Map[String, Any] = Map("sc1" -> "test1", "sc2" -> Array("2","1"))
    val e = new Entity("label1", "id2", m, Array("sc1","sc2"))
    println(e.toString)
  }
}