package cn.piflow.bundle.microorganism.util

import org.json.{JSONArray, JSONObject}

class BioProject {

  def convertConcrete2KeyVal(parent: JSONObject, key: String): Unit = {
    //the object having the key is either a JSONObject, a JSONArray, or a concrete value like string or integer
    if(parent.opt(key) != null){
      val obj= parent.get(key)
      if (obj.isInstanceOf[JSONArray]){
        for (i<- 0 until(obj.asInstanceOf[JSONArray].length)){
          val single = obj.asInstanceOf[JSONArray].get(i)
          if(isConcrete(single)){
            val tmp = new JSONObject
            tmp.put("content", single)
            obj.asInstanceOf[JSONArray].put(i, tmp)
          }
        }
      } else if (isConcrete(obj)){
        val tmp = new JSONObject
        tmp.put("content", obj)
        parent.put(key, tmp);
      }
    }
  }

  def isConcrete(obj: Object): Boolean = { //any other basic format??
    if (obj.isInstanceOf[String] || obj.isInstanceOf[Double] || obj.isInstanceOf[Float] || obj.isInstanceOf[Integer] || obj.isInstanceOf[Long]) true
    else false
  }

}
