package cn.piflow.conf.util

import java.io.File

import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import org.clapper.classutil.ClassFinder
import org.reflections.Reflections


object ClassUtil {

  val configurableStopClass:String = "cn.piflow.conf.ConfigurableStop"
  //val classpath:String = "/opt/project/piflow/classpath"

  /*def findAllConfigurableStop() : List[String] = {

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
      val plugin = Class.forName(it.next().getName).newInstance()
      val stop = plugin.asInstanceOf[ConfigurableStop]
      stopList = stop +: stopList
    }

    //find external stop
    stopList = stopList ::: findAllConfigurableStopInClasspath()
    stopList
  }


  private def findAllConfigurableStopInClasspath() : List[ConfigurableStop] = {

    val classpath = System.getProperty("user.dir")+ "/classpath/"
    var stopList:List[ConfigurableStop] = List()

    val classpathFile = new File(classpath)
    println("classpath is " + classpath)
    val finder = ClassFinder(getJarFile(classpathFile))
    val classes = finder.getClasses
    val classMap = ClassFinder.classInfoMap(classes)
    val plugins = ClassFinder.concreteSubclasses(configurableStopClass,classMap)
    plugins.foreach{
      pluginClassInfo =>
          val plugin = Class.forName(pluginClassInfo.name).newInstance()
          stopList = plugin.asInstanceOf[ConfigurableStop] +: stopList
    }
    stopList
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
    println("classpath is " + classpath)
    val finder = ClassFinder(getJarFile(classpathFile))
    val classes = finder.getClasses
    val classMap = ClassFinder.classInfoMap(classes)
    val plugins = ClassFinder.concreteSubclasses(configurableStopClass,classMap)
    plugins.foreach{
      pluginClassInfo =>
        if(pluginClassInfo.name.equals(bundle)){
          val plugin = Class.forName(pluginClassInfo.name).newInstance()
          stop = Some(plugin.asInstanceOf[ConfigurableStop])
          return stop
        }
    }
    stop
  }

  private def getJarFile(dir : File) : Seq[File] = {
    val files = dir.listFiles.filter(! _.isDirectory).filter( _.toString.endsWith(".jar")).filter(_.toString.contains("piflow"))
    files ++ dir.listFiles().filter(_.isDirectory).flatMap(getJarFile)
  }

  def findConfigurableStop(bundle : String) : ConfigurableStop = {
    try{
      val stop = Class.forName(bundle).newInstance()
      stop.asInstanceOf[ConfigurableStop]
    }catch{

      case classNotFoundException:ClassNotFoundException =>{
        val stop : Option[ConfigurableStop] = ClassUtil.findConfigurableStopInClasspath(bundle)
        stop match {
          case Some(s) => s.asInstanceOf[ConfigurableStop]
          case _ => throw new ClassNotFoundException(bundle + " is not found!!!")
        }
      }
      case ex : Exception => throw ex
    }
  }

  def findConfigurableStopPropertyDescriptor(bundle : String) : List[PropertyDescriptor] = {
    val stopPropertyDesc = ClassUtil.findConfigurableStop(bundle)
    stopPropertyDesc.getPropertyDescriptor()
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
    //println(findAllGroups());

    val stoplist = findAllGroups();
    println(stoplist)

  }

}
