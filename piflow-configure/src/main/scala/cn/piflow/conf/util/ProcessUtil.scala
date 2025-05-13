package cn.piflow.conf.util

import java.io.{ByteArrayOutputStream, PrintStream}
object ProcessUtil {

  /**
   * 执行外部命令并返回标准输出和标准错误输出
   *
   * @param command 要执行的命令及其参数
   * @return 一个包含标准输出和标准错误输出的元组
   */
  def executeCommand(command: Seq[String]): (String, String) = {
    val processBuilder = new ProcessBuilder(command: _*)
    val outBuffer = new ByteArrayOutputStream()
    val errBuffer = new ByteArrayOutputStream()
    val outStream = new PrintStream(outBuffer)
    val errStream = new PrintStream(errBuffer)

    val process = processBuilder.start()
    val threadOut = new Thread(() => scala.io.Source.fromInputStream(process.getInputStream()).getLines().foreach(outStream.println))
    val threadErr = new Thread(() => scala.io.Source.fromInputStream(process.getErrorStream()).getLines().foreach(errStream.println))

    threadOut.start()
    threadErr.start()

    // 等待进程结束
    process.waitFor()
    threadOut.join()
    threadErr.join()

    // 关闭流
    outStream.close()
    errStream.close()

    // 获取输出和错误字符串
    val output = outBuffer.toString("UTF-8")
    val error = errBuffer.toString("UTF-8")

    // 返回输出和错误
    (output, error)
  }
}
