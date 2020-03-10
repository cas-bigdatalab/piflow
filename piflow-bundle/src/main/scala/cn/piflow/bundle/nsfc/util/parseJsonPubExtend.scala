//package cn.piflow.bundle.nsfc.util
//
//import com.alibaba.fastjson.{JSON, JSONArray, JSONObject}
//
///**
//  * @auther ygang@cnic.cn
//  * @create 9/11/19
//  */
//object parseJsonPubExtend extends Serializable {
//
//
//  def parseAuthor(str :String):String={
//
//    val psn_name= new StringBuilder
//    val org_name= new StringBuilder
//    val email= new StringBuilder
//    val is_message= new StringBuilder
//    val firsr_author= new StringBuilder
//    val is_mine= new StringBuilder
//
//    if (str == null){
//      psn_name.append("null"+"#")
//      org_name.append("null"+"#")
//      email.append("null"+"#")
//      is_message.append("null"+"#")
//      firsr_author.append("null"+"#")
//      is_mine.append("null"+"#")
//    }
//    else if (str.contains("author\":[{")){
//      val jsonArray = JSON.parseObject(str).getJSONArray("author")
//      if(jsonArray.size>0) {
//        for (i <- 0 until jsonArray.size()) {
//          if(jsonArray.get(i).toString.contains("psn_name")){
//            val jSONObject = jsonArray.getJSONObject(i)
//
//            psn_name.append(jSONObject.get("psn_name") + "#")
//            org_name.append(jSONObject.get("org_name") + "#")
//            email.append(jSONObject.get("email") + "#")
//            is_message.append(jSONObject.get("is_message") + "#")
//            firsr_author.append(jSONObject.get("first_author") + "#")
//            is_mine.append(jSONObject.get("is_mine") + "#")
//            jSONObject.clear()
//
//          } else {
//            psn_name.append("null"+"#")
//            org_name.append("null"+"#")
//            email.append("null"+"#")
//            is_message.append("null"+"#")
//            firsr_author.append("null"+"#")
//            is_mine.append("null"+"#")
//          }
//        }
//      } else {
//        psn_name.append("null"+"#")
//        org_name.append("null"+"#")
//        email.append("null"+"#")
//        is_message.append("null"+"#")
//        firsr_author.append("null"+"#")
//        is_mine.append("null"+"#")
//      }
//    } else if (str.contains("author\":{")){
//      val jSONObject = JSON.parseObject(str).getJSONObject("author")
//      psn_name.append(jSONObject.get("psn_name")+"#")
//      org_name.append(jSONObject.get("org_name")+"#")
//      email.append(jSONObject.get("email")+"#")
//      is_message.append(jSONObject.get("is_message")+"#")
//      firsr_author.append(jSONObject.get("first_author")+"#")
//      is_mine.append(jSONObject.get("is_mine")+"#")
//      jSONObject.clear()
//    }
//    else {
//      psn_name.append("null"+"#")
//      org_name.append("null"+"#")
//      email.append("null"+"#")
//      is_message.append("null"+"#")
//      firsr_author.append("null"+"#")
//      is_mine.append("null"+"#")
//    }
//
//    psn_name.toString().stripSuffix("#") + "  &  "+
//      org_name.toString().stripSuffix("#")+ "  &  "+
//      email.toString().stripSuffix("#")+ "  &  "+
//      is_message.toString().stripSuffix("#")+ "  &  "+
//      firsr_author.toString().stripSuffix("#")+ "  &  "+
//      is_mine.toString().stripSuffix("#")
//
//  }
//
//
//
//
//
//
//
//
//  def pub_extend(str:String,pub_type_id:String): String ={
//
//
//    var pub_extendString:String = null
//    if(str == null){
//      return pub_extendString
//    }
//
//    if (str.startsWith("{")){
//      val jsonObject = JSON.parseObject(str)
//      pub_extendString = assemblyPub_extend(jsonObject)
//
//    }
//
//    if (str.startsWith("[")){
//      val array: JSONArray = JSON.parseArray(str)
//      for (i<- 0 until array.size() ){
//        val jsonObject: JSONObject = array.getJSONObject(i)
//
//        if(jsonObject.containsKey("pub_type_id") && jsonObject.get("pub_type_id") != null) if (jsonObject.get("pub_type_id").toString == pub_type_id) pub_extendString = assemblyPub_extend(jsonObject)
//
//      }
//    }
//
//    return pub_extendString
//
//  }
//
//
//  def assemblyPub_extend(jsonObject:JSONObject): String ={
//
//    var issue_no_01 :String  = null
//    var issue_no_02 :String  = null
//
//    if (jsonObject.get("issue_no") != null){
//      if (jsonObject.get("issue_no").toString.startsWith("[")) {
//        val issueArray  = jsonObject.getJSONArray("issue_no")
//        if (issueArray.size > 0) {
//          for (i <- 0 until issueArray.size()) {
//            val issueObject = issueArray.getJSONObject(i)
//            if (issueObject != null && issueObject.containsKey("code")) {
//              if (issueObject.get("code") == "01") if (issueObject.containsKey("content") && issueObject.get("content") != null) issue_no_01 = issueObject.get("content").toString
//              if (issueObject.get("code") == "02") if (issueObject.containsKey("content") && issueObject.get("content") != null) issue_no_02 = issueObject.get("content").toString
//            }
//          }
//        }
//      }
//      if (jsonObject.get("issue_no").toString.startsWith("{") && jsonObject.containsKey("code")) {
//        if (jsonObject.get("code") == "01") if (jsonObject.get("content") != null) issue_no_01 = jsonObject.get("content").toString
//        if (jsonObject.get("code") == "02") if (jsonObject.get("content") != null) issue_no_02 = jsonObject.get("content").toString
//      }
//    }
//
//
//    val aaa: String = jsonObject.get("article_no") +  "  &  "+
//      jsonObject.get("begin_num") + "  &  "+
//      jsonObject.get("city") + "  &  "+
//      jsonObject.get("conf_end_day") + "  &  "+
//      jsonObject.get("conf_end_month") + "  &  "+
//      jsonObject.get("conf_end_year") + "  &  "+
//      jsonObject.get("conf_name") + "  &  "+
//      jsonObject.get("conf_org") + "  &  "+
//      jsonObject.get("conf_start_day") + "  &  "+
//      jsonObject.get("conf_start_month") + "  &  "+
//      jsonObject.get("conf_start_year") + "  &  "+
//      jsonObject.get("conf_type") + "  &  "+
//      jsonObject.get("country_name") + "  &  "+
//      jsonObject.get("doi") + "  &  "+
//      jsonObject.get("end_num") + "  &  "+
//      jsonObject.get("paper_type") + "  &  "+
//      jsonObject.get("product_mark") + "  &  "+
//      jsonObject.get("product_mark_name") +"  &  "+
//      jsonObject.get("public_status") + "  &  "+
//      jsonObject.get("impact_factors") + "  &  "+
//      jsonObject.get("include_start")+ "  &  "+
//      jsonObject.get("journal_name")+ "  &  "+
//      issue_no_01+ "  &  "+
//      issue_no_02
//
//    return aaa
//  }
//
//}
