package cn.piflow.bundle.rdf

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}

import scala.sys.process._

class CsvToNeo4J extends ConfigurableStop{
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = "this stop use linux shell & neo4j-import command " +
    "to load CSV file data to create or insert into neo4j" +
    "the neo4j version should be above 3.0"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  //run time parameter
  var argumentFiles : String = _
  var dbPath : String = _
  var dbName : String = _
  var idType : String = _
  //labels has been removed, you need to convey a string ,which combined by labels and files path in files property
//  var labels : String = _
  //files property should looks like => :Label1 xxx.csv,xxx.csv; :Label2 xxx.csv; xxx.csv
  //split by ';'
  var files : String = _
  var relationshipFiles : String = _
  var ignoreEmptyString : String = _
  var delimiter : String = _
  var arrayDelimiter : String = _
  var quote : String = _
  var multilineFields : String = _
  var trimString : String = _
  var encoding : String = _
  var maxProcessorCount : String = _
  var stackTrace : String = _
  var badTolerance : String = _
  var skipDuplicate : String = _
  var logBadEntries : String = _
  var skipBadRelationships : String = _
  var ignoreExtraCol : String = _
  var dbConfigure : String = _
  var configPath : String = _
  var additionalConfig : String = _
  var lagacyQuotingStyle : String = _
  var readBufferSize : String = _
  var maxMemory : String = _
  var cacheOnHeap : String = _
  var highIO : String = _
  var detailProgress : String = _




