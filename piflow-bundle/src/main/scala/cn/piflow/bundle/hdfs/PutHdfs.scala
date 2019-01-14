package cn.piflow.bundle.hdfs


import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.FileSystem
import org.apache.spark.sql.SparkSession


class PutHdfs extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
  override val description: String = "from dataframe write data to hdfs"

  var hdfsPath :String= _
  var hdfsUrl :String= _
  var types :String= _
  var partition :Int= 3

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDF = in.read()
    //inDF.show()
    inDF.schema.printTreeString()

    //val path = new Path(hdfsUrl+hdfsPath)

    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)
    println(hdfsUrl+hdfsPath+"pppppppppppppppppppppppppppppppp--putHdfs")

      if (types=="json"){
        inDF.repartition(partition).write.json(hdfsUrl+hdfsPath)
      } else if (types=="csv"){
        inDF.repartition(partition).write.csv(hdfsUrl+hdfsPath)
      } else {
        //parquet
        inDF.repartition(partition).write.save(hdfsUrl+hdfsPath)
      }

  }
  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsPath = MapUtil.get(map,key="hdfsPath").asInstanceOf[String]
    types = MapUtil.get(map,key="types").asInstanceOf[String]
    val partition1 = MapUtil.get(map,key="partition").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsPath = new PropertyDescriptor().name("hdfsPath").displayName("hdfsPath").defaultValue("").required(true)
    val hdfsUrl = new PropertyDescriptor().name("hdfsUrl").displayName("hdfsUrl").defaultValue("").required(true)
    val types = new PropertyDescriptor().name("types").displayName("json,csv,parquet").defaultValue("").required(true)
    val partition = new PropertyDescriptor().name("partition").displayName("repartition").defaultValue("").required(true)
    descriptor = partition :: descriptor
    descriptor = types :: descriptor
    descriptor = hdfsPath :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("hdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }


}
