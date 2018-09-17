package cn.piflow.bundle.hive

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import cn.piflow.conf.{ConfigurableStop, HiveGroup, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class PutHiveQL extends ConfigurableStop {

  override val authorEmail: String = "xiaoxiao@cnic.cn"
  val inportCount: Int = 0
  val outportCount: Int = 1

  var database:String =_

    var hiveQL_path:String =_

    def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
      val spark = pec.get[SparkSession]()

      import spark.sql

      import scala.io.Source
      sql(sqlText= "use "+database)
      var lines:String=""
      Source.fromFile(hiveQL_path).getLines().foreach(x=>{
        if(x.contains(";")){
          lines=lines+" "+x.replace(";","")
          println(lines)
          sql(sqlText = lines)
          lines=""
        }else{
          lines=lines+" "+x
        }

      })
    }

    def initialize(ctx: ProcessContext): Unit = {

    }

    def setProperties(map : Map[String, Any]): Unit = {
      hiveQL_path = MapUtil.get(map,"hiveQL_path").asInstanceOf[String]
      database = MapUtil.get(map,"database").asInstanceOf[String]
    }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hiveQL_path = new PropertyDescriptor().name("hiveQL_Path").displayName("HiveQL_Path").defaultValue("").required(true)
    val database=new PropertyDescriptor().name("database").displayName("DataBase").defaultValue("").required(true)
    descriptor = hiveQL_path :: descriptor
    descriptor = database :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): StopGroup = {
    HiveGroup
  }

}
