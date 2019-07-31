package cn.piflow.bundle.util.objects

class Result(val resultSeq : Seq[(Hierarchy, KeywordStatus, String)], val keywordName : String) extends Serializable {
  def print : Seq[(String,String,String, String, Int, Double, Double, Int, Int, Int)] = {
    resultSeq.map(f => {
      (f._1.ApplyID, f._1.FOS, f._3, keywordName, f._2.count, f._2.percentage, f._2.weight,f._2.titleTextFrequency, f._2.absTextFrequency, f._2.keywordFrequency)
    })
  }
}