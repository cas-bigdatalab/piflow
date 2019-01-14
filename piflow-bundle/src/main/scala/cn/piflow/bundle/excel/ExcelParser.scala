package cn.piflow.bundle.excel

import java.io.File

import cn.piflow._
import cn.piflow.bundle.util.ExcelToJson
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import net.sf.json.JSONArray
import org.apache.spark.sql.{Row, SparkSession}


class ExcelParser extends ConfigurableStop{

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parse excel file to json "
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var excelPath: String = _

  var list = List("")
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    import spark.implicits._
    val inDf = in.read()


    val rows: Array[Row] = inDf.collect()
    for (i <- 0 until rows.length){
      val path1 = rows(i)(0).toString
      println("***"+path1+"---")
      // "excelPath":"/ftpGoldData/test1.xlsx"
      if (path1.endsWith(".xls") || path1.endsWith("xlsx")){
        println(path1)
        val f1 = new File(path1)
        // 调用 工具类 解析 Excel .xls   .xlsx
        val array: JSONArray = ExcelToJson.readExcel(f1)

        for (i <- 0 until array.size()){
          list = array.get(i).toString :: list
        }
      }
    }

    val outDF = sc.parallelize(list).toDF("jsonObject")
    //println(outDF.count())
    //outDF.show()
    out.write(outDF)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
   // excelPath = MapUtil.get(map,"excelPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
//    val excelPath = new PropertyDescriptor().name("excelPath").displayName("excelPath").description("The path of excel file").defaultValue("").required(true)
//    descriptor = excelPath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("excel.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ExcelGroup.toString)
  }

}

