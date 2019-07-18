package cn.piflow.bundle.nsfc.distinct

import cn.piflow.bundle.util.NSFCUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.{Row, SparkSession}

class PersonIdExpansion extends ConfigurableStop{
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = "nothing to say bro"
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var expandIDFieldName : String = _
  var expandIDTypeName : String = _
  var useSchemaTable : Boolean = _
  var schemaTable : String = _
  var sourceTable :String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    expandIDFieldName = MapUtil.get(map,"expandIDField").asInstanceOf[String]
    expandIDTypeName = MapUtil.get(map,"expandIDType").asInstanceOf[String]
    schemaTable = MapUtil.get(map,"schemaTableName").asInstanceOf[String]
    useSchemaTable = MapUtil.get(map,"usedTableSchema").asInstanceOf[Boolean]
    sourceTable = MapUtil.get(map,"source").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val expandIDFieldName = new PropertyDescriptor().
      name("expandIDField").
      displayName("expand ID field").
      description("the id field you need to expand in your dataFrame").
      defaultValue("card_code").
      required(true)
    descriptor = expandIDFieldName :: descriptor

    val expandIDTypeName = new PropertyDescriptor().
      name("expandIDType").
      displayName("expand ID type").
      description("the id type field you need to expand in your dataFrame").
      defaultValue("card_type").
      required(true)
    descriptor = expandIDTypeName :: descriptor

    val useSchemaTable = new PropertyDescriptor().
      name("usedTableSchema").
      displayName("is table schema used").
      description("if you try to use another table to be the after schema of this DataFrame").
      defaultValue("false").
      required(true).
      allowableValues(Set("true", "false"))

    descriptor = useSchemaTable :: descriptor

    val schemaTable = new PropertyDescriptor().
      name("schemaTableName").
      displayName("the table which you can get the schema").
      description("is usedTableSchema is true, this should be a hive table name").
      defaultValue("middle.m_person").
      required(true)
    descriptor = schemaTable :: descriptor

    val source = new PropertyDescriptor().
      name("source").
      displayName("source").
      description("source table name").
      defaultValue("temp.t_person").
      required(true)
    descriptor = source :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = ImageUtil.getImage("icon/hive/SelectHiveQL.png")

  override def getGroup(): List[String] =  List(StopGroup.NSFC.toString, "sha0w", "distinct")

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    if (in.isEmpty()) throw new Exception("in DF is indispensable")
    val sc: SparkSession = pec.get[SparkSession]()
    val inDF = in.read()
    val beforeSchema = inDF.schema
    val afterSchema = if (useSchemaTable) {
      sc.read.table(schemaTable).schema
    } else {
      NSFCUtil.mkPersonSchemaWithID(beforeSchema, expandIDFieldName, expandIDTypeName)
    }
    val outRow: RDD[Row] = inDF.rdd.map(r => {
      r.toSeq
    }).map(seq => NSFCUtil.buildNewOPersonRow(seq, beforeSchema, afterSchema, expandIDTypeName, expandIDFieldName, sourceTable))
    out.write(sc.createDataFrame(outRow, afterSchema))
  }
}
