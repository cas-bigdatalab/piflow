package cn.piflow.bundle.nsfc.clean

import cn.piflow.bundle.util.CleanUtil
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import org.apache.spark.sql.SparkSession

class CardCodeClean extends ConfigurableStop {
    val authorEmail: String = "songdongze@cnic.cn"
    val description: String = "Clean Id Card data."
    val inportList: List[String] = List(Port.DefaultPort.toString)
    val outportList: List[String] = List(Port.DefaultPort.toString)
    //var regex:String =_
    var cardCodeField:String=_
    var cardTypeField:String=_
    //var replaceStr:String=_

    def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
        val spark = pec.get[SparkSession]()
        val sqlContext=spark.sqlContext
        val dfOld = in.read()
        dfOld.createOrReplaceTempView("thesis")
        sqlContext.udf.register("regexPro",(str:String)=>CleanUtil.processCardCode(str))
        val structFields: Array[String] = dfOld.schema.fieldNames
        val columnNames = cardCodeField.split(",").map(x => x.trim).toSet
        val sqlNewFieldStr = new StringBuilder


        val sqlText:String="select *, if("+ cardTypeField +"='1',regexPro(" + cardCodeField + "),"+cardCodeField+") as " + cardCodeField + "_new"  + " from thesis"

        val dfNew=sqlContext.sql(sqlText)
        dfNew.createOrReplaceTempView("thesis")
        val schemaStr = new StringBuilder
        structFields.foreach(field => {
                schemaStr ++= field
        if (cardCodeField.equals(field)) {
            schemaStr ++= "_new as "
            schemaStr ++= field
        }
        schemaStr ++= ","
    })
        val sqlText1:String = "select " + schemaStr.substring(0,schemaStr.length -1) + " from thesis"
        val dfNew1=sqlContext.sql(sqlText1)

        //dfNew.show()
        out.write(dfNew1)
    }


    def initialize(ctx: ProcessContext): Unit = {

    }


    def setProperties(map: Map[String, Any]): Unit = {
        cardTypeField=MapUtil.get(map,key="cardTypeField").asInstanceOf[String]
        cardCodeField=MapUtil.get(map,key="cardCodeField").asInstanceOf[String]
    }

    override def getPropertyDescriptor(): List[PropertyDescriptor] = {
        var descriptor : List[PropertyDescriptor] = List()
        val cardTypeField = new PropertyDescriptor().name("cardTypeField").displayName("CARD TYPE FIELD NAME").description("The card type for card code ").defaultValue("card_type").required(true)
        descriptor = cardTypeField :: descriptor
        val cardCodeField = new PropertyDescriptor().name("cardCodeField").displayName("CARD CODE FIELD NAME").description("The card code  you want to clean").defaultValue("card_code").required(true)
        descriptor = cardCodeField :: descriptor
        descriptor
    }

    override def getIcon(): Array[Byte] = {
        ImageUtil.getImage("icon/clean/IdentityNumberClean.png")
    }

    override def getGroup(): List[String] = {
        List(StopGroup.NSFC.toString)
    }
}
