package cn.piflow.conf.util

import java.io.File

import cn.piflow.conf.ConfigurableStop
import org.clapper.classutil.ClassFinder


object ClassUtil {

  def findConfigurableStop(bundle : String) : Option[ConfigurableStop] = {

    //val file = new File(".")
    val classpath = List(".").map(new File(_))
    val finder = ClassFinder(classpath)
    val classes = finder.getClasses
    val classMap = ClassFinder.classInfoMap(classes)
    val plugins = ClassFinder.concreteSubclasses("cn.cnic.bigdata.bundle.ConfigurableStop",classMap)
    plugins.foreach{
      pluginString =>
        if(pluginString.name.equals(bundle)){
          val plugin = Class.forName(pluginString.name).newInstance()
          plugin.asInstanceOf[ConfigurableStop]
        }
    }
    None
  }

  def main(args: Array[String]): Unit = {
    val stop = findConfigurableStop("cn.cnic.bigdata.bundle.hive.SelectHiveQL")
  }

}
