package cn.piflow.bundle.nsfc.util

import com.alibaba.fastjson.{JSON, JSONArray, JSONObject}

/**
  * @auther ygang@cnic.cn
  * @create 9/11/19
  */
object parseJsonPubExtend extends Serializable {


  def parseAuthor(str :String):String={

    val psn_name= new StringBuilder
    val org_name= new StringBuilder
    val email= new StringBuilder
    val is_message= new StringBuilder
    val firsr_author= new StringBuilder
    val is_mine= new StringBuilder

    if (str == null){
      psn_name.append("null"+"#")
      org_name.append("null"+"#")
      email.append("null"+"#")
      is_message.append("null"+"#")
      firsr_author.append("null"+"#")
      is_mine.append("null"+"#")
    }
    else if (str.contains("author\":[{")){

      val jsonArray = JSON.parseObject(str).getJSONArray("author")

      if(jsonArray.size()>0) {
        for (i <- 0 until jsonArray.size()) {
          if(jsonArray.get(i).toString.contains("psn_name")){
            val jSONObject = jsonArray.getJSONObject(i)

            psn_name.clear()
            org_name.clear()
            email.clear()
            is_message.clear()
            firsr_author.clear()
            is_mine.clear()

            psn_name.append(jSONObject.get("psn_name") + "#")
            org_name.append(jSONObject.get("org_name") + "#")
            email.append(jSONObject.get("email") + "#")
            is_message.append(jSONObject.get("is_message") + "#")
            firsr_author.append(jSONObject.get("firsr_author") + "#")
            is_mine.append(jSONObject.get("is_mine") + "#")
            jSONObject.clear()

          } else {
            psn_name.clear()
            org_name.clear()
            email.clear()
            is_message.clear()
            firsr_author.clear()
            is_mine.clear()

            psn_name.append("null"+"#")
            org_name.append("null"+"#")
            email.append("null"+"#")
            is_message.append("null"+"#")
            firsr_author.append("null"+"#")
            is_mine.append("null"+"#")
          }
        }
      } else {
        psn_name.clear()
        org_name.clear()
        email.clear()
        is_message.clear()
        firsr_author.clear()
        is_mine.clear()

        psn_name.append("null"+"#")
        org_name.append("null"+"#")
        email.append("null"+"#")
        is_message.append("null"+"#")
        firsr_author.append("null"+"#")
        is_mine.append("null"+"#")
      }
    } else if (str.contains("author\":{")){
      psn_name.clear()
      org_name.clear()
      email.clear()
      is_message.clear()
      firsr_author.clear()
      is_mine.clear()

      val jSONObject = JSON.parseObject(str).getJSONObject("author")
      psn_name.append(jSONObject.get("psn_name")+"#")
      org_name.append(jSONObject.get("org_name")+"#")
      email.append(jSONObject.get("email")+"#")
      is_message.append(jSONObject.get("is_message")+"#")
      firsr_author.append(jSONObject.get("firsr_author")+"#")
      is_mine.append(jSONObject.get("is_mine")+"#")
      jSONObject.clear()
    }
    else {

      psn_name.append("null"+"#")
      org_name.append("null"+"#")
      email.append("null"+"#")
      is_message.append("null"+"#")
      firsr_author.append("null"+"#")
      is_mine.append("null"+"#")
    }

    psn_name.toString().stripSuffix("#") + "\t<&\t"+
      org_name.toString().stripSuffix("#")+ "\t<&\t"+
      email.toString().stripSuffix("#")+ "\t<&\t"+
      is_message.toString().stripSuffix("#")+ "\t<&\t"+
      firsr_author.toString().stripSuffix("#")+ "\t<&\t"+
      is_mine.toString().stripSuffix("#")

  }















  def pub_extend(str:String,pub_type_id:String): String ={
    val pub_extendString:String = null
    if(str == null){
      return pub_extendString
    }

    if (str.startsWith("{")){
      val jsonObject = JSON.parseObject(str)
      pub_extendString == assemblyPub_extend(jsonObject)

    }

    if (str.startsWith("[")){
      val array: JSONArray = JSON.parseArray(str)
      for (i<- 0 until array.size() ){
        val jsonObject: JSONObject = array.getJSONObject(i)
        if (jsonObject.get("pub_type_id").equals(pub_type_id)){
          pub_extendString == assemblyPub_extend(jsonObject)
        }
      }
    }
    return pub_extendString
  }


  def assemblyPub_extend(jsonObject:JSONObject): String ={
    val issue_no_01 :String  = null
    val issue_no_02 :String  = null

    if (jsonObject.get("issue_no") != null){
      if (jsonObject.get("issue_no").toString.startsWith("[")) {
        val issueArray  = jsonObject.getJSONArray("issue_no")
        if (issueArray.size > 0) {
          for (i <- 0 until issueArray.size()) {
            val issueObject = issueArray.getJSONObject(i)
            if (issueObject != null && issueObject.containsKey("code")) {
              if (issueObject.get("code") == "01") if (issueObject.containsKey("content") && issueObject.get("content") != null) issue_no_01 == issueObject.get("content").toString
              if (issueObject.get("code") == "02") if (issueObject.containsKey("content") && issueObject.get("content") != null) issue_no_02 == issueObject.get("content").toString
            }
          }
        }
      }
      if (jsonObject.get("issue_no").toString.startsWith("{") && jsonObject.containsKey("code")) {
        if (jsonObject.get("code") == "01") if (jsonObject.get("content") != null) issue_no_01== jsonObject.get("content").toString
        if (jsonObject.get("code") == "02") if (jsonObject.get("content") != null) issue_no_02== jsonObject.get("content").toString
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
