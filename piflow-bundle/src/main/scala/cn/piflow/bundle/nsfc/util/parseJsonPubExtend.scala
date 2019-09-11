package cn.piflow.bundle.nsfc.util

import com.alibaba.fastjson.{JSON, JSONArray, JSONObject}

/**
  * @auther ygang@cnic.cn
  * @create 9/11/19
  */
object parseJsonPubExtend extends Serializable {
  var issue_no_01 :String  = null
  var issue_no_02 :String  = null
  var issueObject: JSONObject = null
  var pub_extendString:String = null

  def pub_extend(str:String,pub_type_id:String): String ={


    if (str.startsWith("{")){
      val jsonObject = JSON.parseObject(str)
      pub_extendString= assemblyPub_extend(jsonObject)

    }

    if (str.startsWith("[")){
      val array: JSONArray = JSON.parseArray(str)
      for (i<- 0 until array.size() ){
        val jsonObject: JSONObject = array.getJSONObject(i)

        if (jsonObject.get("pub_type_id") == "4"){
          pub_extendString = assemblyPub_extend(jsonObject)
        }
      }
    }
    pub_extendString
  }


  def assemblyPub_extend(jsonObject:JSONObject): String ={

    if (jsonObject.get("issue_no") != null){
      if (jsonObject.get("issue_no").toString.startsWith("[")){
        val issueArray: JSONArray = jsonObject.getJSONArray("issue_no")
        for (i<- 0 until issueArray.size()){
          issueObject = issueArray.getJSONObject(i)
          if (issueObject.get("code") == "01") if (issueObject.get("content") != null) issue_no_01= issueObject.get("content").toString
          if (issueObject.get("code") == "02") if (issueObject.get("content") != null) issue_no_02= issueObject.get("content").toString
        }
      }
      if (jsonObject.get("issue_no").toString.startsWith("{")) {
        if (jsonObject.get("code") == "01") if (jsonObject.get("content") != null) issue_no_01= jsonObject.get("content").toString
        if (jsonObject.get("code") == "02") if (jsonObject.get("content") != null) issue_no_02= jsonObject.get("content").toString
      }
    }






    val aaa: String = jsonObject.get("article_no") + "\t<&\t" +
      jsonObject.get("begin_num") + "\t<&\t" +
      jsonObject.get("city") + "\t<&\t" +
      jsonObject.get("conf_end_day") + "\t<&\t" +
      jsonObject.get("conf_end_month") + "\t<&\t" +
      jsonObject.get("conf_end_year") + "\t<&\t" +
      jsonObject.get("conf_name") + "\t<&\t" +
      jsonObject.get("conf_org") + "\t<&\t" +
      jsonObject.get("conf_start_day") + "\t<&\t" +
      jsonObject.get("conf_start_month") + "\t<&\t" +
      jsonObject.get("conf_start_year") + "\t<&\t" +
      jsonObject.get("conf_type") + "\t<&\t" +
      jsonObject.get("country_name") + "\t<&\t" +
      jsonObject.get("doi") + "\t<&\t" +
      jsonObject.get("end_num") + "\t<&\t" +
      jsonObject.get("paper_type") + "\t<&\t" +
      jsonObject.get("product_mark") + "\t<&\t" +
      jsonObject.get("product_mark_name") + "\t<&\t" +
      jsonObject.get("public_status") + "\t<&\t" +
      jsonObject.get("impact_factors") + "\t<&\t" +
      jsonObject.get("include_start")+ "\t<&\t" +
      issue_no_01+ "\t<&\t" +
      issue_no_02
    aaa
  }

}
