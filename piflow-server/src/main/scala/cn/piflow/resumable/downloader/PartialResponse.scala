package cn.piflow.resumable.downloader

import akka.util.ByteString

case class PartialResponse(byteString: ByteString, actualSize: Int) {
  val bodyAsString: String = byteString.utf8String
  val body: Array[Byte] = byteString.toArray
  val size: Int = byteString.size
}
