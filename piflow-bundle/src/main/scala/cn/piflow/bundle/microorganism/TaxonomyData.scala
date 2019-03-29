package cn.piflow.bundle.microorganism

import java.io._
import java.util.HashMap

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.json.JSONObject


class TaxonomyData extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parse Taxonomy data"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var cachePath:String = _

  var filePath:String = _
  var outWriteDF:DataFrame = _
  var nodesDF:DataFrame = _
  var divisionDF:DataFrame = _
  var gencodeDF:DataFrame = _
  var namesDF:DataFrame = _
  var citationsDF:DataFrame = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    val ssc = spark.sqlContext
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

    var pathDir = ""
    for (x <- 0 until pathARR.length-1){
      pathDir+=(pathARR(x) +"/")
    }
    filePath = pathDir + File.separator + "nodes.dmp"

    if (filePath.endsWith("nodes.dmp")) {
      val hdfsPathJsonCache = hdfsUrl+cachePath+"/taxonomyCache/nodes.json"
      val path: Path = new Path(hdfsPathJsonCache)
      if(fs.exists(path)){
        fs.delete(path)
      }
      fs.create(path).close()
      var fdosOut: FSDataOutputStream = fs.append(path)
      var jsonStr: String =""
      var bisIn: BufferedInputStream =null


      var fdis: FSDataInputStream = fs.open(new Path(filePath.toString))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))
      var line: String = null;
      var count =0
      while ((line = br.readLine) != null  && line != null ) {
        count = count+1
        val doc = new JSONObject()
        val tokens: Array[String] = line.split("\\t\\|\\t")
        doc.put("tax_id", tokens(0))
        doc.put("parent_tax_id", tokens(1))
        doc.put("rank", tokens(2))
        doc.put("embl_code", tokens(3))
        doc.put("division_id", tokens(4))
        doc.put("genetic_code_id", tokens(6))
        doc.put("mitochondrial_genetic_code_id", tokens(8))

        bisIn = new BufferedInputStream(new ByteArrayInputStream((doc.toString+"\n").getBytes()))

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

      fdosOut.close()

      nodesDF = spark.read.json(hdfsPathJsonCache)

      filePath = pathDir + File.separator + "division.dmp"
    }

    if (filePath.endsWith("division.dmp")){
      val hdfsPathJsonCache = hdfsUrl+cachePath+"/taxonomyCache/division.json"

      val path: Path = new Path(hdfsPathJsonCache)
      if(fs.exists(path)){
        fs.delete(path)
      }
      fs.create(path).close()
      var fdosOut: FSDataOutputStream = fs.append(path)
      var jsonStr: String =""
      var bisIn: BufferedInputStream =null

      var fdis: FSDataInputStream = fs.open(new Path(filePath.toString))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))
      var line: String = null;
      var count = 0
      while ((line = br.readLine) != null && line != null ) {
        count=count+1
        val tokens: Array[String] = line.split("\\t\\|\\t")
        val doc = new JSONObject()
        doc.put("division_id", tokens(0))
        doc.put("dive", tokens(1))
        doc.put("diname", tokens(2))


        bisIn = new BufferedInputStream(new ByteArrayInputStream((doc.toString+"\n").getBytes()))

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

      fdosOut.close()

      divisionDF = spark.read.json(hdfsPathJsonCache)
      outWriteDF=nodesDF.join(divisionDF, Seq("division_id"))

      filePath = pathDir + File.separator + "gencode.dmp"
    }

    if (filePath.endsWith("gencode.dmp")){

      val hdfsPathJsonCache = hdfsUrl+cachePath+"/taxonomyCache/gencode.json"
      val path: Path = new Path(hdfsPathJsonCache)
      if(fs.exists(path)){
        fs.delete(path)
      }
      fs.create(path).close()
      var fdosOut: FSDataOutputStream = fs.append(path)
      var jsonStr: String =""
      var bisIn: BufferedInputStream =null

      var fdis: FSDataInputStream = fs.open(new Path(filePath.toString))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))
      var line: String = null;
      var count = 0
      while ((line = br.readLine) != null && line != null ) {
        count += 1
        val tokens: Array[String] = line.split("\\t\\|\\t")
        val doc = new JSONObject()
        doc.put("genetic_code_id", tokens(0))
        doc.put("genetic_code_name", tokens(2).trim)
        doc.put("genetic_code_translation_table", tokens(3).trim)
        doc.put("genetic_code_start_codons", tokens(4).replace("\t|","").trim)


        bisIn = new BufferedInputStream(new ByteArrayInputStream((doc.toString+"\n").getBytes()))

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

      fdosOut.close()


      gencodeDF = spark.read.json(hdfsPathJsonCache)
      outWriteDF=outWriteDF.join(gencodeDF, Seq("genetic_code_id"))


      filePath = pathDir + File.separator + "names.dmp"

    }

    if (filePath.endsWith("names.dmp")){
      val hdfsPathJsonCache = hdfsUrl+cachePath+"/taxonomyCache/names.json"
      val path: Path = new Path(hdfsPathJsonCache)
      if(fs.exists(path)){
        fs.delete(path)
      }
      fs.create(path).close()
      var fdosOut: FSDataOutputStream = fs.append(path)
      var jsonStr: String =""
      var bisIn: BufferedInputStream =null

      var fdis: FSDataInputStream = fs.open(new Path(filePath.toString))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))
      var line: String = null
      var count = 0
      var pre_tax_id = "1"
      var name_key = ""

      var names = new HashMap[String,String]()

      var doc = new JSONObject()
      while ((line = br.readLine) != null && line != null ) {
        val tokens: Array[String] = line.split("\\t\\|\\t")
        name_key = tokens(3).replace("\t|","").trim

        if (tokens(0).equals(pre_tax_id)){
          if (names.containsKey(name_key)){
            names.put(name_key,names.get(name_key).toString+";"+tokens(1))
          } else {
            names.put(name_key,tokens(1))
          }
        } else {
          count += 1
          names.put("tax_id",pre_tax_id)

          doc.put("",names)
          val doc1 = doc.toString().substring(0,doc.toString.length-1)
          jsonStr = doc1.substring(4,doc1.length)

          pre_tax_id = tokens(0)
          names = new HashMap[String,String]()
          names.put(name_key,tokens(1))

          bisIn = new BufferedInputStream(new ByteArrayInputStream((jsonStr.toString+"\n").getBytes()))

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

      fdosOut.close()

      namesDF = spark.read.json(hdfsPathJsonCache)

      outWriteDF = outWriteDF.join(namesDF,Seq("tax_id"))

      filePath = pathDir + File.separator + "citations.dmp"
    }

    if (filePath.endsWith("citations.dmp")){
      var fdis: FSDataInputStream = fs.open(new Path(filePath.toString))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))
      var line: String = null
      var count = 0
      while ((line = br.readLine) != null && line != null  ) {
        count += 1
        val tokens: Array[String] = line.split("\\t\\|\\t")
        if (tokens.size > 6) {
          val pumed_id = tokens(2)
          val medline_id = tokens(3)
          val tar_ids = tokens(6).replace("\t|", "").trim

          var shouldUpdate_pubmed: Boolean = true
          var shouldUpdate_medline: Boolean = true
          var pumed_ids = null
          var medline_ids = null

          if (!tar_ids.isEmpty) {
            if (pumed_id.equals("0") && medline_id.equals("0")) {

            } else if (pumed_id.equals("0")) {
              shouldUpdate_medline = true
              shouldUpdate_pubmed = false
            } else if (medline_id.equals("0")) {
              shouldUpdate_pubmed = true
              shouldUpdate_medline = false
            } else {
              shouldUpdate_pubmed = true
              shouldUpdate_medline = true
            }

          }

        }
      }


    }

    outWriteDF.schema.printTreeString()
    outWriteDF.show()
    println("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"+outWriteDF.count())

    out.write(outWriteDF)


  }
  def processNodes(index:String,types:String)={

  }




  def setProperties(map: Map[String, Any]): Unit = {
    cachePath=MapUtil.get(map,key="cachePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val cachePath = new PropertyDescriptor().name("cachePath").displayName("cachePath").defaultValue("").required(true)
    descriptor = cachePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/TaxonomyData.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Algorithms_OntologyAnnotations.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
