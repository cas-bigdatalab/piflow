package cn.piflow.bundle.util


import org.apache.spark.sql.Row

import scala.collection.mutable.ListBuffer

class Entity( id : String,
              label : String,
              prop : Map[String, Any],
              val schema : Seq[String]
            ) extends Serializable {
  var propSeq : Array[Any] = {
    var ret : ListBuffer[Any] = new ListBuffer[Any]()
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
          ret += value.asInstanceOf[Array[String]]
        case _ => ret += ""
      }
    }
    ret += label
    ret.toArray
  }

  override def toString: String = {
    val l = for {
      prop : Any <- propSeq
    } yield {
      prop match {
        case _ : String =>  prop.asInstanceOf[String]
        case _ : Array[String] =>
          val temp : String = prop.asInstanceOf[Array[String]].reduce(_ + ";" + _)
          temp
        case _ : Any => ""
      }
    }
    l.reduce(_ + "," + _)
  }

  def getEntityRow : Row = {
    Row(propSeq)
  }
}
object Entity{


  def main(args: Array[String]): Unit = {
    val m : Map[String, Any] = Map("sc1" -> "test1", "sc2" -> Array("2","1"))
    val e = new Entity("id1","l1", m, Array("sc1","sc2"))
    println(e.toString)  //"label1","test1","2;1","id2"
  }
}