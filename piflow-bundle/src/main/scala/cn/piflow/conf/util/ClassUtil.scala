package cn.piflow.conf.util

import java.io.File

import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import net.liftweb.json.compactRender
import org.clapper.classutil.ClassFinder
import org.reflections.Reflections
import net.liftweb.json.JsonDSL._
import sun.misc.BASE64Encoder
import util.control.Breaks._


object ClassUtil {

  val configurableStopClass:String = "cn.piflow.conf.ConfigurableStop"
  //val classpath:String = "/opt/project/piflow/classpath"

  /*def findAllConfigurableStopByClassFinder() : List[String] = {

    val classpath = System.getProperty("user.dir")
    var stopList : List[String] = List()

    val classpathFile = new File(classpath)
    val finder = ClassFinder(getJarFile(classpathFile))
    val classes = finder.getClasses
    val classMap = ClassFinder.classInfoMap(classes)
    val plugins = ClassFinder.concreteSubclasses(configurableStopClass,classMap)
    plugins.foreach{
      pluginClassInfo =>{
        val plugin = Class.forName(pluginClassInfo.name).newInstance()
        val stop = plugin.asInstanceOf[ConfigurableStop]
        val stopAndGroup = pluginClassInfo.name + ":" + stop.getGroup().toString
        stopList = stopAndGroup :: stopList
      }

    }
    stopList
  }*/

  def findAllConfigurableStop() : List[ConfigurableStop] = {
    var stopList:List[ConfigurableStop] = List()

    //find internal stop
    val reflections = new Reflections("")
    val allClasses = reflections.getSubTypesOf(classOf[ConfigurableStop])
    val it = allClasses.iterator();
    while(it.hasNext) {

      breakable{

        val stopName = it.next.getName
        if (stopName.equals("cn.piflow.conf.ConfigurableStreamingStop"))
          break
        else{
          //println(stopName + " in findAllConfigurableStop!!!!!")
          val stopClass = Class.forName(stopName)
          val plugin = stopClass.newInstance()
          val stop = plugin.asInstanceOf[ConfigurableStop]
          stopList = stop +: stopList
        }
      }
    }

    //find external stop
    //stopList = stopList ::: findAllConfigurableStopInClasspath()
    stopList
  }


  private def findAllConfigurableStopInClasspath() : List[ConfigurableStop] = {

    val classpath = System.getProperty("user.dir")+ "/classpath/"
    var stopList:List[ConfigurableStop] = List()

    val classpathFile = new File(classpath)
    //println("classpath is " + classpath)
    val jarFile = getJarFile(classpathFile)
    if(jarFile.size != 0){
      val finder = ClassFinder(jarFile)
      val classes = finder.getClasses
      val it = classes.iterator
      while(it.hasNext) {

        val externalClass = it.next()
        if(externalClass.superClassName.equals(configurableStopClass)){

          val stopIntance = Class.forName(externalClass.name).newInstance()
          stopList = stopIntance.asInstanceOf[ConfigurableStop] +: stopList
        }
      }
    }
    stopList

    /*val classMap = ClassFinder.classInfoMap(classes)
    val plugins = ClassFinder.concreteSubclasses(configurableStopClass,classMap)
    plugins.foreach{
      pluginClassInfo =>
          val plugin = Class.forName(pluginClassInfo.name).newInstance()
          stopList = plugin.asInstanceOf[ConfigurableStop] +: stopList
    }
    stopList*/
  }

  def findAllGroups() : List[String] = {

    val stoplist = findAllConfigurableStop();
    val groupList = stoplist.flatMap(_.getGroup()).distinct
    groupList
  }

  private def findConfigurableStopInClasspath(bundle : String) : Option[ConfigurableStop] = {

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
          val stopIntance = Class.forName(externalClass.name).newInstance()
          stop = Some(stopIntance.asInstanceOf[ConfigurableStop])
          return stop
        }
      }
    }
    /*val classMap = ClassFinder.classInfoMap(classes)
    val plugins = ClassFinder.concreteSubclasses(configurableStopClass,classMap)
    plugins.foreach{
      pluginClassInfo =>
        if(pluginClassInfo.name.equals(bundle)){
          val plugin = Class.forName(pluginClassInfo.name).newInstance()
          stop = Some(plugin.asInstanceOf[ConfigurableStop])
          return stop
        }
    }*/
    stop
  }

  private def getJarFile(dir : File) : Seq[File] = {
    val files = dir.listFiles.filter(! _.isDirectory).filter( _.toString.endsWith(".jar")).filter(_.toString.contains("piflow"))
    files ++ dir.listFiles().filter(_.isDirectory).flatMap(getJarFile)
  }

  def findConfigurableStop(bundle : String) : ConfigurableStop = {
    try{
      println("find ConfigurableStop by Class.forName: " + bundle)
      val stop = Class.forName(bundle).newInstance()
      stop.asInstanceOf[ConfigurableStop]
    }catch{

      case classNotFoundException:ClassNotFoundException =>{
        println("find ConfigurableStop in Classpath: " + bundle)
        val stop : Option[ConfigurableStop] = ClassUtil.findConfigurableStopInClasspath(bundle)
        stop match {
          case Some(s) => s.asInstanceOf[ConfigurableStop]
          case _ => throw new ClassNotFoundException(bundle + " is not found!!!")
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

  def findConfigurableStopInfo(bundle : String) : String = {
    val stop = ClassUtil.findConfigurableStop(bundle)
    val propertyDescriptorList:List[PropertyDescriptor] = stop.getPropertyDescriptor()
    propertyDescriptorList.foreach(p=> if (p.allowableValues == null || p.allowableValues == None) p.allowableValues = List(""))
    val stopName = bundle.split("\\.").last
    val base64Encoder = new BASE64Encoder()
    val json =
      ("StopInfo" ->
        ("name" -> stopName)~
        ("bundle" -> bundle) ~
        ("owner" -> stop.authorEmail) ~
          ("inports" -> stop.inportList.mkString(",")) ~
          ("outports" -> stop.outportList.mkString(",")) ~
          ("groups" -> stop.getGroup().mkString(",")) ~
          ("description" -> stop.description) ~
          ("icon" -> base64Encoder.encode(stop.getIcon())) ~
          ("properties" ->
            propertyDescriptorList.map { property =>(
              ("name" -> property.name) ~
                ("displayName" -> property.displayName) ~
                ("description" -> property.description) ~
                ("defaultValue" -> property.defaultValue) ~
                ("allowableValues" -> property.allowableValues) ~
                ("required" -> property.required.toString) ~
                ("sensitive" -> property.sensitive.toString)) }) )
    val jsonString = compactRender(json)
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

    val stop = findAllConfigurableStop()
    stop.foreach(s => println(s.getClass.getName))
    val temp = 1


    //val stop = findConfigurableStop("cn.piflow.bundle.http.PostUrl")
    //println(stop.getClass.getName)


  }

}