  override def setProperties(map: Map[String, Any]): Unit = {
    argumentFiles = MapUtil.get(map, "fileName").asInstanceOf[String]
    dbPath = MapUtil.get(map, "storeDir").asInstanceOf[String]
    dbName = MapUtil.get(map, "databaseName").asInstanceOf[String]
    idType = MapUtil.get(map, "idType").asInstanceOf[String]
    //labels has been removed
//    labels = MapUtil.get(map, "labels").asInstanceOf[String]
    files = MapUtil.get(map, "files").asInstanceOf[String]
    relationshipFiles = MapUtil.get(map, "relationshipFiles").asInstanceOf[String]
    delimiter = MapUtil.get(map, "delimiter").asInstanceOf[String]
    arrayDelimiter = MapUtil.get(map, "arrayDelimiter").asInstanceOf[String]
    quote = MapUtil.get(map, "quote").asInstanceOf[String]
    multilineFields = MapUtil.get(map, "multilineFields").asInstanceOf[String]
    trimString = MapUtil.get(map, "trimStrings").asInstanceOf[String]
    encoding = MapUtil.get(map, "encoding").asInstanceOf[String]
    ignoreEmptyString = MapUtil.get(map, "ignoreEmptyString").asInstanceOf[String]
    maxProcessorCount = MapUtil.get(map, "processors").asInstanceOf[String]
    stackTrace = MapUtil.get(map, "stackTrace").asInstanceOf[String]
    badTolerance = MapUtil.get(map, "badTolerance").asInstanceOf[String]
    logBadEntries = MapUtil.get(map, "skipBadEntriesLogging").asInstanceOf[String]
    skipBadRelationships = MapUtil.get(map, "skipBadRelationships").asInstanceOf[String]
    skipDuplicate = MapUtil.get(map, "skipDuplicateNodes").asInstanceOf[String]
    ignoreExtraCol = MapUtil.get(map, "ignoreExtraColumns").asInstanceOf[String]
    dbConfigure = MapUtil.get(map, "dbConfig").asInstanceOf[String]
    additionalConfig = MapUtil.get(map, "additionalConfig").asInstanceOf[String]
    lagacyQuotingStyle = MapUtil.get(map, "legacyStyleQuoting").asInstanceOf[String]
    readBufferSize = MapUtil.get(map, "readBufferSize").asInstanceOf[String]
    maxMemory = MapUtil.get(map, "maxMemory").asInstanceOf[String]
    cacheOnHeap = MapUtil.get(map, "cache").asInstanceOf[String]
    highIO = MapUtil.get(map, "highIO").asInstanceOf[String]
    detailProgress = MapUtil.get(map, "detailProgress").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    val f : PropertyDescriptor = new PropertyDescriptor()
      .name("fileName")
      .displayName("file name")
      .required(false)
      .defaultValue("default")
      .description("File containing all arguments, used as an alternative to supplying all arguments \n\t" +
        "on the command line directly.Each argument can be on a separate line or multiple \n\t" +
        "arguments per line separated by space.Arguments containing spaces needs to be \n\t" +
        "quoted.Supplying other arguments in addition to this file argument is not \n\t" +
        "supported.")

    val into : PropertyDescriptor = new PropertyDescriptor()
      .name("storeDir")
      .displayName("store directory")
      .required(true)
      .defaultValue("/data/neo4j-db/database/graph.db")
      .description("Database directory to import into. \r\n" +
        "Must not contain existing database.")

    val database : PropertyDescriptor = new PropertyDescriptor()
      .name("databaseName")
      .displayName("database name")
      .required(true)
      .defaultValue("graph.db")
      .description("Database name to import into. \r\n" +
        "Must not contain existing database.")
      // node labels has been removed
//    val nodeLabels : PropertyDescriptor = new PropertyDescriptor()
//      .name("labels")
//      .displayName("nodes labels paths")
//      .required(true)
//      .description("Node CSV header and data. Multiple files will be logically seen as one big file " +
//        "\n\tfrom the perspective of the importer. The first line must contain the header. " +
//        "\n\tMultiple data sources like these can be specified in one import, where each data " +
//        "\n\tsource has its own header. Note that file groups must be enclosed in quotation " +
//        "\n\tmarks. Each file can be a regular expression and will then include all matching " +
//        "\n\tfiles. The file matching is done with number awareness such that e.g. " +
//        "\n\tfiles:'File1Part_001.csv', 'File12Part_003' will be ordered in that order for a " +
//        "\n\tpattern like: 'File.*'")

    val nodesFiles : PropertyDescriptor = new PropertyDescriptor()
      .name("files")
      .displayName("nodes files paths")
      .required(true)
      .description("Node CSV header and data. Multiple files will be logically seen as one big file " +
        "\n\tfrom the perspective of the importer. The first line must contain the header. " +
        "\n\tMultiple data sources like these can be specified in one import, where each data " +
        "\n\tsource has its own header. Note that file groups must be enclosed in quotation " +
        "\n\tmarks. Each file can be a regular expression and will then include all matching " +
        "\n\tfiles. The file matching is done with number awareness such that e.g. " +
        "\n\tfiles property should looks like => :Label1 xxx.csv,xxx.csv;:Label2 xxx.csv;xxx.csv")

    val relationships : PropertyDescriptor = new PropertyDescriptor()
      .name("relationshipFiles")
      .required(true)
      .displayName("relationship file paths")
      .description("Relationship CSV header and data. Multiple files will be logically seen as one " +
        "\n\tbig file from the perspective of the importer. The first line must contain the " +
        "\n\theader. Multiple data sources like these can be specified in one import, where " +
        "\n\teach data source has its own header. Note that file groups must be enclosed in " +
        "\n\tquotation marks. Each file can be a regular expression and will then include all " +
        "\n\tmatching files. The file matching is done with number awareness such that e.g. " +
        "\n\tfiles:'File1Part_001.csv', 'File12Part_003' will be ordered in that order for a " +
        "\n\tfiles property should looks like => :Label1 xxx.csv,xxx.csv;:Label2 xxx.csv;xxx.csv")

    val delimiter : PropertyDescriptor = new PropertyDescriptor()
      .name("delimiter")
      .required(false)
      .defaultValue("default")
      .description("Delimiter character, or 'TAB', between values in CSV data. The default option is \",\".")

    val arrayDelimiter : PropertyDescriptor = new PropertyDescriptor()
      .name("arrayDelimiter")
      .required(false)
      .defaultValue("default")
      .description("Delimiter character, or 'TAB', between array elements within a value in CSV \n\t" +
        "data. The default option is ';'.")

    val quote : PropertyDescriptor = new PropertyDescriptor()
      .name("quote")
      .displayName("quote character")
      .required(false)
      .defaultValue("default")
      .description("Character to treat as quotation character for values in CSV data. The default " +
        "\n\toption is \". Quotes inside quotes escaped like \"\"\"Go away\"\", he said.\" and \"\\\"Go \n\taway\\\", he said.\" are supported. If you have set \"'\" to be used as the quotation " +
        "\n\tcharacter, you could write the previous example like this instead: '\"Go away\", " +
        "\n\the said.'")

    val multilineFields : PropertyDescriptor = new PropertyDescriptor()
      .name("multilineFields")
      .displayName("multiline fields")
      .required(false)
      .defaultValue("false")
      .allowableValues(Set("true","false"))
      .description("Whether or not fields from input source can span multiple lines, i.e. contain " +
        "\n\tnewline characters. Default value: false")

    val trimString : PropertyDescriptor = new PropertyDescriptor()
      .name("trimStrings")
      .displayName("trim strings")
      .required(false)
      .defaultValue("false")
      .allowableValues(Set("true", "false"))
      .description("Whether or not strings should be trimmed for whitespaces. Default value: false")

    val inputEncoding : PropertyDescriptor = new PropertyDescriptor()
      .name("encoding")
      .displayName("input encoding")
      .required(false)
      .defaultValue("default")
      .description("Character set that input data is encoded in. Provided value must be one out of " +
        "\n\tthe available character sets in the JVM, as provided by " +
        "\n\tCharset#availableCharsets(). If no input encoding is provided, the default " +
        "\n\tcharacter set of the JVM will be used.")

    val ignoreEmptyString : PropertyDescriptor = new PropertyDescriptor()
      .name("ignoreEmptyString")
      .displayName("ignore empty string")
      .required(false)
      .defaultValue("false")
      .allowableValues(Set("true", "false"))
      .description("\tWhether or not empty string fields, i.e. \"\" from input source are ignored, i.e. " +
        "\n\ttreated as null. Default value: false")

    val idType : PropertyDescriptor = new PropertyDescriptor()
      .name("idType")
      .displayName("id type")
      .required(false)
      .defaultValue("STRING")
      .allowableValues(Set("STRING","INTEGER","ACTUAL"))
      .description("One out of [STRING, INTEGER, ACTUAL] and specifies how ids in node/relationship " +
        "\n\tinput files are treated." +
        "\n\tSTRING: arbitrary strings for identifying nodes." +
        "\n\tINTEGER: arbitrary integer values for identifying nodes." +
        "\n\tACTUAL: (advanced) actual node ids. The default option is STRING. Default value: " +
        "\n\tSTRING")

    val processors : PropertyDescriptor = new PropertyDescriptor()
      .name("processors")
      .displayName("processor count")
      .required(false)
      .defaultValue("default")
      .description("(advanced) Max number of processors used by the importer. Defaults to the number " +
        "\n\tof available processors reported by the JVM (in your case 16). There is a " +
        "\n\tcertain amount of minimum threads needed so for that reason there is no lower " +
        "\n\tbound for this value. For optimal performance this value shouldn't be greater " +
        "\n\tthan the number of available processors.")

    val stackTrace : PropertyDescriptor = new PropertyDescriptor()
      .name("stackTrace")
      .displayName("stack trace")
      .required(false)
      .defaultValue("false")
      .allowableValues(Set("true", "false"))
      .description("Enable printing of error stack traces. Default value: false")

    val badTolerance : PropertyDescriptor = new PropertyDescriptor()
      .name("badTolerance")
      .displayName("tolerant bad input")
      .required(false)
      .defaultValue("1000")
      .description("Number of bad entries before the import is considered failed. This tolerance " +
        "\n\tthreshold is about relationships refering to missing nodes. Format errors in " +
        "\n\tinput data are still treated as errors. Default value: 1000")

    val skipBadEntriesLogging : PropertyDescriptor = new PropertyDescriptor()
      .name("skipBadEntriesLogging")
      .displayName("skip the bad entries log")
      .required(false)
      .defaultValue("false")
      .allowableValues(Set("true", "false"))
      .description("Whether or not to skip logging bad entries detected during import. Default " +
        "\n\tvalue: false")

    val skipBadRelationships : PropertyDescriptor = new PropertyDescriptor()
      .name("skipBadRelationships")
      .displayName("skip bad relationships")
      .defaultValue("true")
      .required(false)
      .allowableValues(Set("true", "false"))
      .description("Whether or not to skip importing relationships that refers to missing node ids, " +
        "\n\ti.e. either start or end node id/group referring to node that wasn't specified " +
        "\n\tby the node input data. Skipped nodes will be logged, containing at most number " +
        "\n\tof entites specified by bad-tolerance, unless otherwise specified by " +
        "\n\tskip-bad-entries-logging option. Default value: true")


    val skipDuplicateNodes : PropertyDescriptor = new PropertyDescriptor()
      .name("skipDuplicateNodes")
      .displayName("skip the duplicated nodes")
      .defaultValue("false")
      .allowableValues(Set("true", "false"))
      .required(false)
      .description("Whether or not to skip importing nodes that have the same id/group. In the event " +
        "\n\tof multiple nodes within the same group having the same id, the first " +
        "\n\tencountered will be imported whereas consecutive such nodes will be skipped. " +
        "\n\tSkipped nodes will be logged, containing at most number of entities specified by " +
        "\n\tbad-tolerance, unless otherwise specified by skip-bad-entries-loggingoption. " +
        "\n\tDefault value: false")

    val ignoreExtraColumns : PropertyDescriptor = new PropertyDescriptor()
      .name("ignoreExtraColumns")
      .displayName("ignore extra columns")
      .defaultValue("false")
      .allowableValues(Set("true", "false"))
      .required(false)
      .description("Whether or not to ignore extra columns in the data not specified by the header. " +
        "\n\tSkipped columns will be logged, containing at most number of entities specified " +
        "\n\tby bad-tolerance, unless otherwise specified by skip-bad-entries-loggingoption. " +
        "\n\tDefault value: false")

    val dbConfig : PropertyDescriptor = new PropertyDescriptor()
      .name("dbConfig")
      .required(false)
      .defaultValue("default")
      .displayName("db config path")
      .description("(advanced) Option is deprecated and replaced by 'additional-config'. ")


    val additionalConfig : PropertyDescriptor = new PropertyDescriptor()
      .name("additionalConfig")
      .displayName("additional config path")
      .defaultValue("default")
      .required(false)
      .description("(advanced) File specifying database-specific configuration. For more information " +
        "\n\tconsult manual about available configuration options for a neo4j configuration " +
        "\n\tfile. Only configuration affecting store at time of creation will be read. " +
        "\n\tExamples of supported config are:" +
        "\n\tdbms.relationship_grouping_threshold" +
        "\n\tunsupported.dbms.block_size.strings" +
        "\n\tunsupported.dbms.block_size.array_properties")

    val legacyStyleQuoting : PropertyDescriptor = new PropertyDescriptor()
      .name("legacyStyleQuoting")
      .displayName("legacy style quoting")
      .defaultValue("true")
      .allowableValues(Set("true", "false"))
      .required(false)
      .description("Whether or not backslash-escaped quote e.g. \\\" is interpreted as inner quote. " +
        "\n\tDefault value: true")

    val readBufferSize : PropertyDescriptor = new PropertyDescriptor()
      .name("readBufferSize")
      .displayName("read buffer size")
      .defaultValue("4194304")
      .required(false)
      .description("Size of each buffer for reading input data. It has to at least be large enough" +
        "\r\n(eg : bytes, e.g. 10k, 4M)" +
        "\n\tto hold the biggest single value in the input data. Default value: 4194304")

    val maxMemory : PropertyDescriptor = new PropertyDescriptor()
      .name("maxMemory")
      .displayName("max memory")
      .defaultValue("default")
      .required(false)
      .description("(advanced) Maximum memory that importer can use for various data structures and " +
        "\n\tcaching to improve performance. If left as unspecified (null) it is set to 90% " +
        "\n\tof (free memory on machine - max JVM memory). Values can be plain numbers, like " +
        "\n\t10000000 or e.g. 20G for 20 gigabyte, or even e.g. 70%.")

    val cacheOnHeap : PropertyDescriptor = new PropertyDescriptor()
      .name("cache")
      .displayName("cache on heap[advanced]")
      .defaultValue("false")
      .allowableValues(Set("false", "true"))
      .required(false)
      .description("(advanced) Whether or not to allow allocating memory for the cache on heap. If " +
        "\n\t'false' then caches will still be allocated off-heap, but the additional free " +
        "\n\tmemory inside the JVM will not be allocated for the caches. This to be able to " +
        "\n\thave better control over the heap memory. Default value: false")

    val highIO : PropertyDescriptor = new PropertyDescriptor()
      .name("highIO")
      .displayName("is high io[advanced]")
      .allowableValues(Set("true", "false"))
      .defaultValue("false")
      .required(false)
      .description("(advanced) Ignore environment-based heuristics, and assume that the target " +
        "\n\tstorage subsystem can support parallel IO with high throughput.")

    val detailedProgress : PropertyDescriptor = new PropertyDescriptor()
      .name("detailedProgress")
      .displayName("detailed progress")
      .required(false)
      .defaultValue("false")
      .allowableValues(Set("false", "true"))
      .description("Use the old detailed 'spectrum' progress printing. Default value: false")

    List(f, into, database, nodesFiles,
      relationships, delimiter, arrayDelimiter,
      quote, multilineFields, trimString, inputEncoding,
      ignoreEmptyString, idType, processors, stackTrace,
      badTolerance, skipBadEntriesLogging, skipBadEntriesLogging,
      skipBadRelationships, skipDuplicateNodes, ignoreExtraColumns,
      dbConfig, additionalConfig, legacyStyleQuoting, readBufferSize,
      maxMemory, cacheOnHeap, highIO, detailedProgress)
  }

