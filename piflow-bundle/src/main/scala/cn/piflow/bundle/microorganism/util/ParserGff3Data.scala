package cn.piflow.bundle.microorganism.util

import java.util.HashMap

import org.json.JSONObject

class ParserGff3Data {

  def parserAttributes(eachFileStr: String): HashMap[String, String] = {
    val map: HashMap[String, String] = new HashMap[String,String]()
    val eachArr = eachFileStr.split(";")
    for(each <- eachArr){
      try{
        val k: String = each.split("=")(0)
        val v: String = each.split("=")(1)
        map.put(k,v)
      }catch {
        case e : Exception => throw new Exception("File format error")
      }
    }
    map
  }

  def parserGff3(eachLine: String): JSONObject = {
    var doc: JSONObject =new JSONObject()

      val eachArr: Array[String] = eachLine.split("\u0009")
      if(eachArr.size ==9){
        for(x <- (0 until  9)){
          val eachFileStr = eachArr(x)
          if(x == 0){
            doc.put("reference_sequence",eachFileStr)
          }else if(x == 1){
            doc.put("source ",eachFileStr)
          }else if(x == 2){
            doc.put("type",eachFileStr)
          }else if(x == 3){
            doc.put("start_position",eachFileStr)
          }else if(x == 4){
            doc.put("end_position",eachFileStr)
          }else if(x == 5){
            doc.put("score",eachFileStr)
          }else if(x == 6){
            doc.put("strand",eachFileStr)
          }else if(x == 7){
            doc.put("phase",eachFileStr)
          }else if(x == 8){
            var map:HashMap[String, String]=parserAttributes(eachFileStr)
            doc.put("attributes",map)
          }
        }
      }
    return doc
  }
}
