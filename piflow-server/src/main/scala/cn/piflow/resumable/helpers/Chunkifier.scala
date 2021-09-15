package cn.piflow.resumable.helpers

object Chunkifier {
  def chunkify(totalSize: Int, chunkSize: Int): List[(Int, Int)] = {
    if (totalSize > chunkSize) {
      val sizes = (Range.inclusive(0, totalSize, chunkSize).toList ++ List(totalSize)).toSet.toList
      sizes.zip(sizes.tail).map({case (a, b) => if (a != 0) (a + 1, b) else (a, b)})
    } else {
      List((0, totalSize))
    }
  }
}
