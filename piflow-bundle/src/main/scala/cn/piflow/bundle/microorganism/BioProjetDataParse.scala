package cn.piflow.bundle.microorganism

import java.io._
import java.util.regex.{Matcher, Pattern}

import cn.piflow.bundle.microorganism.util.BioProject
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.json.{JSONArray, JSONObject, XML}




class BioProjetDataParse extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parsing BioProjet type data"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var cachePath:String = _
  var name:String = "Package"
  var dp = Pattern.compile("((\\d{4})-(\\d{2})-(\\d{2}))(T.*)")

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext

    val inDf= in.read()

    val configuration: Configuration = new Configuration()
    var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]
    val pathARR: Array[String] = pathStr.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){
      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)

    val hdfsPathTemporary = hdfsUrl+cachePath+"/bioprojectCatch/bioproject.json"

    val path: Path = new Path(hdfsPathTemporary)
    if(fs.exists(path)){
      fs.delete(path)
    }
    fs.create(path).close()
    var fdosOut: FSDataOutputStream = fs.append(path)
    var jsonStr: String =""
    var bisIn: BufferedInputStream =null


    inDf.collect().foreach(row =>{
      val pathStr = row.get(0).asInstanceOf[String]

      var fdis: FSDataInputStream = fs.open(new Path(pathStr))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))
      var line: String = null
      var i= 0
      while(i<2){
        br.readLine()
        i = i + 1
      }
      var count = 0
      var xml = new StringBuffer()
      var x = 0
      while ((line = br.readLine()) != null && x <1  && line!= null) {
        xml.append(line)
        if (line.equals("</PackageSet>")){
          println("----------------------------------break")
          x == 1
        } else if (line.indexOf("</" + name + ">") != -1){ //reach the end of a doc
          count = count + 1
          val doc: JSONObject = XML.toJSONObject(xml.toString()).getJSONObject(name)

          val accession = doc.getJSONObject("Project").getJSONObject("Project")
            .getJSONObject("ProjectID")
            .getJSONObject("ArchiveID")
            .getString("accession")

          val projectDescr = doc.getJSONObject("Project").getJSONObject("Project")
            .getJSONObject("ProjectDescr")

          val bio  = new BioProject
          bio.convertConcrete2KeyVal(projectDescr,"LocusTagPrefix")

          // --------------1
          if (projectDescr.opt("ProjectReleaseDate") != null){
            val date = projectDescr.get("ProjectReleaseDate").toString
            val m: Matcher = dp.matcher(date)
            if (m.matches()){
              projectDescr.put("ProjectReleaseDate",m.group(1))
              projectDescr.put("ProjectReleaseYear",Integer.parseInt(m.group(2)))

            } else {
              projectDescr.put("ProjectReleaseDate",date)
            }
          }
          //           ----------------2
          if (projectDescr.optJSONObject("Publication") !=null){
            val pub = projectDescr.getJSONObject("Publication")
            if (pub.opt("date") !=null){
              val date = pub.get("date").toString
              val m: Matcher = dp.matcher(date)
              if (m.matches()){
                pub.put("date",m.group(1))
                pub.put("year",Integer.parseInt(m.group(2)))
              } else {
                pub.put("date",date)
              }
            }
          }

          // ----------------3
         if(doc.getJSONObject("Project").optJSONObject("Submission") != null){
            val  submission = doc.getJSONObject("Project").optJSONObject("Submission")

            if(submission.opt("submitted") != null){

              val date = submission.get("submitted")
              submission.put("submission_year", Integer.parseInt(date.toString().substring(0, 4)));

            }
          }

          // ----------------4
          val grant: Object = projectDescr.opt("Grant")
          if(grant != null){
            if(grant.isInstanceOf[JSONArray]){
              val array: JSONArray = grant.asInstanceOf[JSONArray]
              for(k <- 0 until  array.length()){
                val singleGrant = array.get(k).asInstanceOf[JSONObject]
                bio.convertConcrete2KeyVal(singleGrant, "Agency");
              }
            }
            else if(grant.isInstanceOf[JSONObject]){
              val array: JSONObject = grant.asInstanceOf[JSONObject]
              bio.convertConcrete2KeyVal(array, "Agency");
            }
          }

          // ----------------5
          val projectID = doc.getJSONObject("Project").getJSONObject("Project").getJSONObject("ProjectID");
          bio.convertConcrete2KeyVal(projectID, "LocalID");
          val  organization =  doc.getJSONObject("Project").optJSONObject("Submission").optJSONObject("Description").opt("Organization");
          if(organization.isInstanceOf[JSONArray] ){
            val array: JSONArray = organization.asInstanceOf[JSONArray]
            for(k <- 0 until  array.length()){
              val orgz =  array.get(k).asInstanceOf[JSONObject]
              bio.convertConcrete2KeyVal(orgz, "Name");
            }
          }else if(organization.isInstanceOf[JSONObject]){
            val orgz: JSONObject = organization.asInstanceOf[JSONObject]
            bio.convertConcrete2KeyVal(orgz, "Name");
          }

          //           ----------------6
          val  projTypeSubmission = doc.getJSONObject("Project").getJSONObject("Project").getJSONObject("ProjectType").optJSONObject("ProjectTypeSubmission");

          if(projTypeSubmission != null){
            val bioSampleSet = projTypeSubmission.getJSONObject("Target").optJSONObject("BioSampleSet");
            if(bioSampleSet != null){
              bio.convertConcrete2KeyVal(bioSampleSet, "ID");
            }
          }
          if (count ==1 ) {
            bisIn = new BufferedInputStream(new ByteArrayInputStream(("[" + doc.toString).getBytes()))
          }
          else {
            bisIn = new BufferedInputStream(new ByteArrayInputStream(("," + doc.toString).getBytes()))
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
          xml = new StringBuffer()

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

    println("start parser HDFSjsonFile")
    val df: DataFrame = spark.read.json(hdfsPathTemporary)

    df.schema.printTreeString()

    out.write(df)

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
    ImageUtil.getImage("microorganism/png/BioProject.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
