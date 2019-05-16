package cn.piflow.util

import scala.util.parsing.json.{JSONArray, JSONFormat, JSONObject}

/**
  * Created by xjzhu@cnic.cn on 4/30/19
  */
object JsonUtil {

  def toJson(arr : List[Any]) : JSONArray = {
    JSONArray(arr.map {
      case (innerMap : Map[String, Any]) => toJson(innerMap)
      case (innerArray : List[Any]) => toJson(innerArray)
      case (other) => other
    })
  }

  def toJson(map:Map[String,Any]):JSONObject = {
    JSONObject(map.map {
      case(key, innerMap:Map[String, Any]) => (key, toJson(innerMap))
      case(key, innerArray: List[Any]) => (key, toJson(innerArray))
      case(key, other) => (key, if (other == null) "" else other )
    })
  }

  def format(t:Any, i: Int = 0) : String = t match {
    case o: JSONObject =>
      o.obj.map{
        case (k, v) =>
          "    "*(i+1) + JSONFormat.defaultFormatter(k) + ": " + format(v, i+1)
      }.mkString("{\n",",\n","\n" + "    "*i + "}")
    case a: JSONArray =>
      a.list.map{
        e => "    "*(i+1) + format(e, i+1)
      }.mkString("[\n",",\n","\n" + "    "*i + "]")
    case _ => JSONFormat defaultFormatter t
  }

}
