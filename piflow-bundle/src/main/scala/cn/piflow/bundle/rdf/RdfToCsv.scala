package cn.piflow.bundle.rdf

import java.util.regex.{Matcher, Pattern}

import cn.piflow.bundle.util.Entity
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Row, SparkSession}

class RdfToCsv extends ConfigurableStop{
  override val authorEmail: String = "shaow@cnic.cn"
  override val inportCount: Int = 1
  override val outportCount: Int = 1
  override val description: String = "Simple spark program to convert *.n3 RDF file to CSV(DataFrame) file"

  var rdfFilepath : String = _
  var isFront : String = _
  var PRegex : String = _
  var RRegex : String = _
  var ERegex : String = _
  var RSchema : String = _
  var entityPort : String = "entityOut"
  var relationshipPort : String = "relationshipOut"

  override def setProperties(map: Map[String, Any]): Unit = {
    isFront = MapUtil.get(map, "isFromFront").asInstanceOf[String]
    PRegex = MapUtil.get(map, "propertyRegex").asInstanceOf[String]
    RRegex = MapUtil.get(map, "relationshipRegex").asInstanceOf[String]
    ERegex = MapUtil.get(map, "entityRegex").asInstanceOf[String]
    RSchema = MapUtil.get(map, "relationshipSchema").asInstanceOf[String]

    if (isFront == "false")
      rdfFilepath = MapUtil.get(map, "filePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {

      var descriptor: List[PropertyDescriptor] = List()
      val filePath = new PropertyDescriptor()
        .name("filePath")
        .displayName("inputHDFSFilePath")
        .description("The path of the input rdf file")
        .defaultValue("")
        .required(true)


      val isFromFront = new PropertyDescriptor()
        .name("isFromFront")
        .displayName("isFromFront")
        .description("identify the file path source(should have same schema)")
        .allowableValues(Set("true", "false"))
        .defaultValue("false")
        .required(true)

      val propertyRegex = new PropertyDescriptor()
        .name("propertyRegex")
        .displayName("property regex")
        .description("define the propertyRegex to parse the n3 file's property lines\r\n" +
          "this regex string should be fully named and regular\r\n" +
          "you need to SPECIFIC five value's name \r\n" +
          "1.prefix 2.id 3.pprefix 4.name 5.value" +
          "the form should be like this : \r\n" +
          "(?<prefix>...?<id>... ?<pprefix>...?<name> ?<value>...)\r\n" +
          "check the default value carefully to knowledge the right structure")
        .defaultValue("<(?<prefix>http:\\/\\/[^>]+\\/)(?<id>[^\\/][-A-Za-z0-9._#$%^&*!@~]+)> <(?<pprefix>http:\\/\\/[^>]+\\/)(?<name>[^\\/][-A-Za-z0-9._#$%^&*!@~]+)> \"(?<value>.+)\" \\.")
        .required(true)

      val relationshipRegex = new PropertyDescriptor()
        .name("relationshipRegex")
        .displayName("relationship regex")
        .description("define the propertyRegex to parse the n3 file's relationship lines\r\n" +
          "this regex string should be fully named and regular\r\n" +
          "you need to SPECIFIC six value's name \r\n" +
          "1.prefix1 2.id1 3.tprefix 4.type 5.prefix2 6.id2" +
          "the form should be like this : \r\n" +
          "(?<prefix1>...?<id1>... ?<tprefix>...?<type> ?<prefix2>...?<id2>)\r\n" +
          "check the default value carefully to knowledge the right structure")
        .defaultValue("<(?<prefix1>http:\\/\\/[^>]+\\/)(?<id1>[^\\/][-A-Za-z0-9._#$%^&*!@~]+)> <(?<tprefix>http:\\/\\/[^>]+\\/)(?<type>[^\\/][-A-Za-z0-9._#$%^&*!@~]+)(?<!#type)> <(?<prefix2>http:\\/\\/[^>]+\\/)(?<id2>[^\\/][-A-Za-z0-9._#$%^&*!@~]+)> \\.")
        .required(true)

      val entityRegex = new PropertyDescriptor()
        .name("entityRegex")
        .displayName("entity regex")
        .description("define the propertyRegex to parse the n3 file's entity lines\r\n" +
          "this regex string should be fully named and regular\r\n" +
          "you need to SPECIFIC four value's name \r\n" +
          "1.prefix 2.id 4.lprefix 5.label" +
          "the form should be like this : \r\n" +
          "(?<prefix>...?<id>... ... ?<lprefix>...?<label>)\r\n" +
          "check the default value carefully to knowledge the right structure")
        .defaultValue("(<(?<prefix>http:\\/\\/[^>]+\\/)(?<id>[^\\/][-A-Za-z0-9._#$%^&*!@~]+)> <(?:http:\\/\\/[^>]+\\/)(?:[^\\/][-A-Za-z0-9._#$%^&*!@~]+)(?:#type)> <(?<lprefix>http:\\/\\/[^>]+\\/)(?<label>[^\\/][-A-Za-z0-9._#$%^&*!@~]+)> \\.")
        .required(true)

      val relationshipSchema = new PropertyDescriptor()
          .name("relationshipSchema")
          .displayName("relationship's schema")
          .description("define the schema of relationship, as a user, \r\n" +
            "you should ponder the name of start id and end id\r\n" +
            "make sure your schema looks like the default value")
          .defaultValue("ENTITY_ID:START_ID,role,ENTITY_ID:END_ID,RELATION_TYPE:TYPE")
          .required(true)



      descriptor = filePath :: descriptor
      descriptor = isFromFront :: descriptor
      descriptor = propertyRegex :: descriptor
      descriptor = entityRegex :: descriptor
      descriptor = relationshipRegex :: descriptor
      descriptor = relationshipSchema :: descriptor
      descriptor
    }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/rdf.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.RDFGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream,
                       out: JobOutputStream,
                       pec: JobContext): Unit = {

    val entityRegexPattern : Pattern = Pattern.compile(ERegex)
    val relationRegexPattern : Pattern = Pattern.compile(RRegex)
    val propertyRegexPattern : Pattern = Pattern.compile(PRegex)
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    val sq = spark.sqlContext
    var hdfsFile : RDD[String] = sc.emptyRDD[String]
    //in
    if (isFront == "true") {
      val inDF : Array[String] = in
        .read()
        .collect()
        .map(r => r.getAs[String](1))
      var index = 0
      val iterator : Iterator[String] = inDF.iterator

      while(iterator.hasNext) {//every row's first col should be the exact hdfs path of the n3 file
        index match {
          case 0 => hdfsFile = sc.textFile(iterator.next())
            index += 1
          case 1000 =>
            println(hdfsFile.count()) //in some case the num of file will excess 10w, use this way to reduce the depth of DAG
            index = 1
          case _ => hdfsFile = hdfsFile.union(sc.textFile(iterator.next))
            index += 1
        }
      }
    } else {
      hdfsFile = sc.textFile(rdfFilepath)
    }
    val entityRdd = hdfsFile
          .filter(s => entityRegexPattern.matcher(s).find() ||
            propertyRegexPattern.matcher(s).find())
        val relationshipRdd = hdfsFile
          .filter(s => relationRegexPattern.matcher(s).find())
        val settleUpEntityRdd = entityRdd.map(s => {
          val me = entityRegexPattern.matcher(s)
          val mp = propertyRegexPattern.matcher(s)
          if (me.find()) {
            (me.group("prefix") + me.group("id"), me.group())
          } else {
            mp.find()
            (mp.group("prefix") + mp.group("id"), mp.group())
          }
        })
          .groupByKey() //main
          .values
          .map(s => s.toList)
        val entitySchema : Set[String] = settleUpEntityRdd
          .map(s => s.filter(l => propertyRegexPattern.matcher(l).find()))
          .map(s => {
            s.map(line => {
              val m = propertyRegexPattern.matcher(line)
              m.find()
              m.group("name")
            })
          })
          .map(l => {
            l.toSet
          })
          .reduce(_ ++ _)


        val finalEntitySchema = "ENTITY_ID:ID," +
          entitySchema.reduce((a, b) => a + "," + b) + ",ENTITY_TYPE:LABEL"
        val entityDFSchema : StructType = StructType(finalEntitySchema.split(",")
          .map(i => StructField(i, StringType, nullable = true)))
        val relationshipDFSchema : StructType = StructType(RSchema.split(",")
          .map(i => StructField(i, StringType, nullable = true)))

        val entityRowRdd = settleUpEntityRdd.map(l => {
          val en = l.filter(s => entityRegexPattern.matcher(s).find()).head
          val label = get(entityRegexPattern.matcher(en),"lprefix") +
            get(entityRegexPattern.matcher(en),"label")
          val id = get(entityRegexPattern.matcher(en),"prefix") + get(entityRegexPattern.matcher(en),"id")
          val prop = l
            .filter(s => ?(propertyRegexPattern, s))
            .map(s => (
              get(propertyRegexPattern.matcher(s),"name")
                ->
                get(propertyRegexPattern.matcher(s),"value").replace("\"", "'")
              )
            ).toArray
            .toMap
          new Entity(id, label, prop, entitySchema.toSeq).getEntityRow
        })
        val relationshipRowRdd = relationshipRdd.map(s => Seq(
            get(relationRegexPattern.matcher(s),"prefix1") ,
            get(relationRegexPattern.matcher(s),"id1") ,
            get(relationRegexPattern.matcher(s),"tprefix") ,
            get(relationRegexPattern.matcher(s),"type") ,
            get(relationRegexPattern.matcher(s),"prefix2") ,
            get(relationRegexPattern.matcher(s),"id2") ,
            get(relationRegexPattern.matcher(s),"type")
        )
        ).map(s => Row(s))
      val entityDF = sq.createDataFrame(entityRowRdd, entityDFSchema)
      val relationDF = sq.createDataFrame(relationshipRowRdd, relationshipDFSchema)
      entityDF.show(1)
      relationDF.show(1)
      out.write(entityPort, entityDF)
      out.write(relationshipPort, relationDF)

  }

  def get(m : Matcher, name : String) : String = {
    if (m.find()) m.group(name)
    else ""
  }

  def ? (regex : Pattern, str : String) : Boolean = {
    regex.matcher(str).find()
  }
}
