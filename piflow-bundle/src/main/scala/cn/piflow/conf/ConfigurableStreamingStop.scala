package cn.piflow.conf

import cn.piflow.StreamingStop
import cn.piflow.conf.bean.PropertyDescriptor

abstract class ConfigurableStreamingStop extends ConfigurableStop with  StreamingStop {

  val timing : Integer

}
