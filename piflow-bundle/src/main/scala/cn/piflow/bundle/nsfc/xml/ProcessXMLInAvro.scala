package cn.piflow.bundle.nsfc.xml

import cn.piflow.bundle.nsfc.util.parseJsonPubExtend
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import com.alibaba.fastjson.JSON
import org.apache.spark.sql.SparkSession

class ProcessXMLInAvro extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "ProcessXMLInAvro"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val df = in.read()

    var psn_name= new StringBuilder
    var org_name= new StringBuilder
    var email= new StringBuilder
    var is_message= new StringBuilder
    var firsr_author= new StringBuilder
    var is_mine= new StringBuilder
    spark.sqlContext.udf.register("parseAuthors",(str:String)=>{
      psn_name.clear()
      org_name.clear()
      email.clear()
      is_message.clear()
      firsr_author.clear()
      is_mine.clear()

      if (str == null ){
        psn_name.append("null"+"#")
        org_name.append("null"+"#")
        email.append("null"+"#")
        is_message.append("null"+"#")
        firsr_author.append("null"+"#")
        is_mine.append("null"+"#")
      } else {

        val str1 = JSON.parseObject(str).get("author")
        if (str1 == null){
          psn_name.append("null"+"#")
          org_name.append("null"+"#")
          email.append("null"+"#")
          is_message.append("null"+"#")
          firsr_author.append("null"+"#")
          is_mine.append("null"+"#")
        }

        else  if (str1.toString.startsWith("[")){
          val jsonArray = JSON.parseArray(str1.toString)
          for (i<- 0 until jsonArray.size()){
            val jSONObject = jsonArray.getJSONObject(i)
            psn_name.append(jSONObject.get("psn_name")+"#")
            org_name.append(jSONObject.get("org_name")+"#")
            email.append(jSONObject.get("email")+"#")
            is_message.append(jSONObject.get("is_message")+"#")
            firsr_author.append(jSONObject.get("firsr_author")+"#")
            is_mine.append(jSONObject.get("is_mine")+"#")
          }


        }
        else if (str1.toString.startsWith("{")){
          val jSONObject = JSON.parseObject(str1.toString)
          psn_name.append(jSONObject.get("psn_name")+"#")
          org_name.append(jSONObject.get("org_name")+"#")
          email.append(jSONObject.get("email")+"#")
          is_message.append(jSONObject.get("is_message")+"#")
          firsr_author.append(jSONObject.get("firsr_author")+"#")
          is_mine.append(jSONObject.get("is_mine")+"#")
        }
      }



      psn_name.toString().stripSuffix("#") + "\t<&\t"+
        org_name.toString().stripSuffix("#")+ "\t<&\t"+
        email.toString().stripSuffix("#")+ "\t<&\t"+
        is_message.toString().stripSuffix("#")+ "\t<&\t"+
        firsr_author.toString().stripSuffix("#")+ "\t<&\t"+
        is_mine.toString().stripSuffix("#")

    })

    spark.sqlContext.udf.register("parseExtend",(str:String,pub_type_id:String)=>{
      parseJsonPubExtend.pub_extend(str,pub_type_id)

    })


    df.createOrReplaceTempView("test")
    val outDF = spark.sql(
      """
        |select
        |id
        |,product_xml.product.pub_basic.authenticated
        |
        |
        |,split(parseAuthors(product_xml.product.pub_basic.authors),'\t<&\t')[0] as psn_name
        |,split(parseAuthors(product_xml.product.pub_basic.authors),'\t<&\t')[1] as org_name
        |,split(parseAuthors(product_xml.product.pub_basic.authors),'\t<&\t')[2] as email
        |,split(parseAuthors(product_xml.product.pub_basic.authors),'\t<&\t')[3] as is_message
        |,split(parseAuthors(product_xml.product.pub_basic.authors),'\t<&\t')[4] as firsr_author
        |,split(parseAuthors(product_xml.product.pub_basic.authors),'\t<&\t')[5] as is_mine
        |
        |
        |,product_xml.product.pub_basic.authors_name
        |,product_xml.product.pub_basic.cited_times
        |,product_xml.product.pub_basic.create_date
        |,product_xml.product.pub_basic.en_pub_type_name
        |,product_xml.product.pub_basic.en_source
        |,product_xml.product.pub_basic.en_title
        |,product_xml.product.pub_basic.full_link
        |,product_xml.product.pub_basic.full_text.description
        |,product_xml.product.pub_basic.full_text.file_code
        |,product_xml.product.pub_basic.full_text.file_name
        |,product_xml.product.pub_basic.full_text.pub_fulltext_file_name
        |,product_xml.product.pub_basic.full_text.upload_date
        |,product_xml.product.pub_basic.full_text_img_url
        |,product_xml.product.pub_basic.has_full_text
        |,product_xml.product.pub_basic.labeled
        |,product_xml.product.pub_basic.language
        |,product_xml.product.pub_basic.list_bdzw
        |,product_xml.product.pub_basic.list_cssci
        |,product_xml.product.pub_basic.list_ei
        |,product_xml.product.pub_basic.list_ei_source
        |,product_xml.product.pub_basic.list_istp
        |,product_xml.product.pub_basic.list_istp_source
        |,product_xml.product.pub_basic.list_qt
        |,product_xml.product.pub_basic.list_sci
        |,product_xml.product.pub_basic.list_sci_source
        |,product_xml.product.pub_basic.list_ssci
        |,product_xml.product.pub_basic.list_ssci_source
        |,product_xml.product.pub_basic.owner
        |,product_xml.product.pub_basic.product_mark
        |,product_xml.product.pub_basic.pub_date_desc
        |,product_xml.product.pub_basic.pub_detail_param
        |,product_xml.product.pub_basic.pub_id
        |,product_xml.product.pub_basic.pub_type_id
        |,product_xml.product.pub_basic.pub_update_date
        |,product_xml.product.pub_basic.public_date
        |,product_xml.product.pub_basic.public_date1
        |,product_xml.product.pub_basic.public_date_j
        |,product_xml.product.pub_basic.public_day
        |,product_xml.product.pub_basic.public_day1
        |,product_xml.product.pub_basic.public_day2
        |,product_xml.product.pub_basic.public_day_j
        |,product_xml.product.pub_basic.public_month
        |,product_xml.product.pub_basic.public_month1
        |,product_xml.product.pub_basic.public_month2
        |,product_xml.product.pub_basic.public_month_j
        |,product_xml.product.pub_basic.public_year
        |,product_xml.product.pub_basic.public_year1
        |,product_xml.product.pub_basic.public_year2
        |,product_xml.product.pub_basic.public_year_j
        |,product_xml.product.pub_basic.publish_day
        |,product_xml.product.pub_basic.publish_month
        |,product_xml.product.pub_basic.publish_year
        |,product_xml.product.pub_basic.relevance
        |,product_xml.product.pub_basic.remark
        |,product_xml.product.pub_basic.status
        |,product_xml.product.pub_basic.update_mark
        |,product_xml.product.pub_basic.version_no
        |,product_xml.product.pub_basic.zh_abstract
        |,product_xml.product.pub_basic.zh_key_word
        |,product_xml.product.pub_basic.zh_pub_type_name
        |,product_xml.product.pub_basic.zh_source
        |,product_xml.product.pub_basic.zh_title
        |
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[0] as article_no
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[1] as begin_num
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[2] as city
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[3] as conf_end_day
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[4] as conf_end_month
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[5] as conf_end_year
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[6] as conf_name
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[7] as conf_org
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[8] as conf_start_day
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[9] as conf_start_month
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[10] as conf_start_year
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[11] as conf_type
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[12] as country_name
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[13] as doi
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[14] as end_num
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[15] as paper_type
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[16] as product_mark
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[17] as product_mark_name
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[18] as public_status
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[19] as impact_factors
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[20] as include_start
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[21] as issue_no_01
        |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'\t<&\t')[22] as issue_no_02
        | from test
      """.stripMargin)


    outDF.printSchema()
    out.write(outDF)

  }



  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()


    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/xml/XmlParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup.toString)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
