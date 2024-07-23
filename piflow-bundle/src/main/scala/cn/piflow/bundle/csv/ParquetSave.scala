package cn.piflow.bundle.csv

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class ParquetSave extends ConfigurableStop {
  override val authorEmail: String = "tianyao@cnic.cn"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  override val description: String = "parquet save"

  var outPath: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val df = in.read()
    //    将DataFrame写入Parquet文件
    df.write
      .mode("overwrite") // 指定写入模式，这里是覆盖已存在的文件
      .parquet(outPath)
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    outPath = MapUtil.get(map, "outPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val outPath = new PropertyDescriptor()
      .name("outPath")
      .displayName("outPath")
      .defaultValue("")
      .required(true)
      .example("1,zs\n2,ls\n3,ww")

    descriptor = outPath :: descriptor

    descriptor

  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/basic/common.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
