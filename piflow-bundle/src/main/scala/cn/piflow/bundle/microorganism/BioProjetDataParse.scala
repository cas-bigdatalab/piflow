package cn.piflow.bundle.microorganism

import java.io._
import java.net.UnknownHostException
import java.util.regex.Pattern

import cn.piflow.bundle.microorganism.util.BioProject
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{Row, SparkSession}
import org.biojava.bio.BioException
import org.elasticsearch.spark.sql.EsSparkSQL
import org.json.{JSONArray, JSONObject, XML}

import scala.util.parsing.json.JSON



class BioProjetDataParse extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Load file from ftp url."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)


  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  var name:String = "Package"
  var dp = Pattern.compile("((\\d{4})-(\\d{2})-(\\d{2}))(T.*)")

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext

    val inDf= in.read()
    inDf.show()
    inDf.schema.printTreeString()

    val rows: Array[Row] = inDf.collect()

    var path:String = null
    for (i <- 0 until rows.size) {
      if (rows(i)(0).toString.endsWith("bioproject.xml")){
        path = rows(i)(0).toString

//        val path1 = "/ftpBioProject/bioproject.xml"
    try {
      val br = new BufferedReader(new FileReader(path))
      var line: String = null

      var i = 0
      while (i < 2) {
        br.readLine()
        i = i + 1
      }
      var count = 0
      var xml = new StringBuffer()
      var x = 0
      while ((line = br.readLine()) != null || x ==0) {

        xml.append(line)
        if (line.equals("</PackageSet>")) {
          println("----------------------------------break")
          x == 1
          return x
        }
        else if (line.indexOf("</" + name + ">") != -1) { //reach the end of a doc
          println("-----------------------------------------"+count)
          count = count + 1
          val doc = XML.toJSONObject(xml.toString()).getJSONObject(name)
          println("#####################################################"+count)
          println(doc)

          xml = new StringBuffer()

          //     accession       PRJNA31525
          val accession = doc.getJSONObject("Project").getJSONObject("Project")
            .getJSONObject("ProjectID")
            .getJSONObject("ArchiveID")
            .getString("accession")

          val projectDescr = doc.getJSONObject("Project").getJSONObject("Project")
                    .getJSONObject("ProjectDescr")

          // 加载 json 字符串 为 df
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString() :: Nil)
          val jsonDF = spark.read.json(jsonRDD)
          jsonDF.show()
          //      jsonDF.schema.printTreeString()

          val options = Map("es.index.auto.create"-> "true",
//             "es.mapping.id"->accession,
            "es.nodes"->es_nodes,"es.port"->port)

          // df 写入 es
          EsSparkSQL.saveToEs(jsonDF,s"${es_index}/${es_type}",options)


//          val bio  = new BioProject
//          bio.convertConcrete2KeyVal(projectDescr,"LocusTagPrefix")

// --------------1
//          if (projectDescr.opt("ProjectReleaseDate") != null){
//            val date = projectDescr.get("ProjectReleaseDate").toString
//            val m = dp.matcher(date)
//            if (m.matches()){
//              //         m.group(1)     2017-04-25
//              //        m.group(2))      2017
//              projectDescr.put("ProjectReleaseDate",m.group(1))
//              projectDescr.put("ProjectReleaseDate",Integer.parseInt(m.group(2)))
//
//            } else {
//              //       date       2012-05-21T00:00:00Z
//              projectDescr.put("ProjectReleaseDate",date)
//            }
//          }

// ----------------2
//          if (projectDescr.optJSONObject("Publication") !=null){
//            val pub = projectDescr.getJSONObject("Publication")
//            if (pub.opt("date") !=null){
//              val date = projectDescr.getJSONObject("Publication").get("date").toString
//              val m = dp.matcher(date)
//              if (m.matches()){
//                //         m.group(1)     2017-04-25
//                //        m.group(2))      2017
//                projectDescr.put("date",m.group(1))
//                projectDescr.put("year",Integer.parseInt(m.group(2)))
//              } else {
//                //       date       2012-05-21T00:00:00Z
//                projectDescr.put("date","##############99#")
//              }
//            }
//          }
//

// ----------------3
//          if(doc.optJSONObject("Submission").optJSONObject("submitted") != null){
//            val  submission = doc.optJSONObject("Submission").optJSONObject("submitted");
//            if(submission.opt("submitted") != null){
//              val  date = submission.get("submitted");
//              submission.put("submission_year", Integer.parseInt(date.toString().substring(0, 4)));
//            }
//          }
// ----------------4
//          val  grant = projectDescr.opt("Grant");
//          if(grant != null){
//            if(grant isInstanceOf[JSONArray]){
//              for(int k = 0 ; k < ((JSONArray)grant).length(); k++){
//                JSONObject singleGrant = (JSONObject)((JSONArray)grant).get(k);
//                convertConcrete2KeyVal(singleGrant, "Agency");
//              }
//            }else if(grant instanceof JSONObject){
//              convertConcrete2KeyVal((JSONObject)grant, "Agency");
//            }
//          }


// ----------------5
//          val projectID = doc.getJSONObject("Project").getJSONObject("Project").getJSONObject("ProjectID");
//          bio.convertConcrete2KeyVal(projectID, "LocalID");
//          Object organization = doc.optJSONObject("Submission").optJSONObject("Submission").optJSONObject("Description").opt("Organization");
//          if(organization instanceof JSONArray){
//            for(int j = 0; j < ((JSONArray) organization).length(); j++){
//              val orgz = ((JSONArray) organization).get(j);
//              bio.convertConcrete2KeyVal(((JSONObject)orgz), "Name");
//            }
//          }else if(organization instanceof JSONObject){
//            val orgz = (JSONObject)organization;
//            bio.convertConcrete2KeyVal(orgz, "Name");
//          }

// ----------------6
//          val  projTypeSubmission = doc.getJSONObject("Project").getJSONObject("Project").getJSONObject("ProjectType").optJSONObject("ProjectTypeSubmission");
//          if(projTypeSubmission != null){
//            val bioSampleSet = projTypeSubmission.getJSONObject("Target").optJSONObject("BioSampleSet");
//            if(bioSampleSet != null){
//              bio.convertConcrete2KeyVal(bioSampleSet, "ID");
//            }
//          }

        }
      }

    } catch {
      case e: UnknownHostException =>
        e.printStackTrace()
      case e: FileNotFoundException =>
        e.printStackTrace()
      case e: IOException =>
        e.printStackTrace()
    }
      }
    }
  }

  def setProperties(map: Map[String, Any]): Unit = {
    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    port=MapUtil.get(map,key="port").asInstanceOf[String]
    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("es_nodes").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("port").defaultValue("").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("es_index").defaultValue("").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("es_type").defaultValue("").required(true)


    descriptor = es_nodes :: descriptor
    descriptor = port :: descriptor
    descriptor = es_index :: descriptor
    descriptor = es_type :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("bioProject.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
