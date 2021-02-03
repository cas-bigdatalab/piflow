package cn.piflow.conf.util

import java.io.File
import java.net.URLClassLoader

import cn.piflow.VisualizationStop
import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import javassist.Modifier
import net.liftweb.json.{JValue, compactRender}
import org.clapper.classutil.ClassFinder
import org.reflections.Reflections
import net.liftweb.json.JsonDSL._
import sun.misc.BASE64Encoder

import util.control.Breaks._


object ClassUtil {


  val configurableStopClass:String = "cn.piflow.conf.ConfigurableStop"
  val configurableStreamingStop:String = "cn.piflow.conf.ConfigurableStreamingStop"
  val configurableIncrementalStop:String = "cn.piflow.conf.ConfigurableIncrementalStop"

  def findAllConfigurableStop() : List[ConfigurableStop] = {

    var stopList:List[ConfigurableStop] = List()

    //find internal stop
    val reflections = new Reflections("")
    val allClasses = reflections.getSubTypesOf(classOf[ConfigurableStop])
    val it = allClasses.iterator();
    var count = 0
    while(it.hasNext) {


      breakable{

        val stop = it.next
        val stopName = stop.getName
        val stopClass = Class.forName(stopName)

        if(Modifier.isAbstract(stopClass.getModifiers())) {
          println("Stop " + stop.getName + " is interface!")
          /*if (stopName.equals("cn.piflow.conf.ConfigurableStreamingStop")
            || stopName.equals("cn.piflow.conf.ConfigurableIncrementalStop")
            || stopName.equals("cn.piflow.conf.ConfigurableVisualizationStop"))*/
          break
        }
        else{


          val plugin = stopClass.newInstance()
          val stop = plugin.asInstanceOf[ConfigurableStop]
          println("Find ConfigurableStop: " + stopName)
          stopList = stop +: stopList
        }
      }
    }

    //find external stop
    val pluginManager = PluginManager.getInstance
    val externalStopList = findAllConfigurableStopInClasspath().toList

    stopList:::externalStopList
  }


  def findAllConfigurableStopInClasspath() : List[ConfigurableStop] = {

      val pluginManager = PluginManager.getInstance
      val stopList= pluginManager.getPluginConfigurableStops()
      stopList

    /*val pluginManager = PluginManager.getInstance()
    var stopList:List[ConfigurableStop] = List()
    val classpath = System.getProperty("user.dir")+ "/classpath/"
    val classpathFile = new File(classpath)
    val jarFile = getJarFile(classpathFile)
    if(jarFile.size != 0){
      val finder = ClassFinder(jarFile)
      val classes = finder.getClasses

      val it = classes.iterator

      try{
        while(it.hasNext) {

          val externalClass = it.next()

          if(externalClass.superClassName.equals(configurableStopClass) &&
            !externalClass.name.equals(configurableStreamingStop) &&
            !externalClass.name.equals(configurableIncrementalStop)){

            //var classLoader = new URLClassLoader(Array(new File(classpath).toURI.toURL),this.getClass.getClassLoader )
            //val stopInstance = classLoader.loadClass(externalClass.name).newInstance()

            val stopInstance = pluginManager.getConfigurableStop(externalClass.name)
            println("Find Stop: " + externalClass.name)
            stopList = stopInstance.asInstanceOf[ConfigurableStop] +: stopList

          }
        }
      }catch {
        case e: UnsupportedOperationException => println("error")
      }

    }
    stopList*/
  }

  def findAllGroups() : List[String] = {

    val stoplist = findAllConfigurableStop();

    val groupList = stoplist.flatMap(stop =>{
      //stop.getGroup()
      var group = List("")
      try{
        group = stop.getGroup()

      }catch {
        //case ex : Exception => println(ex)
        case ex : scala.NotImplementedError => println(stop.getClass.getName + " -> " + ex)
      }

      group

    }).distinct.filter(_ != "")
    groupList
  }

  private def findConfigurableStopInClasspath(bundle : String) : Option[ConfigurableStop] = {

    val pluginManager = PluginManager.getInstance
    val stopInstance = pluginManager.getConfigurableStop(bundle)
    val stop = Some(stopInstance.asInstanceOf[ConfigurableStop])
    stop

    /*val pluginManager = PluginManager.getInstance
    val classpath = System.getProperty("user.dir")+ "/classpath/"
    var stop:Option[ConfigurableStop] = None

    val classpathFile = new File(classpath)
    //println("classpath is " + classpath)
    val finder = ClassFinder(getJarFile(classpathFile))
    val classes = finder.getClasses
    val it = classes.iterator

    while(it.hasNext) {
      val externalClass = it.next()
      if(externalClass.superClassName.equals(configurableStopClass)){
        if (externalClass.name.equals(bundle)){
          //val stopIntance = Class.forName(externalClass.name).newInstance()
          val stopInstance = pluginManager.getConfigurableStop(externalClass.name)
          stop = Some(stopInstance.asInstanceOf[ConfigurableStop])
          return stop
        }
      }
    }

    stop*/
  }


