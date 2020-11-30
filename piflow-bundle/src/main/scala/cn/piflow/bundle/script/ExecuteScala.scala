package cn.piflow.bundle.script


import java.net.{MalformedURLException, URL}

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil, PluginClassLoader}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

import scala.language.experimental.macros
import scala.reflect.runtime.{universe => ru}


class ExecuteScala extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Execute scala script"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var packageName : String = "cn.piflow.bundle.script"
  var script : String = _
  var plugin : String = _

  override def setProperties(map: Map[String, Any]): Unit = {

    script = MapUtil.get(map,"script").asInstanceOf[String]
    plugin = MapUtil.get(map,"plugin").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val pluginName = new PropertyDescriptor()
      .name("plugin")
      .displayName("Plugin")
      .description("The class name of scala code.")
      .defaultValue("")
      .required(true)
    descriptor = pluginName :: descriptor

    val script = new PropertyDescriptor()
      .name("script")
      .displayName("script")
      .description("The code of scala. \nUse in.read() to get dataframe from upstream component. \nUse out.write() to write datafram to downstream component.")
      .defaultValue("")
      .required(true)
      .example("val df = in.read() \nval df1 = df.select(\"author\").filter($\"author\".like(\"%xjzhu%\")) \ndf1.show() \ndf.createOrReplaceTempView(\"person\") \nval df2 = spark.sql(\"select * from person where author like '%xjzhu%'\") \ndf2.show() \nout.write(df2)")
      .language(Language.Scala)

    descriptor = script :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/script/scala.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ScriptGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {
    val flowName = ctx.getFlow().getFlowName()
  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val execMethod = "perform"
    val loader = new PluginClassLoader

    //when local run, use these codes
    //val scalaDir = PropertyUtil.getScalaPath()
    //val pluginurl = s"jar:file:$scalaDir/$plugin.jar!/"

    val userDir = System.getProperty("user.dir")
    //FileUtil.getJarFile(new File(userDir)).foreach(println(_))

    val pluginurl = s"jar:file:$userDir/$plugin.jar!/"
    println(s"Scala Plugin url : $pluginurl")
    var url : URL = null
    try
      url = new URL(pluginurl)
    catch {
      case e: MalformedURLException =>
        e.printStackTrace()
    }
    loader.addURLFile(url)

    val className = plugin.split("/").last.split(".jar")(0)
    val classMirror = ru.runtimeMirror(loader)
    println("staticModule: " + s"$packageName.$className")
    val classTest = classMirror.staticModule(s"$packageName.$className")
    val methods = classMirror.reflectModule(classTest)
    val objectMirror = classMirror.reflect(methods.instance)
    val method = methods.symbol.typeSignature.member(ru.TermName(s"$execMethod")).asMethod
    val result = objectMirror.reflectMethod(method)(in,out,pec)

  }

}
