package cn.piflow.resumable.downloader

import java.net.{HttpURLConnection, URL}

import akka.stream.IOResult
import akka.stream.scaladsl.Source
import akka.stream.scaladsl.StreamConverters._
import cn.piflow.resumable.helpers.Chunkifier
import cn.piflow.resumable.net.HttpRangeConnection

import scala.concurrent.Future
import scala.util.Try

case class RemoteResource(url: String, downloadedOffset: Long = 0) {
  var cachedSize: Int = -1

  def size(): Int = {
    if (cachedSize == -1) {
      val connection = new URL(url).openConnection().asInstanceOf[HttpURLConnection]
      connection.setRequestMethod("HEAD")

      cachedSize = Try(connection.getInputStream)
        .map(_ => connection.getContentLength)
        .getOrElse(0)

      connection.disconnect()
    }
    cachedSize
  }

  def asStream(): Option[Source[PartialResponse, Future[IOResult]]] = {
    asStream(HttpRangeConnection(url, downloadedOffset))
  }

  def asParallelStream(streamSize: Int = 5000000): List[Source[PartialResponse, Future[IOResult]]] = {
    Chunkifier.chunkify(size(), streamSize)
      .map({ case (start, end) => HttpRangeConnection(url, start, end) })
      .map(asStream)
      .filter(_.isDefined)
      .map(_.get)
  }

  private def asStream(connection: HttpRangeConnection): Option[Source[PartialResponse, Future[IOResult]]] = {
    Try(connection.getInputStream)
      .map(stream => fromInputStream(() => stream)
        .map(PartialResponse(_, connection.getContentLength)))
      .toOption
  }
}
