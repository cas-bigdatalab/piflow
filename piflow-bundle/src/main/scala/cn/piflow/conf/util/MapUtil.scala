package cn.piflow.conf.util

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
}
