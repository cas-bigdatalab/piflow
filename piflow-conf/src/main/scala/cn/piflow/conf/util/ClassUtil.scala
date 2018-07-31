package cn.piflow.conf.util

import java.io.File

import cn.piflow.conf.ConfigurableStop
import org.clapper.classutil.ClassFinder


object ClassUtil {

  val configurableStopClass:String = "cn.piflow.conf.ConfigurableStop"
  val classpath:String = "/opt/project/piflow"

  def findAllConfigurableStop() : List[String] = {

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
  }

  def findConfigurableStop(bundle : String) : Option[ConfigurableStop] = {

    var stop:Option[ConfigurableStop] = None

    val classpathFile = new File(classpath)
    val finder = ClassFinder(getJarFile(classpathFile))
    val classes = finder.getClasses
    val classMap = ClassFinder.classInfoMap(classes)
    val plugins = ClassFinder.concreteSubclasses(configurableStopClass,classMap)
    plugins.foreach{
      pluginClassInfo =>
        //println(pluginString.name)
        if(pluginClassInfo.name.equals(bundle)){
          val plugin = Class.forName(pluginClassInfo.name).newInstance()
          stop = Some(plugin.asInstanceOf[ConfigurableStop])
          return stop
        }
    }
    stop
  }

  def getJarFile(dir : File) : Seq[File] = {
    val files = dir.listFiles.filter(! _.isDirectory).filter( _.toString.endsWith(".jar"))
    files ++ dir.listFiles().filter(_.isDirectory).flatMap(getJarFile)
  }

  /*def main(args: Array[String]): Unit = {
    //val stop = findConfigurableStop("cn.piflow.bundle.Class1")
    val allConfigurableStopList = findAllConfigurableStop()
    println("\n\n\n" + allConfigurableStopList)
  }*/

}
