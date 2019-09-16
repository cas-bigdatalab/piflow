package cn.piflow.bundle.util

import org.json.{JSONObject, XML}

/**
  * @auther ygang@cnic.cn
  * @create 9/5/19
  */
object XmlToJson {
  def xmlParse(xmlString:String):String={
    val xmlObject: JSONObject = XML.toJSONObject(xmlString)
    val str: String = xmlObject.toString(4)
    return  str
  }

}