  override def getIcon(): Array[Byte] = ImageUtil.getImage("icon/rdf/CsvToNeo4J.png")

  override def getGroup(): List[String] =  List(StopGroup.RDFGroup.toString)

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val ret : Stream[String] = s" nohup" +
    makeCommand("into", dbPath) +
    makeCommand("f", argumentFiles) +
    makeCommand("database", dbName) +
    makeCommand("nodes", files.split(";").map(x => x.trim)) +
    makeCommand("relationships", relationshipFiles.split(";").map(x => x.trim)) +
    makeCommand("delimiter", delimiter) +
    makeCommand("array-delimiter", arrayDelimiter) +
    makeCommand("quote", quote) +
    makeCommand("multiline-fields", multilineFields) +
    makeCommand("trim-strings", trimString) +
    makeCommand("input-encoding", encoding) +
    makeCommand("ignore-empty-strings", ignoreEmptyString) +
    makeCommand("id-type", idType) +
    makeCommand("processors", maxProcessorCount) +
    makeCommand("stacktrace", stackTrace) +
    makeCommand("bad-tolerance", badTolerance) +
    makeCommand("skip-bad-entries-logging", logBadEntries) +
    makeCommand("skip-bad-relationships", skipBadRelationships) +
    makeCommand("skip-duplicate-nodes", skipDuplicate) +
    makeCommand("ignore-extra-columns", ignoreExtraCol) +
    makeCommand("db-config", dbConfigure) +
    makeCommand("additional-config", additionalConfig) +
    makeCommand("legacy-style-quoting", additionalConfig) +
    makeCommand("read-buffer-size", readBufferSize) +
    makeCommand("max-memory", maxMemory) +
    makeCommand("cache-on-heap", cacheOnHeap) +
    makeCommand("high-io", highIO) +
    makeCommand("detailed-progress", detailProgress) +
    s" &" lineStream

    ret.foreach(println(_))
  }

  def makeCommand (commandPrefix : String, comm : String) : String = {
    if (comm == "default") ""
    else "--" + commandPrefix + " " + comm
  }

  def makeCommand (commandPrefix : String, comm1 : String, comm2 : String): String = {
    "--" + commandPrefix + " " + comm1 + " " + comm2
  }
  def makeCommand (commandPrefix : String, comm1 : Array[String]) : String = {
    comm1.map(str => makeCommand(commandPrefix, str)).reduce(_ + " " + _)
  }
  def makeLabeledCommand (commandPrefix : String, comm : String) : String = {
    if (comm == "default") ""
    else {
      if (comm startsWith ":")
        "--" + commandPrefix + comm
      else {
        "--" + commandPrefix + " " + comm
      }
    }
  }
}
object CsvToNeo4J {

}
