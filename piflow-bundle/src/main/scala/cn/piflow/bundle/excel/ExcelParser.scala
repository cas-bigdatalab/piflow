package cn.piflow.bundle.excel


import java.io.{BufferedInputStream, ByteArrayInputStream}
import cn.piflow._
import cn.piflow.bundle.util.ExcelToJson
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import net.sf.json.JSONArray
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}

class ExcelParser extends ConfigurableStop{

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parse excel file to json "
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var jsonSavePath: String = _


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    val inDf = in.read()

    val configuration: Configuration = new Configuration()
    var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]
    val pathARR: Array[String] = pathStr.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){
      hdfsUrl+=(pathARR(x) +"/")
    }

    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)

    val path: Path = new Path(jsonSavePath)
    if(fs.exists(path)){
      fs.delete(path)
    }
    fs.create(path).close()

    var fdosOut: FSDataOutputStream = fs.append(path)
    var jsonStr: String =""
    var bisIn: BufferedInputStream =null


    var count = 0 ;
    inDf.collect().foreach(row=>{
      val pathStr = row.get(0).asInstanceOf[String]

      if (pathStr.endsWith(".xls") || pathStr.endsWith("xlsx")){

        val array: JSONArray = ExcelToJson.readExcel(pathStr,hdfsUrl)

        println(array.size())

        for (i <- 0 until array.size()){
          jsonStr = array.get(i).toString

          if (count == 0) {
            bisIn = new BufferedInputStream(new ByteArrayInputStream(("[" + jsonStr).getBytes()))
            count+=1
          } else if (count==1){
            bisIn = new BufferedInputStream(new ByteArrayInputStream(("," + jsonStr).getBytes()))
          }

          val buff: Array[Byte] = new Array[Byte](1048576)
          var num: Int = bisIn.read(buff)
          while (num != -1) {
            fdosOut.write(buff, 0, num)
            fdosOut.flush()
            num = bisIn.read(buff)
          }

          fdosOut.flush()
          bisIn = null

        }
      }
    })

    bisIn = new BufferedInputStream(new ByteArrayInputStream(("]").getBytes()))
    val buff: Array[Byte] = new Array[Byte](1048576)

    var num: Int = bisIn.read(buff)
    while (num != -1) {
      fdosOut.write(buff, 0, num)
      fdosOut.flush()
      num = bisIn.read(buff)
    }

    fdosOut.flush()
    fdosOut.close()

    val df: DataFrame = spark.read.json(jsonSavePath)

    out.write(df)


  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    jsonSavePath = MapUtil.get(map,"jsonSavePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val jsonSavePath = new PropertyDescriptor().name("jsonSavePath").displayName("jsonSavePath").description("save path of json").defaultValue("").required(true)
    descriptor = jsonSavePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("excel.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ExcelGroup.toString)
  }

}

