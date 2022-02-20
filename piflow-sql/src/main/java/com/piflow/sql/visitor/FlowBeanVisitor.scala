package com.piflow.sql.visitor
import cn.piflow.conf.bean.{FlowBean, PathBean, StopBean}
import cn.piflow.conf.util.MapUtil
import com.piflow.sql.datasource.RegisterDataSource
import com.piflow.sql.out.{SqlBaseBaseVisitor, SqlBaseParser}

import scala.collection.mutable.{Map => MMap}

class FlowBeanVisitor extends SqlBaseBaseVisitor[FlowBean]{

  var flowBean : FlowBean = null
  def getFlowBeanInstance: FlowBean = {
    if (flowBean == null)
      flowBean = FlowBean(Map())
    flowBean
  }
  var currentStopBean:StopBean = null


  //TODO: return flow json
  override def visitSingleStatement(ctx: SqlBaseParser.SingleStatementContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSingleStatement:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSingleExpression(ctx: SqlBaseParser.SingleExpressionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSingleExpression:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSingleTableIdentifier(ctx: SqlBaseParser.SingleTableIdentifierContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSingleTableIdentifier:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSingleDataType(ctx: SqlBaseParser.SingleDataTypeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSingleDataType:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitStatementDefault(ctx: SqlBaseParser.StatementDefaultContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitStatementDefault:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitUse(ctx: SqlBaseParser.UseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitUse:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateDatabase(ctx: SqlBaseParser.CreateDatabaseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateDatabase:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSetDatabaseProperties(ctx: SqlBaseParser.SetDatabasePropertiesContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSetDatabaseProperties:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDropDatabase(ctx: SqlBaseParser.DropDatabaseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDropDatabase:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateTableUsing(ctx: SqlBaseParser.CreateTableUsingContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateTableUsing:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateTable(ctx: SqlBaseParser.CreateTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateTableLike(ctx: SqlBaseParser.CreateTableLikeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateTableLike:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitAnalyze(ctx: SqlBaseParser.AnalyzeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitAnalyze:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRenameTable(ctx: SqlBaseParser.RenameTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRenameTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSetTableProperties(ctx: SqlBaseParser.SetTablePropertiesContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSetTableProperties:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitUnsetTableProperties(ctx: SqlBaseParser.UnsetTablePropertiesContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitUnsetTableProperties:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSetTableSerDe(ctx: SqlBaseParser.SetTableSerDeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSetTableSerDe:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitAddTablePartition(ctx: SqlBaseParser.AddTablePartitionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitAddTablePartition:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRenameTablePartition(ctx: SqlBaseParser.RenameTablePartitionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRenameTablePartition:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDropTablePartitions(ctx: SqlBaseParser.DropTablePartitionsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSDropTablePartitions:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSetTableLocation(ctx: SqlBaseParser.SetTableLocationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSetTableLocation:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRecoverPartitions(ctx: SqlBaseParser.RecoverPartitionsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRecoverPartitions:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDropTable(ctx: SqlBaseParser.DropTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDropTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateView(ctx: SqlBaseParser.CreateViewContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateView:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateTempViewUsing(ctx: SqlBaseParser.CreateTempViewUsingContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateTempViewUsing:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitAlterViewQuery(ctx: SqlBaseParser.AlterViewQueryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitAlterViewQuery:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateFunction(ctx: SqlBaseParser.CreateFunctionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateFunction:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDropFunction(ctx: SqlBaseParser.DropFunctionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDropFunction:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitExplain(ctx: SqlBaseParser.ExplainContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitExplain:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitShowTables(ctx: SqlBaseParser.ShowTablesContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitShowTables:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitShowDatabases(ctx: SqlBaseParser.ShowDatabasesContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitShowDatabases:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitShowTblProperties(ctx: SqlBaseParser.ShowTblPropertiesContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitShowTblProperties:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitShowColumns(ctx: SqlBaseParser.ShowColumnsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitShowColumns:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitShowPartitions(ctx: SqlBaseParser.ShowPartitionsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitShowPartitions:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitShowFunctions(ctx: SqlBaseParser.ShowFunctionsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitShowFunctions:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitShowCreateTable(ctx: SqlBaseParser.ShowCreateTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitShowCreateTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDescribeFunction(ctx: SqlBaseParser.DescribeFunctionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDescribeFunction:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDescribeDatabase(ctx: SqlBaseParser.DescribeDatabaseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDescribeDatabase:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDescribeTable(ctx: SqlBaseParser.DescribeTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDescribeTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRefreshTable(ctx: SqlBaseParser.RefreshTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRefreshTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRefreshResource(ctx: SqlBaseParser.RefreshResourceContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRefreshResource:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCacheTable(ctx: SqlBaseParser.CacheTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCacheTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitUncacheTable(ctx: SqlBaseParser.UncacheTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitUncacheTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitClearCache(ctx: SqlBaseParser.ClearCacheContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitClearCache:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitLoadData(ctx: SqlBaseParser.LoadDataContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitLoadData:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTruncateTable(ctx: SqlBaseParser.TruncateTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTruncateTable:\t	 " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRepairTable(ctx: SqlBaseParser.RepairTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRepairTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitManageResource(ctx: SqlBaseParser.ManageResourceContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitManageResource:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitFailNativeCommand(ctx: SqlBaseParser.FailNativeCommandContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitFailNativeCommand:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSetConfiguration(ctx: SqlBaseParser.SetConfigurationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSetConfiguration:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitResetConfiguration(ctx: SqlBaseParser.ResetConfigurationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitResetConfiguration:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitUnsupportedHiveNativeCommands(ctx: SqlBaseParser.UnsupportedHiveNativeCommandsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitUnsupportedHiveNativeCommand:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateTableHeader(ctx: SqlBaseParser.CreateTableHeaderContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateTableHeader:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitBucketSpec(ctx: SqlBaseParser.BucketSpecContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitBucketSpec:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSkewSpec(ctx: SqlBaseParser.SkewSpecContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSkewSpec:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitLocationSpec(ctx: SqlBaseParser.LocationSpecContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitLocationSpec:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQuery(ctx: SqlBaseParser.QueryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQuery:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitInsertInto(ctx: SqlBaseParser.InsertIntoContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitInsertInto:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitPartitionSpecLocation(ctx: SqlBaseParser.PartitionSpecLocationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitPartitionSpecLocation:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitPartitionSpec(ctx: SqlBaseParser.PartitionSpecContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitPartitionSpec:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitPartitionVal(ctx: SqlBaseParser.PartitionValContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitPartitionVal:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDescribeFuncName(ctx: SqlBaseParser.DescribeFuncNameContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDescribeFuncName:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDescribeColName(ctx: SqlBaseParser.DescribeColNameContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDescribeColName:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCtes(ctx: SqlBaseParser.CtesContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCtes:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNamedQuery(ctx: SqlBaseParser.NamedQueryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNamedQuery:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTableProvider(ctx: SqlBaseParser.TableProviderContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTableProvider:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTablePropertyList(ctx: SqlBaseParser.TablePropertyListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTablePropertyList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTableProperty(ctx: SqlBaseParser.TablePropertyContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTableProperty:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTablePropertyKey(ctx: SqlBaseParser.TablePropertyKeyContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTablePropertyKey:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTablePropertyValue(ctx: SqlBaseParser.TablePropertyValueContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTablePropertyValue:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitConstantList(ctx: SqlBaseParser.ConstantListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitConstantList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNestedConstantList(ctx: SqlBaseParser.NestedConstantListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNestedConstantList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCreateFileFormat(ctx: SqlBaseParser.CreateFileFormatContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCreateFileFormat:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTableFileFormat(ctx: SqlBaseParser.TableFileFormatContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTableFileFormat:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitGenericFileFormat(ctx: SqlBaseParser.GenericFileFormatContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitGenericFileFormat:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitStorageHandler(ctx: SqlBaseParser.StorageHandlerContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitStorageHandler:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitResource(ctx: SqlBaseParser.ResourceContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitResource:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSingleInsertQuery(ctx: SqlBaseParser.SingleInsertQueryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSingleInsertQuery:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitMultiInsertQuery(ctx: SqlBaseParser.MultiInsertQueryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitMultiInsertQuery:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQueryOrganization(ctx: SqlBaseParser.QueryOrganizationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQueryOrganization:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitMultiInsertQueryBody(ctx: SqlBaseParser.MultiInsertQueryBodyContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitMultiInsertQueryBody:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQueryTermDefault(ctx: SqlBaseParser.QueryTermDefaultContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQueryTermDefault:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSetOperation(ctx: SqlBaseParser.SetOperationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSetOperation:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQueryPrimaryDefault(ctx: SqlBaseParser.QueryPrimaryDefaultContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQueryPrimaryDefault:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTable(ctx: SqlBaseParser.TableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitInlineTableDefault1(ctx: SqlBaseParser.InlineTableDefault1Context): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitInlineTableDefault1:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSubquery(ctx: SqlBaseParser.SubqueryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSubquery:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSortItem(ctx: SqlBaseParser.SortItemContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSortItem:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQuerySpecification(ctx: SqlBaseParser.QuerySpecificationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQuerySpecification:\t " + aa)
    visitChildren(ctx)

    //Select Stop
    val viewName = "test"
    var sql: String =
      "SELECT " + ctx.namedExpressionSeq().getText + " " +
      "FROM " + viewName + " "
    var groupingColumnList : List[String] = List()
    val groupingExpressions = ctx.aggregation().groupingExpressions
    val it = groupingExpressions.iterator()
    while(it.hasNext){
      val item = it.next().getText
      groupingColumnList = item +: groupingColumnList
    }
    sql = sql + "GROUP BY " + groupingColumnList.mkString(",")

    val propertiesMap: Map[String, String] = Map("ViewName" -> viewName, "sql" -> sql)
    val map:Map[String, Any] = Map(
      "uuid" -> "1111",
      "name" -> "ExecuteSQL",
      "bundle" -> "com.piflow.bundle.common.ExecuteSQLStop",
      "properties" -> propertiesMap)
    val executeSQLStop = StopBean("test",map)

    //Path
    val Path = PathBean(currentStopBean.name,"","", executeSQLStop.name)

    flowBean.addStop(executeSQLStop)
    flowBean.addPath(Path)

    currentStopBean = executeSQLStop

    flowBean
  }

  override def visitFromClause(ctx: SqlBaseParser.FromClauseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitFromClause:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitAggregation(ctx: SqlBaseParser.AggregationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitAggregation:\t " + aa)

    /*//GroupBy Stop
    val propertiesMap: Map[String, String] = Map("columns" -> ctx.expression.getText)
    val map:Map[String, Any] = Map(
      "uuid" -> "1111",
      "name" -> "GroupBy",
      "bundle" -> "com.piflow.bundle.common.GroupBy",
      "properties" -> propertiesMap)
    val groupByStop = StopBean("test",map)
    currentStopBean = groupByStop
    //Path
    val Path = PathBean(currentStopBean.name,"","", groupByStop.name)


    flowBean.addStop(groupByStop)
    flowBean.addPath(Path)
*/
    visitChildren(ctx)
    flowBean
  }

  override def visitGroupingSet(ctx: SqlBaseParser.GroupingSetContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitGroupingSet:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitLateralView(ctx: SqlBaseParser.LateralViewContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitLateralView:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSetQuantifier(ctx: SqlBaseParser.SetQuantifierContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSetQuantifier:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRelation(ctx: SqlBaseParser.RelationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRelation:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitJoinRelation(ctx: SqlBaseParser.JoinRelationContext): FlowBean = {

    val text = ctx.getText
    println("visitJoinRelation:\t " + text)

    val flowBean = this.getFlowBeanInstance
    //left stop
    val left = ctx.parent.getChild(0).getText
    val leftStop = RegisterDataSource.getDataSourceStopBean(left)

    //right stop
    val right = ctx.right.getText
    val rightStop = RegisterDataSource.getDataSourceStopBean(right)

    //join Stop
    //val correlationField = ctx.joinCriteria.booleanExpression.getText//TODO: need modify
    val correlationField = "id"
    val propertiesMap: Map[String, String] = Map("join" -> ctx.joinType.getText, "correlationField" -> correlationField)
    val map:Map[String, Any] = Map(
      "uuid" -> "1111",
      "name" -> "join",
      "bundle" -> "com.piflow.bundle.common.join",
      "properties" -> propertiesMap)
    val joinStop = StopBean("test",map)
    currentStopBean = joinStop

    //left Path
    val leftPath = PathBean(leftStop.name,"","Left", joinStop.name)

    //right Path
    val rightPath = PathBean(rightStop.name,"","Right",joinStop.name)

    flowBean.addStop(leftStop)
    flowBean.addStop(rightStop)
    flowBean.addStop(joinStop)
    flowBean.addPath(leftPath)
    flowBean.addPath(rightPath)

    visitChildren(ctx)
    flowBean
  }

  override def visitJoinType(ctx: SqlBaseParser.JoinTypeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitJoinType:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitJoinCriteria(ctx: SqlBaseParser.JoinCriteriaContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitJoinCriteria:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSample(ctx: SqlBaseParser.SampleContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSample:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIdentifierList(ctx: SqlBaseParser.IdentifierListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIdentifierList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIdentifierSeq(ctx: SqlBaseParser.IdentifierSeqContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIdentifierSeq:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitOrderedIdentifierList(ctx: SqlBaseParser.OrderedIdentifierListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitOrderedIdentifierList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitOrderedIdentifier(ctx: SqlBaseParser.OrderedIdentifierContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitOrderedIdentifier:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIdentifierCommentList(ctx: SqlBaseParser.IdentifierCommentListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIdentifierCommentList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIdentifierComment(ctx: SqlBaseParser.IdentifierCommentContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIdentifierComment:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTableName(ctx: SqlBaseParser.TableNameContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTableName:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitAliasedQuery(ctx: SqlBaseParser.AliasedQueryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitAliasedQuery:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitAliasedRelation(ctx: SqlBaseParser.AliasedRelationContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitAliasedRelation:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitInlineTableDefault2(ctx: SqlBaseParser.InlineTableDefault2Context): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitInlineTableDefault2:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTableValuedFunction(ctx: SqlBaseParser.TableValuedFunctionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTableValueFunction:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitInlineTable(ctx: SqlBaseParser.InlineTableContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitInlineTable:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRowFormatSerde(ctx: SqlBaseParser.RowFormatSerdeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRowFormatSerde:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRowFormatDelimited(ctx: SqlBaseParser.RowFormatDelimitedContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRowFormatDelimited:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTableIdentifier(ctx: SqlBaseParser.TableIdentifierContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTableIdentifier:\t table=" + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNamedExpression(ctx: SqlBaseParser.NamedExpressionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNamedExpression:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNamedExpressionSeq(ctx: SqlBaseParser.NamedExpressionSeqContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNamedExpressionSeq:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitExpression(ctx: SqlBaseParser.ExpressionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitExpression:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitLogicalNot(ctx: SqlBaseParser.LogicalNotContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitLogicalNot:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitBooleanDefault(ctx: SqlBaseParser.BooleanDefaultContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitBooleanDefault:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitExists(ctx: SqlBaseParser.ExistsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitExists:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitLogicalBinary(ctx: SqlBaseParser.LogicalBinaryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitLogicalBinary:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitPredicated(ctx: SqlBaseParser.PredicatedContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitPredicated:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitPredicate(ctx: SqlBaseParser.PredicateContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitPredicate:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitValueExpressionDefault(ctx: SqlBaseParser.ValueExpressionDefaultContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitValueExpressionDefault:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitComparison(ctx: SqlBaseParser.ComparisonContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitComparison:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitArithmeticBinary(ctx: SqlBaseParser.ArithmeticBinaryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitArithmeticBinary:\t operator=" + ctx.operator.getText + ctx.operator.getType)
    visitChildren(ctx)
    flowBean
  }

  override def visitArithmeticUnary(ctx: SqlBaseParser.ArithmeticUnaryContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitArithmeticUnary:\t " + ctx.operator)
    visitChildren(ctx)
    flowBean
  }

  override def visitDereference(ctx: SqlBaseParser.DereferenceContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDereference:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSimpleCase(ctx: SqlBaseParser.SimpleCaseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSimpleCase:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitColumnReference(ctx: SqlBaseParser.ColumnReferenceContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitColumnReference:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitRowConstructor(ctx: SqlBaseParser.RowConstructorContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitRowConstructor:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitStar(ctx: SqlBaseParser.StarContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitStar:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSubscript(ctx: SqlBaseParser.SubscriptContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSubscript:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTimeFunctionCall(ctx: SqlBaseParser.TimeFunctionCallContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTimeFunctionCall:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSubqueryExpression(ctx: SqlBaseParser.SubqueryExpressionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSubqueryExpression:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitCast(ctx: SqlBaseParser.CastContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitCast:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitConstantDefault(ctx: SqlBaseParser.ConstantDefaultContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitConstantDefault:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitParenthesizedExpression(ctx: SqlBaseParser.ParenthesizedExpressionContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitParenthesizedExpression:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitFunctionCall(ctx: SqlBaseParser.FunctionCallContext): FlowBean = {
    System.out.println("visitFunctionCall:\t " + ctx.getText + " | qualifiedName=" + ctx.qualifiedName.getText + ctx.expression(0).getText)
    visitChildren(ctx)
    flowBean
  }

  override def visitSearchedCase(ctx: SqlBaseParser.SearchedCaseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSearchedCase:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNullLiteral(ctx: SqlBaseParser.NullLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNullLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIntervalLiteral(ctx: SqlBaseParser.IntervalLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIntervalLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTypeConstructor(ctx: SqlBaseParser.TypeConstructorContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTypeConstructor:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNumericLiteral(ctx: SqlBaseParser.NumericLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNumericLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitBooleanLiteral(ctx: SqlBaseParser.BooleanLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitBooleanLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitStringLiteral(ctx: SqlBaseParser.StringLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitStringLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitComparisonOperator(ctx: SqlBaseParser.ComparisonOperatorContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitComparisonOperator:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitArithmeticOperator(ctx: SqlBaseParser.ArithmeticOperatorContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitArithmeticOperator:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitPredicateOperator(ctx: SqlBaseParser.PredicateOperatorContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitPredicateOperator:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitBooleanValue(ctx: SqlBaseParser.BooleanValueContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitBooleanValue:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitInterval(ctx: SqlBaseParser.IntervalContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitInterval:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIntervalField(ctx: SqlBaseParser.IntervalFieldContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIntervalField:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIntervalValue(ctx: SqlBaseParser.IntervalValueContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIntervalValue:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitComplexDataType(ctx: SqlBaseParser.ComplexDataTypeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitComplexDataType:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitPrimitiveDataType(ctx: SqlBaseParser.PrimitiveDataTypeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitPrimitiveDataType:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitColTypeList(ctx: SqlBaseParser.ColTypeListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitColTypeList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitColType(ctx: SqlBaseParser.ColTypeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitColType:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitComplexColTypeList(ctx: SqlBaseParser.ComplexColTypeListContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitComplexColTypeList:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitComplexColType(ctx: SqlBaseParser.ComplexColTypeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitComplexColType:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitWhenClause(ctx: SqlBaseParser.WhenClauseContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitWhenClause:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitWindows(ctx: SqlBaseParser.WindowsContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitWindows:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNamedWindow(ctx: SqlBaseParser.NamedWindowContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNamedWindow:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitWindowRef(ctx: SqlBaseParser.WindowRefContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitWindowRef:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitWindowDef(ctx: SqlBaseParser.WindowDefContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitWindowDef:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitWindowFrame(ctx: SqlBaseParser.WindowFrameContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitWindowFrame:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitFrameBound(ctx: SqlBaseParser.FrameBoundContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitFrameBound:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQualifiedName(ctx: SqlBaseParser.QualifiedNameContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQualifiedName:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIdentifier(ctx: SqlBaseParser.IdentifierContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIdentifier:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitUnquotedIdentifier(ctx: SqlBaseParser.UnquotedIdentifierContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitUnquotedIdentifier:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQuotedIdentifierAlternative(ctx: SqlBaseParser.QuotedIdentifierAlternativeContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQuotedIdentifierAlternative:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitQuotedIdentifier(ctx: SqlBaseParser.QuotedIdentifierContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitQuotedIdentifer:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDecimalLiteral(ctx: SqlBaseParser.DecimalLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDecimalLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitIntegerLiteral(ctx: SqlBaseParser.IntegerLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitIntegerLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitBigIntLiteral(ctx: SqlBaseParser.BigIntLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitBigIntLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitSmallIntLiteral(ctx: SqlBaseParser.SmallIntLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitSmallIntLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitTinyIntLiteral(ctx: SqlBaseParser.TinyIntLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitTinyIntLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitDoubleLiteral(ctx: SqlBaseParser.DoubleLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitDoubleLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitBigDecimalLiteral(ctx: SqlBaseParser.BigDecimalLiteralContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitBigDecimalLiteral:\t " + aa)
    visitChildren(ctx)
    flowBean
  }

  override def visitNonReserved(ctx: SqlBaseParser.NonReservedContext): FlowBean = {
    val aa = ctx.getText
    System.out.println("visitNonReserved:\t " + aa)
    visitChildren(ctx)
    flowBean
  }



}
