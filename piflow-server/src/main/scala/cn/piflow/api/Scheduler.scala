package cn.piflow.api

import akka.actor.{Actor, ActorSystem, Props}
import cn.piflow.api.HTTPService.config
import com.typesafe.akka.extension.quartz.QuartzSchedulerExtension

/**
  * Created by xjzhu@cnic.cn on 5/21/19
  */


object ScheduleType {
  val FLOW = "Flow"
  val GROUP = "Group"
}

class ExecutionActor(id: String, scheduleType: String) extends Actor {

  override def receive: Receive = {
    case json: String => {
      scheduleType match {
        case ScheduleType.FLOW => API.startFlow(json)
        case ScheduleType.GROUP => API.startGroup(json)
        //case ScheduleType.PROJECT => API.startProject(json)
      }
    }
    case _ => println("error type!")
  }
}

