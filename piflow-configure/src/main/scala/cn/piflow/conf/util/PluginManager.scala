package cn.piflow.conf.util

import java.io.File
import java.net.{MalformedURLException, URL}
import java.util
import java.net.URL

import cn.piflow.conf.ConfigurableStop
import org.clapper.classutil.ClassFinder

import scala.collection.mutable.{Map => MMap}

class PluginManager {

  private val pluginMap = MMap[String, PluginClassLoader]()

  def PlugInManager() = {}

  def getConfigurableStop(plugName: String, bundleName: String): ConfigurableStop = {
    try {
      val forName = Class.forName(bundleName, true, getLoader(plugName))
      val ins = forName.newInstance.asInstanceOf[ConfigurableStop]
      ins
    } catch {
      case e: IllegalAccessException =>
        e.printStackTrace()
      case e: InstantiationException =>
        e.printStackTrace()
      case e: ClassNotFoundException =>
        e.printStackTrace()
    }
    null
  }

  def getConfigurableStop(bundleName: String): ConfigurableStop = {
    val it = pluginMap.keys.iterator
    while (it.hasNext) {
      val pluginName = it.next
      try {
        val forName = Class.forName(bundleName, true, getLoader(pluginName))
        val ins = forName.newInstance.asInstanceOf[ConfigurableStop]
        System.out.println(bundleName + " is found in " + pluginName)
        return ins

      } catch {
        case e: IllegalAccessException =>
          e.printStackTrace()
        case e: InstantiationException =>
          e.printStackTrace()
        case e: ClassNotFoundException =>
          System.err.println(bundleName + " can not be found in " + pluginName)
        //e.printStackTrace();
      }
    }
    null
  }

  def getPluginConfigurableStops(): List[ConfigurableStop] = {

    var stopList = List[ConfigurableStop]()
    val pluginIterator = pluginMap.keys.iterator
    while (pluginIterator.hasNext) {
      val pluginName : String = pluginIterator.next
      val finder = ClassFinder(Seq(new File(pluginName)))
      val classes = finder.getClasses
      //val it = classes.iterator

      try{
        //while(it.hasNext){
        for( externalClass <- classes){

          try {
            if(externalClass.superClassName.equals(ClassUtil.configurableStopClass) &&
              !externalClass.name.equals(ClassUtil.configurableStreamingStop) &&
              !externalClass.name.equals(ClassUtil.configurableIncrementalStop)){
              val forName = Class.forName(externalClass.name, true, getLoader(pluginName))
              val ins = forName.newInstance.asInstanceOf[ConfigurableStop]
              System.out.println("Find ConfigurableStop: " + externalClass.name + " in " + pluginName)
              stopList = ins +: stopList
            }

          } catch {
            case e: IllegalAccessException =>
              e.printStackTrace()
            case e: InstantiationException =>
              System.err.println(externalClass.name + " can not be instantiation in " + pluginName)
            //e.printStackTrace()
            case e: ClassNotFoundException =>
              System.err.println(externalClass.name + " can not be found in " + pluginName)
          }
        }
      }catch {
        case e: UnsupportedOperationException => {
          System.err.println("external plugin throw UnsupportedOperationException.")
          //e.printStackTrace()
        }
      }
    }
    stopList
  }

  private def addLoader(pluginName: String, loader: PluginClassLoader): Unit = {
    this.pluginMap.put(pluginName, loader)
  }

  private def getLoader(pluginName: String) : PluginClassLoader = this.pluginMap(pluginName).asInstanceOf[PluginClassLoader]

  def loadPlugin(pluginName: String): Unit = {
    this.pluginMap.remove(pluginName)
    val loader = new PluginClassLoader
    //String pluginurl = "jar:file:/opt/project/piflow/classpath/" + pluginName + ".jar!/";
    val pluginurl = "jar:file:" + pluginName + "!/"
    var url : URL = null
    try
      url = new URL(pluginurl)
    catch {
      case e: MalformedURLException =>
        e.printStackTrace()
    }
    loader.addURLFile(url)
    addLoader(pluginName, loader)
    System.out.println("load " + pluginName + " success")
  }

  def unloadPlugin(pluginName: String): Unit = {
    if (this.pluginMap.contains(pluginName)) {
      this.pluginMap(pluginName).unloadJarFiles()
      this.pluginMap.remove(pluginName)
    }
  }
}

object PluginManager {
  private var instance : PluginManager = null
  def getInstance: PluginManager = {
    if (instance == null)
      instance = new PluginManager()
    instance
  }
}
