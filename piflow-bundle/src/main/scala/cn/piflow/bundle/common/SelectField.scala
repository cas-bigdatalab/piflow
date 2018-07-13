package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.{Column, DataFrame}


class SelectField extends ConfigurableStop {

  var schema:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()

    val field = schema.split(",")
    val columnArray : Array[Column] = new Array[Column](field.size)
    for(i <- 0 to field.size - 1){
      columnArray(i) = new Column(field(i))
    }


    var finalFieldDF : DataFrame = df.select(columnArray:_*)
    finalFieldDF.show(2)

    out.write(finalFieldDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???
}



