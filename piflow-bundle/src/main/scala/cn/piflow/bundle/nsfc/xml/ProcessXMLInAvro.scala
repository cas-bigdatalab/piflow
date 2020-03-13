//package cn.piflow.bundle.nsfc.xml
//
//import cn.piflow.bundle.nsfc.util.parseJsonPubExtend
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import com.alibaba.fastjson.{JSON, JSONArray, JSONObject}
//import org.apache.spark.sql.{SaveMode, SparkSession}
//
//class ProcessXMLInAvro extends ConfigurableStop{
//  override val authorEmail: String = "ygang@cnic.cn"
//  override val description: String = "ProcessXMLInAvro"
//  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
//  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)
//
//
//  var relevance :String = _
//  var labeled :String = _
//  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
//
//    val spark = pec.get[SparkSession]()
//
//    val df = in.read()
//
//
//    spark.sqlContext.udf.register("parseAuthors",(str:String)=>{
//      parseJsonPubExtend.parseAuthor(str)
//    })
//
//    spark.sqlContext.udf.register("parseExtend",(str:String,pub_type_id:String)=>{
//      parseJsonPubExtend.pub_extend(str,pub_type_id)
//    })
//
//
//    df.createOrReplaceTempView("test")
//
//    if(relevance.equals("true")){
//      relevance=",product_xml.product.pub_basic.relevance"
//    } else {
//      relevance=""
//    }
//    if(labeled.equals("true")){
//      labeled=",product_xml.product.pub_basic.labeled"
//    } else {
//      labeled=""
//    }
//
//    val outDF = spark.sql(
//      s"""
//         |select
//         |id
//         |,product_xml.product.pub_basic.authenticated
//         |
//         |,split(parseAuthors(product_xml.product.pub_basic.authors),'  &  ')[0] as psn_name
//         |,split(parseAuthors(product_xml.product.pub_basic.authors),'  &  ')[1] as org_name
//         |,split(parseAuthors(product_xml.product.pub_basic.authors),'  &  ')[2] as email
//         |,split(parseAuthors(product_xml.product.pub_basic.authors),'  &  ')[3] as is_message
//         |,split(parseAuthors(product_xml.product.pub_basic.authors),'  &  ')[4] as firsr_author
//         |,split(parseAuthors(product_xml.product.pub_basic.authors),'  &  ')[5] as is_mine
//         |
//         |,product_xml.product.pub_basic.authors_name
//         |,product_xml.product.pub_basic.cited_times
//         |,product_xml.product.pub_basic.create_date
//         |,product_xml.product.pub_basic.en_pub_type_name
//         |,product_xml.product.pub_basic.en_source
//         |,product_xml.product.pub_basic.en_title
//         |,product_xml.product.pub_basic.full_link
//         |,product_xml.product.pub_basic.full_text.description
//         |,product_xml.product.pub_basic.full_text.file_code
//         |,product_xml.product.pub_basic.full_text.file_name
//         |,product_xml.product.pub_basic.full_text.upload_date
//         |,product_xml.product.pub_basic.full_text_img_url
//         |,product_xml.product.pub_basic.has_full_text
//         |${labeled}
//         |,product_xml.product.pub_basic.language
//         |,product_xml.product.pub_basic.list_bdzw
//         |,product_xml.product.pub_basic.list_cssci
//         |,product_xml.product.pub_basic.list_ei
//         |,product_xml.product.pub_basic.list_ei_source
//         |,product_xml.product.pub_basic.list_istp
//         |,product_xml.product.pub_basic.list_istp_source
//         |,product_xml.product.pub_basic.list_qt
//         |,product_xml.product.pub_basic.list_sci
//         |,product_xml.product.pub_basic.list_sci_source
//         |,product_xml.product.pub_basic.list_ssci
//         |,product_xml.product.pub_basic.list_ssci_source
//         |,product_xml.product.pub_basic.owner
//         |,product_xml.product.pub_basic.product_mark
//         |,product_xml.product.pub_basic.pub_date_desc
//         |,product_xml.product.pub_basic.pub_detail_param
//         |,product_xml.product.pub_basic.pub_id
//         |,product_xml.product.pub_basic.pub_type_id
//         |,product_xml.product.pub_basic.pub_update_date
//         |,product_xml.product.pub_basic.public_date
//         |,product_xml.product.pub_basic.public_day
//         |,product_xml.product.pub_basic.public_month
//         |,product_xml.product.pub_basic.public_year
//         |,product_xml.product.pub_basic.publish_day
//         |,product_xml.product.pub_basic.publish_month
//         |,product_xml.product.pub_basic.publish_year
//         |${relevance}
//         |,product_xml.product.pub_basic.remark
//         |,product_xml.product.pub_basic.status
//         |,product_xml.product.pub_basic.update_mark
//         |,product_xml.product.pub_basic.version_no
//         |,product_xml.product.pub_basic.zh_abstract
//         |,product_xml.product.pub_basic.zh_key_word
//         |,product_xml.product.pub_basic.zh_pub_type_name
//         |,product_xml.product.pub_basic.zh_source
//         |,product_xml.product.pub_basic.zh_title
//         |
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[0] as article_no
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[1] as begin_num
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[2] as city
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[3] as conf_end_day
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[4] as conf_end_month
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[5] as conf_end_year
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[6] as conf_name
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[7] as conf_org
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[8] as conf_start_day
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[9] as conf_start_month
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[10] as conf_start_year
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[11] as conf_type
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[12] as country_name
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[13] as doi
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[14] as end_num
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[15] as paper_type
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[16] as product_mark_inner
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[17] as product_mark_name
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[18] as public_status
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[19] as impact_factors
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[20] as include_start
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[21] as journal_name
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[22] as issue_no1
//         |,split(parseExtend(product_xml.product.pub_extend,product_xml.product.pub_basic.pub_type_id),'  &  ')[23] as issue_no2
//         | from test
//      """.stripMargin)
//
//    outDF.printSchema()
//    out.write(outDF)
//
//
//  }
//
//
//
//  override def setProperties(map: Map[String, Any]): Unit = {
//    relevance = MapUtil.get(map,"relevance").asInstanceOf[String]
//    labeled = MapUtil.get(map,"labeled").asInstanceOf[String]
//  }
//
//  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
//    var descriptor : List[PropertyDescriptor] = List()
//    val relevance = new PropertyDescriptor().name("relevance").displayName("relevance").description("Does the schema contain an 'relevance' field").
//      allowableValues(Set("true","false")).defaultValue("true").required(true)
//    descriptor = relevance :: descriptor
//
//    val labeled = new PropertyDescriptor().name("labeled").displayName("labeled").description("Does the schema contain an 'labeled' field").
//      allowableValues(Set("true","false")).defaultValue("true").required(true)
//    descriptor = labeled :: descriptor
//
//
//    descriptor
//  }
//
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/xml/XmlParser.png")
//  }
//
//  override def getGroup(): List[String] = {
//    List(StopGroup.XmlGroup.toString)
//  }
//
//
//  override def initialize(ctx: ProcessContext): Unit = {
//
//  }
//
//}
