package cn.piflow.bundle.util
import java.util

import org.apache.spark.sql.{Dataset, Row}
import redis.clients.jedis.JedisCluster
object RedisUtil extends Serializable {
  def manipulateRow(row:Row,column_name:String,jedisClusterImplSer: JedisClusterImplSer):Unit={
    var hm:util.HashMap[String,String]=new util.HashMap()
    val key=row.getAs(column_name).asInstanceOf[String]
    //row.schema.fields.foreach(f=>(if(!f.name.equals(column_name)&&row.getAs(f.name)!=null)hm.put(f.name,row.getAs(f.name).asInstanceOf[String])))
    row.schema.fields.foreach(f=>{
      if(!f.name.equals(column_name)){
        if(row.getAs(f.name)==null)hm.put(f.name,"None")
        else{
          hm.put(f.name,row.getAs(f.name).asInstanceOf[String])
        }
      }
    })
    jedisClusterImplSer.getJedisCluster.hmset(key,hm)

  }
  /**
    *
    * @param row 存入redis的行
    * @param map 字段名称与位置索引
    * @param build 字段名 <- 用以去重的字段
    * @param valueIndex PSNCODE的位置
    * @param jedisCluster
    */
  def putRedis(row: Row, map: Map[String, Int], build :String, valueIndex:Int, jedisCluster: JedisCluster): Unit = {
    var hasNull = false
    var value = row.getString(valueIndex) //get the primary key
    build.split(",").foreach(idKey => { //name&tel,name&email
      var field = idKey
      var key = ""
      if (idKey.contains("&")) { //name&tel
        val sl = idKey.split("&")
        sl.foreach(s_ => {
          if (!row.isNullAt(map(s_))) {
            key += row.getString(map(s_))
          } else {hasNull = true}
        })
      }
      else {
        if (!row.isNullAt(map(idKey))) {
          key += row.getString(map(idKey))
        } else {hasNull = true}
      }
      if (!hasNull) {
        jedisCluster.hset(key,field,value) // combined keys - fields - psn_code
        //        println(key + ":" + field + ":" + value)   test pass
      }
    })
  }
}
