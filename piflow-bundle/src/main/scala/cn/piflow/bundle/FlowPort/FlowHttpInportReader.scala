package cn.piflow.bundle.FlowPort

import java.io.InputStream
import java.util.zip.{ZipEntry, ZipInputStream}

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.util.{AESUtil, PropertyUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataOutputStream, FileSystem, Path}
import org.apache.hadoop.io.IOUtils
import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils
import org.apache.spark.sql.SparkSession



class FlowHttpInportReader extends ConfigurableStop {
  override val authorEmail: String = "llei@cnic.cn"
  override val description: String = "inport for flow through http request."
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)


  var hdfsDir: String = _
  var urlAddress: String = _



  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsDir = MapUtil.get(map,key="hdfsDir").asInstanceOf[String]
    urlAddress = MapUtil.get(map,key="urlAddress").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = { List()}

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/GetHdfs.png")
  }

  override def getGroup(): List[String] = {
    List()
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val sc= spark.sparkContext



    //AES key
    val key :String = System.currentTimeMillis().toString
    val aesKey = AESUtil.wrap(key)

    //url
    val httpUrl = "http://"+urlAddress+"/hdfs/data?key="+aesKey

    val timeout = 1800
    val requestConfig = RequestConfig.custom()
      .setConnectTimeout(timeout*1000)
      .setConnectionRequestTimeout(timeout*1000)
      .setSocketTimeout(timeout*1000).build()

    //return is inputStream
    val client = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).build()

    val post:HttpPost = new HttpPost(httpUrl)
    post.addHeader("Content-Type", "application/json")
    post.setEntity(new StringEntity(hdfsDir))

    val response: CloseableHttpResponse = client.execute(post)

    var outputStream: FSDataOutputStream = null
    var fs:FileSystem = null
    var zipInputStream:ZipInputStream = null
    var myHdfsAddress:String = null
    try {
      if(response.getStatusLine.getStatusCode == 200){
        val inputStream: InputStream = response.getEntity.getContent
        //dec return stream
        val cipherInputStream = AESUtil.decryptInputStream(inputStream,key)
        zipInputStream = new ZipInputStream(cipherInputStream)
        var zipEntry:ZipEntry = null
        var flag = true
        //myself hdfsAddress
        myHdfsAddress = PropertyUtil.getPropertyValue("fs.defaultFS")

        val conf = new Configuration()
        conf.set("fs.defaultFS", myHdfsAddress)
        fs = FileSystem.get(conf)

        while (flag){
          zipEntry = zipInputStream.getNextEntry
          var savePath =hdfsDir+"/temp/"
          if (zipEntry !=null){
            //          println("zipEntryName:"+zipEntry.getName)
            savePath += zipEntry.getName
            val path = new Path(savePath)
            //file is exist
            if (fs.exists(path)){
              outputStream = fs.append(path)
              val haveWriteLength = outputStream.getPos
              zipInputStream.skip(haveWriteLength)
              IOUtils.copyBytes(zipInputStream,outputStream,1024*1024*50,false)
              outputStream.close()
            }else{
              outputStream = fs.create(path,true)
              IOUtils.copyBytes(zipInputStream,outputStream,1024*1024*50,false)
//              throw new Exception("use test !! after delete")
              outputStream.close()
            }
          }else{
            flag = false
          }
        }
      }else{
        throw new Exception("HttpRequest error,the error code"+EntityUtils.toString(response.getEntity,"UTF-8"))
      }
    }catch {
      case ex => throw new Exception(ex.getMessage)
    }finally {
      if (outputStream !=null){
        outputStream.close()
      }
      if (zipInputStream !=null){
        zipInputStream.close()
      }
      if (fs !=null){
        fs.close()
      }
    }
    //read hdfs data
    val sparkReadAddress = myHdfsAddress+hdfsDir+"/temp"
    val df = spark.read.json(sparkReadAddress)
    out.write(df)
  }
}
