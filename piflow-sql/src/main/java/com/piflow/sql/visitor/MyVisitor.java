package com.piflow.sql.visitor;


import com.piflow.sql.out.SqlBaseBaseVisitor;
import com.piflow.sql.out.SqlBaseParser;

public class MyVisitor extends SqlBaseBaseVisitor<String> {

    //TODO: return flow json
    public String visitSingleStatement(SqlBaseParser.SingleStatementContext ctx) {

        String  aa = ctx.getText();
        System.out.println("visitSingleStatement:\t "+aa);
        return visitChildren(ctx);
    }

    public String visitSingleExpression(SqlBaseParser.SingleExpressionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSingleExpression:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitSingleTableIdentifier(SqlBaseParser.SingleTableIdentifierContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSingleTableIdentifier:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitSingleDataType(SqlBaseParser.SingleDataTypeContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSingleDataType:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitStatementDefault(SqlBaseParser.StatementDefaultContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitStatementDefault:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitUse(SqlBaseParser.UseContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitUse:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitCreateDatabase(SqlBaseParser.CreateDatabaseContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateDatabase:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitSetDatabaseProperties(SqlBaseParser.SetDatabasePropertiesContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSetDatabaseProperties:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitDropDatabase(SqlBaseParser.DropDatabaseContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDropDatabase:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitCreateTableUsing(SqlBaseParser.CreateTableUsingContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateTableUsing:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitCreateTable(SqlBaseParser.CreateTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateTable:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitCreateTableLike(SqlBaseParser.CreateTableLikeContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateTableLike:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitAnalyze(SqlBaseParser.AnalyzeContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitAnalyze:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitRenameTable(SqlBaseParser.RenameTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRenameTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSetTableProperties(SqlBaseParser.SetTablePropertiesContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSetTableProperties:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitUnsetTableProperties(SqlBaseParser.UnsetTablePropertiesContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitUnsetTableProperties:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSetTableSerDe(SqlBaseParser.SetTableSerDeContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSetTableSerDe:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitAddTablePartition(SqlBaseParser.AddTablePartitionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitAddTablePartition:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitRenameTablePartition(SqlBaseParser.RenameTablePartitionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRenameTablePartition:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDropTablePartitions(SqlBaseParser.DropTablePartitionsContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSDropTablePartitions:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSetTableLocation(SqlBaseParser.SetTableLocationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSetTableLocation:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitRecoverPartitions(SqlBaseParser.RecoverPartitionsContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRecoverPartitions:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDropTable(SqlBaseParser.DropTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDropTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCreateView(SqlBaseParser.CreateViewContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateView:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCreateTempViewUsing(SqlBaseParser.CreateTempViewUsingContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateTempViewUsing:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitAlterViewQuery(SqlBaseParser.AlterViewQueryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitAlterViewQuery:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCreateFunction(SqlBaseParser.CreateFunctionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateFunction:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDropFunction(SqlBaseParser.DropFunctionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDropFunction:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitExplain(SqlBaseParser.ExplainContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitExplain:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitShowTables(SqlBaseParser.ShowTablesContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitShowTables:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitShowDatabases(SqlBaseParser.ShowDatabasesContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitShowDatabases:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitShowTblProperties(SqlBaseParser.ShowTblPropertiesContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitShowTblProperties:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitShowColumns(SqlBaseParser.ShowColumnsContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitShowColumns:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitShowPartitions(SqlBaseParser.ShowPartitionsContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitShowPartitions:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitShowFunctions(SqlBaseParser.ShowFunctionsContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitShowFunctions:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitShowCreateTable(SqlBaseParser.ShowCreateTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitShowCreateTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDescribeFunction(SqlBaseParser.DescribeFunctionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDescribeFunction:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDescribeDatabase(SqlBaseParser.DescribeDatabaseContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDescribeDatabase:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDescribeTable(SqlBaseParser.DescribeTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDescribeTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitRefreshTable(SqlBaseParser.RefreshTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRefreshTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitRefreshResource(SqlBaseParser.RefreshResourceContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRefreshResource:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCacheTable(SqlBaseParser.CacheTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCacheTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitUncacheTable(SqlBaseParser.UncacheTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitUncacheTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitClearCache(SqlBaseParser.ClearCacheContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitClearCache:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitLoadData(SqlBaseParser.LoadDataContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitLoadData:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTruncateTable(SqlBaseParser.TruncateTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTruncateTable:\t	 "+ aa);
        return visitChildren(ctx);
    }

    public String visitRepairTable(SqlBaseParser.RepairTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRepairTable:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitManageResource(SqlBaseParser.ManageResourceContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitManageResource:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitFailNativeCommand(SqlBaseParser.FailNativeCommandContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitFailNativeCommand:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSetConfiguration(SqlBaseParser.SetConfigurationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSetConfiguration:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitResetConfiguration(SqlBaseParser.ResetConfigurationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitResetConfiguration:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitUnsupportedHiveNativeCommands(SqlBaseParser.UnsupportedHiveNativeCommandsContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitUnsupportedHiveNativeCommand:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCreateTableHeader(SqlBaseParser.CreateTableHeaderContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateTableHeader:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitBucketSpec(SqlBaseParser.BucketSpecContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitBucketSpec:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSkewSpec(SqlBaseParser.SkewSpecContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSkewSpec:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitLocationSpec(SqlBaseParser.LocationSpecContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitLocationSpec:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQuery(SqlBaseParser.QueryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitQuery:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitInsertInto(SqlBaseParser.InsertIntoContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitInsertInto:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitPartitionSpecLocation(SqlBaseParser.PartitionSpecLocationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitPartitionSpecLocation:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitPartitionSpec(SqlBaseParser.PartitionSpecContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitPartitionSpec:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitPartitionVal(SqlBaseParser.PartitionValContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitPartitionVal:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDescribeFuncName(SqlBaseParser.DescribeFuncNameContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDescribeFuncName:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDescribeColName(SqlBaseParser.DescribeColNameContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDescribeColName:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCtes(SqlBaseParser.CtesContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCtes:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitNamedQuery(SqlBaseParser.NamedQueryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitNamedQuery:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTableProvider(SqlBaseParser.TableProviderContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTableProvider:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitTablePropertyList(SqlBaseParser.TablePropertyListContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTablePropertyList:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTableProperty(SqlBaseParser.TablePropertyContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTableProperty:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTablePropertyKey(SqlBaseParser.TablePropertyKeyContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTablePropertyKey:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTablePropertyValue(SqlBaseParser.TablePropertyValueContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTablePropertyValue:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitConstantList(SqlBaseParser.ConstantListContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitConstantList:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitNestedConstantList(SqlBaseParser.NestedConstantListContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitNestedConstantList:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCreateFileFormat(SqlBaseParser.CreateFileFormatContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCreateFileFormat:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitTableFileFormat(SqlBaseParser.TableFileFormatContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTableFileFormat:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitGenericFileFormat(SqlBaseParser.GenericFileFormatContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitGenericFileFormat:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitStorageHandler(SqlBaseParser.StorageHandlerContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitStorageHandler:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitResource(SqlBaseParser.ResourceContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitResource:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSingleInsertQuery(SqlBaseParser.SingleInsertQueryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSingleInsertQuery:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitMultiInsertQuery(SqlBaseParser.MultiInsertQueryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitMultiInsertQuery:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQueryOrganization(SqlBaseParser.QueryOrganizationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitQueryOrganization:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitMultiInsertQueryBody(SqlBaseParser.MultiInsertQueryBodyContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitMultiInsertQueryBody:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQueryTermDefault(SqlBaseParser.QueryTermDefaultContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitQueryTermDefault:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSetOperation(SqlBaseParser.SetOperationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSetOperation:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQueryPrimaryDefault(SqlBaseParser.QueryPrimaryDefaultContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitQueryPrimaryDefault:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTable(SqlBaseParser.TableContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitTable:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitInlineTableDefault1(SqlBaseParser.InlineTableDefault1Context ctx) {
        String  aa = ctx.getText();
        System.out.println("visitInlineTableDefault1:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSubquery(SqlBaseParser.SubqueryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSubquery:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSortItem(SqlBaseParser.SortItemContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSortItem:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQuerySpecification(SqlBaseParser.QuerySpecificationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitQuerySpecification:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitFromClause(SqlBaseParser.FromClauseContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitFromClause:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitAggregation(SqlBaseParser.AggregationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitAggregation:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitGroupingSet(SqlBaseParser.GroupingSetContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitGroupingSet:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitLateralView(SqlBaseParser.LateralViewContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitLateralView:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSetQuantifier(SqlBaseParser.SetQuantifierContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSetQuantifier:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitRelation(SqlBaseParser.RelationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRelation:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitJoinRelation(SqlBaseParser.JoinRelationContext ctx) {
        String  aa = ctx.getText();

        System.out.println("visitJoinRelation:\t "+ aa);
        //System.out.println("visitJoinRelation right: "+ ctx.right);
        //System.out.println("visitJoinRelation joinType: "+ ctx.joinType());

        return visitChildren(ctx);
    }

    public String visitJoinType(SqlBaseParser.JoinTypeContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitJoinType:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitJoinCriteria(SqlBaseParser.JoinCriteriaContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitJoinCriteria:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitSample(SqlBaseParser.SampleContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSample:\t "+ aa);
        return visitChildren(ctx);
    }

    public String visitIdentifierList(SqlBaseParser.IdentifierListContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitIdentifierList:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitIdentifierSeq(SqlBaseParser.IdentifierSeqContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitIdentifierSeq:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitOrderedIdentifierList(SqlBaseParser.OrderedIdentifierListContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitOrderedIdentifierList:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitOrderedIdentifier(SqlBaseParser.OrderedIdentifierContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitOrderedIdentifier:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitIdentifierCommentList(SqlBaseParser.IdentifierCommentListContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitIdentifierCommentList:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitIdentifierComment(SqlBaseParser.IdentifierCommentContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitIdentifierComment:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitTableName(SqlBaseParser.TableNameContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTableName:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitAliasedQuery(SqlBaseParser.AliasedQueryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitAliasedQuery:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitAliasedRelation(SqlBaseParser.AliasedRelationContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitAliasedRelation:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitInlineTableDefault2(SqlBaseParser.InlineTableDefault2Context ctx) {
        String  aa = ctx.getText();
        System.out.println("visitInlineTableDefault2:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitTableValuedFunction(SqlBaseParser.TableValuedFunctionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTableValueFunction:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitInlineTable(SqlBaseParser.InlineTableContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitInlineTable:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitRowFormatSerde(SqlBaseParser.RowFormatSerdeContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRowFormatSerde:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitRowFormatDelimited(SqlBaseParser.RowFormatDelimitedContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRowFormatDelimited:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitTableIdentifier(SqlBaseParser.TableIdentifierContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitTableIdentifier:\t table=" + aa);
        return visitChildren(ctx);
    }

    public String visitNamedExpression(SqlBaseParser.NamedExpressionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitNamedExpression:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitNamedExpressionSeq(SqlBaseParser.NamedExpressionSeqContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitNamedExpressionSeq:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitExpression(SqlBaseParser.ExpressionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitExpression:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitLogicalNot(SqlBaseParser.LogicalNotContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitLogicalNot:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitBooleanDefault(SqlBaseParser.BooleanDefaultContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitBooleanDefault:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitExists(SqlBaseParser.ExistsContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitExists:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitLogicalBinary(SqlBaseParser.LogicalBinaryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitLogicalBinary:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitPredicated(SqlBaseParser.PredicatedContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitPredicated:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitPredicate(SqlBaseParser.PredicateContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitPredicate:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitValueExpressionDefault(SqlBaseParser.ValueExpressionDefaultContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitValueExpressionDefault:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitComparison(SqlBaseParser.ComparisonContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitComparison:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitArithmeticBinary(SqlBaseParser.ArithmeticBinaryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitArithmeticBinary:\t operator=" + ctx.operator.getText() + ctx.operator.getType());
        return visitChildren(ctx);
    }

    public String visitArithmeticUnary(SqlBaseParser.ArithmeticUnaryContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitArithmeticUnary:\t " + ctx.operator);
        return visitChildren(ctx);
    }

    public String visitDereference(SqlBaseParser.DereferenceContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitDereference:\t "  + aa);
        return visitChildren(ctx);
    }
    
    public String visitSimpleCase(SqlBaseParser.SimpleCaseContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSimpleCase:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitColumnReference(SqlBaseParser.ColumnReferenceContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitColumnReference:\t "+aa);
        return visitChildren(ctx);
    }

    public String visitRowConstructor(SqlBaseParser.RowConstructorContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitRowConstructor:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitStar(SqlBaseParser.StarContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitStar:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSubscript(SqlBaseParser.SubscriptContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSubscript:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTimeFunctionCall(SqlBaseParser.TimeFunctionCallContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTimeFunctionCall:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSubqueryExpression(SqlBaseParser.SubqueryExpressionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSubqueryExpression:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitCast(SqlBaseParser.CastContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitCast:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitConstantDefault(SqlBaseParser.ConstantDefaultContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitConstantDefault:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitParenthesizedExpression(SqlBaseParser.ParenthesizedExpressionContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitParenthesizedExpression:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitFunctionCall(SqlBaseParser.FunctionCallContext ctx) {
        System.out.println("visitFunctionCall:\t " + ctx.getText() + " | qualifiedName="
                + ctx.qualifiedName().getText() + ctx.expression(0).getText());
        return visitChildren(ctx);
    }

    public String visitSearchedCase(SqlBaseParser.SearchedCaseContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitSearchedCase:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitNullLiteral(SqlBaseParser.NullLiteralContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitNullLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitIntervalLiteral(SqlBaseParser.IntervalLiteralContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitIntervalLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTypeConstructor(SqlBaseParser.TypeConstructorContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitTypeConstructor:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitNumericLiteral(SqlBaseParser.NumericLiteralContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitNumericLiteral:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitBooleanLiteral(SqlBaseParser.BooleanLiteralContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitBooleanLiteral:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitStringLiteral(SqlBaseParser.StringLiteralContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitStringLiteral:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitComparisonOperator(SqlBaseParser.ComparisonOperatorContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitComparisonOperator:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitArithmeticOperator(SqlBaseParser.ArithmeticOperatorContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitArithmeticOperator:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitPredicateOperator(SqlBaseParser.PredicateOperatorContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitPredicateOperator:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitBooleanValue(SqlBaseParser.BooleanValueContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitBooleanValue:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitInterval(SqlBaseParser.IntervalContext ctx) {
        String  aa = ctx.getText();
        System.out.println("visitInterval:\t "  + aa);
        return visitChildren(ctx);
    }

    public String visitIntervalField(SqlBaseParser.IntervalFieldContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitIntervalField:\t "+aa);
        return visitChildren(ctx);
    }

    public String visitIntervalValue(SqlBaseParser.IntervalValueContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitIntervalValue:\t "+aa);
        return visitChildren(ctx);
    }

    public String visitComplexDataType(SqlBaseParser.ComplexDataTypeContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitComplexDataType:\t "+aa);
        return visitChildren(ctx);
    }

    public String visitPrimitiveDataType(SqlBaseParser.PrimitiveDataTypeContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitPrimitiveDataType:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitColTypeList(SqlBaseParser.ColTypeListContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitColTypeList:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitColType(SqlBaseParser.ColTypeContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitColType:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitComplexColTypeList(SqlBaseParser.ComplexColTypeListContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitComplexColTypeList:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitComplexColType(SqlBaseParser.ComplexColTypeContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitComplexColType:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitWhenClause(SqlBaseParser.WhenClauseContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitWhenClause:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitWindows(SqlBaseParser.WindowsContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitWindows:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitNamedWindow(SqlBaseParser.NamedWindowContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitNamedWindow:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitWindowRef(SqlBaseParser.WindowRefContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitWindowRef:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitWindowDef(SqlBaseParser.WindowDefContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitWindowDef:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitWindowFrame(SqlBaseParser.WindowFrameContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitWindowFrame:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitFrameBound(SqlBaseParser.FrameBoundContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitFrameBound:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQualifiedName(SqlBaseParser.QualifiedNameContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitQualifiedName:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitIdentifier(SqlBaseParser.IdentifierContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitIdentifier:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitUnquotedIdentifier(SqlBaseParser.UnquotedIdentifierContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitUnquotedIdentifier:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQuotedIdentifierAlternative(SqlBaseParser.QuotedIdentifierAlternativeContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitQuotedIdentifierAlternative:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitQuotedIdentifier(SqlBaseParser.QuotedIdentifierContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitQuotedIdentifer:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDecimalLiteral(SqlBaseParser.DecimalLiteralContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitDecimalLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitIntegerLiteral(SqlBaseParser.IntegerLiteralContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitIntegerLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitBigIntLiteral(SqlBaseParser.BigIntLiteralContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitBigIntLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitSmallIntLiteral(SqlBaseParser.SmallIntLiteralContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitSmallIntLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitTinyIntLiteral(SqlBaseParser.TinyIntLiteralContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitTinyIntLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitDoubleLiteral(SqlBaseParser.DoubleLiteralContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitDoubleLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitBigDecimalLiteral(SqlBaseParser.BigDecimalLiteralContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitBigDecimalLiteral:\t " + aa);
        return visitChildren(ctx);
    }

    public String visitNonReserved(SqlBaseParser.NonReservedContext ctx) {
        String aa = ctx.getText();
        System.out.println("visitNonReserved:\t " + aa);
        return visitChildren(ctx);
    }


}