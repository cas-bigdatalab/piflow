/**
  * Created by bluejoe on 2018/5/6.
  */

import java.io.File

import cn.piflow._
import org.apache.commons.io.FileUtils
import org.junit.Test

class SparkETLTest {
  @Test
  def test1(): Unit = {
    val fg = new SparkETLProcess();
    val s1 = fg.loadStream(TextFile("./out/honglou.txt", "text"));
    val s2 = fg.transform(s1, DoMap(
      """
      function(s){
        return s.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", "");
      }""", classOf[String]));

    val s3 = fg.transform(s2, DoFlatMap(
      """
	function (s) {
		var arr = Array();
		var len = s.length;
		for (var i = 0; i < s.length - 1; i++) {
			arr.push(s.substring(i, i + 2));
		}

		return arr;
	}
      """, classOf[String]));

    fg.writeStream(s3, TextFile("./out/wordcount", "json"));

    FileUtils.deleteDirectory(new File("./out/wordcount"));
    fg.run(new SparkProcessContext());
  }
}
