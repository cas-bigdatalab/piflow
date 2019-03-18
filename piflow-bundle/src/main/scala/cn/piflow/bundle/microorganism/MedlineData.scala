package cn.piflow.bundle.microorganism

import java.io.{BufferedReader, InputStreamReader, OutputStreamWriter}
import java.text.SimpleDateFormat
import java.util.Locale

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.json.{JSONObject, XML}

class MedlineData extends  ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Parse Medline data"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)


   var docName = "PubmedArticle"
   val formatter = new SimpleDateFormat("yyyy-MM-dd")
   val format = new SimpleDateFormat("dd-MM-yyyy")
   val format_english = new SimpleDateFormat("dd-MMM-yyyy", Locale.ENGLISH)

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val inDf: DataFrame = in.read()
    var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]

    val configuration: Configuration = new Configuration()
    val pathARR: Array[String] = pathStr.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){
      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)

    val hdfsPathTemporary:String = hdfsUrl+"/yqd/test/medline/medlineAll.json"
    val path: Path = new Path(hdfsPathTemporary)
    if(fs.exists(path)){
      fs.delete(path)
    }
    fs.create(path).close()
    val hdfsWriter: OutputStreamWriter = new OutputStreamWriter(fs.append(path))

    var fdis: FSDataInputStream = null
    var br: BufferedReader = null
    var doc: JSONObject = null

    var count = 0
    var fileNum = 0
    inDf.collect().foreach(row => {
      fileNum += 1

      pathStr = row.get(0).asInstanceOf[String]
      println(fileNum+"-----start parser ^^^" + pathStr)
      fdis = fs.open(new Path(pathStr))
      br = new BufferedReader(new InputStreamReader(fdis))
      var i = 0
      var eachLine: String= ""
      while (i < 3) {
        eachLine = br.readLine()
        i += 1
      }
      var xml = ""
      while ((eachLine = br.readLine) != null   && eachLine != null ) {

        xml += eachLine

        if (eachLine.indexOf("</"+docName+">")!= -1){
          count += 1

          doc = XML.toJSONObject(xml).getJSONObject(docName).optJSONObject("MedlineCitation")
          println(count)
//          println(doc.toString)


          if (doc.optJSONObject("DateCreated") != null) {
            val dateCreated = doc.getJSONObject("DateCreated")
            doc.remove("DateCreated")
            doc.put("CreatedYear", dateCreated.get("Year"))
            if (dateCreated.opt("Day") != null && dateCreated.opt("Month") != null && dateCreated.opt("Year") != null) {
              val date = dateCreated.get("Day") + "-" + dateCreated.get("Month") + "-" + dateCreated.get("Year")
              doc.put("CreatedDate", formatter.format(format.parse(date)))
            }
          }

          if (doc.optJSONObject("DateCompleted") != null) {
            val dateCompleted = doc.getJSONObject("DateCompleted")
            doc.remove("DateCompleted")
            doc.put("CompletedYear", dateCompleted.get("Year"))
            if (dateCompleted.opt("Day") != null && dateCompleted.opt("Month") != null && dateCompleted.opt("Year") != null) {
              val date = dateCompleted.get("Day") + "-" + dateCompleted.get("Month") + "-" + dateCompleted.get("Year")
              doc.put("CompletedDate", formatter.format(format.parse(date)))
            }
          }

          if (doc.optJSONObject("DateRevised") != null) {
            val dateRevised = doc.getJSONObject("DateRevised")
            doc.remove("DateRevised")
            doc.put("RevisedYear", dateRevised.get("Year"))
            if (dateRevised.opt("Day") != null && dateRevised.opt("Month") != null && dateRevised.opt("Year") != null) {
              val date = dateRevised.get("Day") + "-" + dateRevised.get("Month") + "-" + dateRevised.get("Year")
              doc.put("RevisedDate", formatter.format(format.parse(date)))
            }
          }

          if (doc.opt("Article") != null) {
            val article = doc.getJSONObject("Article")
            if (article.opt("Abstract") != null) {
              val abstrac = article.getJSONObject("Abstract")
              if (abstrac != null) {
                val abstract_text = abstrac.opt("AbstractText")
                if (abstract_text.isInstanceOf[String]) {
                  val tmp = new JSONObject
                  tmp.put("content", abstract_text)
                  abstrac.put("AbstractText", tmp)
                }
              }
            }
            if (article.optJSONObject("Journal") != null)
              if (article.getJSONObject("Journal").optJSONObject("JournalIssue") != null)
                if (article.getJSONObject("Journal").getJSONObject("JournalIssue").optJSONObject("PubDate") != null) {

                  val pubDate = article.getJSONObject("Journal").getJSONObject("JournalIssue").getJSONObject("PubDate")

                  if (pubDate.opt("Year") != null) doc.put("PubYear", pubDate.get("Year"))

                  if (pubDate.opt("Year") != null && pubDate.opt("Month") != null && pubDate.opt("Day") != null) {



                    var  month = pubDate.get("Month")
                    if (month.toString.contains("01") || month.toString.contains("1")) month = "Jan"
                    if (month.toString.contains("02") || month.toString.contains("2")) month = "Feb"
                    if (month.toString.contains("03") || month.toString.contains("3")) month = "Mar"
                    if (month.toString.contains("04") || month.toString.contains("4")) month = "Apr"
                    if (month.toString.contains("05") || month.toString.contains("5")) month = "May"
                    if (month.toString.contains("06") || month.toString.contains("6")) month = "Jun"
                    if (month.toString.contains("07") || month.toString.contains("7")) month = "Jul"
                    if (month.toString.contains("08") || month.toString.contains("8")) month = "Aug"
                    if (month.toString.contains("09") || month.toString.contains("9")) month = "Sep"
                    if (month.toString.contains("10")) month = "Oct"
                    if (month.toString.contains("11")) month = "Nov"
                    if (month.toString.contains("12")) month = "Dec"


                    val date = pubDate.get("Day") + "-" +month + "-" + pubDate.get("Year")

//                    println(date+"@@@@@@@@@@@")
                    doc.put("PubDate", formatter.format(format_english.parse(date)))
              }
            }
          }

          val articleDateParent = findJSONObject("ArticleDate", doc)
          if (articleDateParent != null) if (articleDateParent.optJSONObject("ArticleDate") != null) {
            val articleDate = articleDateParent.getJSONObject("ArticleDate")
            if (articleDate.opt("Year") != null && articleDate.opt("Month") != null && articleDate.opt("Day") != null) {
              val date = articleDate.opt("Day") + "-" + articleDate.opt("Month") + "-" + articleDate.opt("Year")
              doc.put("articleDate", formatter.format(format.parse(date)))
            }
          }

          doc.write(hdfsWriter)
          hdfsWriter.write("\n")

          xml = ""

        }
      }
      br.close()
      fdis.close()
    })
    hdfsWriter.close()

    val df: DataFrame = pec.get[SparkSession]().read.json(hdfsPathTemporary)
    df.schema.printTreeString()
//    println(df.count())
    out.write(df)

  }


  def findJSONObject(objKey: String, obj: JSONObject): JSONObject = {
    import scala.collection.JavaConversions._
    for (key <- obj.keySet) {
      if (key == objKey) return obj
      else if (obj.optJSONObject(key) != null) return findJSONObject(objKey, obj.getJSONObject(key))
      else if (obj.optJSONArray(key) != null) {

        for (i<- 0 until(obj.getJSONArray(key).length)){

          if (obj.getJSONArray(key).optJSONObject(i) != null){
            if (findJSONObject(objKey, obj.getJSONArray(key).getJSONObject(i)) != null){
              return findJSONObject(objKey, obj.getJSONArray(key).getJSONObject(i))
            }
          }

        }

      }
    }
    return null
  }




  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] ={
    var descriptor = List()
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/MedlineData.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
