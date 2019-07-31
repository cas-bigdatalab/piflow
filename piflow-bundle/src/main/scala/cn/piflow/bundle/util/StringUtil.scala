package cn.piflow.bundle.util

object StringUtil {
  /**
    * 100000次运行时间1秒内（i5）
    * @param A 母字符串
    * @param B 子字符串
    * @return B在A中出现的次数
    */
  def countString (A : String, B : String) : Int = {
    if (A == null) return 0
    if (B == null) return 0
    val lenA = A.length
    val lenB = B.length
    var count = 0
    if (lenA < lenB || lenB == 0) return count
    var flagB = 0
    var flagA = 0
    while (flagA < lenA && ((lenA - flagA) >= (lenB - flagB))) {
      if (A.charAt(flagA) == B.charAt(flagB)) {
        flagA += 1
        flagB += 1
      } else {
        flagA += 1
        flagB = 0
      }
      if (flagB == lenB) {
        flagB = 0
        count += 1
      }
    }
    count
  }
  def totalSplit(A : String) : Array[String] = {
    Array(A).flatMap(str => {
      if (str.contains("；")) str.split("；")
      else Array(str)
    }).flatMap(str => {
      if (str.contains(";")) str.split(";")
      else Array(str)
    }).flatMap(str => {
      if (str.contains(",")) str.split(",")
      else Array(str)
    }).flatMap(str => {
      if (str.contains("，")) str.split("，")
      else Array(str)
    })
  }
  def main(args: Array[String]): Unit = {
    val count1 = System.currentTimeMillis()
    for (i <- 0 to 100000) {
      countString(testString, "算法")
    }
    println(System.currentTimeMillis() - count1)

  }

  val testString = "\n2019-5-6 完成算法基础梳理 \n\n算法：\n    定义 ： 新词 为下一年该学部所填写的关键词\n    新词的推荐是根据该关键词所出现的频次的加权\n    定义 ： 频次 的加权为 ： 关键词（1.0），摘要（0.2）， 标题（0,4）\n\n每个关键词有三个可能性    \n    （1）研究方向下，出现两次以上，加权2.0以上，研究方向为总数的0.7，则补充新词\n    （2）填写过，但未采纳的次，在研究方向上频率为15以上55以下，加权6.0以上，同时方向内占总数的5.0，则补充新词\n    （3）以上都不能补充，则尝试往更高层去补充，若在高层中为0.5以上，则补充到高层\n\n基础数据与数据结构\n\ny\n\n\n输出表格式\n\n\n\n\n需要沟通实现思路\n已邮件沟通姚老师\n\n\n\n老师您好，我在看算法说明的时候有两个问题\n1、\n假如候选关键词在分布最多的研究方向下不满足上述两个要求，那么计算它在申请代码下的分布（按申请代码累加），如果在最主要的代码下的加权频次比例大于0.5，就把它补充到代码下。即是补充到更高层的结果。\n如果在最主要的代码下的加权频次比例不大于0.5，会跳到更高层的代码下吗？\n例：B010101未满足要求，跳到B0101依然不足0.5，最后跳到B01后满足条件，则补充到B01\n或是 ： B010101下的方向未满足0.5，跳到B010101仍未满足0.5，则抛弃该关键字\n（只推一级，推到末级代码）\n2、\n演示的时候有一个少、适中、多的度量，但在文档中讲到参数（关键词权重=1.0，摘要权重=0.2，标题权重=0.4）时没有提到这个三个不同的设置，请问这部分该怎么设计呢\n\n3、\n数据来源\n\n问题讨论：\n少适中 多 修改为 比例，新出现关键词比例 <- 按照学部希望更新的关键词的数量/比例\n去年已推荐词的标识（前端/后端），添加一个连续几年推荐并未采用的字段？ 拟\n学科代码变换以新的为准（需要考虑历史数据）\n先出到EXCEL，到大数据平台取数据（各个学科）/ 直接发送到___处 导出到一级学科的01/02的EXCEL\n\nORACLE：两个数据来源表需要采集\n\n\n2019-5-16 已从基金委处获取申请书数据（2017-2019）\n数据格式为mdb形式\n还需要获取学科关键词数据\n\n在基金委服务器131上安装mysql进行mdb数据导入\n\n\t* \n在 MySQL 8.0 版本中正确授权语句。\n\n\nmysql> CREATE USER 'mike'@'%' IDENTIFIED BY '000000';\nmysql> GRANT ALL ON *.* TO 'mike'@'%' WITH GRANT OPTION;\n\nCREATE USER 'root'@'%' IDENTIFIED BY 'Bigdata,1234';\nGRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;\n\nCREATE USER 'mysql.infoschema'@'%' IDENTIFIED BY 'Bigdata,1234';\nGRANT ALL ON *.* TO 'mysql.infoschema'@'%' WITH GRANT OPTION;\n\n导入时需要安装access x64的plugin\n问题1、如何实现mdb数据的导入？如何体现在流水线内\n\n\n姚老师需要 ： 项目类似是否只提供了三类 : 面上、青年、地区？\n了解一下数据的数量和结构\n\n\n"

}