  def findConfigurableStop(bundle : String) : ConfigurableStop = {
    try{
      println("find ConfigurableStop by Class.forName: " + bundle)
      val stop = Class.forName(bundle).newInstance()
      stop.asInstanceOf[ConfigurableStop]
    }catch{

      case classNotFoundException:ClassNotFoundException =>{
        val pluginManager = PluginManager.getInstance
        if(pluginManager != null){
          println("find ConfigurableStop in Classpath: " + bundle)
          val stop : Option[ConfigurableStop] = ClassUtil.findConfigurableStopInClasspath(bundle)
          stop match {
            case Some(s) => return s.asInstanceOf[ConfigurableStop]
            case _ => throw new ClassNotFoundException(bundle + " is not found!!!")
          }
        }else{
          println("Can not find Configurable: " + bundle)
          throw classNotFoundException
        }

      }
      case ex : Exception => {
        println("Can not find Configurable: " + bundle)
        throw ex
      }
    }
  }

  def findConfigurableStopPropertyDescriptor(bundle : String) : List[PropertyDescriptor] = {
    val stopPropertyDesc = ClassUtil.findConfigurableStop(bundle)
    stopPropertyDesc.getPropertyDescriptor()
  }

  def constructStopInfoJValue(bundle: String, stop:ConfigurableStop) : JValue ={
    val stopName = bundle.split("\\.").last
    val propertyDescriptorList:List[PropertyDescriptor] = stop.getPropertyDescriptor()
    propertyDescriptorList.foreach(p=> if (p.allowableValues == null || p.allowableValues == None) p.allowableValues = List(""))
    val base64Encoder = new BASE64Encoder()
    var iconArrayByte : Array[Byte]= Array[Byte]()
    try{
      iconArrayByte = stop.getIcon()
    }catch {
      case ex: ClassNotFoundException => println(ex)
      case ex: NoSuchMethodError => println(ex)
    }

    //TODO: add properties for visualization stop
    var visualizationType = ""
    if (stop.isInstanceOf[VisualizationStop]){
      visualizationType = stop.asInstanceOf[VisualizationStop].visualizationType.toString()
    }
    val jsonValue =
      ("StopInfo" ->
        ("name" -> stopName)~
          ("bundle" -> bundle) ~
          ("owner" -> stop.authorEmail) ~
          ("inports" -> stop.inportList.mkString(",")) ~
          ("outports" -> stop.outportList.mkString(",")) ~
          ("groups" -> stop.getGroup().mkString(",")) ~
          ("isCustomized" -> stop.getCustomized().toString) ~
          /*("customizedAllowKey" -> "") ~
          ("customizedAllowValue" -> "")*/
          ("visualizationType" -> visualizationType) ~
          ("description" -> stop.description) ~
          ("icon" -> base64Encoder.encode(iconArrayByte)) ~
          ("properties" ->
            propertyDescriptorList.map { property =>(
              ("name" -> property.name) ~
                ("displayName" -> property.displayName) ~
                ("description" -> property.description) ~
                ("defaultValue" -> property.defaultValue) ~
                ("allowableValues" -> property.allowableValues) ~
                ("required" -> property.required.toString) ~
                ("sensitive" -> property.sensitive.toString) ~
                ("example" -> property.example) ~
                ("language" -> property.language)) }) )
    jsonValue
  }

  def findConfigurableStopInfo(bundle : String) : String = {
    val stop = ClassUtil.findConfigurableStop(bundle)
    val jvalue = constructStopInfoJValue(bundle,stop)
    val jsonString = compactRender(jvalue)
    jsonString
  }

  def findConfigurableStopListInfo(bundleList : List[String]) : String = {

    var stopInfoJValueList = List[JValue]()
    bundleList.foreach(bundle =>{
      val stop = ClassUtil.findConfigurableStop(bundle)
      val stopJValue = constructStopInfoJValue(bundle,stop)
      stopInfoJValueList = stopJValue +: stopInfoJValueList
    })
    val stopInfoJValue = (stopInfoJValueList)
    val jsonString = compactRender(stopInfoJValue)
    jsonString
  }

  def main(args: Array[String]): Unit = {
    //val stop = findConfigurableStop("cn.piflow.bundle.Class1")
    //val allConfigurableStopList = findAllConfigurableStop()
    /*val propertyDescriptorList = findConfigurableStopPropertyDescriptor("cn.piflow.bundle.Xjzhu")
    var propertyJsonList = List[String]()
    propertyDescriptorList.foreach( p => propertyJsonList = p.toJson() +: propertyJsonList  )
    val start ="""{"properties":["""
    val end = """]}"""
    val str = propertyJsonList.mkString(start, ",", end)
    println(str)*/

    //val stop = findAllConfigurableStop()
    //stop.foreach(s => println(s.getClass.getName))
    //findAllGroups().foreach(print(_))
    //val t = findConfigurableStopInClasspath("cn.nsfc.personDistinct.PersonDistinct")

    //val pluginManager = PluginManager.getInstance
    //pluginManager.loadPlugin("piflowexternal.jar")
    //val stop = findConfigurableStopInClasspath("cn.piflow.bundle.external.ShowData")
    //val stopListInClassPath = findAllConfigurableStopInClasspath()
    //val temp = 1


    //val stop = findConfigurableStop("cn.piflow.bundle.http.PostUrl")
    //println(stop.getClass.getName)


  }

}
