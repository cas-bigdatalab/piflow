package cn.piflow.bundle.util
import java.util

import org.apache.spark.sql.{Dataset, Row}
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

}
