//package cn.piflow.bundle.util
//
//import org.apache.commons.net.ftp.FTPClient
//
//object FTPUtil {
//  var ftp : FTPClient = null
//  def initClient(addr : String, user : String, passwd : String, port : Int) : Unit = {
//    if (ftp == null) {
//      ftp = new FTPClient
//      ftp.connect(addr, port)
//      ftp.login(user, passwd)
//    }
//    if (!ftp.isConnected) {
//      ftp = new FTPClient
//      ftp.connect(addr, port)
//      ftp.login(user, passwd)
//    }
//  }
//
//  def listFile (filePath : String) : List[(String, String)] = {
//    if (ftp == null || !ftp.isConnected) throw new Exception
//    var ls = ftp.listFiles(filePath)
//    var ret = List[(String,String)]()
//    for (f <- ls) {
//      if (f.isDirectory) {
//        if (f.getName != "." || f.getName != "..")
//          ret ++= listFile(filePath +"/"+ f.getName)
//      } else {
//        ret :+= (f.getName, filePath +"/"+ f.getName )
//      }
//    }
//    ret
//  }
//
//  def main(args: Array[String]): Unit = {
//    this.initClient("192.168.3.125", "ftp", "", 21)
//    var i = 0
//    println(1)
//    for ( s  <- this.listFile("/springer")
//      .filter(s => {
//        s._1.endsWith(".pdf")
//      })  ) {
//      i += 1
//      println(s)
//    }
//
//    println(i)
//  }
//}
