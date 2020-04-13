package cn.piflow.bundle.hbase

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.hadoop.hbase.HBaseConfiguration
import org.apache.hadoop.hbase.mapreduce.TableInputFormat
import org.apache.hadoop.hbase.util.Bytes
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Row, SparkSession}

import scala.collection.mutable.ArrayBuffer

class ReadHbase extends ConfigurableStop{

  override val authorEmail: String = "bf219319@cnic.com"
  override val description: String = "Read data from Hbase"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var quorum :String= _
  var port :String = _
  var znodeParent:String= _
  var table:String=_
  var rowid:String=_
  var family:String= _
  var qualifier:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val hbaseConf = HBaseConfiguration.create()
    hbaseConf.set("hbase.zookeeper.quorum", quorum)
    hbaseConf.set("hbase.zookeeper.property.clientPort", port)
    hbaseConf.set("zookeeper.znode.parent",znodeParent)
    hbaseConf.set(TableInputFormat.INPUT_TABLE, table)
    val sc = spark.sparkContext

    val hbaseRDD= sc.newAPIHadoopRDD(hbaseConf, classOf[TableInputFormat],
      classOf[org.apache.hadoop.hbase.io.ImmutableBytesWritable],
      classOf[org.apache.hadoop.hbase.client.Result])

    val schema: Array[String] = qualifier.split(",")
    val families=family.split(",")

    val col_str=rowid+","+qualifier
    val newSchema:Array[String]=col_str.split(",")

    val fields: Array[StructField] = newSchema.map(d=>StructField(d,StringType,nullable = true))
    val dfSchema: StructType = StructType(fields)


    val kv = hbaseRDD.map(r => {
      val rowkey = Bytes.toString(r._2.getRow)
      val row = new ArrayBuffer[String]
      row += rowkey
      if(families.size==1){
        schema.foreach(c => {
          val fields = Bytes.toString(r._2.getValue(Bytes.toBytes(family), Bytes.toBytes(c)))
          row += fields

        })
      }else{
        families.foreach(f=>{
          schema.foreach(c => {
            val fields = Bytes.toString(r._2.getValue(Bytes.toBytes(f), Bytes.toBytes(c)))
            if (fields==null){
              row
            }else{
              row += fields
            }
          })
        })
      }
      Row.fromSeq(row.toArray.toSeq)
    })

    val df=spark.createDataFrame(kv,dfSchema)

    out.write(df)

  }
  override def setProperties(map: Map[String, Any]): Unit = {
    quorum = MapUtil.get(map,key="quorum").asInstanceOf[String]
    port = MapUtil.get(map,key="port").asInstanceOf[String]
    znodeParent = MapUtil.get(map,key="znodeParent").asInstanceOf[String]
    table = MapUtil.get(map,key="table").asInstanceOf[String]
    rowid = MapUtil.get(map,key="rowid").asInstanceOf[String]
    family = MapUtil.get(map,key="family").asInstanceOf[String]
    qualifier = MapUtil.get(map,key="qualifier").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val quorum = new PropertyDescriptor()
      .name("quorum")
      .displayName("Quorum")
      .defaultValue("")
      .description("Zookeeper cluster address")
      .required(true)
      .example("10.0.0.101,10.0.0.102,10.0.0.103")
    descriptor = quorum :: descriptor

    val port = new PropertyDescriptor()
      .name("port")
      .displayName("Port")
      .defaultValue("")
      .description("Zookeeper connection port")
      .required(true)
      .example("2181")
    descriptor = port :: descriptor

    val znodeParent = new PropertyDescriptor()
      .name("znodeParent")
      .displayName("ZnodeParent")
      .defaultValue("")
      .description("Hbase znode location in zookeeper")
      .required(true)
      .example("/hbase-unsecure")
    descriptor = znodeParent :: descriptor

    val table = new PropertyDescriptor()
      .name("table")
      .displayName("Table")
      .defaultValue("")
      .description("Table in Hbase")
      .required(true)
      .example("test or dbname:test")
    descriptor = table :: descriptor

    val rowid = new PropertyDescriptor()
      .name("rowid")
      .displayName("rowid")
      .defaultValue("")
      .description("Rowkey of table in Hbase")
      .required(true)
      .example("rowkey")
    descriptor = rowid :: descriptor

    val family = new PropertyDescriptor()
      .name("family")
      .displayName("Family")
      .defaultValue("")
      .description("The column family of table")
      .required(true)
      .example("info")
    descriptor = family :: descriptor

    val qualifier = new PropertyDescriptor()
      .name("qualifier")
      .displayName("Qualifier")
      .defaultValue("")
      .description("Field of column family")
      .required(true)
      .example("name,age")
    descriptor = qualifier :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hbase/GetHbase.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HbaseGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
