package cn.piflow.bundle.ml_feature

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.feature.Word2Vec
import org.apache.spark.ml.feature.Word2VecModel
import org.apache.spark.sql.SparkSession

class WordToVec extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Transfer word to vector"
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)
  var maxIter:String=_
  var maxSentenceLength:String=_
  var minCount:String=_
  var numPartitions:String=_
  var stepSize:String=_
  var vectorSize:String=_
  var colName:String=_
  var outputCol:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val df=in.read()
    df.createOrReplaceTempView("doc")
    sqlContext.udf.register("split",(str:String)=>str.split(" "))
    val sqlText:String="select split("+colName+") as "+colName+"_new from doc"
    val dfNew=sqlContext.sql(sqlText)
    dfNew.show()

    //Param for maximum number of iterations (>= 0)
    var maxIterValue:Int=50
    if(maxIter!=""){
      maxIterValue=maxIter.toInt
    }

    //Sets the maximum length (in words) of each sentence in the input data. Any sentence longer than this threshold will be divided into chunks of up to maxSentenceLength size. Default: 1000
    var maxSentenceLengthValue:Int=1000
    if(maxSentenceLength!=""){
      maxSentenceLengthValue=maxSentenceLength.toInt
    }

    //The minimum number of times a token must appear to be included in the word2vec model's vocabulary. Default: 5
    var minCountValue:Int=1
    if(minCount!=""){
      minCountValue=minCount.toInt
    }

    var numPartitionsValue:Int=1
    if(numPartitions!=""){
      numPartitionsValue=numPartitions.toInt
    }

    //Param for Step size to be used for each iteration of optimization (> 0).
    var stepSizeValue:Int=5
    if(stepSize!=""){
      stepSizeValue=stepSize.toInt
    }

    //The dimension of the code that you want to transform from words. Default: 100
    var vectorSizeValue:Int=5
    if(vectorSize!=""){
      vectorSizeValue=vectorSize.toInt
    }

    //clustering with kmeans algorithm
    val word2vec=new Word2Vec()
        .setMaxIter(maxIterValue)
        .setMaxSentenceLength(maxSentenceLengthValue)
        .setMinCount(minCountValue)
        .setNumPartitions(numPartitionsValue)
        .setStepSize(stepSizeValue)
        .setVectorSize(vectorSizeValue)
        .setInputCol(colName+"_new")
        .setOutputCol(outputCol)
        .fit(dfNew)

    import spark.implicits._
    val dfOut=word2vec.transform(dfNew)
    dfOut.show()
    out.write(dfOut)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    maxIter=MapUtil.get(map,key="maxIter").asInstanceOf[String]
    vectorSize=MapUtil.get(map,key="vectorSize").toString
    maxSentenceLength=MapUtil.get(map,key="maxSentenceLength").toString
    minCount=MapUtil.get(map,key="minCount").toString
    numPartitions=MapUtil.get(map,key="numPartitions").toString
    stepSize=MapUtil.get(map,key="stepSize").toString
    colName=MapUtil.get(map,key="colName").asInstanceOf[String]
    outputCol=MapUtil.get(map,key="outputCol").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val vectorSize = new PropertyDescriptor().name("vectorSize").displayName("VECTOR_SIZE").description("The dimension of the code that you want to transform from words. Default: 100").defaultValue("").required(false)
    val maxSentenceLength = new PropertyDescriptor().name("maxSentenceLength").displayName("MAX_SENTENCE_LENGTH").description("Sets the maximum length (in words) of each sentence in the input data. Any sentence longer than this threshold will be divided into chunks of up to maxSentenceLength size. Default: 1000").defaultValue("").required(false)
    val maxIter=new PropertyDescriptor().name("maxIter").displayName("MAX_ITER").description("Param for maximum number of iterations (>= 0)").defaultValue("").required(false)
    val minCount=new PropertyDescriptor().name("minCount").displayName("MIN_COUNT").description("The minimum number of times a token must appear to be included in the word2vec model's vocabulary. Default: 5").defaultValue("").required(false)
    val stepSize=new PropertyDescriptor().name("stepSize").displayName("STEP_SIZE").defaultValue("").required(false)
    val numPartitions=new PropertyDescriptor().name("numPartitions").displayName("NUM_PARTITIONS").description("Param for Step size to be used for each iteration of optimization (> 0).").defaultValue("").required(false)
    val colName=new PropertyDescriptor().name("colName").displayName("INPUT_COL").description("").defaultValue("").required(true)
    val outputCol=new PropertyDescriptor().name("outputCol").displayName("OUTPUT_COL").description("").defaultValue("").required(true)
    descriptor = vectorSize :: descriptor
    descriptor = maxSentenceLength :: descriptor
    descriptor = maxIter :: descriptor
    descriptor = minCount :: descriptor
    descriptor = stepSize :: descriptor
    descriptor = numPartitions :: descriptor
    descriptor = colName :: descriptor
    descriptor = outputCol :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_feature/WordToVec.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }
}
