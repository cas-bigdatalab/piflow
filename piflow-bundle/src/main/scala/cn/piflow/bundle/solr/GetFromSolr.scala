package cn.piflow.bundle.solr
import java.util

import scala.collection.JavaConversions._
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.solr.client.solrj.SolrQuery
import org.apache.solr.client.solrj.SolrQuery.ORDER
import org.apache.solr.client.solrj.impl.HttpSolrClient
import org.apache.solr.client.solrj.response.QueryResponse
import org.apache.solr.common.SolrDocumentList
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.mutable.ListBuffer


class GetFromSolr extends ConfigurableStop{
  override val authorEmail: String ="18525746364@163.com"
  override val description: String = ""
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var solrURL:String=_
  var SolrCollection:String=_
  var q:String=_
  var start:String=_
  var rows:String=_
  var sortBy:String=_
  var DescentOrAscend:String=_
  var fl:String=_
  var fq:String=_
  var df:String=_
  var indent:String=_


  var ss: SparkSession=_

  override def setProperties(map: Map[String, Any]): Unit = {
    solrURL=MapUtil.get(map,"solrURL").asInstanceOf[String]
    SolrCollection=MapUtil.get(map,"SolrCollection").asInstanceOf[String]
    q=MapUtil.get(map,"QueryStr").asInstanceOf[String]
    start=MapUtil.get(map,"start").asInstanceOf[String]
    rows=MapUtil.get(map,"rows").asInstanceOf[String]
    sortBy=MapUtil.get(map,"sortBy").asInstanceOf[String]
    DescentOrAscend=MapUtil.get(map,"DescentOrAscend").asInstanceOf[String]
    fl=MapUtil.get(map,"fl").asInstanceOf[String]
    fq=MapUtil.get(map,"fq").asInstanceOf[String]
    df=MapUtil.get(map,"df").asInstanceOf[String]
    indent=MapUtil.get(map,"indent").asInstanceOf[String]
  }



  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    var url=solrURL+"/"+SolrCollection
    ss =pec.get[SparkSession]()
    val context: SparkContext = ss.sparkContext
    val client: HttpSolrClient = new HttpSolrClient.Builder(url).build()


    val query: SolrQuery = new SolrQuery()
    query.set("q",q)

    if(start.size>0){
      query.setStart(start.toInt)
    }
    if(rows.size>0){
      query .setRows(rows.toInt)
    }
    if(sortBy.size>0){
      if(DescentOrAscend.equals("descent")||DescentOrAscend.equals("Descent")){
        query.setSort(sortBy,ORDER.desc)
      }else if(DescentOrAscend.equals("Ascend")||DescentOrAscend.equals("ascend")){
        query.setSort(sortBy,ORDER.asc)
      }else{
        query.setSort(sortBy,ORDER.asc)
      }
    }
    if(fl.size>0){
      query.set("fl",fl)
    }
    if(fq.size>0){
      query.set("fq",fq)
    }
    if(df.size>0){
      query.set("df",fq)
    }
    if(indent.size>0){
      query.set("df",indent)
    }


    val response: QueryResponse = client.query(query)
    var resultsList:SolrDocumentList=response.getResults()
    var listbuffer : ListBuffer[Map[String, AnyRef]] = new ListBuffer[Map[String,AnyRef]]
    var keySTR:String=""

    for (i <- resultsList) {
      val SolrDocumentMap: util.Map[String, AnyRef] = i.getFieldValueMap
      val set: util.Set[String] = SolrDocumentMap.keySet()
      var DFmap:Map[String,AnyRef]=Map()

      keySTR=""
      for(x <- set){
        var key:String=x
        keySTR+=(key+" ")
        DFmap += ( key -> SolrDocumentMap.get(key))
      }
      listbuffer += DFmap
    }

    val rows1: List[Row] = listbuffer.toList.map(map => {
      val values: Iterable[AnyRef] = map.values
      val seq: Seq[AnyRef] = values.toSeq
      val seqSTR: Seq[String] = values.toSeq.map(x=>x.toString)
      val row: Row = Row.fromSeq(seqSTR)
      row
    })
    val rowRDD: RDD[Row] = context.makeRDD(rows1)

    val arrKey: Array[String] = keySTR.split(" ")
    val fields: Array[StructField] = arrKey.map(d=>StructField(d,StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val Fdf: DataFrame = ss.createDataFrame(rowRDD,schema)

    Fdf.show()

    out.write(Fdf)
  }



  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("solr.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.SolrGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val solrURL = new PropertyDescriptor().name("solrURL").displayName("solrURL").defaultValue("").allowableValues(Set("")).required(true)
    descriptor = solrURL :: descriptor
    val SolrCollection = new PropertyDescriptor().name("SolrCollection").displayName("SolrCollection").defaultValue("").allowableValues(Set("")).required(true)
    descriptor = SolrCollection :: descriptor
    val q = new PropertyDescriptor().name("q").displayName("q").defaultValue("").allowableValues(Set("")).description("Query String").required(true)
    descriptor = q :: descriptor
    val start = new PropertyDescriptor().name("start").displayName("start").defaultValue("Start Display Position").allowableValues(Set("")).description("   ").required(false)
    descriptor = start :: descriptor
    val rows = new PropertyDescriptor().name("rows").displayName("rows").description("Display Number Each Page").defaultValue("").allowableValues(Set("")).required(false)
    descriptor = rows :: descriptor
    val sortBy = new PropertyDescriptor().name("sortBy").displayName("sortBy").description("Sort Field").defaultValue("").allowableValues(Set("")).required(false)
    descriptor = sortBy :: descriptor
    val DescentOrAscend = new PropertyDescriptor().name("DescentOrAscend").displayName("DescentOrAscend").defaultValue("").allowableValues(Set("")).required(false)
    descriptor = DescentOrAscend :: descriptor
    val fq = new PropertyDescriptor().name("fq").displayName("fq").description("Filter Query").defaultValue("").allowableValues(Set("")).required(false)
    descriptor = fq :: descriptor
    val fl = new PropertyDescriptor().name("fl").description("Return Field").displayName("fl").defaultValue("").allowableValues(Set("")).required(false)
    descriptor = fl :: descriptor
    val df = new PropertyDescriptor().name("df").displayName("df").description("Default Query Field").defaultValue("").allowableValues(Set("")).required(false)
    descriptor = df :: descriptor
    val indent = new PropertyDescriptor().name("indent").displayName("indent").defaultValue("").allowableValues(Set("")).required(false)
    descriptor = indent :: descriptor
    descriptor
  }
}