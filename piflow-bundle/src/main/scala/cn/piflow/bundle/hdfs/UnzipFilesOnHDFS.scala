//package cn.piflow.bundle.hdfs
//
//import java.io._
//import java.util.zip.GZIPInputStream
//
//import cn.piflow.conf._
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import org.apache.hadoop.conf.Configuration
//import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
//import org.apache.spark.rdd.RDD
//import org.apache.spark.sql.types.{StringType, StructField, StructType}
//import org.apache.spark.sql.{DataFrame, Row, SparkSession}
//import org.apache.tools.tar.{TarEntry, TarInputStream}
//
//import scala.collection.mutable.ArrayBuffer
//
//class UnzipFilesOnHDFS extends ConfigurableStop {
//  val authorEmail: String = "yangqidong@cnic.cn"
//  val description: String = "Extract files on hdfs"
//  val inportList: List[String] = List(Port.DefaultPort)
//  val outportList: List[String] = List(Port.DefaultPort)
//
//  var isCustomize:String=_
//  var hdfsUrl:String=_
//  var filePath:String=_
//  var savePath:String=_
//
//  var session: SparkSession = null
//  var arr:ArrayBuffer[Row]=ArrayBuffer()
//
//  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
//
//    session = pec.get[SparkSession]()
//
//    if(isCustomize.equals("true")){
//
//      unzipFile(hdfsUrl+filePath,savePath)
//
//    }else if (isCustomize .equals("false")){
//
//      val inDf: DataFrame = in.read()
//      inDf.collect().foreach(row => {
//        filePath = row.get(0).asInstanceOf[String]
//        unzipFile(filePath,savePath)
//      })
//    }
//
//    val rdd: RDD[Row] = session.sparkContext.makeRDD(arr.toList)
//    val fields: Array[StructField] =Array(StructField("savePath",StringType,nullable = true))
//    val schema: StructType = StructType(fields)
//    val df: DataFrame = session.createDataFrame(rdd,schema)
//
//    out.write(df)
//  }
//
//  def whatType(p:String): String = {
//    var typeStr:String=""
//    val pathNames: Array[String] = p.split("\\.")
//    val lastStr: String = pathNames.last
//    if(lastStr.equals("gz")){
//      val penultStr: String = pathNames(pathNames.length-2)
//      if(penultStr.equals("tar")){
//        typeStr="tar.gz"
//      }else {
//        typeStr="gz"
//      }
//  }else{
//      throw new RuntimeException("The file type is incorrect,or is not supported.")
//    }
//    typeStr
//  }
//
//
//  def getFs(fileHdfsPath: String): FileSystem = {
//    var configuration: Configuration = new Configuration()
//    var fs: FileSystem =null
//    if (isCustomize.equals("false")) {
//      val pathARR: Array[String] = fileHdfsPath.split("\\/")
//      hdfsUrl = ""
//      for (x <- (0 until 3)) {
//        hdfsUrl += (pathARR(x) + "/")
//      }
//    }
//    configuration.set("fs.defaultFS", hdfsUrl)
//    fs = FileSystem.get(configuration)
//    fs
//  }
//
//  def unzipFile(fileHdfsPath: String, saveHdfsPath: String)= {
//    var eachSavePath : String=""
//
//    var unType: String = whatType(fileHdfsPath)
//    var fileName: String = fileHdfsPath.split("\\/").last
//    var fs: FileSystem= getFs(fileHdfsPath)
//
//    var sp:String=""
//    if(saveHdfsPath.length < 1){
//      sp=fileHdfsPath.replace(fileName,"")
//    }else{
//      sp = hdfsUrl + saveHdfsPath
//    }
//
//    val fdis: FSDataInputStream = fs.open(new Path(fileHdfsPath))
//
//
//    if(unType.equals("gz")){
//      val gzip: GZIPInputStream = new GZIPInputStream(fdis)
//      var n = -1
//      val buf=new Array[Byte](10*1024*1024)
//
//      eachSavePath = sp +fileName.replace(".gz","")
//      arr += Row.fromSeq(Array(eachSavePath))
//      val path = new Path(eachSavePath)
//      val fdos = fs.create(path)
//      while((n=gzip.read(buf)) != -1 && n != -1){
//        fdos.write(buf,0,n)
//        fdos.flush()
//      }
//      fdos.close()
//      gzip.close()
//      fdis.close()
//    }else if(unType.equals("tar.gz")){
//
//      try {
//        val gzip = new GZIPInputStream(new BufferedInputStream(fdis))
//        val tarIn = new TarInputStream(gzip, 1024 * 2)
//
//        var entry: TarEntry = null
//
//        while ((entry = tarIn.getNextEntry) != null  && entry !=null) {
//
//          if (entry.isDirectory()) {
//            val outPath = sp + "/" + entry.getName
//            fs.create(new Path(outPath)).close()
//
//          } else {
//            val outPath = sp + "/" + entry.getName
//
//            arr += Row.fromSeq(Array(outPath))
//            val fos: FSDataOutputStream = fs.create(new Path(outPath))
//
//            var lenth = 0
//            val buff = new Array[Byte](1024)
//            while ((lenth = tarIn.read(buff)) != -1 && (lenth != -1)) {
//              fos.write(buff, 0, lenth)
//            }
//            fos.close()
//          }
//        }
//      }catch {
//        case  e: IOException =>
//          e.printStackTrace()
//      }
//
//    }
//  }
//
//
//  def initialize(ctx: ProcessContext): Unit = {
//
//  }
//
//  def setProperties(map : Map[String, Any]) = {
//    isCustomize=MapUtil.get(map,key="isCustomize").asInstanceOf[String]
//    filePath=MapUtil.get(map,key="filePath").asInstanceOf[String]
//    hdfsUrl=MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
//    savePath=MapUtil.get(map,key="savePath").asInstanceOf[String]
//  }
//
//  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
//    var descriptor : List[PropertyDescriptor] = List()
//
//    val filePath = new PropertyDescriptor()
//      .name("filePath")
//      .displayName("FilePath")
//      .defaultValue("")
//      .description("File path of HDFS")
//      .required(false)
//      .example("/work/a.gz ")
//
//
//    val hdfsUrl = new PropertyDescriptor()
//      .name("hdfsUrl")
//      .displayName("HdfsUrl")
//      .defaultValue("")
//      .description("URL address of HDFS")
//      .required(true)
//      .example("hdfs://192.168.3.138:8020")
//
//
//    val savePath = new PropertyDescriptor()
//      .name("savePath")
//      .displayName("SavePath")
//      .description("This parameter can specify the location of the decompressed file, you can choose not to fill in, " +
//      "the program saves the decompressed file in the folder where the source file is located by default. If you fill in, you can specify a folder, such as /A/AB/")
//      .defaultValue("")
//      .required(false)
//      .example("/work/aa/")
//
//
//
//    val isCustomize = new PropertyDescriptor()
//      .name("isCustomize")
//      .displayName("isCustomize")
//      .description("Whether to customize the compressed file path, if true, \n" +
//        "you must specify the path where the compressed file is located . \n" +
//        "If false, it will automatically find the file path data from the upstream port ")
//
//      .defaultValue("false").allowableValues(Set("true","false")).required(true)
//    descriptor = isCustomize :: descriptor
//    descriptor = filePath :: descriptor
//    descriptor = hdfsUrl :: descriptor
//    descriptor = savePath :: descriptor
//
//    descriptor
//  }
//
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/hdfs/UnzipFilesOnHDFS.png")
//  }
//
//  override def getGroup(): List[String] = {
//    List(StopGroup.HdfsGroup)
//  }
//}
