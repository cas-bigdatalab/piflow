package cn.piflow.bundle.json

import cn.piflow._
import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.SaveMode

class JsonSave extends ConfigurableStop{

  var jsonSavePath: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val jsonDF = in.read()
    jsonDF.show()

    jsonDF.write.format("json").mode(SaveMode.Overwrite).save(jsonSavePath)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonSavePath = MapUtil.get(map,"jsonSavePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???
}
