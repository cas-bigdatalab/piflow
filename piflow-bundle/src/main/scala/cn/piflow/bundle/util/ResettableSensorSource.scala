/*
 * Copyright 2015 Fabian Hueske / Vasia Kalavri
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package cn.piflow.bundle.util

import java.util.Calendar

import org.apache.flink.api.common.state.{ListState, ListStateDescriptor}
import org.apache.flink.runtime.state.{FunctionInitializationContext, FunctionSnapshotContext}
import org.apache.flink.streaming.api.checkpoint.CheckpointedFunction
import org.apache.flink.streaming.api.functions.source.RichParallelSourceFunction
import org.apache.flink.streaming.api.functions.source.SourceFunction.SourceContext

import scala.collection.JavaConverters._
import scala.util.Random

/**
  * A resettable Flink SourceFunction to generate SensorReadings with random temperature values.
  *
  * Each parallel instance of the source simulates 10 sensors which emit one sensor
  * reading every 100 ms.
  *
  * The sink is integrated with Flink's checkpointing mechanism and can be reset to reproduce
  * previously emitted records.
  */
class ResettableSensorSource extends RichParallelSourceFunction[SensorReading] with CheckpointedFunction {

  // flag indicating whether source is still running.
  var running: Boolean = true

  // the last emitted sensor readings
  var readings: Array[SensorReading] = _

  // state to checkpoint last emitted readings
  var sensorsState: ListState[SensorReading] = _

  /** run() continuously emits SensorReadings by emitting them through the SourceContext. */
  override def run(srcCtx: SourceContext[SensorReading]): Unit = {

    // initialize random number generator
    val rand = new Random()

    // emit data until being canceled
    while (running) {

      // take a lock to ensure we don't emit while taking a checkpoint
      srcCtx.getCheckpointLock.synchronized {

        // emit readings for all sensors
        for (i <- readings.indices) {
          // get reading
          val reading = readings(i)

          // update timestamp and temperature
          val newTime = reading.timestamp + 100
          // set seed for deterministic temperature generation
          rand.setSeed(newTime ^ reading.temperature.toLong)
          val newTemp = reading.temperature + (rand.nextGaussian() * 0.5)
          val newReading = SensorReading(reading.id, newTime, newTemp)

          // store new reading and emit it
          readings(i) = newReading
          srcCtx.collect(newReading)
        }
      }

      // wait for 100 ms
      Thread.sleep(100)
    }
  }

  /** Cancels this SourceFunction. */
  override def cancel(): Unit = {
    running = false
  }

  /** Load the previous readings from checkpointed state or generate initial readings. */
  override def initializeState(ctx: FunctionInitializationContext): Unit = {

    // define state of sink as union list operator state
    this.sensorsState = ctx.getOperatorStateStore.getUnionListState(
      new ListStateDescriptor[SensorReading]("sensorsState", classOf[SensorReading]))

    // get iterator over state
    val sensorsStateIt = sensorsState.get().iterator()

    if (!sensorsStateIt.hasNext) {
      // state is empty, this is the first run
      // create initial sensor data
      val rand = new Random()
      val numTasks = getRuntimeContext.getNumberOfParallelSubtasks
      val thisTask = getRuntimeContext.getIndexOfThisSubtask
      val curTime = Calendar.getInstance().getTimeInMillis

      // initialize sensor ids and temperatures
      this.readings = (0 until 10)
        .map { i =>
          val idx = thisTask + i * numTasks
          val sensorId = s"sensor_$idx"
          val temp = 65 + rand.nextGaussian() * 20
          SensorReading(sensorId, curTime, temp)
        }
        .toArray
    } else {
      // select the sensors to handle in this task
      val numTasks = getRuntimeContext.getNumberOfParallelSubtasks
      val thisTask = getRuntimeContext.getIndexOfThisSubtask

      val allReadings = sensorsStateIt.asScala.toSeq
      this.readings = allReadings.zipWithIndex
        .filter(x => x._2 % numTasks == thisTask)
        .map(_._1)
        .toArray
    }
  }

  /** Save the current readings in the operator state. */
  override def snapshotState(ctx: FunctionSnapshotContext): Unit = {
    // replace sensor state by current readings
    this.sensorsState.update(readings.toList.asJava)
  }
}
