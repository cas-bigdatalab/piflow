package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientStartFlowGroup {

  def main(args: Array[String]): Unit = {

    /*val json =
      """
        |{
        |  "group": {
        |    "name": "Group",
        |    "uuid": "1111111111111",
        |    "groups": [
        |      {"group": {
        |        "name": "Group1",
        |        "uuid": "1111111111111",
        |
        |        "flows": [
        |          {"flow": {
        |            "name": "flow1",
        |            "uuid": "1234",
        |            "executorNumber": "2",
        |            "executorMemory": "1g",
        |            "executorCores": "1",
        |            "stops": [{
        |              "uuid": "1111",
        |              "name": "XmlParser",
        |              "bundle": "cn.piflow.bundle.xml.XmlParser",
        |              "properties": {
        |                "xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |                "rowTag": "phdthesis"
        |              }
        |            },
        |              {
        |                "uuid": "2222",
        |                "name": "SelectField",
        |                "bundle": "cn.piflow.bundle.common.SelectField",
        |                "properties": {
        |                  "schema": "title,author,pages"
        |                }
        |
        |              },
        |              {
        |                "uuid": "3333",
        |                "name": "PutHiveStreaming",
        |                "bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |                "properties": {
        |                  "database": "sparktest",
        |                  "table": "dblp_phdthesis"
        |                }
        |              }
        |            ],
        |            "paths": [{
        |              "from": "XmlParser",
        |              "outport": "",
        |              "inport": "",
        |              "to": "SelectField"
        |            },
        |              {
        |                "from": "SelectField",
        |                "outport": "",
        |                "inport": "",
        |                "to": "PutHiveStreaming"
        |              }
        |            ]
        |          }},
        |          {"flow": {
        |            "name": "flow2",
        |            "uuid": "5678",
        |            "stops": [{
        |              "uuid": "1111",
        |              "name": "XmlParser",
        |              "bundle": "cn.piflow.bundle.xml.XmlParser",
        |              "properties": {
        |                "xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |                "rowTag": "phdthesis"
        |              }
        |            },
        |              {
        |                "uuid": "2222",
        |                "name": "SelectField",
        |                "bundle": "cn.piflow.bundle.common.SelectField",
        |                "properties": {
        |                  "schema": "title,author,pages"
        |                }
        |
        |              },
        |              {
        |                "uuid": "3333",
        |                "name": "PutHiveStreaming",
        |                "bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |                "properties": {
        |                  "database": "sparktest",
        |                  "table": "dblp_phdthesis"
        |                }
        |              }
        |            ],
        |            "paths": [{
        |              "from": "XmlParser",
        |              "outport": "",
        |              "inport": "",
        |              "to": "SelectField"
        |            },
        |              {
        |                "from": "SelectField",
        |                "outport": "",
        |                "inport": "",
        |                "to": "PutHiveStreaming"
        |              }
        |            ]
        |          }}
        |        ],
        |
        |        "conditions": [{
        |          "entry": "flow2",
        |          "after": "flow1"
        |        }]
        |      }},
        |      {"group": {
        |        "name": "Group3",
        |        "uuid": "1111111111111",
        |
        |        "flows": [
        |          {"flow": {
        |            "name": "flow4",
        |            "uuid": "1234",
        |            "executorNumber": "2",
        |            "executorMemory": "1g",
        |            "executorCores": "1",
        |            "stops": [{
        |              "uuid": "1111",
        |              "name": "XmlParser",
        |              "bundle": "cn.piflow.bundle.xml.XmlParser",
        |              "properties": {
        |                "xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |                "rowTag": "phdthesis"
        |              }
        |            },
        |              {
        |                "uuid": "2222",
        |                "name": "SelectField",
        |                "bundle": "cn.piflow.bundle.common.SelectField",
        |                "properties": {
        |                  "schema": "title,author,pages"
        |                }
        |
        |              },
        |              {
        |                "uuid": "3333",
        |                "name": "PutHiveStreaming",
        |                "bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |                "properties": {
        |                  "database": "sparktest",
        |                  "table": "dblp_phdthesis"
        |                }
        |              }
        |            ],
        |            "paths": [{
        |              "from": "XmlParser",
        |              "outport": "",
        |              "inport": "",
        |              "to": "SelectField"
        |            },
        |              {
        |                "from": "SelectField",
        |                "outport": "",
        |                "inport": "",
        |                "to": "PutHiveStreaming"
        |              }
        |            ]
        |          }},
        |          {"flow": {
        |            "name": "flow5",
        |            "uuid": "5678",
        |            "stops": [{
        |              "uuid": "1111",
        |              "name": "XmlParser",
        |              "bundle": "cn.piflow.bundle.xml.XmlParser",
        |              "properties": {
        |                "xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |                "rowTag": "phdthesis"
        |              }
        |            },
        |              {
        |                "uuid": "2222",
        |                "name": "SelectField",
        |                "bundle": "cn.piflow.bundle.common.SelectField",
        |                "properties": {
        |                  "schema": "title,author,pages"
        |                }
        |
        |              },
        |              {
        |                "uuid": "3333",
        |                "name": "PutHiveStreaming",
        |                "bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |                "properties": {
        |                  "database": "sparktest",
        |                  "table": "dblp_phdthesis"
        |                }
        |              }
        |            ],
        |            "paths": [{
        |              "from": "XmlParser",
        |              "outport": "",
        |              "inport": "",
        |              "to": "SelectField"
        |            },
        |              {
        |                "from": "SelectField",
        |                "outport": "",
        |                "inport": "",
        |                "to": "PutHiveStreaming"
        |              }
        |            ]
        |          }}
        |        ],
        |
        |
        |        "conditions": [{
        |          "entry": "flow5",
        |          "after": "flow4"
        |        }]
        |      }}
        |    ],
        |
        |    "flows":[
        |      {"flow": {
        |        "name": "flow3",
        |        "uuid": "91011",
        |        "executorNumber": "2",
        |        "executorMemory": "1g",
        |        "executorCores": "1",
        |        "stops": [{
        |          "uuid": "1111",
        |          "name": "XmlParser",
        |          "bundle": "cn.piflow.bundle.xml.XmlParser",
        |          "properties": {
        |            "xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |            "rowTag": "phdthesis"
        |          }
        |        },
        |          {
        |            "uuid": "2222",
        |            "name": "SelectField",
        |            "bundle": "cn.piflow.bundle.common.SelectField",
        |            "properties": {
        |              "schema": "title,author,pages"
        |            }
        |
        |          },
        |          {
        |            "uuid": "3333",
        |            "name": "PutHiveStreaming",
        |            "bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |            "properties": {
        |              "database": "sparktest",
        |              "table": "dblp_phdthesis"
        |            }
        |          }
        |        ],
        |        "paths": [{
        |          "from": "XmlParser",
        |          "outport": "",
        |          "inport": "",
        |          "to": "SelectField"
        |        },
        |          {
        |            "from": "SelectField",
        |            "outport": "",
        |            "inport": "",
        |            "to": "PutHiveStreaming"
        |          }
        |        ]
        |      }}
        |    ],
        |
        |    "conditions": [
        |      {
        |      "entry": "flow3",
        |      "after": "Group1"
        |      },
        |      {
        |        "entry": "Group3",
        |        "after": "flow3"
        |      }
        |    ]
        |  }
        |}
        |
      """.stripMargin*/
    /*val json=
      """
        |{
        |  "group" : {
        |    "name" : "xjzhu",
        |    "flows" : [ {
        |      "flow" : {
        |        "executorNumber" : "1",
        |        "driverMemory" : "1g",
        |        "executorMemory" : "1g",
        |        "executorCores" : "1",
        |        "paths" : [ ],
        |        "name" : "flow1",
        |        "stops" : [ {
        |          "customizedProperties" : { },
        |          "name" : "SelectHiveQL",
        |          "uuid" : "8a80d88d712aa8c601717c68f7220272",
        |          "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |          "properties" : {
        |            "hiveQL" : "show databases"
        |          }
        |        } ],
        |        "uuid" : "8a80d88d712aa8c601717c68f7220271"
        |      }
        |    } ],
        |    "groups" : [ {
        |      "group" : {
        |        "flows" : [ {
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow3",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        }, {
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow2",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f721026e",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases;"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f721026d"
        |          }
        |        },{
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow4",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        },{
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow5",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        }],
        |        "conditions" : [ {
        |          "entry" : "flow3",
        |          "after" : "flow2"
        |        },
        |         {
        |          "entry" : "flow5",
        |          "after" : "flow4"
        |        }],
        |        "name" : "group1",
        |        "uuid" : "8a80d88d712aa8c601717c68f71f0269"
        |      }
        |    } ],
        |    "conditions" : [ {
        |      "entry" : "group1",
        |      "after" : "flow1"
        |    } ],
        |    "uuid" : "8a80d88d712aa8c601717c68f71e0268"
        |  }
        |}
      """.stripMargin*/

    val json =
      """
        |{
        |  "group" : {
        |    "name" : "xjzhu",
        |    "flows" : [ {
        |      "flow" : {
        |        "executorNumber" : "1",
        |        "driverMemory" : "1g",
        |        "executorMemory" : "1g",
        |        "executorCores" : "1",
        |        "paths" : [ ],
        |        "name" : "flow1",
        |        "stops" : [ {
        |          "customizedProperties" : { },
        |          "name" : "SelectHiveQL",
        |          "uuid" : "8a80d88d712aa8c601717c68f7220272",
        |          "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |          "properties" : {
        |            "hiveQL" : "show databases"
        |          }
        |        } ],
        |        "uuid" : "8a80d88d712aa8c601717c68f7220271"
        |      }
        |    } ],
        |    "groups" : [ {
        |      "group" : {
        |        "flows" : [ {
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow3",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        }, {
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow2",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f721026e",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases;"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f721026d"
        |          }
        |        },{
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow4",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        },{
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow5",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        }],
        |        "conditions" : [ {
        |          "entry" : "flow3",
        |          "after" : "flow2"
        |        },
        |         {
        |          "entry" : "flow5",
        |          "after" : "flow4"
        |        }],
        |        "name" : "group1",
        |        "uuid" : "8a80d88d712aa8c601717c68f71f0269"
        |      }
        |    },{
        |      "group" : {
        |        "flows" : [ {
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow6",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases;"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        }, {
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow7",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f721026e",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f721026d"
        |          }
        |        },{
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow8",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        },{
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow9",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f720026b",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f71f026a"
        |          }
        |        }],
        |        "conditions" : [ {
        |          "entry" : "flow7",
        |          "after" : "flow6"
        |        },
        |         {
        |          "entry" : "flow9",
        |          "after" : "flow8"
        |        }],
        |        "name" : "group2",
        |        "uuid" : "8a80d88d712aa8c601717c68f71f0269"
        |      }
        |    } ],
        |    "conditions" : [ {
        |      "entry" : "group1",
        |      "after" : "flow1"
        |    },{
        |      "entry" : "group2",
        |      "after" : "flow1"
        |    } ],
        |    "uuid" : "8a80d88d712aa8c601717c68f71e0268"
        |  }
        |}
      """.stripMargin

    /*val json=
      """
        |{
        |  "group" : {
        |    "flows" : [ {
        |      "flow" : {
        |        "executorNumber" : "1",
        |        "driverMemory" : "1g",
        |        "executorMemory" : "1g",
        |        "executorCores" : "1",
        |        "paths" : [ ],
        |        "name" : "flow1",
        |        "stops" : [ {
        |          "customizedProperties" : { },
        |          "name" : "SelectHiveQL",
        |          "uuid" : "8a80d88d712aa8c601717c68f7220272",
        |          "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |          "properties" : {
        |            "hiveQL" : "show databases"
        |          }
        |        } ],
        |        "uuid" : "8a80d88d712aa8c601717c68f7220271"
        |      }
        |    } ],
        |    "name" : "xjzhu",
        |    "groups" : [ {
        |      "group" : {
        |        "flows" : [ {
        |          "flow" : {
        |            "executorNumber" : "1",
        |            "driverMemory" : "1g",
        |            "executorMemory" : "1g",
        |            "executorCores" : "1",
        |            "paths" : [ ],
        |            "name" : "flow2",
        |            "stops" : [ {
        |              "customizedProperties" : { },
        |              "name" : "SelectHiveQL",
        |              "uuid" : "8a80d88d712aa8c601717c68f721026e",
        |              "bundle" : "cn.piflow.bundle.hive.SelectHiveQL",
        |              "properties" : {
        |                "hiveQL" : "show databases;"
        |              }
        |            } ],
        |            "uuid" : "8a80d88d712aa8c601717c68f721026d"
        |          }
        |        }],
        |        "conditions" : [ ],
        |        "name" : "group1",
        |        "uuid" : "8a80d88d712aa8c601717c68f71f0269"
        |      }
        |    } ],
        |    "conditions" : [ {
        |      "entry" : "group1",
        |      "after" : "flow1"
        |    } ],
        |    "uuid" : "8a80d88d712aa8c601717c68f71e0268"
        |  }
        |}
      """.stripMargin*/

    val url = "http://10.0.85.83:8001/group/start"
    val timeout = 1800
    val requestConfig = RequestConfig.custom()
      .setConnectTimeout(timeout*1000)
      .setConnectionRequestTimeout(timeout*1000)
      .setSocketTimeout(timeout*1000).build()

    val client = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).build()

    val post:HttpPost = new HttpPost(url)
    post.addHeader("Content-Type", "application/json")
    post.setEntity(new StringEntity(json))


    val response:CloseableHttpResponse = client.execute(post)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)

    /*val map = OptionUtil.getAny(JSON.parseFull(json))d.asInstanceOf[Map[String, Any]]

    val jsonObj = JsonUtil.toJson(map)
    val str = JsonUtil.format(jsonObj)
    //convertJson = convertJson.replaceAll("\\{","\\{\t\n")


    //var convertJson1 = convertJson.replaceAll("{","{\n")
    //var convertJson2 = convertJson1.replaceAll("}","}\n")
    println("Convert Json===" + str)

    val convertMap = OptionUtil.getAny(JSON.parseFull(str)).asInstanceOf[Map[String, Any]]
    println("Convert Map===" + convertMap)*/


  }

}
