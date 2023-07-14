//package cn.piflow.bundle.hbase
//
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import org.apache.hadoop.hbase.HBaseConfiguration
//import org.apache.hadoop.hbase.client.{Put, Result}
//import org.apache.hadoop.hbase.io.ImmutableBytesWritable
//import org.apache.hadoop.hbase.mapreduce.{TableInputFormat, TableOutputFormat}
//import org.apache.hadoop.hbase.util.Bytes
//import org.apache.hadoop.mapreduce.Job
//import org.apache.spark.sql.SparkSession
//
//
//class PutHbase extends ConfigurableStop{
//
//  override val authorEmail: String = "bf219319@163.com"
//  override val description: String = "Put data to Hbase"
//  override val inportList: List[String] = List(Port.DefaultPort)
//  override val outportList: List[String] = List(Port.DefaultPort)
//
//  var quorum :String= _
//  var port :String = _
//  var znodeParent:String= _
//  var outPutDir : String =_
//  var table:String=_
//  var rowid:String=_
//  var family:String= _
//  var qualifier:String=_
//
//  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
//
//    val spark = pec.get[SparkSession]()
//
//    val sc = spark.sparkContext
//
//    val hbaseConf=sc.hadoopConfiguration
//    hbaseConf.set("hbase.zookeeper.quorum", quorum)
//    hbaseConf.set("hbase.zookeeper.property.clientPort", port)
//    hbaseConf.set("zookeeper.znode.parent",znodeParent)
//    hbaseConf.set("mapreduce.output.fileoutputformat.outputdir", outPutDir)
//    hbaseConf.set(TableOutputFormat.OUTPUT_TABLE, table)
//
//    val job=Job.getInstance(hbaseConf)
//    job.setOutputKeyClass(classOf[ImmutableBytesWritable])
//    job.setOutputValueClass(classOf[Result])
//    job.setOutputFormatClass(classOf[TableOutputFormat[ImmutableBytesWritable]])
//    job.setJobName("dfToHbase")
//
//    val df = in.read()
//
//    val qualifiers=qualifier.split(",").map(x => x.trim)
//
//    df.rdd.map(row =>{
//      val rowkey = nullHandle(row.getAs[String](rowid))
//      val p=new Put(Bytes.toBytes(rowkey))
//
//      qualifiers.foreach(a=>{
//        val value = nullHandle(row.getAs[String](a))
//        p.addColumn(Bytes.toBytes(family),Bytes.toBytes(a),Bytes.toBytes(value))
//      })
//
//      (new ImmutableBytesWritable,p)
//    }).saveAsNewAPIHadoopDataset(job.getConfiguration)
//
//
//    sc.stop()
//    spark.stop()
//
//  }
//  def nullHandle(str:String):String={
//    if (str == null || "".equals(str)){
//      return "null"
//    }else {
//      return str
//    }
//  }
//  override def setProperties(map: Map[String, Any]): Unit = {
//    quorum = MapUtil.get(map,key="quorum").asInstanceOf[String]
//    port = MapUtil.get(map,key="port").asInstanceOf[String]
//    znodeParent = MapUtil.get(map,key="znodeParent").asInstanceOf[String]
//    outPutDir = MapUtil.get(map,key="outPutDir").asInstanceOf[String]
//    table = MapUtil.get(map,key="table").asInstanceOf[String]
//    rowid = MapUtil.get(map,key="rowid").asInstanceOf[String]
//    family = MapUtil.get(map,key="family").asInstanceOf[String]
//    qualifier = MapUtil.get(map,key="qualifier").asInstanceOf[String]
//
//  }
//
//  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
//    var descriptor : List[PropertyDescriptor] = List()
//    val quorum = new PropertyDescriptor()
//      .name("quorum")
//      .displayName("Quorum")
//      .defaultValue("")
//      .description("Zookeeper cluster address")
//      .required(true)
//      .example("10.0.0.101,10.0.0.102,10.0.0.103")
//    descriptor = quorum :: descriptor
//
//    val port = new PropertyDescriptor()
//      .name("port")
//      .displayName("Port")
//      .defaultValue("")
//      .description("Zookeeper connection port")
//      .required(true)
//      .example("2181")
//    descriptor = port :: descriptor
//
//    val znodeParent = new PropertyDescriptor()
//      .name("znodeParent")
//      .displayName("ZnodeParent")
//      .defaultValue("")
//      .description("Hbase znode location in zookeeper")
//      .required(true)
//      .example("/hbase-unsecure")
//    descriptor = znodeParent :: descriptor
//
//    val outPutDir = new PropertyDescriptor()
//      .name("outPutDir")
//      .displayName("outPutDir")
//      .defaultValue("")
//      .description("Hbase temporary workspace,job output path")
//      .required(true)
//      .example("/tmp")
//    descriptor = znodeParent :: descriptor
//
//    val table = new PropertyDescriptor()
//      .name("table")
//      .displayName("Table")
//      .defaultValue("")
//      .description("Table in Hbase")
//      .required(true)
//      .example("test or dbname:test")
//    descriptor = table :: descriptor
//
//    val rowid = new PropertyDescriptor()
//      .name("rowid")
//      .displayName("RowId")
//      .defaultValue("")
//      .description("Id of table in hive and Rowkey of table in Hbase")
//      .required(true)
//      .example("id")
//    descriptor = rowid :: descriptor
//
//    val family = new PropertyDescriptor()
//      .name("family")
//      .displayName("Family")
//      .defaultValue("")
//      .description("The column family of table,only one column family is allowed")
//      .required(true)
//      .example("info")
//    descriptor = family :: descriptor
//
//    val qualifier = new PropertyDescriptor()
//      .name("qualifier")
//      .displayName("Qualifier")
//      .defaultValue("")
//      .description("Field of column family,the column that does contain the unique id in the hive table")
//      .required(true)
//      .example("name,age,gender")
//    descriptor = qualifier :: descriptor
//
//    descriptor
//  }
//
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/hbase/GetHbase.png")
//  }
//
//  override def getGroup(): List[String] = {
//    List(StopGroup.HbaseGroup)
//  }
//
//  override def initialize(ctx: ProcessContext): Unit = {
//
//  }
//}
