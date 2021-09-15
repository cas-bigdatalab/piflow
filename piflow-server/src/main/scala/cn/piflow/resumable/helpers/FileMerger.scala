package cn.piflow.resumable.helpers

import java.io.{File, FileInputStream, SequenceInputStream}
import java.nio.file.{Files, Paths}
import java.util.Collections

import scala.collection.JavaConverters._

case class FileMerger(prefix: String, fileName: String) {
  def merge(): Unit = {
    val files = filesByNamePrefix(prefix).sorted
    val streams = files.map(f => new FileInputStream(f)).asJavaCollection
    val in = new SequenceInputStream(Collections.enumeration[FileInputStream](streams))

    Files.copy(in, Paths.get(fileName))

    in.close()

    //TODO:need to check
    //streams.forEach(f => f.close())
    files.foreach(f => f.delete())
  }

  private def filesByNamePrefix(partFileNamePrefix: String) = {
    new File(".")
      .listFiles()
      .toList
      .filter(f => f.getName.startsWith(partFileNamePrefix))
  }
}

