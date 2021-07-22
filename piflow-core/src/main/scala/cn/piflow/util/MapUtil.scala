package cn.piflow.util

import scala.collection.mutable.{Map => MMap}
import scala.util.parsing.json.{JSONArray, JSONObject}

object MapUtil {

  def get(map : Map[String,Any], key:String) : Any = {
    map.get(key) match {
      case None => None
      case Some(x:String) => x
      case Some(x:Integer) => x
      case Some(x:List[String]) => x
      case Some(x:List[Map[String, String]]) => x
      case Some(x:Map[String, Any]) => x
      case _ => throw new IllegalArgumentException
    }
  }

  def get(map : MMap[String,Any], key:String) : Any = {
    map.get(key) match {
      case None => None
      case Some(x:String) => x
      case Some(x:Integer) => x
      case Some(x:List[String]) => x
      case Some(x:List[Map[String, String]]) => x
      case Some(x:Map[String, Any]) => MMap(x.toSeq: _*)
      case Some(x:MMap[String, Any]) => x
      case _ => throw new IllegalArgumentException
    }
  }

  def getJSON(map: Map[String, Any], key: String): Any = {
    map.get(key) match {
      case None => None
      case Some(x: JSONObject) => x.obj
      case Some(x: JSONArray) => x.list
      case _ => throw new IllegalArgumentException
    }
  }

}
