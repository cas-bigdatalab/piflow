package cn.piflow.bundle.microorganism

import java.io.{BufferedInputStream, BufferedReader, ByteArrayInputStream, InputStreamReader}
import java.text.SimpleDateFormat

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.json.JSONObject

class GeneParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Parsing gene type data"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session = pec.get[SparkSession]()

    val inDf: DataFrame = in.read()
    val configuration: Configuration = new Configuration()

    var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]
    val pathARR: Array[String] = pathStr.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){
      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)

    val hdfsPathTemporary:String = hdfsUrl+"/Refseq_genomeParser_temporary.json"
    val path: Path = new Path(hdfsPathTemporary)

    if(fs.exists(path)){
      fs.delete(path)
    }

    fs.create(path).close()
    var fdos: FSDataOutputStream = fs.append(path)

    var jsonStr: String =""

    var bis: BufferedInputStream =null

    var names:Array[String]=Array("tax_id", "geneID", "symbol", "locus_tag", "synonyms", "dbxrefs", "chromosome", "map_location", "description", "type_of_gene",
      "symbol_from_nomenclature_authority", "full_name_from_nomenclature_authority",
      "nomenclature_status", "other_designations", "modification_date")
    val format: java.text.DateFormat = new SimpleDateFormat("yyyyMMdd").asInstanceOf[java.text.DateFormat]
    val newFormat: SimpleDateFormat = new SimpleDateFormat("yyyy-MM-dd")

    var n:Int=0
    inDf.collect().foreach(row => {

      pathStr = row.get(0).asInstanceOf[String]

      var fdis: FSDataInputStream = fs.open(new Path(pathStr))

      var br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))

      var line:String=""
      var doc:JSONObject=null

      while ((line=br.readLine()) != null){
        if( ! line.startsWith("#")){
          n += 1
          doc=new JSONObject()
          val tokens: Array[String] = line.split("\\\t")
          for(i <- (0 until 15)){
            if(i < 2){
              doc.put(names(i),Integer.parseInt(tokens(i).trim))
            }else if(i < 14){
              if(tokens(i).equals("-")){
                doc.put(names(i),"")
              }else{
                doc.put(names(i),tokens(i))
              }
            }else{
              doc.put(names(i),newFormat.format(format.parse(tokens(i))))
            }
          }
          jsonStr = doc.toString
          if (n == 1) {
            bis = new BufferedInputStream(new ByteArrayInputStream(("[" + jsonStr).getBytes()))
          } else {
            bis = new BufferedInputStream(new ByteArrayInputStream(("," + jsonStr).getBytes()))
          }

          val buff: Array[Byte] = new Array[Byte](1048576)

          var count: Int = bis.read(buff)
          while (count != -1) {
            fdos.write(buff, 0, count)
            fdos.flush()
            count = bis.read(buff)
          }
          fdos.flush()
          bis = null
          doc = null
        }
      }

    })
    bis = new BufferedInputStream(new ByteArrayInputStream(("]").getBytes()))
    val buff: Array[Byte] = new Array[Byte](1048576)

    var count: Int = bis.read(buff)
    while (count != -1) {
      fdos.write(buff, 0, count)
      fdos.flush()
      count = bis.read(buff)
    }
    fdos.flush()

    fdos.close()

    val df: DataFrame = session.read.json(hdfsPathTemporary)

    out.write(df)


  }

  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("microorganism/png/Gene.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
