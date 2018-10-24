package cn.piflow.bundle.util


import org.apache.spark.sql.Row

import scala.collection.mutable.ListBuffer

class Entity( id : String,
              label : String,
              prop : Map[String, Array[String]],
              val schema : Seq[String]
            ) extends Serializable {
  var propSeq : Array[AnyRef] = {
    var ret : ListBuffer[AnyRef] = new ListBuffer[AnyRef]()
    ret +:= id
    val l =  for (name <- schema) yield {
      val value : Array[String] = {
        if (prop.contains(name))
          prop(name)
        else
          Array("")
      }
      val str = value
        .map(f => if (f == "") "\"\"" else f)
        .map(_.replaceAll(";", " "))
        .reduce((a,b) => a + ";" + b)

      if (str.contains(";")) str.split(";")
      else str
    }
    ret ++= l
    ret += label
    ret.map {
      case c: String =>
        if (c.contains(","))
          "\"" + c + "\""
        else
          c
      case c: Array[String] => c.asInstanceOf[Array[String]].map(a => if (a.contains(",")) "\"" + a + "\"" else a)
      case _ => ""
    }.toArray
  }

  override def toString: String = {
    val list = this.propSeq
    val ret = for (c <- list) yield {
      c match {
        case c : String => c.asInstanceOf[String]
        case c : Array[String] => c.asInstanceOf[Array[String]].reduce(_ + ";" + _)
        case _ => ""
      }
    }
    ret.reduce(_ + "," + _)
  }

  def getEntityRow : Row = {
    Row(propSeq)
  }
}
object Entity{


  def main(args: Array[String]): Unit = {
//    val m : Map[String, Any] = Map("sc1" -> "test1", "sc2" -> Array("2","1"))
//    val e = new Entity("id1","l1", m, Array("sc1","sc2"))
//    println(e.toString)  //"label1","test1","2;1","id2"
  }
}