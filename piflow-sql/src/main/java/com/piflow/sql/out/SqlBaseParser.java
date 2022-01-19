// Generated from D:/Development/AntlrTest/src\SqlBase.g4 by ANTLR 4.5.3
package com.piflow.sql.out;

import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.atn.ATN;
import org.antlr.v4.runtime.atn.ATNDeserializer;
import org.antlr.v4.runtime.atn.ParserATNSimulator;
import org.antlr.v4.runtime.atn.PredictionContextCache;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.tree.ParseTreeListener;
import org.antlr.v4.runtime.tree.ParseTreeVisitor;
import org.antlr.v4.runtime.tree.TerminalNode;

import java.util.ArrayList;
import java.util.List;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast"})
public class SqlBaseParser extends Parser {
	static { RuntimeMetaData.checkVersion("4.5.3", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		T__0=1, T__1=2, T__2=3, T__3=4, T__4=5, T__5=6, T__6=7, SELECT=8, FROM=9, 
		ADD=10, AS=11, ALL=12, DISTINCT=13, WHERE=14, GROUP=15, BY=16, GROUPING=17, 
		SETS=18, CUBE=19, ROLLUP=20, ORDER=21, HAVING=22, LIMIT=23, AT=24, OR=25, 
		AND=26, IN=27, NOT=28, NO=29, EXISTS=30, BETWEEN=31, LIKE=32, RLIKE=33, 
		IS=34, NULL=35, TRUE=36, FALSE=37, NULLS=38, ASC=39, DESC=40, FOR=41, 
		INTERVAL=42, CASE=43, WHEN=44, THEN=45, ELSE=46, END=47, JOIN=48, CROSS=49, 
		OUTER=50, INNER=51, LEFT=52, SEMI=53, RIGHT=54, FULL=55, NATURAL=56, ON=57, 
		LATERAL=58, WINDOW=59, OVER=60, PARTITION=61, RANGE=62, ROWS=63, UNBOUNDED=64, 
		PRECEDING=65, FOLLOWING=66, CURRENT=67, FIRST=68, LAST=69, ROW=70, WITH=71, 
		VALUES=72, CREATE=73, TABLE=74, VIEW=75, REPLACE=76, INSERT=77, DELETE=78, 
		INTO=79, DESCRIBE=80, EXPLAIN=81, FORMAT=82, LOGICAL=83, CODEGEN=84, CAST=85, 
		SHOW=86, TABLES=87, COLUMNS=88, COLUMN=89, USE=90, PARTITIONS=91, FUNCTIONS=92, 
		DROP=93, UNION=94, EXCEPT=95, SETMINUS=96, INTERSECT=97, TO=98, TABLESAMPLE=99, 
		STRATIFY=100, ALTER=101, RENAME=102, ARRAY=103, MAP=104, STRUCT=105, COMMENT=106, 
		SET=107, RESET=108, DATA=109, START=110, TRANSACTION=111, COMMIT=112, 
		ROLLBACK=113, MACRO=114, IF=115, EQ=116, NSEQ=117, NEQ=118, NEQJ=119, 
		LT=120, LTE=121, GT=122, GTE=123, PLUS=124, MINUS=125, ASTERISK=126, SLASH=127, 
		PERCENT=128, DIV=129, TILDE=130, AMPERSAND=131, PIPE=132, HAT=133, RSHIFT=134, 
		PERCENTLIT=135, BUCKET=136, OUT=137, OF=138, SORT=139, CLUSTER=140, DISTRIBUTE=141, 
		OVERWRITE=142, TRANSFORM=143, REDUCE=144, USING=145, SERDE=146, SERDEPROPERTIES=147, 
		RECORDREADER=148, RECORDWRITER=149, DELIMITED=150, FIELDS=151, TERMINATED=152, 
		COLLECTION=153, ITEMS=154, KEYS=155, ESCAPED=156, LINES=157, SEPARATED=158, 
		FUNCTION=159, EXTENDED=160, REFRESH=161, CLEAR=162, CACHE=163, UNCACHE=164, 
		LAZY=165, FORMATTED=166, GLOBAL=167, TEMPORARY=168, OPTIONS=169, UNSET=170, 
		TBLPROPERTIES=171, DBPROPERTIES=172, BUCKETS=173, SKEWED=174, STORED=175, 
		DIRECTORIES=176, LOCATION=177, EXCHANGE=178, ARCHIVE=179, UNARCHIVE=180, 
		FILEFORMAT=181, TOUCH=182, COMPACT=183, CONCATENATE=184, CHANGE=185, CASCADE=186, 
		RESTRICT=187, CLUSTERED=188, SORTED=189, PURGE=190, INPUTFORMAT=191, OUTPUTFORMAT=192, 
		DATABASE=193, DATABASES=194, DFS=195, TRUNCATE=196, ANALYZE=197, COMPUTE=198, 
		LIST=199, STATISTICS=200, PARTITIONED=201, EXTERNAL=202, DEFINED=203, 
		REVOKE=204, GRANT=205, LOCK=206, UNLOCK=207, MSCK=208, REPAIR=209, RECOVER=210, 
		EXPORT=211, IMPORT=212, LOAD=213, ROLE=214, ROLES=215, COMPACTIONS=216, 
		PRINCIPALS=217, TRANSACTIONS=218, INDEX=219, INDEXES=220, LOCKS=221, OPTION=222, 
		ANTI=223, LOCAL=224, INPATH=225, CURRENT_DATE=226, CURRENT_TIMESTAMP=227, 
		STRING=228, BIGINT_LITERAL=229, SMALLINT_LITERAL=230, TINYINT_LITERAL=231, 
		BYTELENGTH_LITERAL=232, INTEGER_VALUE=233, DECIMAL_VALUE=234, DOUBLE_LITERAL=235, 
		BIGDECIMAL_LITERAL=236, IDENTIFIER=237, BACKQUOTED_IDENTIFIER=238, SIMPLE_COMMENT=239, 
		BRACKETED_COMMENT=240, WS=241, UNRECOGNIZED=242, DELIMITER=243;
	public static final int
		RULE_singleStatement = 0, RULE_singleExpression = 1, RULE_singleTableIdentifier = 2, 
		RULE_singleDataType = 3, RULE_statement = 4, RULE_unsupportedHiveNativeCommands = 5, 
		RULE_createTableHeader = 6, RULE_bucketSpec = 7, RULE_skewSpec = 8, RULE_locationSpec = 9, 
		RULE_query = 10, RULE_insertInto = 11, RULE_partitionSpecLocation = 12, 
		RULE_partitionSpec = 13, RULE_partitionVal = 14, RULE_describeFuncName = 15, 
		RULE_describeColName = 16, RULE_ctes = 17, RULE_namedQuery = 18, RULE_tableProvider = 19, 
		RULE_tablePropertyList = 20, RULE_tableProperty = 21, RULE_tablePropertyKey = 22, 
		RULE_tablePropertyValue = 23, RULE_constantList = 24, RULE_nestedConstantList = 25, 
		RULE_createFileFormat = 26, RULE_fileFormat = 27, RULE_storageHandler = 28, 
		RULE_resource = 29, RULE_queryNoWith = 30, RULE_queryOrganization = 31, 
		RULE_multiInsertQueryBody = 32, RULE_queryTerm = 33, RULE_queryPrimary = 34, 
		RULE_sortItem = 35, RULE_querySpecification = 36, RULE_fromClause = 37, 
		RULE_aggregation = 38, RULE_groupingSet = 39, RULE_lateralView = 40, RULE_setQuantifier = 41, 
		RULE_relation = 42, RULE_joinRelation = 43, RULE_joinType = 44, RULE_joinCriteria = 45, 
		RULE_sample = 46, RULE_identifierList = 47, RULE_identifierSeq = 48, RULE_orderedIdentifierList = 49, 
		RULE_orderedIdentifier = 50, RULE_identifierCommentList = 51, RULE_identifierComment = 52, 
		RULE_relationPrimary = 53, RULE_inlineTable = 54, RULE_rowFormat = 55, 
		RULE_tableIdentifier = 56, RULE_namedExpression = 57, RULE_namedExpressionSeq = 58, 
		RULE_expression = 59, RULE_booleanExpression = 60, RULE_predicated = 61, 
		RULE_predicate = 62, RULE_valueExpression = 63, RULE_primaryExpression = 64, 
		RULE_constant = 65, RULE_comparisonOperator = 66, RULE_arithmeticOperator = 67, 
		RULE_predicateOperator = 68, RULE_booleanValue = 69, RULE_interval = 70, 
		RULE_intervalField = 71, RULE_intervalValue = 72, RULE_dataType = 73, 
		RULE_colTypeList = 74, RULE_colType = 75, RULE_complexColTypeList = 76, 
		RULE_complexColType = 77, RULE_whenClause = 78, RULE_windows = 79, RULE_namedWindow = 80, 
		RULE_windowSpec = 81, RULE_windowFrame = 82, RULE_frameBound = 83, RULE_qualifiedName = 84, 
		RULE_identifier = 85, RULE_strictIdentifier = 86, RULE_quotedIdentifier = 87, 
		RULE_number = 88, RULE_nonReserved = 89;
	public static final String[] ruleNames = {
		"singleStatement", "singleExpression", "singleTableIdentifier", "singleDataType", 
		"statement", "unsupportedHiveNativeCommands", "createTableHeader", "bucketSpec", 
		"skewSpec", "locationSpec", "query", "insertInto", "partitionSpecLocation", 
		"partitionSpec", "partitionVal", "describeFuncName", "describeColName", 
		"ctes", "namedQuery", "tableProvider", "tablePropertyList", "tableProperty", 
		"tablePropertyKey", "tablePropertyValue", "constantList", "nestedConstantList", 
		"createFileFormat", "fileFormat", "storageHandler", "resource", "queryNoWith", 
		"queryOrganization", "multiInsertQueryBody", "queryTerm", "queryPrimary", 
		"sortItem", "querySpecification", "fromClause", "aggregation", "groupingSet", 
		"lateralView", "setQuantifier", "relation", "joinRelation", "joinType", 
		"joinCriteria", "sample", "identifierList", "identifierSeq", "orderedIdentifierList", 
		"orderedIdentifier", "identifierCommentList", "identifierComment", "relationPrimary", 
		"inlineTable", "rowFormat", "tableIdentifier", "namedExpression", "namedExpressionSeq", 
		"expression", "booleanExpression", "predicated", "predicate", "valueExpression", 
		"primaryExpression", "constant", "comparisonOperator", "arithmeticOperator", 
		"predicateOperator", "booleanValue", "interval", "intervalField", "intervalValue", 
		"dataType", "colTypeList", "colType", "complexColTypeList", "complexColType", 
		"whenClause", "windows", "namedWindow", "windowSpec", "windowFrame", "frameBound", 
		"qualifiedName", "identifier", "strictIdentifier", "quotedIdentifier", 
		"number", "nonReserved"
	};

	private static final String[] _LITERAL_NAMES = {
		null, "'('", "')'", "','", "'.'", "'['", "']'", "':'", "'SELECT'", "'FROM'", 
		"'ADD'", "'AS'", "'ALL'", "'DISTINCT'", "'WHERE'", "'GROUP'", "'BY'", 
		"'GROUPING'", "'SETS'", "'CUBE'", "'ROLLUP'", "'ORDER'", "'HAVING'", "'LIMIT'", 
		"'AT'", "'OR'", "'AND'", "'IN'", null, "'NO'", "'EXISTS'", "'BETWEEN'", 
		"'LIKE'", null, "'IS'", "'NULL'", "'TRUE'", "'FALSE'", "'NULLS'", "'ASC'", 
		"'DESC'", "'FOR'", "'INTERVAL'", "'CASE'", "'WHEN'", "'THEN'", "'ELSE'", 
		"'END'", "'JOIN'", "'CROSS'", "'OUTER'", "'INNER'", "'LEFT'", "'SEMI'", 
		"'RIGHT'", "'FULL'", "'NATURAL'", "'ON'", "'LATERAL'", "'WINDOW'", "'OVER'", 
		"'PARTITION'", "'RANGE'", "'ROWS'", "'UNBOUNDED'", "'PRECEDING'", "'FOLLOWING'", 
		"'CURRENT'", "'FIRST'", "'LAST'", "'ROW'", "'WITH'", "'VALUES'", "'CREATE'", 
		"'TABLE'", "'VIEW'", "'REPLACE'", "'INSERT'", "'DELETE'", "'INTO'", "'DESCRIBE'", 
		"'EXPLAIN'", "'FORMAT'", "'LOGICAL'", "'CODEGEN'", "'CAST'", "'SHOW'", 
		"'TABLES'", "'COLUMNS'", "'COLUMN'", "'USE'", "'PARTITIONS'", "'FUNCTIONS'", 
		"'DROP'", "'UNION'", "'EXCEPT'", "'MINUS'", "'INTERSECT'", "'TO'", "'TABLESAMPLE'", 
		"'STRATIFY'", "'ALTER'", "'RENAME'", "'ARRAY'", "'MAP'", "'STRUCT'", "'COMMENT'", 
		"'SET'", "'RESET'", "'DATA'", "'START'", "'TRANSACTION'", "'COMMIT'", 
		"'ROLLBACK'", "'MACRO'", "'IF'", null, "'<=>'", "'<>'", "'!='", "'<'", 
		null, "'>'", null, "'+'", "'-'", "'*'", null, "'%'", "'DIV'", "'~'", "'&'", 
		"'|'", "'^'", "'>>'", "'PERCENT'", "'BUCKET'", "'OUT'", "'OF'", "'SORT'", 
		"'CLUSTER'", "'DISTRIBUTE'", "'OVERWRITE'", "'TRANSFORM'", "'REDUCE'", 
		"'USING'", "'SERDE'", "'SERDEPROPERTIES'", "'RECORDREADER'", "'RECORDWRITER'", 
		"'DELIMITED'", "'FIELDS'", "'TERMINATED'", "'COLLECTION'", "'ITEMS'", 
		"'KEYS'", "'ESCAPED'", "'LINES'", "'SEPARATED'", "'FUNCTION'", "'EXTENDED'", 
		"'REFRESH'", "'CLEAR'", "'CACHE'", "'UNCACHE'", "'LAZY'", "'FORMATTED'", 
		"'GLOBAL'", null, "'OPTIONS'", "'UNSET'", "'TBLPROPERTIES'", "'DBPROPERTIES'", 
		"'BUCKETS'", "'SKEWED'", "'STORED'", "'DIRECTORIES'", "'LOCATION'", "'EXCHANGE'", 
		"'ARCHIVE'", "'UNARCHIVE'", "'FILEFORMAT'", "'TOUCH'", "'COMPACT'", "'CONCATENATE'", 
		"'CHANGE'", "'CASCADE'", "'RESTRICT'", "'CLUSTERED'", "'SORTED'", "'PURGE'", 
		"'INPUTFORMAT'", "'OUTPUTFORMAT'", null, null, "'DFS'", "'TRUNCATE'", 
		"'ANALYZE'", "'COMPUTE'", "'LIST'", "'STATISTICS'", "'PARTITIONED'", "'EXTERNAL'", 
		"'DEFINED'", "'REVOKE'", "'GRANT'", "'LOCK'", "'UNLOCK'", "'MSCK'", "'REPAIR'", 
		"'RECOVER'", "'EXPORT'", "'IMPORT'", "'LOAD'", "'ROLE'", "'ROLES'", "'COMPACTIONS'", 
		"'PRINCIPALS'", "'TRANSACTIONS'", "'INDEX'", "'INDEXES'", "'LOCKS'", "'OPTION'", 
		"'ANTI'", "'LOCAL'", "'INPATH'", "'CURRENT_DATE'", "'CURRENT_TIMESTAMP'"
	};
	private static final String[] _SYMBOLIC_NAMES = {
		null, null, null, null, null, null, null, null, "SELECT", "FROM", "ADD", 
		"AS", "ALL", "DISTINCT", "WHERE", "GROUP", "BY", "GROUPING", "SETS", "CUBE", 
		"ROLLUP", "ORDER", "HAVING", "LIMIT", "AT", "OR", "AND", "IN", "NOT", 
		"NO", "EXISTS", "BETWEEN", "LIKE", "RLIKE", "IS", "NULL", "TRUE", "FALSE", 
		"NULLS", "ASC", "DESC", "FOR", "INTERVAL", "CASE", "WHEN", "THEN", "ELSE", 
		"END", "JOIN", "CROSS", "OUTER", "INNER", "LEFT", "SEMI", "RIGHT", "FULL", 
		"NATURAL", "ON", "LATERAL", "WINDOW", "OVER", "PARTITION", "RANGE", "ROWS", 
		"UNBOUNDED", "PRECEDING", "FOLLOWING", "CURRENT", "FIRST", "LAST", "ROW", 
		"WITH", "VALUES", "CREATE", "TABLE", "VIEW", "REPLACE", "INSERT", "DELETE", 
		"INTO", "DESCRIBE", "EXPLAIN", "FORMAT", "LOGICAL", "CODEGEN", "CAST", 
		"SHOW", "TABLES", "COLUMNS", "COLUMN", "USE", "PARTITIONS", "FUNCTIONS", 
		"DROP", "UNION", "EXCEPT", "SETMINUS", "INTERSECT", "TO", "TABLESAMPLE", 
		"STRATIFY", "ALTER", "RENAME", "ARRAY", "MAP", "STRUCT", "COMMENT", "SET", 
		"RESET", "DATA", "START", "TRANSACTION", "COMMIT", "ROLLBACK", "MACRO", 
		"IF", "EQ", "NSEQ", "NEQ", "NEQJ", "LT", "LTE", "GT", "GTE", "PLUS", "MINUS", 
		"ASTERISK", "SLASH", "PERCENT", "DIV", "TILDE", "AMPERSAND", "PIPE", "HAT", 
		"RSHIFT", "PERCENTLIT", "BUCKET", "OUT", "OF", "SORT", "CLUSTER", "DISTRIBUTE", 
		"OVERWRITE", "TRANSFORM", "REDUCE", "USING", "SERDE", "SERDEPROPERTIES", 
		"RECORDREADER", "RECORDWRITER", "DELIMITED", "FIELDS", "TERMINATED", "COLLECTION", 
		"ITEMS", "KEYS", "ESCAPED", "LINES", "SEPARATED", "FUNCTION", "EXTENDED", 
		"REFRESH", "CLEAR", "CACHE", "UNCACHE", "LAZY", "FORMATTED", "GLOBAL", 
		"TEMPORARY", "OPTIONS", "UNSET", "TBLPROPERTIES", "DBPROPERTIES", "BUCKETS", 
		"SKEWED", "STORED", "DIRECTORIES", "LOCATION", "EXCHANGE", "ARCHIVE", 
		"UNARCHIVE", "FILEFORMAT", "TOUCH", "COMPACT", "CONCATENATE", "CHANGE", 
		"CASCADE", "RESTRICT", "CLUSTERED", "SORTED", "PURGE", "INPUTFORMAT", 
		"OUTPUTFORMAT", "DATABASE", "DATABASES", "DFS", "TRUNCATE", "ANALYZE", 
		"COMPUTE", "LIST", "STATISTICS", "PARTITIONED", "EXTERNAL", "DEFINED", 
		"REVOKE", "GRANT", "LOCK", "UNLOCK", "MSCK", "REPAIR", "RECOVER", "EXPORT", 
		"IMPORT", "LOAD", "ROLE", "ROLES", "COMPACTIONS", "PRINCIPALS", "TRANSACTIONS", 
		"INDEX", "INDEXES", "LOCKS", "OPTION", "ANTI", "LOCAL", "INPATH", "CURRENT_DATE", 
		"CURRENT_TIMESTAMP", "STRING", "BIGINT_LITERAL", "SMALLINT_LITERAL", "TINYINT_LITERAL", 
		"BYTELENGTH_LITERAL", "INTEGER_VALUE", "DECIMAL_VALUE", "DOUBLE_LITERAL", 
		"BIGDECIMAL_LITERAL", "IDENTIFIER", "BACKQUOTED_IDENTIFIER", "SIMPLE_COMMENT", 
		"BRACKETED_COMMENT", "WS", "UNRECOGNIZED", "DELIMITER"
	};
	public static final Vocabulary VOCABULARY = new VocabularyImpl(_LITERAL_NAMES, _SYMBOLIC_NAMES);

	/**
	 * @deprecated Use {@link #VOCABULARY} instead.
	 */
	@Deprecated
	public static final String[] tokenNames;
	static {
		tokenNames = new String[_SYMBOLIC_NAMES.length];
		for (int i = 0; i < tokenNames.length; i++) {
			tokenNames[i] = VOCABULARY.getLiteralName(i);
			if (tokenNames[i] == null) {
				tokenNames[i] = VOCABULARY.getSymbolicName(i);
			}

			if (tokenNames[i] == null) {
				tokenNames[i] = "<INVALID>";
			}
		}
	}

	@Override
	@Deprecated
	public String[] getTokenNames() {
		return tokenNames;
	}

	@Override

	public Vocabulary getVocabulary() {
		return VOCABULARY;
	}

	@Override
	public String getGrammarFileName() { return "SqlBase.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public ATN getATN() { return _ATN; }


	  /**
	   * Verify whether current token is a valid decimal token (which contains dot).
	   * Returns true if the character that follows the token is not a digit or letter or underscore.
	   *
	   * For example:
	   * For char stream "2.3", "2." is not a valid decimal token, because it is followed by digit '3'.
	   * For char stream "2.3_", "2.3" is not a valid decimal token, because it is followed by '_'.
	   * For char stream "2.3W", "2.3" is not a valid decimal token, because it is followed by 'W'.
	   * For char stream "12.0D 34.E2+0.12 "  12.0D is a valid decimal token because it is folllowed
	   * by a space. 34.E2 is a valid decimal token because it is followed by symbol '+'
	   * which is not a digit or letter or underscore.
	   */
	  public boolean isValidDecimal() {
	    int nextChar = _input.LA(1);
	    if (nextChar >= 'A' && nextChar <= 'Z' || nextChar >= '0' && nextChar <= '9' ||
	      nextChar == '_') {
	      return false;
	    } else {
	      return true;
	    }
	  }

	public SqlBaseParser(TokenStream input) {
		super(input);
		_interp = new ParserATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}
	public static class SingleStatementContext extends ParserRuleContext {
		public StatementContext statement() {
			return getRuleContext(StatementContext.class,0);
		}
		public TerminalNode EOF() { return getToken(SqlBaseParser.EOF, 0); }
		public SingleStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_singleStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSingleStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSingleStatement(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSingleStatement(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SingleStatementContext singleStatement() throws RecognitionException {
		SingleStatementContext _localctx = new SingleStatementContext(_ctx, getState());
		enterRule(_localctx, 0, RULE_singleStatement);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(180);
			statement();
			setState(181);
			match(EOF);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class SingleExpressionContext extends ParserRuleContext {
		public NamedExpressionContext namedExpression() {
			return getRuleContext(NamedExpressionContext.class,0);
		}
		public TerminalNode EOF() { return getToken(SqlBaseParser.EOF, 0); }
		public SingleExpressionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_singleExpression; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSingleExpression(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSingleExpression(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSingleExpression(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SingleExpressionContext singleExpression() throws RecognitionException {
		SingleExpressionContext _localctx = new SingleExpressionContext(_ctx, getState());
		enterRule(_localctx, 2, RULE_singleExpression);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(183);
			namedExpression();
			setState(184);
			match(EOF);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class SingleTableIdentifierContext extends ParserRuleContext {
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode EOF() { return getToken(SqlBaseParser.EOF, 0); }
		public SingleTableIdentifierContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_singleTableIdentifier; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSingleTableIdentifier(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSingleTableIdentifier(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSingleTableIdentifier(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SingleTableIdentifierContext singleTableIdentifier() throws RecognitionException {
		SingleTableIdentifierContext _localctx = new SingleTableIdentifierContext(_ctx, getState());
		enterRule(_localctx, 4, RULE_singleTableIdentifier);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(186);
			tableIdentifier();
			setState(187);
			match(EOF);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class SingleDataTypeContext extends ParserRuleContext {
		public DataTypeContext dataType() {
			return getRuleContext(DataTypeContext.class,0);
		}
		public TerminalNode EOF() { return getToken(SqlBaseParser.EOF, 0); }
		public SingleDataTypeContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_singleDataType; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSingleDataType(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSingleDataType(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSingleDataType(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SingleDataTypeContext singleDataType() throws RecognitionException {
		SingleDataTypeContext _localctx = new SingleDataTypeContext(_ctx, getState());
		enterRule(_localctx, 6, RULE_singleDataType);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(189);
			dataType();
			setState(190);
			match(EOF);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class StatementContext extends ParserRuleContext {
		public StatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_statement; }
	 
		public StatementContext() { }
		public void copyFrom(StatementContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class ExplainContext extends StatementContext {
		public TerminalNode EXPLAIN() { return getToken(SqlBaseParser.EXPLAIN, 0); }
		public StatementContext statement() {
			return getRuleContext(StatementContext.class,0);
		}
		public TerminalNode LOGICAL() { return getToken(SqlBaseParser.LOGICAL, 0); }
		public TerminalNode FORMATTED() { return getToken(SqlBaseParser.FORMATTED, 0); }
		public TerminalNode EXTENDED() { return getToken(SqlBaseParser.EXTENDED, 0); }
		public TerminalNode CODEGEN() { return getToken(SqlBaseParser.CODEGEN, 0); }
		public ExplainContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterExplain(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitExplain(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitExplain(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SetDatabasePropertiesContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode DATABASE() { return getToken(SqlBaseParser.DATABASE, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public TerminalNode DBPROPERTIES() { return getToken(SqlBaseParser.DBPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public SetDatabasePropertiesContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSetDatabaseProperties(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSetDatabaseProperties(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSetDatabaseProperties(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DropDatabaseContext extends StatementContext {
		public TerminalNode DROP() { return getToken(SqlBaseParser.DROP, 0); }
		public TerminalNode DATABASE() { return getToken(SqlBaseParser.DATABASE, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public TerminalNode RESTRICT() { return getToken(SqlBaseParser.RESTRICT, 0); }
		public TerminalNode CASCADE() { return getToken(SqlBaseParser.CASCADE, 0); }
		public DropDatabaseContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDropDatabase(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDropDatabase(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDropDatabase(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CreateTableContext extends StatementContext {
		public ColTypeListContext columns;
		public ColTypeListContext partitionColumns;
		public CreateTableHeaderContext createTableHeader() {
			return getRuleContext(CreateTableHeaderContext.class,0);
		}
		public TerminalNode COMMENT() { return getToken(SqlBaseParser.COMMENT, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TerminalNode PARTITIONED() { return getToken(SqlBaseParser.PARTITIONED, 0); }
		public TerminalNode BY() { return getToken(SqlBaseParser.BY, 0); }
		public BucketSpecContext bucketSpec() {
			return getRuleContext(BucketSpecContext.class,0);
		}
		public SkewSpecContext skewSpec() {
			return getRuleContext(SkewSpecContext.class,0);
		}
		public RowFormatContext rowFormat() {
			return getRuleContext(RowFormatContext.class,0);
		}
		public CreateFileFormatContext createFileFormat() {
			return getRuleContext(CreateFileFormatContext.class,0);
		}
		public LocationSpecContext locationSpec() {
			return getRuleContext(LocationSpecContext.class,0);
		}
		public TerminalNode TBLPROPERTIES() { return getToken(SqlBaseParser.TBLPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public List<ColTypeListContext> colTypeList() {
			return getRuleContexts(ColTypeListContext.class);
		}
		public ColTypeListContext colTypeList(int i) {
			return getRuleContext(ColTypeListContext.class,i);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public CreateTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ResetConfigurationContext extends StatementContext {
		public TerminalNode RESET() { return getToken(SqlBaseParser.RESET, 0); }
		public ResetConfigurationContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterResetConfiguration(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitResetConfiguration(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitResetConfiguration(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DescribeDatabaseContext extends StatementContext {
		public TerminalNode DATABASE() { return getToken(SqlBaseParser.DATABASE, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode DESC() { return getToken(SqlBaseParser.DESC, 0); }
		public TerminalNode DESCRIBE() { return getToken(SqlBaseParser.DESCRIBE, 0); }
		public TerminalNode EXTENDED() { return getToken(SqlBaseParser.EXTENDED, 0); }
		public DescribeDatabaseContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDescribeDatabase(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDescribeDatabase(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDescribeDatabase(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class AlterViewQueryContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public AlterViewQueryContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterAlterViewQuery(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitAlterViewQuery(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitAlterViewQuery(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DescribeTableContext extends StatementContext {
		public Token option;
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode DESC() { return getToken(SqlBaseParser.DESC, 0); }
		public TerminalNode DESCRIBE() { return getToken(SqlBaseParser.DESCRIBE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public DescribeColNameContext describeColName() {
			return getRuleContext(DescribeColNameContext.class,0);
		}
		public TerminalNode EXTENDED() { return getToken(SqlBaseParser.EXTENDED, 0); }
		public TerminalNode FORMATTED() { return getToken(SqlBaseParser.FORMATTED, 0); }
		public DescribeTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDescribeTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDescribeTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDescribeTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class UseContext extends StatementContext {
		public IdentifierContext db;
		public TerminalNode USE() { return getToken(SqlBaseParser.USE, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public UseContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterUse(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitUse(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitUse(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CreateTempViewUsingContext extends StatementContext {
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode TEMPORARY() { return getToken(SqlBaseParser.TEMPORARY, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TableProviderContext tableProvider() {
			return getRuleContext(TableProviderContext.class,0);
		}
		public TerminalNode OR() { return getToken(SqlBaseParser.OR, 0); }
		public TerminalNode REPLACE() { return getToken(SqlBaseParser.REPLACE, 0); }
		public TerminalNode GLOBAL() { return getToken(SqlBaseParser.GLOBAL, 0); }
		public ColTypeListContext colTypeList() {
			return getRuleContext(ColTypeListContext.class,0);
		}
		public TerminalNode OPTIONS() { return getToken(SqlBaseParser.OPTIONS, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public CreateTempViewUsingContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateTempViewUsing(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateTempViewUsing(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateTempViewUsing(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CreateTableLikeContext extends StatementContext {
		public TableIdentifierContext target;
		public TableIdentifierContext source;
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TerminalNode LIKE() { return getToken(SqlBaseParser.LIKE, 0); }
		public List<TableIdentifierContext> tableIdentifier() {
			return getRuleContexts(TableIdentifierContext.class);
		}
		public TableIdentifierContext tableIdentifier(int i) {
			return getRuleContext(TableIdentifierContext.class,i);
		}
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public CreateTableLikeContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateTableLike(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateTableLike(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateTableLike(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RenameTableContext extends StatementContext {
		public TableIdentifierContext from;
		public TableIdentifierContext to;
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode RENAME() { return getToken(SqlBaseParser.RENAME, 0); }
		public TerminalNode TO() { return getToken(SqlBaseParser.TO, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public List<TableIdentifierContext> tableIdentifier() {
			return getRuleContexts(TableIdentifierContext.class);
		}
		public TableIdentifierContext tableIdentifier(int i) {
			return getRuleContext(TableIdentifierContext.class,i);
		}
		public RenameTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRenameTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRenameTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRenameTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class UncacheTableContext extends StatementContext {
		public TerminalNode UNCACHE() { return getToken(SqlBaseParser.UNCACHE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public UncacheTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterUncacheTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitUncacheTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitUncacheTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DropFunctionContext extends StatementContext {
		public TerminalNode DROP() { return getToken(SqlBaseParser.DROP, 0); }
		public TerminalNode FUNCTION() { return getToken(SqlBaseParser.FUNCTION, 0); }
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public TerminalNode TEMPORARY() { return getToken(SqlBaseParser.TEMPORARY, 0); }
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public DropFunctionContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDropFunction(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDropFunction(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDropFunction(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class FailNativeCommandContext extends StatementContext {
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public TerminalNode ROLE() { return getToken(SqlBaseParser.ROLE, 0); }
		public UnsupportedHiveNativeCommandsContext unsupportedHiveNativeCommands() {
			return getRuleContext(UnsupportedHiveNativeCommandsContext.class,0);
		}
		public FailNativeCommandContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterFailNativeCommand(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitFailNativeCommand(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitFailNativeCommand(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class LoadDataContext extends StatementContext {
		public Token path;
		public TerminalNode LOAD() { return getToken(SqlBaseParser.LOAD, 0); }
		public TerminalNode DATA() { return getToken(SqlBaseParser.DATA, 0); }
		public TerminalNode INPATH() { return getToken(SqlBaseParser.INPATH, 0); }
		public TerminalNode INTO() { return getToken(SqlBaseParser.INTO, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TerminalNode LOCAL() { return getToken(SqlBaseParser.LOCAL, 0); }
		public TerminalNode OVERWRITE() { return getToken(SqlBaseParser.OVERWRITE, 0); }
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public LoadDataContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterLoadData(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitLoadData(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitLoadData(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ShowPartitionsContext extends StatementContext {
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode PARTITIONS() { return getToken(SqlBaseParser.PARTITIONS, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public ShowPartitionsContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterShowPartitions(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitShowPartitions(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitShowPartitions(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DescribeFunctionContext extends StatementContext {
		public TerminalNode FUNCTION() { return getToken(SqlBaseParser.FUNCTION, 0); }
		public DescribeFuncNameContext describeFuncName() {
			return getRuleContext(DescribeFuncNameContext.class,0);
		}
		public TerminalNode DESC() { return getToken(SqlBaseParser.DESC, 0); }
		public TerminalNode DESCRIBE() { return getToken(SqlBaseParser.DESCRIBE, 0); }
		public TerminalNode EXTENDED() { return getToken(SqlBaseParser.EXTENDED, 0); }
		public DescribeFunctionContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDescribeFunction(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDescribeFunction(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDescribeFunction(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ClearCacheContext extends StatementContext {
		public TerminalNode CLEAR() { return getToken(SqlBaseParser.CLEAR, 0); }
		public TerminalNode CACHE() { return getToken(SqlBaseParser.CACHE, 0); }
		public ClearCacheContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterClearCache(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitClearCache(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitClearCache(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ShowTablesContext extends StatementContext {
		public IdentifierContext db;
		public Token pattern;
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode TABLES() { return getToken(SqlBaseParser.TABLES, 0); }
		public TerminalNode FROM() { return getToken(SqlBaseParser.FROM, 0); }
		public TerminalNode IN() { return getToken(SqlBaseParser.IN, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TerminalNode LIKE() { return getToken(SqlBaseParser.LIKE, 0); }
		public ShowTablesContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterShowTables(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitShowTables(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitShowTables(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RecoverPartitionsContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode RECOVER() { return getToken(SqlBaseParser.RECOVER, 0); }
		public TerminalNode PARTITIONS() { return getToken(SqlBaseParser.PARTITIONS, 0); }
		public RecoverPartitionsContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRecoverPartitions(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRecoverPartitions(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRecoverPartitions(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class StatementDefaultContext extends StatementContext {
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public StatementDefaultContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterStatementDefault(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitStatementDefault(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitStatementDefault(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RenameTablePartitionContext extends StatementContext {
		public PartitionSpecContext from;
		public PartitionSpecContext to;
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode RENAME() { return getToken(SqlBaseParser.RENAME, 0); }
		public TerminalNode TO() { return getToken(SqlBaseParser.TO, 0); }
		public List<PartitionSpecContext> partitionSpec() {
			return getRuleContexts(PartitionSpecContext.class);
		}
		public PartitionSpecContext partitionSpec(int i) {
			return getRuleContext(PartitionSpecContext.class,i);
		}
		public RenameTablePartitionContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRenameTablePartition(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRenameTablePartition(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRenameTablePartition(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RepairTableContext extends StatementContext {
		public TerminalNode MSCK() { return getToken(SqlBaseParser.MSCK, 0); }
		public TerminalNode REPAIR() { return getToken(SqlBaseParser.REPAIR, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public RepairTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRepairTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRepairTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRepairTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RefreshResourceContext extends StatementContext {
		public TerminalNode REFRESH() { return getToken(SqlBaseParser.REFRESH, 0); }
		public RefreshResourceContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRefreshResource(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRefreshResource(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRefreshResource(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class TruncateTableContext extends StatementContext {
		public TerminalNode TRUNCATE() { return getToken(SqlBaseParser.TRUNCATE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public TruncateTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTruncateTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTruncateTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTruncateTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SetTableSerDeContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public TerminalNode SERDE() { return getToken(SqlBaseParser.SERDE, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public TerminalNode WITH() { return getToken(SqlBaseParser.WITH, 0); }
		public TerminalNode SERDEPROPERTIES() { return getToken(SqlBaseParser.SERDEPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public SetTableSerDeContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSetTableSerDe(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSetTableSerDe(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSetTableSerDe(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CreateViewContext extends StatementContext {
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public TerminalNode OR() { return getToken(SqlBaseParser.OR, 0); }
		public TerminalNode REPLACE() { return getToken(SqlBaseParser.REPLACE, 0); }
		public TerminalNode TEMPORARY() { return getToken(SqlBaseParser.TEMPORARY, 0); }
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public IdentifierCommentListContext identifierCommentList() {
			return getRuleContext(IdentifierCommentListContext.class,0);
		}
		public TerminalNode COMMENT() { return getToken(SqlBaseParser.COMMENT, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TerminalNode PARTITIONED() { return getToken(SqlBaseParser.PARTITIONED, 0); }
		public TerminalNode ON() { return getToken(SqlBaseParser.ON, 0); }
		public IdentifierListContext identifierList() {
			return getRuleContext(IdentifierListContext.class,0);
		}
		public TerminalNode TBLPROPERTIES() { return getToken(SqlBaseParser.TBLPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public TerminalNode GLOBAL() { return getToken(SqlBaseParser.GLOBAL, 0); }
		public CreateViewContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateView(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateView(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateView(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DropTablePartitionsContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode DROP() { return getToken(SqlBaseParser.DROP, 0); }
		public List<PartitionSpecContext> partitionSpec() {
			return getRuleContexts(PartitionSpecContext.class);
		}
		public PartitionSpecContext partitionSpec(int i) {
			return getRuleContext(PartitionSpecContext.class,i);
		}
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public TerminalNode PURGE() { return getToken(SqlBaseParser.PURGE, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public DropTablePartitionsContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDropTablePartitions(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDropTablePartitions(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDropTablePartitions(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ShowCreateTableContext extends StatementContext {
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public ShowCreateTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterShowCreateTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitShowCreateTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitShowCreateTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SetConfigurationContext extends StatementContext {
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public SetConfigurationContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSetConfiguration(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSetConfiguration(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSetConfiguration(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DropTableContext extends StatementContext {
		public TerminalNode DROP() { return getToken(SqlBaseParser.DROP, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public TerminalNode PURGE() { return getToken(SqlBaseParser.PURGE, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public DropTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDropTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDropTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDropTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ShowColumnsContext extends StatementContext {
		public IdentifierContext db;
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode COLUMNS() { return getToken(SqlBaseParser.COLUMNS, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public List<TerminalNode> FROM() { return getTokens(SqlBaseParser.FROM); }
		public TerminalNode FROM(int i) {
			return getToken(SqlBaseParser.FROM, i);
		}
		public List<TerminalNode> IN() { return getTokens(SqlBaseParser.IN); }
		public TerminalNode IN(int i) {
			return getToken(SqlBaseParser.IN, i);
		}
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public ShowColumnsContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterShowColumns(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitShowColumns(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitShowColumns(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CreateTableUsingContext extends StatementContext {
		public IdentifierListContext partitionColumnNames;
		public CreateTableHeaderContext createTableHeader() {
			return getRuleContext(CreateTableHeaderContext.class,0);
		}
		public TableProviderContext tableProvider() {
			return getRuleContext(TableProviderContext.class,0);
		}
		public ColTypeListContext colTypeList() {
			return getRuleContext(ColTypeListContext.class,0);
		}
		public TerminalNode OPTIONS() { return getToken(SqlBaseParser.OPTIONS, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public TerminalNode PARTITIONED() { return getToken(SqlBaseParser.PARTITIONED, 0); }
		public TerminalNode BY() { return getToken(SqlBaseParser.BY, 0); }
		public BucketSpecContext bucketSpec() {
			return getRuleContext(BucketSpecContext.class,0);
		}
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public IdentifierListContext identifierList() {
			return getRuleContext(IdentifierListContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public CreateTableUsingContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateTableUsing(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateTableUsing(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateTableUsing(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ShowDatabasesContext extends StatementContext {
		public Token pattern;
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode DATABASES() { return getToken(SqlBaseParser.DATABASES, 0); }
		public TerminalNode LIKE() { return getToken(SqlBaseParser.LIKE, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public ShowDatabasesContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterShowDatabases(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitShowDatabases(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitShowDatabases(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class AddTablePartitionContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode ADD() { return getToken(SqlBaseParser.ADD, 0); }
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public List<PartitionSpecLocationContext> partitionSpecLocation() {
			return getRuleContexts(PartitionSpecLocationContext.class);
		}
		public PartitionSpecLocationContext partitionSpecLocation(int i) {
			return getRuleContext(PartitionSpecLocationContext.class,i);
		}
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public List<PartitionSpecContext> partitionSpec() {
			return getRuleContexts(PartitionSpecContext.class);
		}
		public PartitionSpecContext partitionSpec(int i) {
			return getRuleContext(PartitionSpecContext.class,i);
		}
		public AddTablePartitionContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterAddTablePartition(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitAddTablePartition(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitAddTablePartition(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RefreshTableContext extends StatementContext {
		public TerminalNode REFRESH() { return getToken(SqlBaseParser.REFRESH, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public RefreshTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRefreshTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRefreshTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRefreshTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ManageResourceContext extends StatementContext {
		public Token op;
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode ADD() { return getToken(SqlBaseParser.ADD, 0); }
		public TerminalNode LIST() { return getToken(SqlBaseParser.LIST, 0); }
		public ManageResourceContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterManageResource(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitManageResource(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitManageResource(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CreateDatabaseContext extends StatementContext {
		public Token comment;
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode DATABASE() { return getToken(SqlBaseParser.DATABASE, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public TerminalNode COMMENT() { return getToken(SqlBaseParser.COMMENT, 0); }
		public LocationSpecContext locationSpec() {
			return getRuleContext(LocationSpecContext.class,0);
		}
		public TerminalNode WITH() { return getToken(SqlBaseParser.WITH, 0); }
		public TerminalNode DBPROPERTIES() { return getToken(SqlBaseParser.DBPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public CreateDatabaseContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateDatabase(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateDatabase(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateDatabase(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ShowTblPropertiesContext extends StatementContext {
		public TableIdentifierContext table;
		public TablePropertyKeyContext key;
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode TBLPROPERTIES() { return getToken(SqlBaseParser.TBLPROPERTIES, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TablePropertyKeyContext tablePropertyKey() {
			return getRuleContext(TablePropertyKeyContext.class,0);
		}
		public ShowTblPropertiesContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterShowTblProperties(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitShowTblProperties(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitShowTblProperties(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class AnalyzeContext extends StatementContext {
		public TerminalNode ANALYZE() { return getToken(SqlBaseParser.ANALYZE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode COMPUTE() { return getToken(SqlBaseParser.COMPUTE, 0); }
		public TerminalNode STATISTICS() { return getToken(SqlBaseParser.STATISTICS, 0); }
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode FOR() { return getToken(SqlBaseParser.FOR, 0); }
		public TerminalNode COLUMNS() { return getToken(SqlBaseParser.COLUMNS, 0); }
		public IdentifierSeqContext identifierSeq() {
			return getRuleContext(IdentifierSeqContext.class,0);
		}
		public AnalyzeContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterAnalyze(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitAnalyze(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitAnalyze(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class UnsetTablePropertiesContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode UNSET() { return getToken(SqlBaseParser.UNSET, 0); }
		public TerminalNode TBLPROPERTIES() { return getToken(SqlBaseParser.TBLPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public UnsetTablePropertiesContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterUnsetTableProperties(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitUnsetTableProperties(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitUnsetTableProperties(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SetTableLocationContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public LocationSpecContext locationSpec() {
			return getRuleContext(LocationSpecContext.class,0);
		}
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public SetTableLocationContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSetTableLocation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSetTableLocation(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSetTableLocation(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CreateFunctionContext extends StatementContext {
		public Token className;
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode FUNCTION() { return getToken(SqlBaseParser.FUNCTION, 0); }
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TerminalNode TEMPORARY() { return getToken(SqlBaseParser.TEMPORARY, 0); }
		public TerminalNode USING() { return getToken(SqlBaseParser.USING, 0); }
		public List<ResourceContext> resource() {
			return getRuleContexts(ResourceContext.class);
		}
		public ResourceContext resource(int i) {
			return getRuleContext(ResourceContext.class,i);
		}
		public CreateFunctionContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateFunction(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateFunction(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateFunction(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ShowFunctionsContext extends StatementContext {
		public Token pattern;
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode FUNCTIONS() { return getToken(SqlBaseParser.FUNCTIONS, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public TerminalNode LIKE() { return getToken(SqlBaseParser.LIKE, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public ShowFunctionsContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterShowFunctions(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitShowFunctions(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitShowFunctions(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CacheTableContext extends StatementContext {
		public TerminalNode CACHE() { return getToken(SqlBaseParser.CACHE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode LAZY() { return getToken(SqlBaseParser.LAZY, 0); }
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public CacheTableContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCacheTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCacheTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCacheTable(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SetTablePropertiesContext extends StatementContext {
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public TerminalNode TBLPROPERTIES() { return getToken(SqlBaseParser.TBLPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public SetTablePropertiesContext(StatementContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSetTableProperties(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSetTableProperties(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSetTableProperties(this);
			else return visitor.visitChildren(this);
		}
	}

	public final StatementContext statement() throws RecognitionException {
		StatementContext _localctx = new StatementContext(_ctx, getState());
		enterRule(_localctx, 8, RULE_statement);
		int _la;
		try {
			int _alt;
			setState(753);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,92,_ctx) ) {
			case 1:
				_localctx = new StatementDefaultContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(192);
				query();
				}
				break;
			case 2:
				_localctx = new UseContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(193);
				match(USE);
				setState(194);
				((UseContext)_localctx).db = identifier();
				}
				break;
			case 3:
				_localctx = new CreateDatabaseContext(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(195);
				match(CREATE);
				setState(196);
				match(DATABASE);
				setState(200);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,0,_ctx) ) {
				case 1:
					{
					setState(197);
					match(IF);
					setState(198);
					match(NOT);
					setState(199);
					match(EXISTS);
					}
					break;
				}
				setState(202);
				identifier();
				setState(205);
				_la = _input.LA(1);
				if (_la==COMMENT) {
					{
					setState(203);
					match(COMMENT);
					setState(204);
					((CreateDatabaseContext)_localctx).comment = match(STRING);
					}
				}

				setState(208);
				_la = _input.LA(1);
				if (_la==LOCATION) {
					{
					setState(207);
					locationSpec();
					}
				}

				setState(213);
				_la = _input.LA(1);
				if (_la==WITH) {
					{
					setState(210);
					match(WITH);
					setState(211);
					match(DBPROPERTIES);
					setState(212);
					tablePropertyList();
					}
				}

				}
				break;
			case 4:
				_localctx = new SetDatabasePropertiesContext(_localctx);
				enterOuterAlt(_localctx, 4);
				{
				setState(215);
				match(ALTER);
				setState(216);
				match(DATABASE);
				setState(217);
				identifier();
				setState(218);
				match(SET);
				setState(219);
				match(DBPROPERTIES);
				setState(220);
				tablePropertyList();
				}
				break;
			case 5:
				_localctx = new DropDatabaseContext(_localctx);
				enterOuterAlt(_localctx, 5);
				{
				setState(222);
				match(DROP);
				setState(223);
				match(DATABASE);
				setState(226);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,4,_ctx) ) {
				case 1:
					{
					setState(224);
					match(IF);
					setState(225);
					match(EXISTS);
					}
					break;
				}
				setState(228);
				identifier();
				setState(230);
				_la = _input.LA(1);
				if (_la==CASCADE || _la==RESTRICT) {
					{
					setState(229);
					_la = _input.LA(1);
					if ( !(_la==CASCADE || _la==RESTRICT) ) {
					_errHandler.recoverInline(this);
					} else {
						consume();
					}
					}
				}

				}
				break;
			case 6:
				_localctx = new CreateTableUsingContext(_localctx);
				enterOuterAlt(_localctx, 6);
				{
				setState(232);
				createTableHeader();
				setState(237);
				_la = _input.LA(1);
				if (_la==T__0) {
					{
					setState(233);
					match(T__0);
					setState(234);
					colTypeList();
					setState(235);
					match(T__1);
					}
				}

				setState(239);
				tableProvider();
				setState(242);
				_la = _input.LA(1);
				if (_la==OPTIONS) {
					{
					setState(240);
					match(OPTIONS);
					setState(241);
					tablePropertyList();
					}
				}

				setState(247);
				_la = _input.LA(1);
				if (_la==PARTITIONED) {
					{
					setState(244);
					match(PARTITIONED);
					setState(245);
					match(BY);
					setState(246);
					((CreateTableUsingContext)_localctx).partitionColumnNames = identifierList();
					}
				}

				setState(250);
				_la = _input.LA(1);
				if (_la==CLUSTERED) {
					{
					setState(249);
					bucketSpec();
					}
				}

				setState(256);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << SELECT) | (1L << FROM) | (1L << AS))) != 0) || ((((_la - 71)) & ~0x3f) == 0 && ((1L << (_la - 71)) & ((1L << (WITH - 71)) | (1L << (VALUES - 71)) | (1L << (TABLE - 71)) | (1L << (INSERT - 71)) | (1L << (MAP - 71)))) != 0) || _la==REDUCE) {
					{
					setState(253);
					_la = _input.LA(1);
					if (_la==AS) {
						{
						setState(252);
						match(AS);
						}
					}

					setState(255);
					query();
					}
				}

				}
				break;
			case 7:
				_localctx = new CreateTableContext(_localctx);
				enterOuterAlt(_localctx, 7);
				{
				setState(258);
				createTableHeader();
				setState(263);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,12,_ctx) ) {
				case 1:
					{
					setState(259);
					match(T__0);
					setState(260);
					((CreateTableContext)_localctx).columns = colTypeList();
					setState(261);
					match(T__1);
					}
					break;
				}
				setState(267);
				_la = _input.LA(1);
				if (_la==COMMENT) {
					{
					setState(265);
					match(COMMENT);
					setState(266);
					match(STRING);
					}
				}

				setState(275);
				_la = _input.LA(1);
				if (_la==PARTITIONED) {
					{
					setState(269);
					match(PARTITIONED);
					setState(270);
					match(BY);
					setState(271);
					match(T__0);
					setState(272);
					((CreateTableContext)_localctx).partitionColumns = colTypeList();
					setState(273);
					match(T__1);
					}
				}

				setState(278);
				_la = _input.LA(1);
				if (_la==CLUSTERED) {
					{
					setState(277);
					bucketSpec();
					}
				}

				setState(281);
				_la = _input.LA(1);
				if (_la==SKEWED) {
					{
					setState(280);
					skewSpec();
					}
				}

				setState(284);
				_la = _input.LA(1);
				if (_la==ROW) {
					{
					setState(283);
					rowFormat();
					}
				}

				setState(287);
				_la = _input.LA(1);
				if (_la==STORED) {
					{
					setState(286);
					createFileFormat();
					}
				}

				setState(290);
				_la = _input.LA(1);
				if (_la==LOCATION) {
					{
					setState(289);
					locationSpec();
					}
				}

				setState(294);
				_la = _input.LA(1);
				if (_la==TBLPROPERTIES) {
					{
					setState(292);
					match(TBLPROPERTIES);
					setState(293);
					tablePropertyList();
					}
				}

				setState(300);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << SELECT) | (1L << FROM) | (1L << AS))) != 0) || ((((_la - 71)) & ~0x3f) == 0 && ((1L << (_la - 71)) & ((1L << (WITH - 71)) | (1L << (VALUES - 71)) | (1L << (TABLE - 71)) | (1L << (INSERT - 71)) | (1L << (MAP - 71)))) != 0) || _la==REDUCE) {
					{
					setState(297);
					_la = _input.LA(1);
					if (_la==AS) {
						{
						setState(296);
						match(AS);
						}
					}

					setState(299);
					query();
					}
				}

				}
				break;
			case 8:
				_localctx = new CreateTableLikeContext(_localctx);
				enterOuterAlt(_localctx, 8);
				{
				setState(302);
				match(CREATE);
				setState(303);
				match(TABLE);
				setState(307);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,23,_ctx) ) {
				case 1:
					{
					setState(304);
					match(IF);
					setState(305);
					match(NOT);
					setState(306);
					match(EXISTS);
					}
					break;
				}
				setState(309);
				((CreateTableLikeContext)_localctx).target = tableIdentifier();
				setState(310);
				match(LIKE);
				setState(311);
				((CreateTableLikeContext)_localctx).source = tableIdentifier();
				}
				break;
			case 9:
				_localctx = new AnalyzeContext(_localctx);
				enterOuterAlt(_localctx, 9);
				{
				setState(313);
				match(ANALYZE);
				setState(314);
				match(TABLE);
				setState(315);
				tableIdentifier();
				setState(317);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(316);
					partitionSpec();
					}
				}

				setState(319);
				match(COMPUTE);
				setState(320);
				match(STATISTICS);
				setState(325);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,25,_ctx) ) {
				case 1:
					{
					setState(321);
					identifier();
					}
					break;
				case 2:
					{
					setState(322);
					match(FOR);
					setState(323);
					match(COLUMNS);
					setState(324);
					identifierSeq();
					}
					break;
				}
				}
				break;
			case 10:
				_localctx = new RenameTableContext(_localctx);
				enterOuterAlt(_localctx, 10);
				{
				setState(327);
				match(ALTER);
				setState(328);
				_la = _input.LA(1);
				if ( !(_la==TABLE || _la==VIEW) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(329);
				((RenameTableContext)_localctx).from = tableIdentifier();
				setState(330);
				match(RENAME);
				setState(331);
				match(TO);
				setState(332);
				((RenameTableContext)_localctx).to = tableIdentifier();
				}
				break;
			case 11:
				_localctx = new SetTablePropertiesContext(_localctx);
				enterOuterAlt(_localctx, 11);
				{
				setState(334);
				match(ALTER);
				setState(335);
				_la = _input.LA(1);
				if ( !(_la==TABLE || _la==VIEW) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(336);
				tableIdentifier();
				setState(337);
				match(SET);
				setState(338);
				match(TBLPROPERTIES);
				setState(339);
				tablePropertyList();
				}
				break;
			case 12:
				_localctx = new UnsetTablePropertiesContext(_localctx);
				enterOuterAlt(_localctx, 12);
				{
				setState(341);
				match(ALTER);
				setState(342);
				_la = _input.LA(1);
				if ( !(_la==TABLE || _la==VIEW) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(343);
				tableIdentifier();
				setState(344);
				match(UNSET);
				setState(345);
				match(TBLPROPERTIES);
				setState(348);
				_la = _input.LA(1);
				if (_la==IF) {
					{
					setState(346);
					match(IF);
					setState(347);
					match(EXISTS);
					}
				}

				setState(350);
				tablePropertyList();
				}
				break;
			case 13:
				_localctx = new SetTableSerDeContext(_localctx);
				enterOuterAlt(_localctx, 13);
				{
				setState(352);
				match(ALTER);
				setState(353);
				match(TABLE);
				setState(354);
				tableIdentifier();
				setState(356);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(355);
					partitionSpec();
					}
				}

				setState(358);
				match(SET);
				setState(359);
				match(SERDE);
				setState(360);
				match(STRING);
				setState(364);
				_la = _input.LA(1);
				if (_la==WITH) {
					{
					setState(361);
					match(WITH);
					setState(362);
					match(SERDEPROPERTIES);
					setState(363);
					tablePropertyList();
					}
				}

				}
				break;
			case 14:
				_localctx = new SetTableSerDeContext(_localctx);
				enterOuterAlt(_localctx, 14);
				{
				setState(366);
				match(ALTER);
				setState(367);
				match(TABLE);
				setState(368);
				tableIdentifier();
				setState(370);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(369);
					partitionSpec();
					}
				}

				setState(372);
				match(SET);
				setState(373);
				match(SERDEPROPERTIES);
				setState(374);
				tablePropertyList();
				}
				break;
			case 15:
				_localctx = new AddTablePartitionContext(_localctx);
				enterOuterAlt(_localctx, 15);
				{
				setState(376);
				match(ALTER);
				setState(377);
				match(TABLE);
				setState(378);
				tableIdentifier();
				setState(379);
				match(ADD);
				setState(383);
				_la = _input.LA(1);
				if (_la==IF) {
					{
					setState(380);
					match(IF);
					setState(381);
					match(NOT);
					setState(382);
					match(EXISTS);
					}
				}

				setState(386); 
				_errHandler.sync(this);
				_la = _input.LA(1);
				do {
					{
					{
					setState(385);
					partitionSpecLocation();
					}
					}
					setState(388); 
					_errHandler.sync(this);
					_la = _input.LA(1);
				} while ( _la==PARTITION );
				}
				break;
			case 16:
				_localctx = new AddTablePartitionContext(_localctx);
				enterOuterAlt(_localctx, 16);
				{
				setState(390);
				match(ALTER);
				setState(391);
				match(VIEW);
				setState(392);
				tableIdentifier();
				setState(393);
				match(ADD);
				setState(397);
				_la = _input.LA(1);
				if (_la==IF) {
					{
					setState(394);
					match(IF);
					setState(395);
					match(NOT);
					setState(396);
					match(EXISTS);
					}
				}

				setState(400); 
				_errHandler.sync(this);
				_la = _input.LA(1);
				do {
					{
					{
					setState(399);
					partitionSpec();
					}
					}
					setState(402); 
					_errHandler.sync(this);
					_la = _input.LA(1);
				} while ( _la==PARTITION );
				}
				break;
			case 17:
				_localctx = new RenameTablePartitionContext(_localctx);
				enterOuterAlt(_localctx, 17);
				{
				setState(404);
				match(ALTER);
				setState(405);
				match(TABLE);
				setState(406);
				tableIdentifier();
				setState(407);
				((RenameTablePartitionContext)_localctx).from = partitionSpec();
				setState(408);
				match(RENAME);
				setState(409);
				match(TO);
				setState(410);
				((RenameTablePartitionContext)_localctx).to = partitionSpec();
				}
				break;
			case 18:
				_localctx = new DropTablePartitionsContext(_localctx);
				enterOuterAlt(_localctx, 18);
				{
				setState(412);
				match(ALTER);
				setState(413);
				match(TABLE);
				setState(414);
				tableIdentifier();
				setState(415);
				match(DROP);
				setState(418);
				_la = _input.LA(1);
				if (_la==IF) {
					{
					setState(416);
					match(IF);
					setState(417);
					match(EXISTS);
					}
				}

				setState(420);
				partitionSpec();
				setState(425);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(421);
					match(T__2);
					setState(422);
					partitionSpec();
					}
					}
					setState(427);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				setState(429);
				_la = _input.LA(1);
				if (_la==PURGE) {
					{
					setState(428);
					match(PURGE);
					}
				}

				}
				break;
			case 19:
				_localctx = new DropTablePartitionsContext(_localctx);
				enterOuterAlt(_localctx, 19);
				{
				setState(431);
				match(ALTER);
				setState(432);
				match(VIEW);
				setState(433);
				tableIdentifier();
				setState(434);
				match(DROP);
				setState(437);
				_la = _input.LA(1);
				if (_la==IF) {
					{
					setState(435);
					match(IF);
					setState(436);
					match(EXISTS);
					}
				}

				setState(439);
				partitionSpec();
				setState(444);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(440);
					match(T__2);
					setState(441);
					partitionSpec();
					}
					}
					setState(446);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
				break;
			case 20:
				_localctx = new SetTableLocationContext(_localctx);
				enterOuterAlt(_localctx, 20);
				{
				setState(447);
				match(ALTER);
				setState(448);
				match(TABLE);
				setState(449);
				tableIdentifier();
				setState(451);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(450);
					partitionSpec();
					}
				}

				setState(453);
				match(SET);
				setState(454);
				locationSpec();
				}
				break;
			case 21:
				_localctx = new RecoverPartitionsContext(_localctx);
				enterOuterAlt(_localctx, 21);
				{
				setState(456);
				match(ALTER);
				setState(457);
				match(TABLE);
				setState(458);
				tableIdentifier();
				setState(459);
				match(RECOVER);
				setState(460);
				match(PARTITIONS);
				}
				break;
			case 22:
				_localctx = new DropTableContext(_localctx);
				enterOuterAlt(_localctx, 22);
				{
				setState(462);
				match(DROP);
				setState(463);
				match(TABLE);
				setState(466);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,40,_ctx) ) {
				case 1:
					{
					setState(464);
					match(IF);
					setState(465);
					match(EXISTS);
					}
					break;
				}
				setState(468);
				tableIdentifier();
				setState(470);
				_la = _input.LA(1);
				if (_la==PURGE) {
					{
					setState(469);
					match(PURGE);
					}
				}

				}
				break;
			case 23:
				_localctx = new DropTableContext(_localctx);
				enterOuterAlt(_localctx, 23);
				{
				setState(472);
				match(DROP);
				setState(473);
				match(VIEW);
				setState(476);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,42,_ctx) ) {
				case 1:
					{
					setState(474);
					match(IF);
					setState(475);
					match(EXISTS);
					}
					break;
				}
				setState(478);
				tableIdentifier();
				}
				break;
			case 24:
				_localctx = new CreateViewContext(_localctx);
				enterOuterAlt(_localctx, 24);
				{
				setState(479);
				match(CREATE);
				setState(482);
				_la = _input.LA(1);
				if (_la==OR) {
					{
					setState(480);
					match(OR);
					setState(481);
					match(REPLACE);
					}
				}

				setState(488);
				_la = _input.LA(1);
				if (_la==GLOBAL || _la==TEMPORARY) {
					{
					setState(485);
					_la = _input.LA(1);
					if (_la==GLOBAL) {
						{
						setState(484);
						match(GLOBAL);
						}
					}

					setState(487);
					match(TEMPORARY);
					}
				}

				setState(490);
				match(VIEW);
				setState(494);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,46,_ctx) ) {
				case 1:
					{
					setState(491);
					match(IF);
					setState(492);
					match(NOT);
					setState(493);
					match(EXISTS);
					}
					break;
				}
				setState(496);
				tableIdentifier();
				setState(498);
				_la = _input.LA(1);
				if (_la==T__0) {
					{
					setState(497);
					identifierCommentList();
					}
				}

				setState(502);
				_la = _input.LA(1);
				if (_la==COMMENT) {
					{
					setState(500);
					match(COMMENT);
					setState(501);
					match(STRING);
					}
				}

				setState(507);
				_la = _input.LA(1);
				if (_la==PARTITIONED) {
					{
					setState(504);
					match(PARTITIONED);
					setState(505);
					match(ON);
					setState(506);
					identifierList();
					}
				}

				setState(511);
				_la = _input.LA(1);
				if (_la==TBLPROPERTIES) {
					{
					setState(509);
					match(TBLPROPERTIES);
					setState(510);
					tablePropertyList();
					}
				}

				setState(513);
				match(AS);
				setState(514);
				query();
				}
				break;
			case 25:
				_localctx = new CreateTempViewUsingContext(_localctx);
				enterOuterAlt(_localctx, 25);
				{
				setState(516);
				match(CREATE);
				setState(519);
				_la = _input.LA(1);
				if (_la==OR) {
					{
					setState(517);
					match(OR);
					setState(518);
					match(REPLACE);
					}
				}

				setState(522);
				_la = _input.LA(1);
				if (_la==GLOBAL) {
					{
					setState(521);
					match(GLOBAL);
					}
				}

				setState(524);
				match(TEMPORARY);
				setState(525);
				match(VIEW);
				setState(526);
				tableIdentifier();
				setState(531);
				_la = _input.LA(1);
				if (_la==T__0) {
					{
					setState(527);
					match(T__0);
					setState(528);
					colTypeList();
					setState(529);
					match(T__1);
					}
				}

				setState(533);
				tableProvider();
				setState(536);
				_la = _input.LA(1);
				if (_la==OPTIONS) {
					{
					setState(534);
					match(OPTIONS);
					setState(535);
					tablePropertyList();
					}
				}

				}
				break;
			case 26:
				_localctx = new AlterViewQueryContext(_localctx);
				enterOuterAlt(_localctx, 26);
				{
				setState(538);
				match(ALTER);
				setState(539);
				match(VIEW);
				setState(540);
				tableIdentifier();
				setState(542);
				_la = _input.LA(1);
				if (_la==AS) {
					{
					setState(541);
					match(AS);
					}
				}

				setState(544);
				query();
				}
				break;
			case 27:
				_localctx = new CreateFunctionContext(_localctx);
				enterOuterAlt(_localctx, 27);
				{
				setState(546);
				match(CREATE);
				setState(548);
				_la = _input.LA(1);
				if (_la==TEMPORARY) {
					{
					setState(547);
					match(TEMPORARY);
					}
				}

				setState(550);
				match(FUNCTION);
				setState(551);
				qualifiedName();
				setState(552);
				match(AS);
				setState(553);
				((CreateFunctionContext)_localctx).className = match(STRING);
				setState(563);
				_la = _input.LA(1);
				if (_la==USING) {
					{
					setState(554);
					match(USING);
					setState(555);
					resource();
					setState(560);
					_errHandler.sync(this);
					_la = _input.LA(1);
					while (_la==T__2) {
						{
						{
						setState(556);
						match(T__2);
						setState(557);
						resource();
						}
						}
						setState(562);
						_errHandler.sync(this);
						_la = _input.LA(1);
					}
					}
				}

				}
				break;
			case 28:
				_localctx = new DropFunctionContext(_localctx);
				enterOuterAlt(_localctx, 28);
				{
				setState(565);
				match(DROP);
				setState(567);
				_la = _input.LA(1);
				if (_la==TEMPORARY) {
					{
					setState(566);
					match(TEMPORARY);
					}
				}

				setState(569);
				match(FUNCTION);
				setState(572);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,60,_ctx) ) {
				case 1:
					{
					setState(570);
					match(IF);
					setState(571);
					match(EXISTS);
					}
					break;
				}
				setState(574);
				qualifiedName();
				}
				break;
			case 29:
				_localctx = new ExplainContext(_localctx);
				enterOuterAlt(_localctx, 29);
				{
				setState(575);
				match(EXPLAIN);
				setState(577);
				_la = _input.LA(1);
				if (_la==LOGICAL || _la==CODEGEN || _la==EXTENDED || _la==FORMATTED) {
					{
					setState(576);
					_la = _input.LA(1);
					if ( !(_la==LOGICAL || _la==CODEGEN || _la==EXTENDED || _la==FORMATTED) ) {
					_errHandler.recoverInline(this);
					} else {
						consume();
					}
					}
				}

				setState(579);
				statement();
				}
				break;
			case 30:
				_localctx = new ShowTablesContext(_localctx);
				enterOuterAlt(_localctx, 30);
				{
				setState(580);
				match(SHOW);
				setState(581);
				match(TABLES);
				setState(584);
				_la = _input.LA(1);
				if (_la==FROM || _la==IN) {
					{
					setState(582);
					_la = _input.LA(1);
					if ( !(_la==FROM || _la==IN) ) {
					_errHandler.recoverInline(this);
					} else {
						consume();
					}
					setState(583);
					((ShowTablesContext)_localctx).db = identifier();
					}
				}

				setState(590);
				_la = _input.LA(1);
				if (_la==LIKE || _la==STRING) {
					{
					setState(587);
					_la = _input.LA(1);
					if (_la==LIKE) {
						{
						setState(586);
						match(LIKE);
						}
					}

					setState(589);
					((ShowTablesContext)_localctx).pattern = match(STRING);
					}
				}

				}
				break;
			case 31:
				_localctx = new ShowDatabasesContext(_localctx);
				enterOuterAlt(_localctx, 31);
				{
				setState(592);
				match(SHOW);
				setState(593);
				match(DATABASES);
				setState(596);
				_la = _input.LA(1);
				if (_la==LIKE) {
					{
					setState(594);
					match(LIKE);
					setState(595);
					((ShowDatabasesContext)_localctx).pattern = match(STRING);
					}
				}

				}
				break;
			case 32:
				_localctx = new ShowTblPropertiesContext(_localctx);
				enterOuterAlt(_localctx, 32);
				{
				setState(598);
				match(SHOW);
				setState(599);
				match(TBLPROPERTIES);
				setState(600);
				((ShowTblPropertiesContext)_localctx).table = tableIdentifier();
				setState(605);
				_la = _input.LA(1);
				if (_la==T__0) {
					{
					setState(601);
					match(T__0);
					setState(602);
					((ShowTblPropertiesContext)_localctx).key = tablePropertyKey();
					setState(603);
					match(T__1);
					}
				}

				}
				break;
			case 33:
				_localctx = new ShowColumnsContext(_localctx);
				enterOuterAlt(_localctx, 33);
				{
				setState(607);
				match(SHOW);
				setState(608);
				match(COLUMNS);
				setState(609);
				_la = _input.LA(1);
				if ( !(_la==FROM || _la==IN) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(610);
				tableIdentifier();
				setState(613);
				_la = _input.LA(1);
				if (_la==FROM || _la==IN) {
					{
					setState(611);
					_la = _input.LA(1);
					if ( !(_la==FROM || _la==IN) ) {
					_errHandler.recoverInline(this);
					} else {
						consume();
					}
					setState(612);
					((ShowColumnsContext)_localctx).db = identifier();
					}
				}

				}
				break;
			case 34:
				_localctx = new ShowPartitionsContext(_localctx);
				enterOuterAlt(_localctx, 34);
				{
				setState(615);
				match(SHOW);
				setState(616);
				match(PARTITIONS);
				setState(617);
				tableIdentifier();
				setState(619);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(618);
					partitionSpec();
					}
				}

				}
				break;
			case 35:
				_localctx = new ShowFunctionsContext(_localctx);
				enterOuterAlt(_localctx, 35);
				{
				setState(621);
				match(SHOW);
				setState(623);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,69,_ctx) ) {
				case 1:
					{
					setState(622);
					identifier();
					}
					break;
				}
				setState(625);
				match(FUNCTIONS);
				setState(633);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << JOIN) | (1L << CROSS) | (1L << OUTER) | (1L << INNER) | (1L << LEFT) | (1L << SEMI) | (1L << RIGHT) | (1L << FULL) | (1L << NATURAL) | (1L << ON) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (UNION - 64)) | (1L << (EXCEPT - 64)) | (1L << (SETMINUS - 64)) | (1L << (INTERSECT - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (ANTI - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)) | (1L << (STRING - 193)) | (1L << (IDENTIFIER - 193)) | (1L << (BACKQUOTED_IDENTIFIER - 193)))) != 0)) {
					{
					setState(627);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,70,_ctx) ) {
					case 1:
						{
						setState(626);
						match(LIKE);
						}
						break;
					}
					setState(631);
					switch (_input.LA(1)) {
					case SELECT:
					case FROM:
					case ADD:
					case AS:
					case ALL:
					case DISTINCT:
					case WHERE:
					case GROUP:
					case BY:
					case GROUPING:
					case SETS:
					case CUBE:
					case ROLLUP:
					case ORDER:
					case HAVING:
					case LIMIT:
					case AT:
					case OR:
					case AND:
					case IN:
					case NOT:
					case NO:
					case EXISTS:
					case BETWEEN:
					case LIKE:
					case RLIKE:
					case IS:
					case NULL:
					case TRUE:
					case FALSE:
					case NULLS:
					case ASC:
					case DESC:
					case FOR:
					case INTERVAL:
					case CASE:
					case WHEN:
					case THEN:
					case ELSE:
					case END:
					case JOIN:
					case CROSS:
					case OUTER:
					case INNER:
					case LEFT:
					case SEMI:
					case RIGHT:
					case FULL:
					case NATURAL:
					case ON:
					case LATERAL:
					case WINDOW:
					case OVER:
					case PARTITION:
					case RANGE:
					case ROWS:
					case UNBOUNDED:
					case PRECEDING:
					case FOLLOWING:
					case CURRENT:
					case FIRST:
					case LAST:
					case ROW:
					case WITH:
					case VALUES:
					case CREATE:
					case TABLE:
					case VIEW:
					case REPLACE:
					case INSERT:
					case DELETE:
					case INTO:
					case DESCRIBE:
					case EXPLAIN:
					case FORMAT:
					case LOGICAL:
					case CODEGEN:
					case CAST:
					case SHOW:
					case TABLES:
					case COLUMNS:
					case COLUMN:
					case USE:
					case PARTITIONS:
					case FUNCTIONS:
					case DROP:
					case UNION:
					case EXCEPT:
					case SETMINUS:
					case INTERSECT:
					case TO:
					case TABLESAMPLE:
					case STRATIFY:
					case ALTER:
					case RENAME:
					case ARRAY:
					case MAP:
					case STRUCT:
					case COMMENT:
					case SET:
					case RESET:
					case DATA:
					case START:
					case TRANSACTION:
					case COMMIT:
					case ROLLBACK:
					case MACRO:
					case IF:
					case DIV:
					case PERCENTLIT:
					case BUCKET:
					case OUT:
					case OF:
					case SORT:
					case CLUSTER:
					case DISTRIBUTE:
					case OVERWRITE:
					case TRANSFORM:
					case REDUCE:
					case USING:
					case SERDE:
					case SERDEPROPERTIES:
					case RECORDREADER:
					case RECORDWRITER:
					case DELIMITED:
					case FIELDS:
					case TERMINATED:
					case COLLECTION:
					case ITEMS:
					case KEYS:
					case ESCAPED:
					case LINES:
					case SEPARATED:
					case FUNCTION:
					case EXTENDED:
					case REFRESH:
					case CLEAR:
					case CACHE:
					case UNCACHE:
					case LAZY:
					case FORMATTED:
					case GLOBAL:
					case TEMPORARY:
					case OPTIONS:
					case UNSET:
					case TBLPROPERTIES:
					case DBPROPERTIES:
					case BUCKETS:
					case SKEWED:
					case STORED:
					case DIRECTORIES:
					case LOCATION:
					case EXCHANGE:
					case ARCHIVE:
					case UNARCHIVE:
					case FILEFORMAT:
					case TOUCH:
					case COMPACT:
					case CONCATENATE:
					case CHANGE:
					case CASCADE:
					case RESTRICT:
					case CLUSTERED:
					case SORTED:
					case PURGE:
					case INPUTFORMAT:
					case OUTPUTFORMAT:
					case DATABASE:
					case DATABASES:
					case DFS:
					case TRUNCATE:
					case ANALYZE:
					case COMPUTE:
					case LIST:
					case STATISTICS:
					case PARTITIONED:
					case EXTERNAL:
					case DEFINED:
					case REVOKE:
					case GRANT:
					case LOCK:
					case UNLOCK:
					case MSCK:
					case REPAIR:
					case RECOVER:
					case EXPORT:
					case IMPORT:
					case LOAD:
					case ROLE:
					case ROLES:
					case COMPACTIONS:
					case PRINCIPALS:
					case TRANSACTIONS:
					case INDEX:
					case INDEXES:
					case LOCKS:
					case OPTION:
					case ANTI:
					case LOCAL:
					case INPATH:
					case CURRENT_DATE:
					case CURRENT_TIMESTAMP:
					case IDENTIFIER:
					case BACKQUOTED_IDENTIFIER:
						{
						setState(629);
						qualifiedName();
						}
						break;
					case STRING:
						{
						setState(630);
						((ShowFunctionsContext)_localctx).pattern = match(STRING);
						}
						break;
					default:
						throw new NoViableAltException(this);
					}
					}
				}

				}
				break;
			case 36:
				_localctx = new ShowCreateTableContext(_localctx);
				enterOuterAlt(_localctx, 36);
				{
				setState(635);
				match(SHOW);
				setState(636);
				match(CREATE);
				setState(637);
				match(TABLE);
				setState(638);
				tableIdentifier();
				}
				break;
			case 37:
				_localctx = new DescribeFunctionContext(_localctx);
				enterOuterAlt(_localctx, 37);
				{
				setState(639);
				_la = _input.LA(1);
				if ( !(_la==DESC || _la==DESCRIBE) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(640);
				match(FUNCTION);
				setState(642);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,73,_ctx) ) {
				case 1:
					{
					setState(641);
					match(EXTENDED);
					}
					break;
				}
				setState(644);
				describeFuncName();
				}
				break;
			case 38:
				_localctx = new DescribeDatabaseContext(_localctx);
				enterOuterAlt(_localctx, 38);
				{
				setState(645);
				_la = _input.LA(1);
				if ( !(_la==DESC || _la==DESCRIBE) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(646);
				match(DATABASE);
				setState(648);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,74,_ctx) ) {
				case 1:
					{
					setState(647);
					match(EXTENDED);
					}
					break;
				}
				setState(650);
				identifier();
				}
				break;
			case 39:
				_localctx = new DescribeTableContext(_localctx);
				enterOuterAlt(_localctx, 39);
				{
				setState(651);
				_la = _input.LA(1);
				if ( !(_la==DESC || _la==DESCRIBE) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(653);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,75,_ctx) ) {
				case 1:
					{
					setState(652);
					match(TABLE);
					}
					break;
				}
				setState(656);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,76,_ctx) ) {
				case 1:
					{
					setState(655);
					((DescribeTableContext)_localctx).option = _input.LT(1);
					_la = _input.LA(1);
					if ( !(_la==EXTENDED || _la==FORMATTED) ) {
						((DescribeTableContext)_localctx).option = (Token)_errHandler.recoverInline(this);
					} else {
						consume();
					}
					}
					break;
				}
				setState(658);
				tableIdentifier();
				setState(660);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,77,_ctx) ) {
				case 1:
					{
					setState(659);
					partitionSpec();
					}
					break;
				}
				setState(663);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << JOIN) | (1L << CROSS) | (1L << OUTER) | (1L << INNER) | (1L << LEFT) | (1L << SEMI) | (1L << RIGHT) | (1L << FULL) | (1L << NATURAL) | (1L << ON) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (UNION - 64)) | (1L << (EXCEPT - 64)) | (1L << (SETMINUS - 64)) | (1L << (INTERSECT - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (ANTI - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)) | (1L << (IDENTIFIER - 193)) | (1L << (BACKQUOTED_IDENTIFIER - 193)))) != 0)) {
					{
					setState(662);
					describeColName();
					}
				}

				}
				break;
			case 40:
				_localctx = new RefreshTableContext(_localctx);
				enterOuterAlt(_localctx, 40);
				{
				setState(665);
				match(REFRESH);
				setState(666);
				match(TABLE);
				setState(667);
				tableIdentifier();
				}
				break;
			case 41:
				_localctx = new RefreshResourceContext(_localctx);
				enterOuterAlt(_localctx, 41);
				{
				setState(668);
				match(REFRESH);
				setState(672);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,79,_ctx);
				while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
					if ( _alt==1+1 ) {
						{
						{
						setState(669);
						matchWildcard();
						}
						}
					}
					setState(674);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,79,_ctx);
				}
				}
				break;
			case 42:
				_localctx = new CacheTableContext(_localctx);
				enterOuterAlt(_localctx, 42);
				{
				setState(675);
				match(CACHE);
				setState(677);
				_la = _input.LA(1);
				if (_la==LAZY) {
					{
					setState(676);
					match(LAZY);
					}
				}

				setState(679);
				match(TABLE);
				setState(680);
				tableIdentifier();
				setState(685);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << SELECT) | (1L << FROM) | (1L << AS))) != 0) || ((((_la - 71)) & ~0x3f) == 0 && ((1L << (_la - 71)) & ((1L << (WITH - 71)) | (1L << (VALUES - 71)) | (1L << (TABLE - 71)) | (1L << (INSERT - 71)) | (1L << (MAP - 71)))) != 0) || _la==REDUCE) {
					{
					setState(682);
					_la = _input.LA(1);
					if (_la==AS) {
						{
						setState(681);
						match(AS);
						}
					}

					setState(684);
					query();
					}
				}

				}
				break;
			case 43:
				_localctx = new UncacheTableContext(_localctx);
				enterOuterAlt(_localctx, 43);
				{
				setState(687);
				match(UNCACHE);
				setState(688);
				match(TABLE);
				setState(691);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,83,_ctx) ) {
				case 1:
					{
					setState(689);
					match(IF);
					setState(690);
					match(EXISTS);
					}
					break;
				}
				setState(693);
				tableIdentifier();
				}
				break;
			case 44:
				_localctx = new ClearCacheContext(_localctx);
				enterOuterAlt(_localctx, 44);
				{
				setState(694);
				match(CLEAR);
				setState(695);
				match(CACHE);
				}
				break;
			case 45:
				_localctx = new LoadDataContext(_localctx);
				enterOuterAlt(_localctx, 45);
				{
				setState(696);
				match(LOAD);
				setState(697);
				match(DATA);
				setState(699);
				_la = _input.LA(1);
				if (_la==LOCAL) {
					{
					setState(698);
					match(LOCAL);
					}
				}

				setState(701);
				match(INPATH);
				setState(702);
				((LoadDataContext)_localctx).path = match(STRING);
				setState(704);
				_la = _input.LA(1);
				if (_la==OVERWRITE) {
					{
					setState(703);
					match(OVERWRITE);
					}
				}

				setState(706);
				match(INTO);
				setState(707);
				match(TABLE);
				setState(708);
				tableIdentifier();
				setState(710);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(709);
					partitionSpec();
					}
				}

				}
				break;
			case 46:
				_localctx = new TruncateTableContext(_localctx);
				enterOuterAlt(_localctx, 46);
				{
				setState(712);
				match(TRUNCATE);
				setState(713);
				match(TABLE);
				setState(714);
				tableIdentifier();
				setState(716);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(715);
					partitionSpec();
					}
				}

				}
				break;
			case 47:
				_localctx = new RepairTableContext(_localctx);
				enterOuterAlt(_localctx, 47);
				{
				setState(718);
				match(MSCK);
				setState(719);
				match(REPAIR);
				setState(720);
				match(TABLE);
				setState(721);
				tableIdentifier();
				}
				break;
			case 48:
				_localctx = new ManageResourceContext(_localctx);
				enterOuterAlt(_localctx, 48);
				{
				setState(722);
				((ManageResourceContext)_localctx).op = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==ADD || _la==LIST) ) {
					((ManageResourceContext)_localctx).op = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(723);
				identifier();
				setState(727);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,88,_ctx);
				while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
					if ( _alt==1+1 ) {
						{
						{
						setState(724);
						matchWildcard();
						}
						}
					}
					setState(729);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,88,_ctx);
				}
				}
				break;
			case 49:
				_localctx = new FailNativeCommandContext(_localctx);
				enterOuterAlt(_localctx, 49);
				{
				setState(730);
				match(SET);
				setState(731);
				match(ROLE);
				setState(735);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,89,_ctx);
				while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
					if ( _alt==1+1 ) {
						{
						{
						setState(732);
						matchWildcard();
						}
						}
					}
					setState(737);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,89,_ctx);
				}
				}
				break;
			case 50:
				_localctx = new SetConfigurationContext(_localctx);
				enterOuterAlt(_localctx, 50);
				{
				setState(738);
				match(SET);
				setState(742);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,90,_ctx);
				while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
					if ( _alt==1+1 ) {
						{
						{
						setState(739);
						matchWildcard();
						}
						}
					}
					setState(744);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,90,_ctx);
				}
				}
				break;
			case 51:
				_localctx = new ResetConfigurationContext(_localctx);
				enterOuterAlt(_localctx, 51);
				{
				setState(745);
				match(RESET);
				}
				break;
			case 52:
				_localctx = new FailNativeCommandContext(_localctx);
				enterOuterAlt(_localctx, 52);
				{
				setState(746);
				unsupportedHiveNativeCommands();
				setState(750);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,91,_ctx);
				while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
					if ( _alt==1+1 ) {
						{
						{
						setState(747);
						matchWildcard();
						}
						}
					}
					setState(752);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,91,_ctx);
				}
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class UnsupportedHiveNativeCommandsContext extends ParserRuleContext {
		public Token kw1;
		public Token kw2;
		public Token kw3;
		public Token kw4;
		public Token kw5;
		public Token kw6;
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode ROLE() { return getToken(SqlBaseParser.ROLE, 0); }
		public TerminalNode DROP() { return getToken(SqlBaseParser.DROP, 0); }
		public TerminalNode GRANT() { return getToken(SqlBaseParser.GRANT, 0); }
		public TerminalNode REVOKE() { return getToken(SqlBaseParser.REVOKE, 0); }
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode PRINCIPALS() { return getToken(SqlBaseParser.PRINCIPALS, 0); }
		public TerminalNode ROLES() { return getToken(SqlBaseParser.ROLES, 0); }
		public TerminalNode CURRENT() { return getToken(SqlBaseParser.CURRENT, 0); }
		public TerminalNode EXPORT() { return getToken(SqlBaseParser.EXPORT, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TerminalNode IMPORT() { return getToken(SqlBaseParser.IMPORT, 0); }
		public TerminalNode COMPACTIONS() { return getToken(SqlBaseParser.COMPACTIONS, 0); }
		public TerminalNode TRANSACTIONS() { return getToken(SqlBaseParser.TRANSACTIONS, 0); }
		public TerminalNode INDEXES() { return getToken(SqlBaseParser.INDEXES, 0); }
		public TerminalNode LOCKS() { return getToken(SqlBaseParser.LOCKS, 0); }
		public TerminalNode INDEX() { return getToken(SqlBaseParser.INDEX, 0); }
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode LOCK() { return getToken(SqlBaseParser.LOCK, 0); }
		public TerminalNode DATABASE() { return getToken(SqlBaseParser.DATABASE, 0); }
		public TerminalNode UNLOCK() { return getToken(SqlBaseParser.UNLOCK, 0); }
		public TerminalNode TEMPORARY() { return getToken(SqlBaseParser.TEMPORARY, 0); }
		public TerminalNode MACRO() { return getToken(SqlBaseParser.MACRO, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode CLUSTERED() { return getToken(SqlBaseParser.CLUSTERED, 0); }
		public TerminalNode BY() { return getToken(SqlBaseParser.BY, 0); }
		public TerminalNode SORTED() { return getToken(SqlBaseParser.SORTED, 0); }
		public TerminalNode SKEWED() { return getToken(SqlBaseParser.SKEWED, 0); }
		public TerminalNode STORED() { return getToken(SqlBaseParser.STORED, 0); }
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public TerminalNode DIRECTORIES() { return getToken(SqlBaseParser.DIRECTORIES, 0); }
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public TerminalNode LOCATION() { return getToken(SqlBaseParser.LOCATION, 0); }
		public TerminalNode EXCHANGE() { return getToken(SqlBaseParser.EXCHANGE, 0); }
		public TerminalNode PARTITION() { return getToken(SqlBaseParser.PARTITION, 0); }
		public TerminalNode ARCHIVE() { return getToken(SqlBaseParser.ARCHIVE, 0); }
		public TerminalNode UNARCHIVE() { return getToken(SqlBaseParser.UNARCHIVE, 0); }
		public TerminalNode TOUCH() { return getToken(SqlBaseParser.TOUCH, 0); }
		public TerminalNode COMPACT() { return getToken(SqlBaseParser.COMPACT, 0); }
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public TerminalNode CONCATENATE() { return getToken(SqlBaseParser.CONCATENATE, 0); }
		public TerminalNode FILEFORMAT() { return getToken(SqlBaseParser.FILEFORMAT, 0); }
		public TerminalNode ADD() { return getToken(SqlBaseParser.ADD, 0); }
		public TerminalNode COLUMNS() { return getToken(SqlBaseParser.COLUMNS, 0); }
		public TerminalNode CHANGE() { return getToken(SqlBaseParser.CHANGE, 0); }
		public TerminalNode COLUMN() { return getToken(SqlBaseParser.COLUMN, 0); }
		public TerminalNode REPLACE() { return getToken(SqlBaseParser.REPLACE, 0); }
		public TerminalNode START() { return getToken(SqlBaseParser.START, 0); }
		public TerminalNode TRANSACTION() { return getToken(SqlBaseParser.TRANSACTION, 0); }
		public TerminalNode COMMIT() { return getToken(SqlBaseParser.COMMIT, 0); }
		public TerminalNode ROLLBACK() { return getToken(SqlBaseParser.ROLLBACK, 0); }
		public TerminalNode DFS() { return getToken(SqlBaseParser.DFS, 0); }
		public TerminalNode DELETE() { return getToken(SqlBaseParser.DELETE, 0); }
		public TerminalNode FROM() { return getToken(SqlBaseParser.FROM, 0); }
		public UnsupportedHiveNativeCommandsContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_unsupportedHiveNativeCommands; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterUnsupportedHiveNativeCommands(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitUnsupportedHiveNativeCommands(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitUnsupportedHiveNativeCommands(this);
			else return visitor.visitChildren(this);
		}
	}

	public final UnsupportedHiveNativeCommandsContext unsupportedHiveNativeCommands() throws RecognitionException {
		UnsupportedHiveNativeCommandsContext _localctx = new UnsupportedHiveNativeCommandsContext(_ctx, getState());
		enterRule(_localctx, 10, RULE_unsupportedHiveNativeCommands);
		int _la;
		try {
			setState(944);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,103,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(755);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(CREATE);
				setState(756);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(ROLE);
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(757);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(DROP);
				setState(758);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(ROLE);
				}
				break;
			case 3:
				enterOuterAlt(_localctx, 3);
				{
				setState(759);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(GRANT);
				setState(761);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,93,_ctx) ) {
				case 1:
					{
					setState(760);
					((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(ROLE);
					}
					break;
				}
				}
				break;
			case 4:
				enterOuterAlt(_localctx, 4);
				{
				setState(763);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(REVOKE);
				setState(765);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,94,_ctx) ) {
				case 1:
					{
					setState(764);
					((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(ROLE);
					}
					break;
				}
				}
				break;
			case 5:
				enterOuterAlt(_localctx, 5);
				{
				setState(767);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(768);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(GRANT);
				}
				break;
			case 6:
				enterOuterAlt(_localctx, 6);
				{
				setState(769);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(770);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(ROLE);
				setState(772);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,95,_ctx) ) {
				case 1:
					{
					setState(771);
					((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(GRANT);
					}
					break;
				}
				}
				break;
			case 7:
				enterOuterAlt(_localctx, 7);
				{
				setState(774);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(775);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(PRINCIPALS);
				}
				break;
			case 8:
				enterOuterAlt(_localctx, 8);
				{
				setState(776);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(777);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(ROLES);
				}
				break;
			case 9:
				enterOuterAlt(_localctx, 9);
				{
				setState(778);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(779);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(CURRENT);
				setState(780);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(ROLES);
				}
				break;
			case 10:
				enterOuterAlt(_localctx, 10);
				{
				setState(781);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(EXPORT);
				setState(782);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				}
				break;
			case 11:
				enterOuterAlt(_localctx, 11);
				{
				setState(783);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(IMPORT);
				setState(784);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				}
				break;
			case 12:
				enterOuterAlt(_localctx, 12);
				{
				setState(785);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(786);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(COMPACTIONS);
				}
				break;
			case 13:
				enterOuterAlt(_localctx, 13);
				{
				setState(787);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(788);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(CREATE);
				setState(789);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(TABLE);
				}
				break;
			case 14:
				enterOuterAlt(_localctx, 14);
				{
				setState(790);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(791);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TRANSACTIONS);
				}
				break;
			case 15:
				enterOuterAlt(_localctx, 15);
				{
				setState(792);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(793);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(INDEXES);
				}
				break;
			case 16:
				enterOuterAlt(_localctx, 16);
				{
				setState(794);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(SHOW);
				setState(795);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(LOCKS);
				}
				break;
			case 17:
				enterOuterAlt(_localctx, 17);
				{
				setState(796);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(CREATE);
				setState(797);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(INDEX);
				}
				break;
			case 18:
				enterOuterAlt(_localctx, 18);
				{
				setState(798);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(DROP);
				setState(799);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(INDEX);
				}
				break;
			case 19:
				enterOuterAlt(_localctx, 19);
				{
				setState(800);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(801);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(INDEX);
				}
				break;
			case 20:
				enterOuterAlt(_localctx, 20);
				{
				setState(802);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(LOCK);
				setState(803);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				}
				break;
			case 21:
				enterOuterAlt(_localctx, 21);
				{
				setState(804);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(LOCK);
				setState(805);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(DATABASE);
				}
				break;
			case 22:
				enterOuterAlt(_localctx, 22);
				{
				setState(806);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(UNLOCK);
				setState(807);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				}
				break;
			case 23:
				enterOuterAlt(_localctx, 23);
				{
				setState(808);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(UNLOCK);
				setState(809);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(DATABASE);
				}
				break;
			case 24:
				enterOuterAlt(_localctx, 24);
				{
				setState(810);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(CREATE);
				setState(811);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TEMPORARY);
				setState(812);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(MACRO);
				}
				break;
			case 25:
				enterOuterAlt(_localctx, 25);
				{
				setState(813);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(DROP);
				setState(814);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TEMPORARY);
				setState(815);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(MACRO);
				}
				break;
			case 26:
				enterOuterAlt(_localctx, 26);
				{
				setState(816);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(817);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(818);
				tableIdentifier();
				setState(819);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(NOT);
				setState(820);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(CLUSTERED);
				}
				break;
			case 27:
				enterOuterAlt(_localctx, 27);
				{
				setState(822);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(823);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(824);
				tableIdentifier();
				setState(825);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(CLUSTERED);
				setState(826);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(BY);
				}
				break;
			case 28:
				enterOuterAlt(_localctx, 28);
				{
				setState(828);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(829);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(830);
				tableIdentifier();
				setState(831);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(NOT);
				setState(832);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(SORTED);
				}
				break;
			case 29:
				enterOuterAlt(_localctx, 29);
				{
				setState(834);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(835);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(836);
				tableIdentifier();
				setState(837);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(SKEWED);
				setState(838);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(BY);
				}
				break;
			case 30:
				enterOuterAlt(_localctx, 30);
				{
				setState(840);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(841);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(842);
				tableIdentifier();
				setState(843);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(NOT);
				setState(844);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(SKEWED);
				}
				break;
			case 31:
				enterOuterAlt(_localctx, 31);
				{
				setState(846);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(847);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(848);
				tableIdentifier();
				setState(849);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(NOT);
				setState(850);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(STORED);
				setState(851);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw5 = match(AS);
				setState(852);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw6 = match(DIRECTORIES);
				}
				break;
			case 32:
				enterOuterAlt(_localctx, 32);
				{
				setState(854);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(855);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(856);
				tableIdentifier();
				setState(857);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(SET);
				setState(858);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(SKEWED);
				setState(859);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw5 = match(LOCATION);
				}
				break;
			case 33:
				enterOuterAlt(_localctx, 33);
				{
				setState(861);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(862);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(863);
				tableIdentifier();
				setState(864);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(EXCHANGE);
				setState(865);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(PARTITION);
				}
				break;
			case 34:
				enterOuterAlt(_localctx, 34);
				{
				setState(867);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(868);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(869);
				tableIdentifier();
				setState(870);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(ARCHIVE);
				setState(871);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(PARTITION);
				}
				break;
			case 35:
				enterOuterAlt(_localctx, 35);
				{
				setState(873);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(874);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(875);
				tableIdentifier();
				setState(876);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(UNARCHIVE);
				setState(877);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(PARTITION);
				}
				break;
			case 36:
				enterOuterAlt(_localctx, 36);
				{
				setState(879);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(880);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(881);
				tableIdentifier();
				setState(882);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(TOUCH);
				}
				break;
			case 37:
				enterOuterAlt(_localctx, 37);
				{
				setState(884);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(885);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(886);
				tableIdentifier();
				setState(888);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(887);
					partitionSpec();
					}
				}

				setState(890);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(COMPACT);
				}
				break;
			case 38:
				enterOuterAlt(_localctx, 38);
				{
				setState(892);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(893);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(894);
				tableIdentifier();
				setState(896);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(895);
					partitionSpec();
					}
				}

				setState(898);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(CONCATENATE);
				}
				break;
			case 39:
				enterOuterAlt(_localctx, 39);
				{
				setState(900);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(901);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(902);
				tableIdentifier();
				setState(904);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(903);
					partitionSpec();
					}
				}

				setState(906);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(SET);
				setState(907);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(FILEFORMAT);
				}
				break;
			case 40:
				enterOuterAlt(_localctx, 40);
				{
				setState(909);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(910);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(911);
				tableIdentifier();
				setState(913);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(912);
					partitionSpec();
					}
				}

				setState(915);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(ADD);
				setState(916);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(COLUMNS);
				}
				break;
			case 41:
				enterOuterAlt(_localctx, 41);
				{
				setState(918);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(919);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(920);
				tableIdentifier();
				setState(922);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(921);
					partitionSpec();
					}
				}

				setState(924);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(CHANGE);
				setState(926);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,101,_ctx) ) {
				case 1:
					{
					setState(925);
					((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(COLUMN);
					}
					break;
				}
				}
				break;
			case 42:
				enterOuterAlt(_localctx, 42);
				{
				setState(928);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ALTER);
				setState(929);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TABLE);
				setState(930);
				tableIdentifier();
				setState(932);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(931);
					partitionSpec();
					}
				}

				setState(934);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw3 = match(REPLACE);
				setState(935);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw4 = match(COLUMNS);
				}
				break;
			case 43:
				enterOuterAlt(_localctx, 43);
				{
				setState(937);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(START);
				setState(938);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(TRANSACTION);
				}
				break;
			case 44:
				enterOuterAlt(_localctx, 44);
				{
				setState(939);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(COMMIT);
				}
				break;
			case 45:
				enterOuterAlt(_localctx, 45);
				{
				setState(940);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(ROLLBACK);
				}
				break;
			case 46:
				enterOuterAlt(_localctx, 46);
				{
				setState(941);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(DFS);
				}
				break;
			case 47:
				enterOuterAlt(_localctx, 47);
				{
				setState(942);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw1 = match(DELETE);
				setState(943);
				((UnsupportedHiveNativeCommandsContext)_localctx).kw2 = match(FROM);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class CreateTableHeaderContext extends ParserRuleContext {
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TerminalNode TEMPORARY() { return getToken(SqlBaseParser.TEMPORARY, 0); }
		public TerminalNode EXTERNAL() { return getToken(SqlBaseParser.EXTERNAL, 0); }
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public CreateTableHeaderContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_createTableHeader; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateTableHeader(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateTableHeader(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateTableHeader(this);
			else return visitor.visitChildren(this);
		}
	}

	public final CreateTableHeaderContext createTableHeader() throws RecognitionException {
		CreateTableHeaderContext _localctx = new CreateTableHeaderContext(_ctx, getState());
		enterRule(_localctx, 12, RULE_createTableHeader);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(946);
			match(CREATE);
			setState(948);
			_la = _input.LA(1);
			if (_la==TEMPORARY) {
				{
				setState(947);
				match(TEMPORARY);
				}
			}

			setState(951);
			_la = _input.LA(1);
			if (_la==EXTERNAL) {
				{
				setState(950);
				match(EXTERNAL);
				}
			}

			setState(953);
			match(TABLE);
			setState(957);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,106,_ctx) ) {
			case 1:
				{
				setState(954);
				match(IF);
				setState(955);
				match(NOT);
				setState(956);
				match(EXISTS);
				}
				break;
			}
			setState(959);
			tableIdentifier();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class BucketSpecContext extends ParserRuleContext {
		public TerminalNode CLUSTERED() { return getToken(SqlBaseParser.CLUSTERED, 0); }
		public List<TerminalNode> BY() { return getTokens(SqlBaseParser.BY); }
		public TerminalNode BY(int i) {
			return getToken(SqlBaseParser.BY, i);
		}
		public IdentifierListContext identifierList() {
			return getRuleContext(IdentifierListContext.class,0);
		}
		public TerminalNode INTO() { return getToken(SqlBaseParser.INTO, 0); }
		public TerminalNode INTEGER_VALUE() { return getToken(SqlBaseParser.INTEGER_VALUE, 0); }
		public TerminalNode BUCKETS() { return getToken(SqlBaseParser.BUCKETS, 0); }
		public TerminalNode SORTED() { return getToken(SqlBaseParser.SORTED, 0); }
		public OrderedIdentifierListContext orderedIdentifierList() {
			return getRuleContext(OrderedIdentifierListContext.class,0);
		}
		public BucketSpecContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_bucketSpec; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterBucketSpec(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitBucketSpec(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitBucketSpec(this);
			else return visitor.visitChildren(this);
		}
	}

	public final BucketSpecContext bucketSpec() throws RecognitionException {
		BucketSpecContext _localctx = new BucketSpecContext(_ctx, getState());
		enterRule(_localctx, 14, RULE_bucketSpec);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(961);
			match(CLUSTERED);
			setState(962);
			match(BY);
			setState(963);
			identifierList();
			setState(967);
			_la = _input.LA(1);
			if (_la==SORTED) {
				{
				setState(964);
				match(SORTED);
				setState(965);
				match(BY);
				setState(966);
				orderedIdentifierList();
				}
			}

			setState(969);
			match(INTO);
			setState(970);
			match(INTEGER_VALUE);
			setState(971);
			match(BUCKETS);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class SkewSpecContext extends ParserRuleContext {
		public TerminalNode SKEWED() { return getToken(SqlBaseParser.SKEWED, 0); }
		public TerminalNode BY() { return getToken(SqlBaseParser.BY, 0); }
		public IdentifierListContext identifierList() {
			return getRuleContext(IdentifierListContext.class,0);
		}
		public TerminalNode ON() { return getToken(SqlBaseParser.ON, 0); }
		public ConstantListContext constantList() {
			return getRuleContext(ConstantListContext.class,0);
		}
		public NestedConstantListContext nestedConstantList() {
			return getRuleContext(NestedConstantListContext.class,0);
		}
		public TerminalNode STORED() { return getToken(SqlBaseParser.STORED, 0); }
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public TerminalNode DIRECTORIES() { return getToken(SqlBaseParser.DIRECTORIES, 0); }
		public SkewSpecContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_skewSpec; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSkewSpec(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSkewSpec(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSkewSpec(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SkewSpecContext skewSpec() throws RecognitionException {
		SkewSpecContext _localctx = new SkewSpecContext(_ctx, getState());
		enterRule(_localctx, 16, RULE_skewSpec);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(973);
			match(SKEWED);
			setState(974);
			match(BY);
			setState(975);
			identifierList();
			setState(976);
			match(ON);
			setState(979);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,108,_ctx) ) {
			case 1:
				{
				setState(977);
				constantList();
				}
				break;
			case 2:
				{
				setState(978);
				nestedConstantList();
				}
				break;
			}
			setState(984);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,109,_ctx) ) {
			case 1:
				{
				setState(981);
				match(STORED);
				setState(982);
				match(AS);
				setState(983);
				match(DIRECTORIES);
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class LocationSpecContext extends ParserRuleContext {
		public TerminalNode LOCATION() { return getToken(SqlBaseParser.LOCATION, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public LocationSpecContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_locationSpec; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterLocationSpec(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitLocationSpec(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitLocationSpec(this);
			else return visitor.visitChildren(this);
		}
	}

	public final LocationSpecContext locationSpec() throws RecognitionException {
		LocationSpecContext _localctx = new LocationSpecContext(_ctx, getState());
		enterRule(_localctx, 18, RULE_locationSpec);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(986);
			match(LOCATION);
			setState(987);
			match(STRING);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class QueryContext extends ParserRuleContext {
		public QueryNoWithContext queryNoWith() {
			return getRuleContext(QueryNoWithContext.class,0);
		}
		public CtesContext ctes() {
			return getRuleContext(CtesContext.class,0);
		}
		public QueryContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_query; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQuery(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQuery(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQuery(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QueryContext query() throws RecognitionException {
		QueryContext _localctx = new QueryContext(_ctx, getState());
		enterRule(_localctx, 20, RULE_query);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(990);
			_la = _input.LA(1);
			if (_la==WITH) {
				{
				setState(989);
				ctes();
				}
			}

			setState(992);
			queryNoWith();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class InsertIntoContext extends ParserRuleContext {
		public TerminalNode INSERT() { return getToken(SqlBaseParser.INSERT, 0); }
		public TerminalNode OVERWRITE() { return getToken(SqlBaseParser.OVERWRITE, 0); }
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public TerminalNode INTO() { return getToken(SqlBaseParser.INTO, 0); }
		public InsertIntoContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_insertInto; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterInsertInto(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitInsertInto(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitInsertInto(this);
			else return visitor.visitChildren(this);
		}
	}

	public final InsertIntoContext insertInto() throws RecognitionException {
		InsertIntoContext _localctx = new InsertIntoContext(_ctx, getState());
		enterRule(_localctx, 22, RULE_insertInto);
		int _la;
		try {
			setState(1015);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,115,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(994);
				match(INSERT);
				setState(995);
				match(OVERWRITE);
				setState(996);
				match(TABLE);
				setState(997);
				tableIdentifier();
				setState(1004);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(998);
					partitionSpec();
					setState(1002);
					_la = _input.LA(1);
					if (_la==IF) {
						{
						setState(999);
						match(IF);
						setState(1000);
						match(NOT);
						setState(1001);
						match(EXISTS);
						}
					}

					}
				}

				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(1006);
				match(INSERT);
				setState(1007);
				match(INTO);
				setState(1009);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,113,_ctx) ) {
				case 1:
					{
					setState(1008);
					match(TABLE);
					}
					break;
				}
				setState(1011);
				tableIdentifier();
				setState(1013);
				_la = _input.LA(1);
				if (_la==PARTITION) {
					{
					setState(1012);
					partitionSpec();
					}
				}

				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class PartitionSpecLocationContext extends ParserRuleContext {
		public PartitionSpecContext partitionSpec() {
			return getRuleContext(PartitionSpecContext.class,0);
		}
		public LocationSpecContext locationSpec() {
			return getRuleContext(LocationSpecContext.class,0);
		}
		public PartitionSpecLocationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_partitionSpecLocation; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterPartitionSpecLocation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitPartitionSpecLocation(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitPartitionSpecLocation(this);
			else return visitor.visitChildren(this);
		}
	}

	public final PartitionSpecLocationContext partitionSpecLocation() throws RecognitionException {
		PartitionSpecLocationContext _localctx = new PartitionSpecLocationContext(_ctx, getState());
		enterRule(_localctx, 24, RULE_partitionSpecLocation);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1017);
			partitionSpec();
			setState(1019);
			_la = _input.LA(1);
			if (_la==LOCATION) {
				{
				setState(1018);
				locationSpec();
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class PartitionSpecContext extends ParserRuleContext {
		public TerminalNode PARTITION() { return getToken(SqlBaseParser.PARTITION, 0); }
		public List<PartitionValContext> partitionVal() {
			return getRuleContexts(PartitionValContext.class);
		}
		public PartitionValContext partitionVal(int i) {
			return getRuleContext(PartitionValContext.class,i);
		}
		public PartitionSpecContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_partitionSpec; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterPartitionSpec(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitPartitionSpec(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitPartitionSpec(this);
			else return visitor.visitChildren(this);
		}
	}

	public final PartitionSpecContext partitionSpec() throws RecognitionException {
		PartitionSpecContext _localctx = new PartitionSpecContext(_ctx, getState());
		enterRule(_localctx, 26, RULE_partitionSpec);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1021);
			match(PARTITION);
			setState(1022);
			match(T__0);
			setState(1023);
			partitionVal();
			setState(1028);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(1024);
				match(T__2);
				setState(1025);
				partitionVal();
				}
				}
				setState(1030);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(1031);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class PartitionValContext extends ParserRuleContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode EQ() { return getToken(SqlBaseParser.EQ, 0); }
		public ConstantContext constant() {
			return getRuleContext(ConstantContext.class,0);
		}
		public PartitionValContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_partitionVal; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterPartitionVal(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitPartitionVal(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitPartitionVal(this);
			else return visitor.visitChildren(this);
		}
	}

	public final PartitionValContext partitionVal() throws RecognitionException {
		PartitionValContext _localctx = new PartitionValContext(_ctx, getState());
		enterRule(_localctx, 28, RULE_partitionVal);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1033);
			identifier();
			setState(1036);
			_la = _input.LA(1);
			if (_la==EQ) {
				{
				setState(1034);
				match(EQ);
				setState(1035);
				constant();
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class DescribeFuncNameContext extends ParserRuleContext {
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public ComparisonOperatorContext comparisonOperator() {
			return getRuleContext(ComparisonOperatorContext.class,0);
		}
		public ArithmeticOperatorContext arithmeticOperator() {
			return getRuleContext(ArithmeticOperatorContext.class,0);
		}
		public PredicateOperatorContext predicateOperator() {
			return getRuleContext(PredicateOperatorContext.class,0);
		}
		public DescribeFuncNameContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_describeFuncName; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDescribeFuncName(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDescribeFuncName(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDescribeFuncName(this);
			else return visitor.visitChildren(this);
		}
	}

	public final DescribeFuncNameContext describeFuncName() throws RecognitionException {
		DescribeFuncNameContext _localctx = new DescribeFuncNameContext(_ctx, getState());
		enterRule(_localctx, 30, RULE_describeFuncName);
		try {
			setState(1043);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,119,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(1038);
				qualifiedName();
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(1039);
				match(STRING);
				}
				break;
			case 3:
				enterOuterAlt(_localctx, 3);
				{
				setState(1040);
				comparisonOperator();
				}
				break;
			case 4:
				enterOuterAlt(_localctx, 4);
				{
				setState(1041);
				arithmeticOperator();
				}
				break;
			case 5:
				enterOuterAlt(_localctx, 5);
				{
				setState(1042);
				predicateOperator();
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class DescribeColNameContext extends ParserRuleContext {
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public List<TerminalNode> STRING() { return getTokens(SqlBaseParser.STRING); }
		public TerminalNode STRING(int i) {
			return getToken(SqlBaseParser.STRING, i);
		}
		public DescribeColNameContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_describeColName; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDescribeColName(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDescribeColName(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDescribeColName(this);
			else return visitor.visitChildren(this);
		}
	}

	public final DescribeColNameContext describeColName() throws RecognitionException {
		DescribeColNameContext _localctx = new DescribeColNameContext(_ctx, getState());
		enterRule(_localctx, 32, RULE_describeColName);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1045);
			identifier();
			setState(1053);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__3) {
				{
				{
				setState(1046);
				match(T__3);
				setState(1049);
				switch (_input.LA(1)) {
				case SELECT:
				case FROM:
				case ADD:
				case AS:
				case ALL:
				case DISTINCT:
				case WHERE:
				case GROUP:
				case BY:
				case GROUPING:
				case SETS:
				case CUBE:
				case ROLLUP:
				case ORDER:
				case HAVING:
				case LIMIT:
				case AT:
				case OR:
				case AND:
				case IN:
				case NOT:
				case NO:
				case EXISTS:
				case BETWEEN:
				case LIKE:
				case RLIKE:
				case IS:
				case NULL:
				case TRUE:
				case FALSE:
				case NULLS:
				case ASC:
				case DESC:
				case FOR:
				case INTERVAL:
				case CASE:
				case WHEN:
				case THEN:
				case ELSE:
				case END:
				case JOIN:
				case CROSS:
				case OUTER:
				case INNER:
				case LEFT:
				case SEMI:
				case RIGHT:
				case FULL:
				case NATURAL:
				case ON:
				case LATERAL:
				case WINDOW:
				case OVER:
				case PARTITION:
				case RANGE:
				case ROWS:
				case UNBOUNDED:
				case PRECEDING:
				case FOLLOWING:
				case CURRENT:
				case FIRST:
				case LAST:
				case ROW:
				case WITH:
				case VALUES:
				case CREATE:
				case TABLE:
				case VIEW:
				case REPLACE:
				case INSERT:
				case DELETE:
				case INTO:
				case DESCRIBE:
				case EXPLAIN:
				case FORMAT:
				case LOGICAL:
				case CODEGEN:
				case CAST:
				case SHOW:
				case TABLES:
				case COLUMNS:
				case COLUMN:
				case USE:
				case PARTITIONS:
				case FUNCTIONS:
				case DROP:
				case UNION:
				case EXCEPT:
				case SETMINUS:
				case INTERSECT:
				case TO:
				case TABLESAMPLE:
				case STRATIFY:
				case ALTER:
				case RENAME:
				case ARRAY:
				case MAP:
				case STRUCT:
				case COMMENT:
				case SET:
				case RESET:
				case DATA:
				case START:
				case TRANSACTION:
				case COMMIT:
				case ROLLBACK:
				case MACRO:
				case IF:
				case DIV:
				case PERCENTLIT:
				case BUCKET:
				case OUT:
				case OF:
				case SORT:
				case CLUSTER:
				case DISTRIBUTE:
				case OVERWRITE:
				case TRANSFORM:
				case REDUCE:
				case USING:
				case SERDE:
				case SERDEPROPERTIES:
				case RECORDREADER:
				case RECORDWRITER:
				case DELIMITED:
				case FIELDS:
				case TERMINATED:
				case COLLECTION:
				case ITEMS:
				case KEYS:
				case ESCAPED:
				case LINES:
				case SEPARATED:
				case FUNCTION:
				case EXTENDED:
				case REFRESH:
				case CLEAR:
				case CACHE:
				case UNCACHE:
				case LAZY:
				case FORMATTED:
				case GLOBAL:
				case TEMPORARY:
				case OPTIONS:
				case UNSET:
				case TBLPROPERTIES:
				case DBPROPERTIES:
				case BUCKETS:
				case SKEWED:
				case STORED:
				case DIRECTORIES:
				case LOCATION:
				case EXCHANGE:
				case ARCHIVE:
				case UNARCHIVE:
				case FILEFORMAT:
				case TOUCH:
				case COMPACT:
				case CONCATENATE:
				case CHANGE:
				case CASCADE:
				case RESTRICT:
				case CLUSTERED:
				case SORTED:
				case PURGE:
				case INPUTFORMAT:
				case OUTPUTFORMAT:
				case DATABASE:
				case DATABASES:
				case DFS:
				case TRUNCATE:
				case ANALYZE:
				case COMPUTE:
				case LIST:
				case STATISTICS:
				case PARTITIONED:
				case EXTERNAL:
				case DEFINED:
				case REVOKE:
				case GRANT:
				case LOCK:
				case UNLOCK:
				case MSCK:
				case REPAIR:
				case RECOVER:
				case EXPORT:
				case IMPORT:
				case LOAD:
				case ROLE:
				case ROLES:
				case COMPACTIONS:
				case PRINCIPALS:
				case TRANSACTIONS:
				case INDEX:
				case INDEXES:
				case LOCKS:
				case OPTION:
				case ANTI:
				case LOCAL:
				case INPATH:
				case CURRENT_DATE:
				case CURRENT_TIMESTAMP:
				case IDENTIFIER:
				case BACKQUOTED_IDENTIFIER:
					{
					setState(1047);
					identifier();
					}
					break;
				case STRING:
					{
					setState(1048);
					match(STRING);
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				}
				}
				setState(1055);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class CtesContext extends ParserRuleContext {
		public TerminalNode WITH() { return getToken(SqlBaseParser.WITH, 0); }
		public List<NamedQueryContext> namedQuery() {
			return getRuleContexts(NamedQueryContext.class);
		}
		public NamedQueryContext namedQuery(int i) {
			return getRuleContext(NamedQueryContext.class,i);
		}
		public CtesContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_ctes; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCtes(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCtes(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCtes(this);
			else return visitor.visitChildren(this);
		}
	}

	public final CtesContext ctes() throws RecognitionException {
		CtesContext _localctx = new CtesContext(_ctx, getState());
		enterRule(_localctx, 34, RULE_ctes);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1056);
			match(WITH);
			setState(1057);
			namedQuery();
			setState(1062);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(1058);
				match(T__2);
				setState(1059);
				namedQuery();
				}
				}
				setState(1064);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class NamedQueryContext extends ParserRuleContext {
		public IdentifierContext name;
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public NamedQueryContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_namedQuery; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNamedQuery(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNamedQuery(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNamedQuery(this);
			else return visitor.visitChildren(this);
		}
	}

	public final NamedQueryContext namedQuery() throws RecognitionException {
		NamedQueryContext _localctx = new NamedQueryContext(_ctx, getState());
		enterRule(_localctx, 36, RULE_namedQuery);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1065);
			((NamedQueryContext)_localctx).name = identifier();
			setState(1067);
			_la = _input.LA(1);
			if (_la==AS) {
				{
				setState(1066);
				match(AS);
				}
			}

			setState(1069);
			match(T__0);
			setState(1070);
			query();
			setState(1071);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class TableProviderContext extends ParserRuleContext {
		public TerminalNode USING() { return getToken(SqlBaseParser.USING, 0); }
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public TableProviderContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_tableProvider; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTableProvider(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTableProvider(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTableProvider(this);
			else return visitor.visitChildren(this);
		}
	}

	public final TableProviderContext tableProvider() throws RecognitionException {
		TableProviderContext _localctx = new TableProviderContext(_ctx, getState());
		enterRule(_localctx, 38, RULE_tableProvider);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1073);
			match(USING);
			setState(1074);
			qualifiedName();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class TablePropertyListContext extends ParserRuleContext {
		public List<TablePropertyContext> tableProperty() {
			return getRuleContexts(TablePropertyContext.class);
		}
		public TablePropertyContext tableProperty(int i) {
			return getRuleContext(TablePropertyContext.class,i);
		}
		public TablePropertyListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_tablePropertyList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTablePropertyList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTablePropertyList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTablePropertyList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final TablePropertyListContext tablePropertyList() throws RecognitionException {
		TablePropertyListContext _localctx = new TablePropertyListContext(_ctx, getState());
		enterRule(_localctx, 40, RULE_tablePropertyList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1076);
			match(T__0);
			setState(1077);
			tableProperty();
			setState(1082);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(1078);
				match(T__2);
				setState(1079);
				tableProperty();
				}
				}
				setState(1084);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(1085);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class TablePropertyContext extends ParserRuleContext {
		public TablePropertyKeyContext key;
		public TablePropertyValueContext value;
		public TablePropertyKeyContext tablePropertyKey() {
			return getRuleContext(TablePropertyKeyContext.class,0);
		}
		public TablePropertyValueContext tablePropertyValue() {
			return getRuleContext(TablePropertyValueContext.class,0);
		}
		public TerminalNode EQ() { return getToken(SqlBaseParser.EQ, 0); }
		public TablePropertyContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_tableProperty; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTableProperty(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTableProperty(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTableProperty(this);
			else return visitor.visitChildren(this);
		}
	}

	public final TablePropertyContext tableProperty() throws RecognitionException {
		TablePropertyContext _localctx = new TablePropertyContext(_ctx, getState());
		enterRule(_localctx, 42, RULE_tableProperty);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1087);
			((TablePropertyContext)_localctx).key = tablePropertyKey();
			setState(1092);
			_la = _input.LA(1);
			if (_la==TRUE || _la==FALSE || _la==EQ || ((((_la - 228)) & ~0x3f) == 0 && ((1L << (_la - 228)) & ((1L << (STRING - 228)) | (1L << (INTEGER_VALUE - 228)) | (1L << (DECIMAL_VALUE - 228)))) != 0)) {
				{
				setState(1089);
				_la = _input.LA(1);
				if (_la==EQ) {
					{
					setState(1088);
					match(EQ);
					}
				}

				setState(1091);
				((TablePropertyContext)_localctx).value = tablePropertyValue();
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class TablePropertyKeyContext extends ParserRuleContext {
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TablePropertyKeyContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_tablePropertyKey; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTablePropertyKey(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTablePropertyKey(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTablePropertyKey(this);
			else return visitor.visitChildren(this);
		}
	}

	public final TablePropertyKeyContext tablePropertyKey() throws RecognitionException {
		TablePropertyKeyContext _localctx = new TablePropertyKeyContext(_ctx, getState());
		enterRule(_localctx, 44, RULE_tablePropertyKey);
		int _la;
		try {
			setState(1103);
			switch (_input.LA(1)) {
			case SELECT:
			case FROM:
			case ADD:
			case AS:
			case ALL:
			case DISTINCT:
			case WHERE:
			case GROUP:
			case BY:
			case GROUPING:
			case SETS:
			case CUBE:
			case ROLLUP:
			case ORDER:
			case HAVING:
			case LIMIT:
			case AT:
			case OR:
			case AND:
			case IN:
			case NOT:
			case NO:
			case EXISTS:
			case BETWEEN:
			case LIKE:
			case RLIKE:
			case IS:
			case NULL:
			case TRUE:
			case FALSE:
			case NULLS:
			case ASC:
			case DESC:
			case FOR:
			case INTERVAL:
			case CASE:
			case WHEN:
			case THEN:
			case ELSE:
			case END:
			case JOIN:
			case CROSS:
			case OUTER:
			case INNER:
			case LEFT:
			case SEMI:
			case RIGHT:
			case FULL:
			case NATURAL:
			case ON:
			case LATERAL:
			case WINDOW:
			case OVER:
			case PARTITION:
			case RANGE:
			case ROWS:
			case UNBOUNDED:
			case PRECEDING:
			case FOLLOWING:
			case CURRENT:
			case FIRST:
			case LAST:
			case ROW:
			case WITH:
			case VALUES:
			case CREATE:
			case TABLE:
			case VIEW:
			case REPLACE:
			case INSERT:
			case DELETE:
			case INTO:
			case DESCRIBE:
			case EXPLAIN:
			case FORMAT:
			case LOGICAL:
			case CODEGEN:
			case CAST:
			case SHOW:
			case TABLES:
			case COLUMNS:
			case COLUMN:
			case USE:
			case PARTITIONS:
			case FUNCTIONS:
			case DROP:
			case UNION:
			case EXCEPT:
			case SETMINUS:
			case INTERSECT:
			case TO:
			case TABLESAMPLE:
			case STRATIFY:
			case ALTER:
			case RENAME:
			case ARRAY:
			case MAP:
			case STRUCT:
			case COMMENT:
			case SET:
			case RESET:
			case DATA:
			case START:
			case TRANSACTION:
			case COMMIT:
			case ROLLBACK:
			case MACRO:
			case IF:
			case DIV:
			case PERCENTLIT:
			case BUCKET:
			case OUT:
			case OF:
			case SORT:
			case CLUSTER:
			case DISTRIBUTE:
			case OVERWRITE:
			case TRANSFORM:
			case REDUCE:
			case USING:
			case SERDE:
			case SERDEPROPERTIES:
			case RECORDREADER:
			case RECORDWRITER:
			case DELIMITED:
			case FIELDS:
			case TERMINATED:
			case COLLECTION:
			case ITEMS:
			case KEYS:
			case ESCAPED:
			case LINES:
			case SEPARATED:
			case FUNCTION:
			case EXTENDED:
			case REFRESH:
			case CLEAR:
			case CACHE:
			case UNCACHE:
			case LAZY:
			case FORMATTED:
			case GLOBAL:
			case TEMPORARY:
			case OPTIONS:
			case UNSET:
			case TBLPROPERTIES:
			case DBPROPERTIES:
			case BUCKETS:
			case SKEWED:
			case STORED:
			case DIRECTORIES:
			case LOCATION:
			case EXCHANGE:
			case ARCHIVE:
			case UNARCHIVE:
			case FILEFORMAT:
			case TOUCH:
			case COMPACT:
			case CONCATENATE:
			case CHANGE:
			case CASCADE:
			case RESTRICT:
			case CLUSTERED:
			case SORTED:
			case PURGE:
			case INPUTFORMAT:
			case OUTPUTFORMAT:
			case DATABASE:
			case DATABASES:
			case DFS:
			case TRUNCATE:
			case ANALYZE:
			case COMPUTE:
			case LIST:
			case STATISTICS:
			case PARTITIONED:
			case EXTERNAL:
			case DEFINED:
			case REVOKE:
			case GRANT:
			case LOCK:
			case UNLOCK:
			case MSCK:
			case REPAIR:
			case RECOVER:
			case EXPORT:
			case IMPORT:
			case LOAD:
			case ROLE:
			case ROLES:
			case COMPACTIONS:
			case PRINCIPALS:
			case TRANSACTIONS:
			case INDEX:
			case INDEXES:
			case LOCKS:
			case OPTION:
			case ANTI:
			case LOCAL:
			case INPATH:
			case CURRENT_DATE:
			case CURRENT_TIMESTAMP:
			case IDENTIFIER:
			case BACKQUOTED_IDENTIFIER:
				enterOuterAlt(_localctx, 1);
				{
				setState(1094);
				identifier();
				setState(1099);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__3) {
					{
					{
					setState(1095);
					match(T__3);
					setState(1096);
					identifier();
					}
					}
					setState(1101);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
				break;
			case STRING:
				enterOuterAlt(_localctx, 2);
				{
				setState(1102);
				match(STRING);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class TablePropertyValueContext extends ParserRuleContext {
		public TerminalNode INTEGER_VALUE() { return getToken(SqlBaseParser.INTEGER_VALUE, 0); }
		public TerminalNode DECIMAL_VALUE() { return getToken(SqlBaseParser.DECIMAL_VALUE, 0); }
		public BooleanValueContext booleanValue() {
			return getRuleContext(BooleanValueContext.class,0);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TablePropertyValueContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_tablePropertyValue; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTablePropertyValue(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTablePropertyValue(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTablePropertyValue(this);
			else return visitor.visitChildren(this);
		}
	}

	public final TablePropertyValueContext tablePropertyValue() throws RecognitionException {
		TablePropertyValueContext _localctx = new TablePropertyValueContext(_ctx, getState());
		enterRule(_localctx, 46, RULE_tablePropertyValue);
		try {
			setState(1109);
			switch (_input.LA(1)) {
			case INTEGER_VALUE:
				enterOuterAlt(_localctx, 1);
				{
				setState(1105);
				match(INTEGER_VALUE);
				}
				break;
			case DECIMAL_VALUE:
				enterOuterAlt(_localctx, 2);
				{
				setState(1106);
				match(DECIMAL_VALUE);
				}
				break;
			case TRUE:
			case FALSE:
				enterOuterAlt(_localctx, 3);
				{
				setState(1107);
				booleanValue();
				}
				break;
			case STRING:
				enterOuterAlt(_localctx, 4);
				{
				setState(1108);
				match(STRING);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ConstantListContext extends ParserRuleContext {
		public List<ConstantContext> constant() {
			return getRuleContexts(ConstantContext.class);
		}
		public ConstantContext constant(int i) {
			return getRuleContext(ConstantContext.class,i);
		}
		public ConstantListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_constantList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterConstantList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitConstantList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitConstantList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ConstantListContext constantList() throws RecognitionException {
		ConstantListContext _localctx = new ConstantListContext(_ctx, getState());
		enterRule(_localctx, 48, RULE_constantList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1111);
			match(T__0);
			setState(1112);
			constant();
			setState(1117);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(1113);
				match(T__2);
				setState(1114);
				constant();
				}
				}
				setState(1119);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(1120);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class NestedConstantListContext extends ParserRuleContext {
		public List<ConstantListContext> constantList() {
			return getRuleContexts(ConstantListContext.class);
		}
		public ConstantListContext constantList(int i) {
			return getRuleContext(ConstantListContext.class,i);
		}
		public NestedConstantListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_nestedConstantList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNestedConstantList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNestedConstantList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNestedConstantList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final NestedConstantListContext nestedConstantList() throws RecognitionException {
		NestedConstantListContext _localctx = new NestedConstantListContext(_ctx, getState());
		enterRule(_localctx, 50, RULE_nestedConstantList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1122);
			match(T__0);
			setState(1123);
			constantList();
			setState(1128);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(1124);
				match(T__2);
				setState(1125);
				constantList();
				}
				}
				setState(1130);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(1131);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class CreateFileFormatContext extends ParserRuleContext {
		public TerminalNode STORED() { return getToken(SqlBaseParser.STORED, 0); }
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public FileFormatContext fileFormat() {
			return getRuleContext(FileFormatContext.class,0);
		}
		public TerminalNode BY() { return getToken(SqlBaseParser.BY, 0); }
		public StorageHandlerContext storageHandler() {
			return getRuleContext(StorageHandlerContext.class,0);
		}
		public CreateFileFormatContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_createFileFormat; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCreateFileFormat(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCreateFileFormat(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCreateFileFormat(this);
			else return visitor.visitChildren(this);
		}
	}

	public final CreateFileFormatContext createFileFormat() throws RecognitionException {
		CreateFileFormatContext _localctx = new CreateFileFormatContext(_ctx, getState());
		enterRule(_localctx, 52, RULE_createFileFormat);
		try {
			setState(1139);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,132,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(1133);
				match(STORED);
				setState(1134);
				match(AS);
				setState(1135);
				fileFormat();
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(1136);
				match(STORED);
				setState(1137);
				match(BY);
				setState(1138);
				storageHandler();
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class FileFormatContext extends ParserRuleContext {
		public FileFormatContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_fileFormat; }

		public FileFormatContext() { }
		public void copyFrom(FileFormatContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class TableFileFormatContext extends FileFormatContext {
		public Token inFmt;
		public Token outFmt;
		public TerminalNode INPUTFORMAT() { return getToken(SqlBaseParser.INPUTFORMAT, 0); }
		public TerminalNode OUTPUTFORMAT() { return getToken(SqlBaseParser.OUTPUTFORMAT, 0); }
		public List<TerminalNode> STRING() { return getTokens(SqlBaseParser.STRING); }
		public TerminalNode STRING(int i) {
			return getToken(SqlBaseParser.STRING, i);
		}
		public TableFileFormatContext(FileFormatContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTableFileFormat(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTableFileFormat(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTableFileFormat(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class GenericFileFormatContext extends FileFormatContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public GenericFileFormatContext(FileFormatContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterGenericFileFormat(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitGenericFileFormat(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitGenericFileFormat(this);
			else return visitor.visitChildren(this);
		}
	}

	public final FileFormatContext fileFormat() throws RecognitionException {
		FileFormatContext _localctx = new FileFormatContext(_ctx, getState());
		enterRule(_localctx, 54, RULE_fileFormat);
		try {
			setState(1146);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,133,_ctx) ) {
			case 1:
				_localctx = new TableFileFormatContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(1141);
				match(INPUTFORMAT);
				setState(1142);
				((TableFileFormatContext)_localctx).inFmt = match(STRING);
				setState(1143);
				match(OUTPUTFORMAT);
				setState(1144);
				((TableFileFormatContext)_localctx).outFmt = match(STRING);
				}
				break;
			case 2:
				_localctx = new GenericFileFormatContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(1145);
				identifier();
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class StorageHandlerContext extends ParserRuleContext {
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TerminalNode WITH() { return getToken(SqlBaseParser.WITH, 0); }
		public TerminalNode SERDEPROPERTIES() { return getToken(SqlBaseParser.SERDEPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public StorageHandlerContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_storageHandler; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterStorageHandler(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitStorageHandler(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitStorageHandler(this);
			else return visitor.visitChildren(this);
		}
	}

	public final StorageHandlerContext storageHandler() throws RecognitionException {
		StorageHandlerContext _localctx = new StorageHandlerContext(_ctx, getState());
		enterRule(_localctx, 56, RULE_storageHandler);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1148);
			match(STRING);
			setState(1152);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,134,_ctx) ) {
			case 1:
				{
				setState(1149);
				match(WITH);
				setState(1150);
				match(SERDEPROPERTIES);
				setState(1151);
				tablePropertyList();
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ResourceContext extends ParserRuleContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public ResourceContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_resource; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterResource(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitResource(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitResource(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ResourceContext resource() throws RecognitionException {
		ResourceContext _localctx = new ResourceContext(_ctx, getState());
		enterRule(_localctx, 58, RULE_resource);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1154);
			identifier();
			setState(1155);
			match(STRING);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class QueryNoWithContext extends ParserRuleContext {
		public QueryNoWithContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_queryNoWith; }

		public QueryNoWithContext() { }
		public void copyFrom(QueryNoWithContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class SingleInsertQueryContext extends QueryNoWithContext {
		public QueryTermContext queryTerm() {
			return getRuleContext(QueryTermContext.class,0);
		}
		public QueryOrganizationContext queryOrganization() {
			return getRuleContext(QueryOrganizationContext.class,0);
		}
		public InsertIntoContext insertInto() {
			return getRuleContext(InsertIntoContext.class,0);
		}
		public SingleInsertQueryContext(QueryNoWithContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSingleInsertQuery(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSingleInsertQuery(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSingleInsertQuery(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class MultiInsertQueryContext extends QueryNoWithContext {
		public FromClauseContext fromClause() {
			return getRuleContext(FromClauseContext.class,0);
		}
		public List<MultiInsertQueryBodyContext> multiInsertQueryBody() {
			return getRuleContexts(MultiInsertQueryBodyContext.class);
		}
		public MultiInsertQueryBodyContext multiInsertQueryBody(int i) {
			return getRuleContext(MultiInsertQueryBodyContext.class,i);
		}
		public MultiInsertQueryContext(QueryNoWithContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterMultiInsertQuery(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitMultiInsertQuery(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitMultiInsertQuery(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QueryNoWithContext queryNoWith() throws RecognitionException {
		QueryNoWithContext _localctx = new QueryNoWithContext(_ctx, getState());
		enterRule(_localctx, 60, RULE_queryNoWith);
		int _la;
		try {
			setState(1169);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,137,_ctx) ) {
			case 1:
				_localctx = new SingleInsertQueryContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(1158);
				_la = _input.LA(1);
				if (_la==INSERT) {
					{
					setState(1157);
					insertInto();
					}
				}

				setState(1160);
				queryTerm(0);
				setState(1161);
				queryOrganization();
				}
				break;
			case 2:
				_localctx = new MultiInsertQueryContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(1163);
				fromClause();
				setState(1165);
				_errHandler.sync(this);
				_la = _input.LA(1);
				do {
					{
					{
					setState(1164);
					multiInsertQueryBody();
					}
					}
					setState(1167);
					_errHandler.sync(this);
					_la = _input.LA(1);
				} while ( _la==SELECT || _la==FROM || _la==INSERT || _la==MAP || _la==REDUCE );
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class QueryOrganizationContext extends ParserRuleContext {
		public SortItemContext sortItem;
		public List<SortItemContext> order = new ArrayList<SortItemContext>();
		public ExpressionContext expression;
		public List<ExpressionContext> clusterBy = new ArrayList<ExpressionContext>();
		public List<ExpressionContext> distributeBy = new ArrayList<ExpressionContext>();
		public List<SortItemContext> sort = new ArrayList<SortItemContext>();
		public ExpressionContext limit;
		public TerminalNode ORDER() { return getToken(SqlBaseParser.ORDER, 0); }
		public List<TerminalNode> BY() { return getTokens(SqlBaseParser.BY); }
		public TerminalNode BY(int i) {
			return getToken(SqlBaseParser.BY, i);
		}
		public TerminalNode CLUSTER() { return getToken(SqlBaseParser.CLUSTER, 0); }
		public TerminalNode DISTRIBUTE() { return getToken(SqlBaseParser.DISTRIBUTE, 0); }
		public TerminalNode SORT() { return getToken(SqlBaseParser.SORT, 0); }
		public WindowsContext windows() {
			return getRuleContext(WindowsContext.class,0);
		}
		public TerminalNode LIMIT() { return getToken(SqlBaseParser.LIMIT, 0); }
		public List<SortItemContext> sortItem() {
			return getRuleContexts(SortItemContext.class);
		}
		public SortItemContext sortItem(int i) {
			return getRuleContext(SortItemContext.class,i);
		}
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public QueryOrganizationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_queryOrganization; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQueryOrganization(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQueryOrganization(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQueryOrganization(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QueryOrganizationContext queryOrganization() throws RecognitionException {
		QueryOrganizationContext _localctx = new QueryOrganizationContext(_ctx, getState());
		enterRule(_localctx, 62, RULE_queryOrganization);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1181);
			_la = _input.LA(1);
			if (_la==ORDER) {
				{
				setState(1171);
				match(ORDER);
				setState(1172);
				match(BY);
				setState(1173);
				((QueryOrganizationContext)_localctx).sortItem = sortItem();
				((QueryOrganizationContext)_localctx).order.add(((QueryOrganizationContext)_localctx).sortItem);
				setState(1178);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1174);
					match(T__2);
					setState(1175);
					((QueryOrganizationContext)_localctx).sortItem = sortItem();
					((QueryOrganizationContext)_localctx).order.add(((QueryOrganizationContext)_localctx).sortItem);
					}
					}
					setState(1180);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
			}

			setState(1193);
			_la = _input.LA(1);
			if (_la==CLUSTER) {
				{
				setState(1183);
				match(CLUSTER);
				setState(1184);
				match(BY);
				setState(1185);
				((QueryOrganizationContext)_localctx).expression = expression();
				((QueryOrganizationContext)_localctx).clusterBy.add(((QueryOrganizationContext)_localctx).expression);
				setState(1190);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1186);
					match(T__2);
					setState(1187);
					((QueryOrganizationContext)_localctx).expression = expression();
					((QueryOrganizationContext)_localctx).clusterBy.add(((QueryOrganizationContext)_localctx).expression);
					}
					}
					setState(1192);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
			}

			setState(1205);
			_la = _input.LA(1);
			if (_la==DISTRIBUTE) {
				{
				setState(1195);
				match(DISTRIBUTE);
				setState(1196);
				match(BY);
				setState(1197);
				((QueryOrganizationContext)_localctx).expression = expression();
				((QueryOrganizationContext)_localctx).distributeBy.add(((QueryOrganizationContext)_localctx).expression);
				setState(1202);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1198);
					match(T__2);
					setState(1199);
					((QueryOrganizationContext)_localctx).expression = expression();
					((QueryOrganizationContext)_localctx).distributeBy.add(((QueryOrganizationContext)_localctx).expression);
					}
					}
					setState(1204);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
			}

			setState(1217);
			_la = _input.LA(1);
			if (_la==SORT) {
				{
				setState(1207);
				match(SORT);
				setState(1208);
				match(BY);
				setState(1209);
				((QueryOrganizationContext)_localctx).sortItem = sortItem();
				((QueryOrganizationContext)_localctx).sort.add(((QueryOrganizationContext)_localctx).sortItem);
				setState(1214);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1210);
					match(T__2);
					setState(1211);
					((QueryOrganizationContext)_localctx).sortItem = sortItem();
					((QueryOrganizationContext)_localctx).sort.add(((QueryOrganizationContext)_localctx).sortItem);
					}
					}
					setState(1216);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
			}

			setState(1220);
			_la = _input.LA(1);
			if (_la==WINDOW) {
				{
				setState(1219);
				windows();
				}
			}

			setState(1224);
			_la = _input.LA(1);
			if (_la==LIMIT) {
				{
				setState(1222);
				match(LIMIT);
				setState(1223);
				((QueryOrganizationContext)_localctx).limit = expression();
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class MultiInsertQueryBodyContext extends ParserRuleContext {
		public QuerySpecificationContext querySpecification() {
			return getRuleContext(QuerySpecificationContext.class,0);
		}
		public QueryOrganizationContext queryOrganization() {
			return getRuleContext(QueryOrganizationContext.class,0);
		}
		public InsertIntoContext insertInto() {
			return getRuleContext(InsertIntoContext.class,0);
		}
		public MultiInsertQueryBodyContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_multiInsertQueryBody; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterMultiInsertQueryBody(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitMultiInsertQueryBody(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitMultiInsertQueryBody(this);
			else return visitor.visitChildren(this);
		}
	}

	public final MultiInsertQueryBodyContext multiInsertQueryBody() throws RecognitionException {
		MultiInsertQueryBodyContext _localctx = new MultiInsertQueryBodyContext(_ctx, getState());
		enterRule(_localctx, 64, RULE_multiInsertQueryBody);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1227);
			_la = _input.LA(1);
			if (_la==INSERT) {
				{
				setState(1226);
				insertInto();
				}
			}

			setState(1229);
			querySpecification();
			setState(1230);
			queryOrganization();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class QueryTermContext extends ParserRuleContext {
		public QueryTermContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_queryTerm; }

		public QueryTermContext() { }
		public void copyFrom(QueryTermContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class QueryTermDefaultContext extends QueryTermContext {
		public QueryPrimaryContext queryPrimary() {
			return getRuleContext(QueryPrimaryContext.class,0);
		}
		public QueryTermDefaultContext(QueryTermContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQueryTermDefault(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQueryTermDefault(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQueryTermDefault(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SetOperationContext extends QueryTermContext {
		public QueryTermContext left;
		public Token operator;
		public QueryTermContext right;
		public List<QueryTermContext> queryTerm() {
			return getRuleContexts(QueryTermContext.class);
		}
		public QueryTermContext queryTerm(int i) {
			return getRuleContext(QueryTermContext.class,i);
		}
		public TerminalNode INTERSECT() { return getToken(SqlBaseParser.INTERSECT, 0); }
		public TerminalNode UNION() { return getToken(SqlBaseParser.UNION, 0); }
		public TerminalNode EXCEPT() { return getToken(SqlBaseParser.EXCEPT, 0); }
		public TerminalNode SETMINUS() { return getToken(SqlBaseParser.SETMINUS, 0); }
		public SetQuantifierContext setQuantifier() {
			return getRuleContext(SetQuantifierContext.class,0);
		}
		public SetOperationContext(QueryTermContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSetOperation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSetOperation(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSetOperation(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QueryTermContext queryTerm() throws RecognitionException {
		return queryTerm(0);
	}

	private QueryTermContext queryTerm(int _p) throws RecognitionException {
		ParserRuleContext _parentctx = _ctx;
		int _parentState = getState();
		QueryTermContext _localctx = new QueryTermContext(_ctx, _parentState);
		QueryTermContext _prevctx = _localctx;
		int _startState = 66;
		enterRecursionRule(_localctx, 66, RULE_queryTerm, _p);
		int _la;
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			{
			_localctx = new QueryTermDefaultContext(_localctx);
			_ctx = _localctx;
			_prevctx = _localctx;

			setState(1233);
			queryPrimary();
			}
			_ctx.stop = _input.LT(-1);
			setState(1243);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,150,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					if ( _parseListeners!=null ) triggerExitRuleEvent();
					_prevctx = _localctx;
					{
					{
					_localctx = new SetOperationContext(new QueryTermContext(_parentctx, _parentState));
					((SetOperationContext)_localctx).left = _prevctx;
					pushNewRecursionContext(_localctx, _startState, RULE_queryTerm);
					setState(1235);
					if (!(precpred(_ctx, 1))) throw new FailedPredicateException(this, "precpred(_ctx, 1)");
					setState(1236);
					((SetOperationContext)_localctx).operator = _input.LT(1);
					_la = _input.LA(1);
					if ( !(((((_la - 94)) & ~0x3f) == 0 && ((1L << (_la - 94)) & ((1L << (UNION - 94)) | (1L << (EXCEPT - 94)) | (1L << (SETMINUS - 94)) | (1L << (INTERSECT - 94)))) != 0)) ) {
						((SetOperationContext)_localctx).operator = (Token)_errHandler.recoverInline(this);
					} else {
						consume();
					}
					setState(1238);
					_la = _input.LA(1);
					if (_la==ALL || _la==DISTINCT) {
						{
						setState(1237);
						setQuantifier();
						}
					}

					setState(1240);
					((SetOperationContext)_localctx).right = queryTerm(2);
					}
					}
				}
				setState(1245);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,150,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			unrollRecursionContexts(_parentctx);
		}
		return _localctx;
	}

	public static class QueryPrimaryContext extends ParserRuleContext {
		public QueryPrimaryContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_queryPrimary; }

		public QueryPrimaryContext() { }
		public void copyFrom(QueryPrimaryContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class SubqueryContext extends QueryPrimaryContext {
		public QueryNoWithContext queryNoWith() {
			return getRuleContext(QueryNoWithContext.class,0);
		}
		public SubqueryContext(QueryPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSubquery(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSubquery(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSubquery(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class QueryPrimaryDefaultContext extends QueryPrimaryContext {
		public QuerySpecificationContext querySpecification() {
			return getRuleContext(QuerySpecificationContext.class,0);
		}
		public QueryPrimaryDefaultContext(QueryPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQueryPrimaryDefault(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQueryPrimaryDefault(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQueryPrimaryDefault(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class InlineTableDefault1Context extends QueryPrimaryContext {
		public InlineTableContext inlineTable() {
			return getRuleContext(InlineTableContext.class,0);
		}
		public InlineTableDefault1Context(QueryPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterInlineTableDefault1(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitInlineTableDefault1(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitInlineTableDefault1(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class TableContext extends QueryPrimaryContext {
		public TerminalNode TABLE() { return getToken(SqlBaseParser.TABLE, 0); }
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public TableContext(QueryPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTable(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QueryPrimaryContext queryPrimary() throws RecognitionException {
		QueryPrimaryContext _localctx = new QueryPrimaryContext(_ctx, getState());
		enterRule(_localctx, 68, RULE_queryPrimary);
		try {
			setState(1254);
			switch (_input.LA(1)) {
			case SELECT:
			case FROM:
			case MAP:
			case REDUCE:
				_localctx = new QueryPrimaryDefaultContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(1246);
				querySpecification();
				}
				break;
			case TABLE:
				_localctx = new TableContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(1247);
				match(TABLE);
				setState(1248);
				tableIdentifier();
				}
				break;
			case VALUES:
				_localctx = new InlineTableDefault1Context(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(1249);
				inlineTable();
				}
				break;
			case T__0:
				_localctx = new SubqueryContext(_localctx);
				enterOuterAlt(_localctx, 4);
				{
				setState(1250);
				match(T__0);
				setState(1251);
				queryNoWith();
				setState(1252);
				match(T__1);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class SortItemContext extends ParserRuleContext {
		public Token ordering;
		public Token nullOrder;
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public TerminalNode NULLS() { return getToken(SqlBaseParser.NULLS, 0); }
		public TerminalNode ASC() { return getToken(SqlBaseParser.ASC, 0); }
		public TerminalNode DESC() { return getToken(SqlBaseParser.DESC, 0); }
		public TerminalNode LAST() { return getToken(SqlBaseParser.LAST, 0); }
		public TerminalNode FIRST() { return getToken(SqlBaseParser.FIRST, 0); }
		public SortItemContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_sortItem; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSortItem(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSortItem(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSortItem(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SortItemContext sortItem() throws RecognitionException {
		SortItemContext _localctx = new SortItemContext(_ctx, getState());
		enterRule(_localctx, 70, RULE_sortItem);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1256);
			expression();
			setState(1258);
			_la = _input.LA(1);
			if (_la==ASC || _la==DESC) {
				{
				setState(1257);
				((SortItemContext)_localctx).ordering = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==ASC || _la==DESC) ) {
					((SortItemContext)_localctx).ordering = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				}
			}

			setState(1262);
			_la = _input.LA(1);
			if (_la==NULLS) {
				{
				setState(1260);
				match(NULLS);
				setState(1261);
				((SortItemContext)_localctx).nullOrder = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==FIRST || _la==LAST) ) {
					((SortItemContext)_localctx).nullOrder = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class QuerySpecificationContext extends ParserRuleContext {
		public Token kind;
		public RowFormatContext inRowFormat;
		public Token recordWriter;
		public Token script;
		public RowFormatContext outRowFormat;
		public Token recordReader;
		public BooleanExpressionContext where;
		public BooleanExpressionContext having;
		public TerminalNode USING() { return getToken(SqlBaseParser.USING, 0); }
		public List<TerminalNode> STRING() { return getTokens(SqlBaseParser.STRING); }
		public TerminalNode STRING(int i) {
			return getToken(SqlBaseParser.STRING, i);
		}
		public TerminalNode RECORDWRITER() { return getToken(SqlBaseParser.RECORDWRITER, 0); }
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public TerminalNode RECORDREADER() { return getToken(SqlBaseParser.RECORDREADER, 0); }
		public FromClauseContext fromClause() {
			return getRuleContext(FromClauseContext.class,0);
		}
		public TerminalNode WHERE() { return getToken(SqlBaseParser.WHERE, 0); }
		public TerminalNode SELECT() { return getToken(SqlBaseParser.SELECT, 0); }
		public NamedExpressionSeqContext namedExpressionSeq() {
			return getRuleContext(NamedExpressionSeqContext.class,0);
		}
		public List<RowFormatContext> rowFormat() {
			return getRuleContexts(RowFormatContext.class);
		}
		public RowFormatContext rowFormat(int i) {
			return getRuleContext(RowFormatContext.class,i);
		}
		public List<BooleanExpressionContext> booleanExpression() {
			return getRuleContexts(BooleanExpressionContext.class);
		}
		public BooleanExpressionContext booleanExpression(int i) {
			return getRuleContext(BooleanExpressionContext.class,i);
		}
		public TerminalNode TRANSFORM() { return getToken(SqlBaseParser.TRANSFORM, 0); }
		public TerminalNode MAP() { return getToken(SqlBaseParser.MAP, 0); }
		public TerminalNode REDUCE() { return getToken(SqlBaseParser.REDUCE, 0); }
		public IdentifierSeqContext identifierSeq() {
			return getRuleContext(IdentifierSeqContext.class,0);
		}
		public ColTypeListContext colTypeList() {
			return getRuleContext(ColTypeListContext.class,0);
		}
		public List<LateralViewContext> lateralView() {
			return getRuleContexts(LateralViewContext.class);
		}
		public LateralViewContext lateralView(int i) {
			return getRuleContext(LateralViewContext.class,i);
		}
		public AggregationContext aggregation() {
			return getRuleContext(AggregationContext.class,0);
		}
		public TerminalNode HAVING() { return getToken(SqlBaseParser.HAVING, 0); }
		public WindowsContext windows() {
			return getRuleContext(WindowsContext.class,0);
		}
		public SetQuantifierContext setQuantifier() {
			return getRuleContext(SetQuantifierContext.class,0);
		}
		public QuerySpecificationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_querySpecification; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQuerySpecification(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQuerySpecification(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQuerySpecification(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QuerySpecificationContext querySpecification() throws RecognitionException {
		QuerySpecificationContext _localctx = new QuerySpecificationContext(_ctx, getState());
		enterRule(_localctx, 72, RULE_querySpecification);
		int _la;
		try {
			int _alt;
			setState(1351);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,174,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				{
				{
				setState(1274);
				switch (_input.LA(1)) {
				case SELECT:
					{
					setState(1264);
					match(SELECT);
					setState(1265);
					((QuerySpecificationContext)_localctx).kind = match(TRANSFORM);
					setState(1266);
					match(T__0);
					setState(1267);
					namedExpressionSeq();
					setState(1268);
					match(T__1);
					}
					break;
				case MAP:
					{
					setState(1270);
					((QuerySpecificationContext)_localctx).kind = match(MAP);
					setState(1271);
					namedExpressionSeq();
					}
					break;
				case REDUCE:
					{
					setState(1272);
					((QuerySpecificationContext)_localctx).kind = match(REDUCE);
					setState(1273);
					namedExpressionSeq();
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				}
				setState(1277);
				_la = _input.LA(1);
				if (_la==ROW) {
					{
					setState(1276);
					((QuerySpecificationContext)_localctx).inRowFormat = rowFormat();
					}
				}

				setState(1281);
				_la = _input.LA(1);
				if (_la==RECORDWRITER) {
					{
					setState(1279);
					match(RECORDWRITER);
					setState(1280);
					((QuerySpecificationContext)_localctx).recordWriter = match(STRING);
					}
				}

				setState(1283);
				match(USING);
				setState(1284);
				((QuerySpecificationContext)_localctx).script = match(STRING);
				setState(1297);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,159,_ctx) ) {
				case 1:
					{
					setState(1285);
					match(AS);
					setState(1295);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,158,_ctx) ) {
					case 1:
						{
						setState(1286);
						identifierSeq();
						}
						break;
					case 2:
						{
						setState(1287);
						colTypeList();
						}
						break;
					case 3:
						{
						{
						setState(1288);
						match(T__0);
						setState(1291);
						_errHandler.sync(this);
						switch ( getInterpreter().adaptivePredict(_input,157,_ctx) ) {
						case 1:
							{
							setState(1289);
							identifierSeq();
							}
							break;
						case 2:
							{
							setState(1290);
							colTypeList();
							}
							break;
						}
						setState(1293);
						match(T__1);
						}
						}
						break;
					}
					}
					break;
				}
				setState(1300);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,160,_ctx) ) {
				case 1:
					{
					setState(1299);
					((QuerySpecificationContext)_localctx).outRowFormat = rowFormat();
					}
					break;
				}
				setState(1304);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,161,_ctx) ) {
				case 1:
					{
					setState(1302);
					match(RECORDREADER);
					setState(1303);
					((QuerySpecificationContext)_localctx).recordReader = match(STRING);
					}
					break;
				}
				setState(1307);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,162,_ctx) ) {
				case 1:
					{
					setState(1306);
					fromClause();
					}
					break;
				}
				setState(1311);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,163,_ctx) ) {
				case 1:
					{
					setState(1309);
					match(WHERE);
					setState(1310);
					((QuerySpecificationContext)_localctx).where = booleanExpression(0);
					}
					break;
				}
				}
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				{
				setState(1329);
				switch (_input.LA(1)) {
				case SELECT:
					{
					setState(1313);
					((QuerySpecificationContext)_localctx).kind = match(SELECT);
					setState(1315);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,164,_ctx) ) {
					case 1:
						{
						setState(1314);
						setQuantifier();
						}
						break;
					}
					setState(1317);
					namedExpressionSeq();
					setState(1319);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,165,_ctx) ) {
					case 1:
						{
						setState(1318);
						fromClause();
						}
						break;
					}
					}
					break;
				case FROM:
					{
					setState(1321);
					fromClause();
					setState(1327);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,167,_ctx) ) {
					case 1:
						{
						setState(1322);
						((QuerySpecificationContext)_localctx).kind = match(SELECT);
						setState(1324);
						_errHandler.sync(this);
						switch ( getInterpreter().adaptivePredict(_input,166,_ctx) ) {
						case 1:
							{
							setState(1323);
							setQuantifier();
							}
							break;
						}
						setState(1326);
						namedExpressionSeq();
						}
						break;
					}
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				setState(1334);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,169,_ctx);
				while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
					if ( _alt==1 ) {
						{
						{
						setState(1331);
						lateralView();
						}
						}
					}
					setState(1336);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,169,_ctx);
				}
				setState(1339);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,170,_ctx) ) {
				case 1:
					{
					setState(1337);
					match(WHERE);
					setState(1338);
					((QuerySpecificationContext)_localctx).where = booleanExpression(0);
					}
					break;
				}
				setState(1342);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,171,_ctx) ) {
				case 1:
					{
					setState(1341);
					aggregation();
					}
					break;
				}
				setState(1346);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,172,_ctx) ) {
				case 1:
					{
					setState(1344);
					match(HAVING);
					setState(1345);
					((QuerySpecificationContext)_localctx).having = booleanExpression(0);
					}
					break;
				}
				setState(1349);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,173,_ctx) ) {
				case 1:
					{
					setState(1348);
					windows();
					}
					break;
				}
				}
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class FromClauseContext extends ParserRuleContext {
		public TerminalNode FROM() { return getToken(SqlBaseParser.FROM, 0); }
		public List<RelationContext> relation() {
			return getRuleContexts(RelationContext.class);
		}
		public RelationContext relation(int i) {
			return getRuleContext(RelationContext.class,i);
		}
		public List<LateralViewContext> lateralView() {
			return getRuleContexts(LateralViewContext.class);
		}
		public LateralViewContext lateralView(int i) {
			return getRuleContext(LateralViewContext.class,i);
		}
		public FromClauseContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_fromClause; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterFromClause(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitFromClause(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitFromClause(this);
			else return visitor.visitChildren(this);
		}
	}

	public final FromClauseContext fromClause() throws RecognitionException {
		FromClauseContext _localctx = new FromClauseContext(_ctx, getState());
		enterRule(_localctx, 74, RULE_fromClause);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1353);
			match(FROM);
			setState(1354);
			relation();
			setState(1359);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,175,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1355);
					match(T__2);
					setState(1356);
					relation();
					}
					}
				}
				setState(1361);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,175,_ctx);
			}
			setState(1365);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,176,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1362);
					lateralView();
					}
					}
				}
				setState(1367);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,176,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class AggregationContext extends ParserRuleContext {
		public ExpressionContext expression;
		public List<ExpressionContext> groupingExpressions = new ArrayList<ExpressionContext>();
		public Token kind;
		public TerminalNode GROUP() { return getToken(SqlBaseParser.GROUP, 0); }
		public TerminalNode BY() { return getToken(SqlBaseParser.BY, 0); }
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public TerminalNode WITH() { return getToken(SqlBaseParser.WITH, 0); }
		public TerminalNode SETS() { return getToken(SqlBaseParser.SETS, 0); }
		public List<GroupingSetContext> groupingSet() {
			return getRuleContexts(GroupingSetContext.class);
		}
		public GroupingSetContext groupingSet(int i) {
			return getRuleContext(GroupingSetContext.class,i);
		}
		public TerminalNode ROLLUP() { return getToken(SqlBaseParser.ROLLUP, 0); }
		public TerminalNode CUBE() { return getToken(SqlBaseParser.CUBE, 0); }
		public TerminalNode GROUPING() { return getToken(SqlBaseParser.GROUPING, 0); }
		public AggregationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_aggregation; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterAggregation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitAggregation(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitAggregation(this);
			else return visitor.visitChildren(this);
		}
	}

	public final AggregationContext aggregation() throws RecognitionException {
		AggregationContext _localctx = new AggregationContext(_ctx, getState());
		enterRule(_localctx, 76, RULE_aggregation);
		int _la;
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1368);
			match(GROUP);
			setState(1369);
			match(BY);
			setState(1370);
			((AggregationContext)_localctx).expression = expression();
			((AggregationContext)_localctx).groupingExpressions.add(((AggregationContext)_localctx).expression);
			setState(1375);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,177,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1371);
					match(T__2);
					setState(1372);
					((AggregationContext)_localctx).expression = expression();
					((AggregationContext)_localctx).groupingExpressions.add(((AggregationContext)_localctx).expression);
					}
					}
				}
				setState(1377);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,177,_ctx);
			}
			setState(1395);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,179,_ctx) ) {
			case 1:
				{
				setState(1378);
				match(WITH);
				setState(1379);
				((AggregationContext)_localctx).kind = match(ROLLUP);
				}
				break;
			case 2:
				{
				setState(1380);
				match(WITH);
				setState(1381);
				((AggregationContext)_localctx).kind = match(CUBE);
				}
				break;
			case 3:
				{
				setState(1382);
				((AggregationContext)_localctx).kind = match(GROUPING);
				setState(1383);
				match(SETS);
				setState(1384);
				match(T__0);
				setState(1385);
				groupingSet();
				setState(1390);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1386);
					match(T__2);
					setState(1387);
					groupingSet();
					}
					}
					setState(1392);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				setState(1393);
				match(T__1);
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class GroupingSetContext extends ParserRuleContext {
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public GroupingSetContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_groupingSet; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterGroupingSet(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitGroupingSet(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitGroupingSet(this);
			else return visitor.visitChildren(this);
		}
	}

	public final GroupingSetContext groupingSet() throws RecognitionException {
		GroupingSetContext _localctx = new GroupingSetContext(_ctx, getState());
		enterRule(_localctx, 78, RULE_groupingSet);
		int _la;
		try {
			setState(1410);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,182,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(1397);
				match(T__0);
				setState(1406);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << JOIN) | (1L << CROSS) | (1L << OUTER) | (1L << INNER) | (1L << LEFT) | (1L << SEMI) | (1L << RIGHT) | (1L << FULL) | (1L << NATURAL) | (1L << ON) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (UNION - 64)) | (1L << (EXCEPT - 64)) | (1L << (SETMINUS - 64)) | (1L << (INTERSECT - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)) | (1L << (PLUS - 64)) | (1L << (MINUS - 64)) | (1L << (ASTERISK - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (TILDE - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (ANTI - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)) | (1L << (STRING - 193)) | (1L << (BIGINT_LITERAL - 193)) | (1L << (SMALLINT_LITERAL - 193)) | (1L << (TINYINT_LITERAL - 193)) | (1L << (INTEGER_VALUE - 193)) | (1L << (DECIMAL_VALUE - 193)) | (1L << (DOUBLE_LITERAL - 193)) | (1L << (BIGDECIMAL_LITERAL - 193)) | (1L << (IDENTIFIER - 193)) | (1L << (BACKQUOTED_IDENTIFIER - 193)))) != 0)) {
					{
					setState(1398);
					expression();
					setState(1403);
					_errHandler.sync(this);
					_la = _input.LA(1);
					while (_la==T__2) {
						{
						{
						setState(1399);
						match(T__2);
						setState(1400);
						expression();
						}
						}
						setState(1405);
						_errHandler.sync(this);
						_la = _input.LA(1);
					}
					}
				}

				setState(1408);
				match(T__1);
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(1409);
				expression();
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class LateralViewContext extends ParserRuleContext {
		public IdentifierContext tblName;
		public IdentifierContext identifier;
		public List<IdentifierContext> colName = new ArrayList<IdentifierContext>();
		public TerminalNode LATERAL() { return getToken(SqlBaseParser.LATERAL, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public TerminalNode OUTER() { return getToken(SqlBaseParser.OUTER, 0); }
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public LateralViewContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_lateralView; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterLateralView(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitLateralView(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitLateralView(this);
			else return visitor.visitChildren(this);
		}
	}

	public final LateralViewContext lateralView() throws RecognitionException {
		LateralViewContext _localctx = new LateralViewContext(_ctx, getState());
		enterRule(_localctx, 80, RULE_lateralView);
		int _la;
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1412);
			match(LATERAL);
			setState(1413);
			match(VIEW);
			setState(1415);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,183,_ctx) ) {
			case 1:
				{
				setState(1414);
				match(OUTER);
				}
				break;
			}
			setState(1417);
			qualifiedName();
			setState(1418);
			match(T__0);
			setState(1427);
			_la = _input.LA(1);
			if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << JOIN) | (1L << CROSS) | (1L << OUTER) | (1L << INNER) | (1L << LEFT) | (1L << SEMI) | (1L << RIGHT) | (1L << FULL) | (1L << NATURAL) | (1L << ON) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (UNION - 64)) | (1L << (EXCEPT - 64)) | (1L << (SETMINUS - 64)) | (1L << (INTERSECT - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)) | (1L << (PLUS - 64)) | (1L << (MINUS - 64)) | (1L << (ASTERISK - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (TILDE - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (ANTI - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)) | (1L << (STRING - 193)) | (1L << (BIGINT_LITERAL - 193)) | (1L << (SMALLINT_LITERAL - 193)) | (1L << (TINYINT_LITERAL - 193)) | (1L << (INTEGER_VALUE - 193)) | (1L << (DECIMAL_VALUE - 193)) | (1L << (DOUBLE_LITERAL - 193)) | (1L << (BIGDECIMAL_LITERAL - 193)) | (1L << (IDENTIFIER - 193)) | (1L << (BACKQUOTED_IDENTIFIER - 193)))) != 0)) {
				{
				setState(1419);
				expression();
				setState(1424);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1420);
					match(T__2);
					setState(1421);
					expression();
					}
					}
					setState(1426);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
			}

			setState(1429);
			match(T__1);
			setState(1430);
			((LateralViewContext)_localctx).tblName = identifier();
			setState(1442);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,188,_ctx) ) {
			case 1:
				{
				setState(1432);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,186,_ctx) ) {
				case 1:
					{
					setState(1431);
					match(AS);
					}
					break;
				}
				setState(1434);
				((LateralViewContext)_localctx).identifier = identifier();
				((LateralViewContext)_localctx).colName.add(((LateralViewContext)_localctx).identifier);
				setState(1439);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,187,_ctx);
				while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
					if ( _alt==1 ) {
						{
						{
						setState(1435);
						match(T__2);
						setState(1436);
						((LateralViewContext)_localctx).identifier = identifier();
						((LateralViewContext)_localctx).colName.add(((LateralViewContext)_localctx).identifier);
						}
						}
					}
					setState(1441);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,187,_ctx);
				}
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class SetQuantifierContext extends ParserRuleContext {
		public TerminalNode DISTINCT() { return getToken(SqlBaseParser.DISTINCT, 0); }
		public TerminalNode ALL() { return getToken(SqlBaseParser.ALL, 0); }
		public SetQuantifierContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_setQuantifier; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSetQuantifier(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSetQuantifier(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSetQuantifier(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SetQuantifierContext setQuantifier() throws RecognitionException {
		SetQuantifierContext _localctx = new SetQuantifierContext(_ctx, getState());
		enterRule(_localctx, 82, RULE_setQuantifier);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1444);
			_la = _input.LA(1);
			if ( !(_la==ALL || _la==DISTINCT) ) {
			_errHandler.recoverInline(this);
			} else {
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class RelationContext extends ParserRuleContext {
		public RelationPrimaryContext relationPrimary() {
			return getRuleContext(RelationPrimaryContext.class,0);
		}
		public List<JoinRelationContext> joinRelation() {
			return getRuleContexts(JoinRelationContext.class);
		}
		public JoinRelationContext joinRelation(int i) {
			return getRuleContext(JoinRelationContext.class,i);
		}
		public RelationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_relation; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRelation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRelation(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRelation(this);
			else return visitor.visitChildren(this);
		}
	}

	public final RelationContext relation() throws RecognitionException {
		RelationContext _localctx = new RelationContext(_ctx, getState());
		enterRule(_localctx, 84, RULE_relation);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1446);
			relationPrimary();
			setState(1450);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,189,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1447);
					joinRelation();
					}
					}
				}
				setState(1452);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,189,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class JoinRelationContext extends ParserRuleContext {
		public RelationPrimaryContext right;
		public TerminalNode JOIN() { return getToken(SqlBaseParser.JOIN, 0); }
		public RelationPrimaryContext relationPrimary() {
			return getRuleContext(RelationPrimaryContext.class,0);
		}
		public JoinTypeContext joinType() {
			return getRuleContext(JoinTypeContext.class,0);
		}
		public JoinCriteriaContext joinCriteria() {
			return getRuleContext(JoinCriteriaContext.class,0);
		}
		public TerminalNode NATURAL() { return getToken(SqlBaseParser.NATURAL, 0); }
		public JoinRelationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_joinRelation; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterJoinRelation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitJoinRelation(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitJoinRelation(this);
			else return visitor.visitChildren(this);
		}
	}

	public final JoinRelationContext joinRelation() throws RecognitionException {
		JoinRelationContext _localctx = new JoinRelationContext(_ctx, getState());
		enterRule(_localctx, 86, RULE_joinRelation);
		try {
			setState(1464);
			switch (_input.LA(1)) {
			case JOIN:
			case CROSS:
			case INNER:
			case LEFT:
			case RIGHT:
			case FULL:
			case ANTI:
				enterOuterAlt(_localctx, 1);
				{
				{
				setState(1453);
				joinType();
				}
				setState(1454);
				match(JOIN);
				setState(1455);
				((JoinRelationContext)_localctx).right = relationPrimary();
				setState(1457);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,190,_ctx) ) {
				case 1:
					{
					setState(1456);
					joinCriteria();
					}
					break;
				}
				}
				break;
			case NATURAL:
				enterOuterAlt(_localctx, 2);
				{
				setState(1459);
				match(NATURAL);
				setState(1460);
				joinType();
				setState(1461);
				match(JOIN);
				setState(1462);
				((JoinRelationContext)_localctx).right = relationPrimary();
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class JoinTypeContext extends ParserRuleContext {
		public TerminalNode INNER() { return getToken(SqlBaseParser.INNER, 0); }
		public TerminalNode CROSS() { return getToken(SqlBaseParser.CROSS, 0); }
		public TerminalNode LEFT() { return getToken(SqlBaseParser.LEFT, 0); }
		public TerminalNode OUTER() { return getToken(SqlBaseParser.OUTER, 0); }
		public TerminalNode SEMI() { return getToken(SqlBaseParser.SEMI, 0); }
		public TerminalNode RIGHT() { return getToken(SqlBaseParser.RIGHT, 0); }
		public TerminalNode FULL() { return getToken(SqlBaseParser.FULL, 0); }
		public TerminalNode ANTI() { return getToken(SqlBaseParser.ANTI, 0); }
		public JoinTypeContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_joinType; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterJoinType(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitJoinType(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitJoinType(this);
			else return visitor.visitChildren(this);
		}
	}

	public final JoinTypeContext joinType() throws RecognitionException {
		JoinTypeContext _localctx = new JoinTypeContext(_ctx, getState());
		enterRule(_localctx, 88, RULE_joinType);
		int _la;
		try {
			setState(1488);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,197,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(1467);
				_la = _input.LA(1);
				if (_la==INNER) {
					{
					setState(1466);
					match(INNER);
					}
				}

				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(1469);
				match(CROSS);
				}
				break;
			case 3:
				enterOuterAlt(_localctx, 3);
				{
				setState(1470);
				match(LEFT);
				setState(1472);
				_la = _input.LA(1);
				if (_la==OUTER) {
					{
					setState(1471);
					match(OUTER);
					}
				}

				}
				break;
			case 4:
				enterOuterAlt(_localctx, 4);
				{
				setState(1474);
				match(LEFT);
				setState(1475);
				match(SEMI);
				}
				break;
			case 5:
				enterOuterAlt(_localctx, 5);
				{
				setState(1476);
				match(RIGHT);
				setState(1478);
				_la = _input.LA(1);
				if (_la==OUTER) {
					{
					setState(1477);
					match(OUTER);
					}
				}

				}
				break;
			case 6:
				enterOuterAlt(_localctx, 6);
				{
				setState(1480);
				match(FULL);
				setState(1482);
				_la = _input.LA(1);
				if (_la==OUTER) {
					{
					setState(1481);
					match(OUTER);
					}
				}

				}
				break;
			case 7:
				enterOuterAlt(_localctx, 7);
				{
				setState(1485);
				_la = _input.LA(1);
				if (_la==LEFT) {
					{
					setState(1484);
					match(LEFT);
					}
				}

				setState(1487);
				match(ANTI);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class JoinCriteriaContext extends ParserRuleContext {
		public TerminalNode ON() { return getToken(SqlBaseParser.ON, 0); }
		public BooleanExpressionContext booleanExpression() {
			return getRuleContext(BooleanExpressionContext.class,0);
		}
		public TerminalNode USING() { return getToken(SqlBaseParser.USING, 0); }
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public JoinCriteriaContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_joinCriteria; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterJoinCriteria(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitJoinCriteria(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitJoinCriteria(this);
			else return visitor.visitChildren(this);
		}
	}

	public final JoinCriteriaContext joinCriteria() throws RecognitionException {
		JoinCriteriaContext _localctx = new JoinCriteriaContext(_ctx, getState());
		enterRule(_localctx, 90, RULE_joinCriteria);
		int _la;
		try {
			setState(1504);
			switch (_input.LA(1)) {
			case ON:
				enterOuterAlt(_localctx, 1);
				{
				setState(1490);
				match(ON);
				setState(1491);
				booleanExpression(0);
				}
				break;
			case USING:
				enterOuterAlt(_localctx, 2);
				{
				setState(1492);
				match(USING);
				setState(1493);
				match(T__0);
				setState(1494);
				identifier();
				setState(1499);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1495);
					match(T__2);
					setState(1496);
					identifier();
					}
					}
					setState(1501);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				setState(1502);
				match(T__1);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class SampleContext extends ParserRuleContext {
		public Token percentage;
		public Token sampleType;
		public Token numerator;
		public Token denominator;
		public TerminalNode TABLESAMPLE() { return getToken(SqlBaseParser.TABLESAMPLE, 0); }
		public TerminalNode BYTELENGTH_LITERAL() { return getToken(SqlBaseParser.BYTELENGTH_LITERAL, 0); }
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public TerminalNode OUT() { return getToken(SqlBaseParser.OUT, 0); }
		public TerminalNode OF() { return getToken(SqlBaseParser.OF, 0); }
		public TerminalNode PERCENTLIT() { return getToken(SqlBaseParser.PERCENTLIT, 0); }
		public TerminalNode ROWS() { return getToken(SqlBaseParser.ROWS, 0); }
		public TerminalNode BUCKET() { return getToken(SqlBaseParser.BUCKET, 0); }
		public List<TerminalNode> INTEGER_VALUE() { return getTokens(SqlBaseParser.INTEGER_VALUE); }
		public TerminalNode INTEGER_VALUE(int i) {
			return getToken(SqlBaseParser.INTEGER_VALUE, i);
		}
		public TerminalNode DECIMAL_VALUE() { return getToken(SqlBaseParser.DECIMAL_VALUE, 0); }
		public TerminalNode ON() { return getToken(SqlBaseParser.ON, 0); }
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public SampleContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_sample; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSample(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSample(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSample(this);
			else return visitor.visitChildren(this);
		}
	}

	public final SampleContext sample() throws RecognitionException {
		SampleContext _localctx = new SampleContext(_ctx, getState());
		enterRule(_localctx, 92, RULE_sample);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1506);
			match(TABLESAMPLE);
			setState(1507);
			match(T__0);
			setState(1529);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,202,_ctx) ) {
			case 1:
				{
				{
				setState(1508);
				((SampleContext)_localctx).percentage = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==INTEGER_VALUE || _la==DECIMAL_VALUE) ) {
					((SampleContext)_localctx).percentage = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(1509);
				((SampleContext)_localctx).sampleType = match(PERCENTLIT);
				}
				}
				break;
			case 2:
				{
				{
				setState(1510);
				expression();
				setState(1511);
				((SampleContext)_localctx).sampleType = match(ROWS);
				}
				}
				break;
			case 3:
				{
				setState(1513);
				((SampleContext)_localctx).sampleType = match(BYTELENGTH_LITERAL);
				}
				break;
			case 4:
				{
				{
				setState(1514);
				((SampleContext)_localctx).sampleType = match(BUCKET);
				setState(1515);
				((SampleContext)_localctx).numerator = match(INTEGER_VALUE);
				setState(1516);
				match(OUT);
				setState(1517);
				match(OF);
				setState(1518);
				((SampleContext)_localctx).denominator = match(INTEGER_VALUE);
				setState(1527);
				_la = _input.LA(1);
				if (_la==ON) {
					{
					setState(1519);
					match(ON);
					setState(1525);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,200,_ctx) ) {
					case 1:
						{
						setState(1520);
						identifier();
						}
						break;
					case 2:
						{
						setState(1521);
						qualifiedName();
						setState(1522);
						match(T__0);
						setState(1523);
						match(T__1);
						}
						break;
					}
					}
				}

				}
				}
				break;
			}
			setState(1531);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IdentifierListContext extends ParserRuleContext {
		public IdentifierSeqContext identifierSeq() {
			return getRuleContext(IdentifierSeqContext.class,0);
		}
		public IdentifierListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_identifierList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIdentifierList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIdentifierList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIdentifierList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IdentifierListContext identifierList() throws RecognitionException {
		IdentifierListContext _localctx = new IdentifierListContext(_ctx, getState());
		enterRule(_localctx, 94, RULE_identifierList);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1533);
			match(T__0);
			setState(1534);
			identifierSeq();
			setState(1535);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IdentifierSeqContext extends ParserRuleContext {
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public IdentifierSeqContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_identifierSeq; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIdentifierSeq(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIdentifierSeq(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIdentifierSeq(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IdentifierSeqContext identifierSeq() throws RecognitionException {
		IdentifierSeqContext _localctx = new IdentifierSeqContext(_ctx, getState());
		enterRule(_localctx, 96, RULE_identifierSeq);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1537);
			identifier();
			setState(1542);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,203,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1538);
					match(T__2);
					setState(1539);
					identifier();
					}
					}
				}
				setState(1544);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,203,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class OrderedIdentifierListContext extends ParserRuleContext {
		public List<OrderedIdentifierContext> orderedIdentifier() {
			return getRuleContexts(OrderedIdentifierContext.class);
		}
		public OrderedIdentifierContext orderedIdentifier(int i) {
			return getRuleContext(OrderedIdentifierContext.class,i);
		}
		public OrderedIdentifierListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_orderedIdentifierList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterOrderedIdentifierList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitOrderedIdentifierList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitOrderedIdentifierList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final OrderedIdentifierListContext orderedIdentifierList() throws RecognitionException {
		OrderedIdentifierListContext _localctx = new OrderedIdentifierListContext(_ctx, getState());
		enterRule(_localctx, 98, RULE_orderedIdentifierList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1545);
			match(T__0);
			setState(1546);
			orderedIdentifier();
			setState(1551);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(1547);
				match(T__2);
				setState(1548);
				orderedIdentifier();
				}
				}
				setState(1553);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(1554);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class OrderedIdentifierContext extends ParserRuleContext {
		public Token ordering;
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode ASC() { return getToken(SqlBaseParser.ASC, 0); }
		public TerminalNode DESC() { return getToken(SqlBaseParser.DESC, 0); }
		public OrderedIdentifierContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_orderedIdentifier; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterOrderedIdentifier(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitOrderedIdentifier(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitOrderedIdentifier(this);
			else return visitor.visitChildren(this);
		}
	}

	public final OrderedIdentifierContext orderedIdentifier() throws RecognitionException {
		OrderedIdentifierContext _localctx = new OrderedIdentifierContext(_ctx, getState());
		enterRule(_localctx, 100, RULE_orderedIdentifier);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1556);
			identifier();
			setState(1558);
			_la = _input.LA(1);
			if (_la==ASC || _la==DESC) {
				{
				setState(1557);
				((OrderedIdentifierContext)_localctx).ordering = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==ASC || _la==DESC) ) {
					((OrderedIdentifierContext)_localctx).ordering = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IdentifierCommentListContext extends ParserRuleContext {
		public List<IdentifierCommentContext> identifierComment() {
			return getRuleContexts(IdentifierCommentContext.class);
		}
		public IdentifierCommentContext identifierComment(int i) {
			return getRuleContext(IdentifierCommentContext.class,i);
		}
		public IdentifierCommentListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_identifierCommentList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIdentifierCommentList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIdentifierCommentList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIdentifierCommentList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IdentifierCommentListContext identifierCommentList() throws RecognitionException {
		IdentifierCommentListContext _localctx = new IdentifierCommentListContext(_ctx, getState());
		enterRule(_localctx, 102, RULE_identifierCommentList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1560);
			match(T__0);
			setState(1561);
			identifierComment();
			setState(1566);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(1562);
				match(T__2);
				setState(1563);
				identifierComment();
				}
				}
				setState(1568);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(1569);
			match(T__1);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IdentifierCommentContext extends ParserRuleContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode COMMENT() { return getToken(SqlBaseParser.COMMENT, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public IdentifierCommentContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_identifierComment; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIdentifierComment(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIdentifierComment(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIdentifierComment(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IdentifierCommentContext identifierComment() throws RecognitionException {
		IdentifierCommentContext _localctx = new IdentifierCommentContext(_ctx, getState());
		enterRule(_localctx, 104, RULE_identifierComment);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1571);
			identifier();
			setState(1574);
			_la = _input.LA(1);
			if (_la==COMMENT) {
				{
				setState(1572);
				match(COMMENT);
				setState(1573);
				match(STRING);
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class RelationPrimaryContext extends ParserRuleContext {
		public RelationPrimaryContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_relationPrimary; }

		public RelationPrimaryContext() { }
		public void copyFrom(RelationPrimaryContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class TableValuedFunctionContext extends RelationPrimaryContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public TableValuedFunctionContext(RelationPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTableValuedFunction(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTableValuedFunction(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTableValuedFunction(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class InlineTableDefault2Context extends RelationPrimaryContext {
		public InlineTableContext inlineTable() {
			return getRuleContext(InlineTableContext.class,0);
		}
		public InlineTableDefault2Context(RelationPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterInlineTableDefault2(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitInlineTableDefault2(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitInlineTableDefault2(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class AliasedRelationContext extends RelationPrimaryContext {
		public RelationContext relation() {
			return getRuleContext(RelationContext.class,0);
		}
		public SampleContext sample() {
			return getRuleContext(SampleContext.class,0);
		}
		public StrictIdentifierContext strictIdentifier() {
			return getRuleContext(StrictIdentifierContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public AliasedRelationContext(RelationPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterAliasedRelation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitAliasedRelation(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitAliasedRelation(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class AliasedQueryContext extends RelationPrimaryContext {
		public QueryNoWithContext queryNoWith() {
			return getRuleContext(QueryNoWithContext.class,0);
		}
		public SampleContext sample() {
			return getRuleContext(SampleContext.class,0);
		}
		public StrictIdentifierContext strictIdentifier() {
			return getRuleContext(StrictIdentifierContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public AliasedQueryContext(RelationPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterAliasedQuery(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitAliasedQuery(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitAliasedQuery(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class TableNameContext extends RelationPrimaryContext {
		public TableIdentifierContext tableIdentifier() {
			return getRuleContext(TableIdentifierContext.class,0);
		}
		public SampleContext sample() {
			return getRuleContext(SampleContext.class,0);
		}
		public StrictIdentifierContext strictIdentifier() {
			return getRuleContext(StrictIdentifierContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public TableNameContext(RelationPrimaryContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTableName(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTableName(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTableName(this);
			else return visitor.visitChildren(this);
		}
	}

	public final RelationPrimaryContext relationPrimary() throws RecognitionException {
		RelationPrimaryContext _localctx = new RelationPrimaryContext(_ctx, getState());
		enterRule(_localctx, 106, RULE_relationPrimary);
		int _la;
		try {
			setState(1625);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,219,_ctx) ) {
			case 1:
				_localctx = new TableNameContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(1576);
				tableIdentifier();
				setState(1578);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,208,_ctx) ) {
				case 1:
					{
					setState(1577);
					sample();
					}
					break;
				}
				setState(1584);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,210,_ctx) ) {
				case 1:
					{
					setState(1581);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,209,_ctx) ) {
					case 1:
						{
						setState(1580);
						match(AS);
						}
						break;
					}
					setState(1583);
					strictIdentifier();
					}
					break;
				}
				}
				break;
			case 2:
				_localctx = new AliasedQueryContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(1586);
				match(T__0);
				setState(1587);
				queryNoWith();
				setState(1588);
				match(T__1);
				setState(1590);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,211,_ctx) ) {
				case 1:
					{
					setState(1589);
					sample();
					}
					break;
				}
				setState(1596);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,213,_ctx) ) {
				case 1:
					{
					setState(1593);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,212,_ctx) ) {
					case 1:
						{
						setState(1592);
						match(AS);
						}
						break;
					}
					setState(1595);
					strictIdentifier();
					}
					break;
				}
				}
				break;
			case 3:
				_localctx = new AliasedRelationContext(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(1598);
				match(T__0);
				setState(1599);
				relation();
				setState(1600);
				match(T__1);
				setState(1602);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,214,_ctx) ) {
				case 1:
					{
					setState(1601);
					sample();
					}
					break;
				}
				setState(1608);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,216,_ctx) ) {
				case 1:
					{
					setState(1605);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,215,_ctx) ) {
					case 1:
						{
						setState(1604);
						match(AS);
						}
						break;
					}
					setState(1607);
					strictIdentifier();
					}
					break;
				}
				}
				break;
			case 4:
				_localctx = new InlineTableDefault2Context(_localctx);
				enterOuterAlt(_localctx, 4);
				{
				setState(1610);
				inlineTable();
				}
				break;
			case 5:
				_localctx = new TableValuedFunctionContext(_localctx);
				enterOuterAlt(_localctx, 5);
				{
				setState(1611);
				identifier();
				setState(1612);
				match(T__0);
				setState(1621);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << JOIN) | (1L << CROSS) | (1L << OUTER) | (1L << INNER) | (1L << LEFT) | (1L << SEMI) | (1L << RIGHT) | (1L << FULL) | (1L << NATURAL) | (1L << ON) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (UNION - 64)) | (1L << (EXCEPT - 64)) | (1L << (SETMINUS - 64)) | (1L << (INTERSECT - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)) | (1L << (PLUS - 64)) | (1L << (MINUS - 64)) | (1L << (ASTERISK - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (TILDE - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (ANTI - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)) | (1L << (STRING - 193)) | (1L << (BIGINT_LITERAL - 193)) | (1L << (SMALLINT_LITERAL - 193)) | (1L << (TINYINT_LITERAL - 193)) | (1L << (INTEGER_VALUE - 193)) | (1L << (DECIMAL_VALUE - 193)) | (1L << (DOUBLE_LITERAL - 193)) | (1L << (BIGDECIMAL_LITERAL - 193)) | (1L << (IDENTIFIER - 193)) | (1L << (BACKQUOTED_IDENTIFIER - 193)))) != 0)) {
					{
					setState(1613);
					expression();
					setState(1618);
					_errHandler.sync(this);
					_la = _input.LA(1);
					while (_la==T__2) {
						{
						{
						setState(1614);
						match(T__2);
						setState(1615);
						expression();
						}
						}
						setState(1620);
						_errHandler.sync(this);
						_la = _input.LA(1);
					}
					}
				}

				setState(1623);
				match(T__1);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class InlineTableContext extends ParserRuleContext {
		public TerminalNode VALUES() { return getToken(SqlBaseParser.VALUES, 0); }
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public IdentifierListContext identifierList() {
			return getRuleContext(IdentifierListContext.class,0);
		}
		public InlineTableContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_inlineTable; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterInlineTable(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitInlineTable(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitInlineTable(this);
			else return visitor.visitChildren(this);
		}
	}

	public final InlineTableContext inlineTable() throws RecognitionException {
		InlineTableContext _localctx = new InlineTableContext(_ctx, getState());
		enterRule(_localctx, 108, RULE_inlineTable);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1627);
			match(VALUES);
			setState(1628);
			expression();
			setState(1633);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,220,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1629);
					match(T__2);
					setState(1630);
					expression();
					}
					}
				}
				setState(1635);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,220,_ctx);
			}
			setState(1643);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,223,_ctx) ) {
			case 1:
				{
				setState(1637);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,221,_ctx) ) {
				case 1:
					{
					setState(1636);
					match(AS);
					}
					break;
				}
				setState(1639);
				identifier();
				setState(1641);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,222,_ctx) ) {
				case 1:
					{
					setState(1640);
					identifierList();
					}
					break;
				}
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class RowFormatContext extends ParserRuleContext {
		public RowFormatContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_rowFormat; }

		public RowFormatContext() { }
		public void copyFrom(RowFormatContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class RowFormatSerdeContext extends RowFormatContext {
		public Token name;
		public TablePropertyListContext props;
		public TerminalNode ROW() { return getToken(SqlBaseParser.ROW, 0); }
		public TerminalNode FORMAT() { return getToken(SqlBaseParser.FORMAT, 0); }
		public TerminalNode SERDE() { return getToken(SqlBaseParser.SERDE, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TerminalNode WITH() { return getToken(SqlBaseParser.WITH, 0); }
		public TerminalNode SERDEPROPERTIES() { return getToken(SqlBaseParser.SERDEPROPERTIES, 0); }
		public TablePropertyListContext tablePropertyList() {
			return getRuleContext(TablePropertyListContext.class,0);
		}
		public RowFormatSerdeContext(RowFormatContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRowFormatSerde(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRowFormatSerde(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRowFormatSerde(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RowFormatDelimitedContext extends RowFormatContext {
		public Token fieldsTerminatedBy;
		public Token escapedBy;
		public Token collectionItemsTerminatedBy;
		public Token keysTerminatedBy;
		public Token linesSeparatedBy;
		public Token nullDefinedAs;
		public TerminalNode ROW() { return getToken(SqlBaseParser.ROW, 0); }
		public TerminalNode FORMAT() { return getToken(SqlBaseParser.FORMAT, 0); }
		public TerminalNode DELIMITED() { return getToken(SqlBaseParser.DELIMITED, 0); }
		public TerminalNode FIELDS() { return getToken(SqlBaseParser.FIELDS, 0); }
		public List<TerminalNode> TERMINATED() { return getTokens(SqlBaseParser.TERMINATED); }
		public TerminalNode TERMINATED(int i) {
			return getToken(SqlBaseParser.TERMINATED, i);
		}
		public List<TerminalNode> BY() { return getTokens(SqlBaseParser.BY); }
		public TerminalNode BY(int i) {
			return getToken(SqlBaseParser.BY, i);
		}
		public TerminalNode COLLECTION() { return getToken(SqlBaseParser.COLLECTION, 0); }
		public TerminalNode ITEMS() { return getToken(SqlBaseParser.ITEMS, 0); }
		public TerminalNode MAP() { return getToken(SqlBaseParser.MAP, 0); }
		public TerminalNode KEYS() { return getToken(SqlBaseParser.KEYS, 0); }
		public TerminalNode LINES() { return getToken(SqlBaseParser.LINES, 0); }
		public TerminalNode NULL() { return getToken(SqlBaseParser.NULL, 0); }
		public TerminalNode DEFINED() { return getToken(SqlBaseParser.DEFINED, 0); }
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public List<TerminalNode> STRING() { return getTokens(SqlBaseParser.STRING); }
		public TerminalNode STRING(int i) {
			return getToken(SqlBaseParser.STRING, i);
		}
		public TerminalNode ESCAPED() { return getToken(SqlBaseParser.ESCAPED, 0); }
		public RowFormatDelimitedContext(RowFormatContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRowFormatDelimited(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRowFormatDelimited(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRowFormatDelimited(this);
			else return visitor.visitChildren(this);
		}
	}

	public final RowFormatContext rowFormat() throws RecognitionException {
		RowFormatContext _localctx = new RowFormatContext(_ctx, getState());
		enterRule(_localctx, 110, RULE_rowFormat);
		try {
			setState(1694);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,231,_ctx) ) {
			case 1:
				_localctx = new RowFormatSerdeContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(1645);
				match(ROW);
				setState(1646);
				match(FORMAT);
				setState(1647);
				match(SERDE);
				setState(1648);
				((RowFormatSerdeContext)_localctx).name = match(STRING);
				setState(1652);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,224,_ctx) ) {
				case 1:
					{
					setState(1649);
					match(WITH);
					setState(1650);
					match(SERDEPROPERTIES);
					setState(1651);
					((RowFormatSerdeContext)_localctx).props = tablePropertyList();
					}
					break;
				}
				}
				break;
			case 2:
				_localctx = new RowFormatDelimitedContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(1654);
				match(ROW);
				setState(1655);
				match(FORMAT);
				setState(1656);
				match(DELIMITED);
				setState(1666);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,226,_ctx) ) {
				case 1:
					{
					setState(1657);
					match(FIELDS);
					setState(1658);
					match(TERMINATED);
					setState(1659);
					match(BY);
					setState(1660);
					((RowFormatDelimitedContext)_localctx).fieldsTerminatedBy = match(STRING);
					setState(1664);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,225,_ctx) ) {
					case 1:
						{
						setState(1661);
						match(ESCAPED);
						setState(1662);
						match(BY);
						setState(1663);
						((RowFormatDelimitedContext)_localctx).escapedBy = match(STRING);
						}
						break;
					}
					}
					break;
				}
				setState(1673);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,227,_ctx) ) {
				case 1:
					{
					setState(1668);
					match(COLLECTION);
					setState(1669);
					match(ITEMS);
					setState(1670);
					match(TERMINATED);
					setState(1671);
					match(BY);
					setState(1672);
					((RowFormatDelimitedContext)_localctx).collectionItemsTerminatedBy = match(STRING);
					}
					break;
				}
				setState(1680);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,228,_ctx) ) {
				case 1:
					{
					setState(1675);
					match(MAP);
					setState(1676);
					match(KEYS);
					setState(1677);
					match(TERMINATED);
					setState(1678);
					match(BY);
					setState(1679);
					((RowFormatDelimitedContext)_localctx).keysTerminatedBy = match(STRING);
					}
					break;
				}
				setState(1686);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,229,_ctx) ) {
				case 1:
					{
					setState(1682);
					match(LINES);
					setState(1683);
					match(TERMINATED);
					setState(1684);
					match(BY);
					setState(1685);
					((RowFormatDelimitedContext)_localctx).linesSeparatedBy = match(STRING);
					}
					break;
				}
				setState(1692);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,230,_ctx) ) {
				case 1:
					{
					setState(1688);
					match(NULL);
					setState(1689);
					match(DEFINED);
					setState(1690);
					match(AS);
					setState(1691);
					((RowFormatDelimitedContext)_localctx).nullDefinedAs = match(STRING);
					}
					break;
				}
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class TableIdentifierContext extends ParserRuleContext {
		public IdentifierContext db;
		public IdentifierContext table;
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public TableIdentifierContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_tableIdentifier; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTableIdentifier(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTableIdentifier(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTableIdentifier(this);
			else return visitor.visitChildren(this);
		}
	}

	public final TableIdentifierContext tableIdentifier() throws RecognitionException {
		TableIdentifierContext _localctx = new TableIdentifierContext(_ctx, getState());
		enterRule(_localctx, 112, RULE_tableIdentifier);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1699);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,232,_ctx) ) {
			case 1:
				{
				setState(1696);
				((TableIdentifierContext)_localctx).db = identifier();
				setState(1697);
				match(T__3);
				}
				break;
			}
			setState(1701);
			((TableIdentifierContext)_localctx).table = identifier();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class NamedExpressionContext extends ParserRuleContext {
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public IdentifierListContext identifierList() {
			return getRuleContext(IdentifierListContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public NamedExpressionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_namedExpression; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNamedExpression(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNamedExpression(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNamedExpression(this);
			else return visitor.visitChildren(this);
		}
	}

	public final NamedExpressionContext namedExpression() throws RecognitionException {
		NamedExpressionContext _localctx = new NamedExpressionContext(_ctx, getState());
		enterRule(_localctx, 114, RULE_namedExpression);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1703);
			expression();
			setState(1711);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,235,_ctx) ) {
			case 1:
				{
				setState(1705);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,233,_ctx) ) {
				case 1:
					{
					setState(1704);
					match(AS);
					}
					break;
				}
				setState(1709);
				switch (_input.LA(1)) {
				case SELECT:
				case FROM:
				case ADD:
				case AS:
				case ALL:
				case DISTINCT:
				case WHERE:
				case GROUP:
				case BY:
				case GROUPING:
				case SETS:
				case CUBE:
				case ROLLUP:
				case ORDER:
				case HAVING:
				case LIMIT:
				case AT:
				case OR:
				case AND:
				case IN:
				case NOT:
				case NO:
				case EXISTS:
				case BETWEEN:
				case LIKE:
				case RLIKE:
				case IS:
				case NULL:
				case TRUE:
				case FALSE:
				case NULLS:
				case ASC:
				case DESC:
				case FOR:
				case INTERVAL:
				case CASE:
				case WHEN:
				case THEN:
				case ELSE:
				case END:
				case JOIN:
				case CROSS:
				case OUTER:
				case INNER:
				case LEFT:
				case SEMI:
				case RIGHT:
				case FULL:
				case NATURAL:
				case ON:
				case LATERAL:
				case WINDOW:
				case OVER:
				case PARTITION:
				case RANGE:
				case ROWS:
				case UNBOUNDED:
				case PRECEDING:
				case FOLLOWING:
				case CURRENT:
				case FIRST:
				case LAST:
				case ROW:
				case WITH:
				case VALUES:
				case CREATE:
				case TABLE:
				case VIEW:
				case REPLACE:
				case INSERT:
				case DELETE:
				case INTO:
				case DESCRIBE:
				case EXPLAIN:
				case FORMAT:
				case LOGICAL:
				case CODEGEN:
				case CAST:
				case SHOW:
				case TABLES:
				case COLUMNS:
				case COLUMN:
				case USE:
				case PARTITIONS:
				case FUNCTIONS:
				case DROP:
				case UNION:
				case EXCEPT:
				case SETMINUS:
				case INTERSECT:
				case TO:
				case TABLESAMPLE:
				case STRATIFY:
				case ALTER:
				case RENAME:
				case ARRAY:
				case MAP:
				case STRUCT:
				case COMMENT:
				case SET:
				case RESET:
				case DATA:
				case START:
				case TRANSACTION:
				case COMMIT:
				case ROLLBACK:
				case MACRO:
				case IF:
				case DIV:
				case PERCENTLIT:
				case BUCKET:
				case OUT:
				case OF:
				case SORT:
				case CLUSTER:
				case DISTRIBUTE:
				case OVERWRITE:
				case TRANSFORM:
				case REDUCE:
				case USING:
				case SERDE:
				case SERDEPROPERTIES:
				case RECORDREADER:
				case RECORDWRITER:
				case DELIMITED:
				case FIELDS:
				case TERMINATED:
				case COLLECTION:
				case ITEMS:
				case KEYS:
				case ESCAPED:
				case LINES:
				case SEPARATED:
				case FUNCTION:
				case EXTENDED:
				case REFRESH:
				case CLEAR:
				case CACHE:
				case UNCACHE:
				case LAZY:
				case FORMATTED:
				case GLOBAL:
				case TEMPORARY:
				case OPTIONS:
				case UNSET:
				case TBLPROPERTIES:
				case DBPROPERTIES:
				case BUCKETS:
				case SKEWED:
				case STORED:
				case DIRECTORIES:
				case LOCATION:
				case EXCHANGE:
				case ARCHIVE:
				case UNARCHIVE:
				case FILEFORMAT:
				case TOUCH:
				case COMPACT:
				case CONCATENATE:
				case CHANGE:
				case CASCADE:
				case RESTRICT:
				case CLUSTERED:
				case SORTED:
				case PURGE:
				case INPUTFORMAT:
				case OUTPUTFORMAT:
				case DATABASE:
				case DATABASES:
				case DFS:
				case TRUNCATE:
				case ANALYZE:
				case COMPUTE:
				case LIST:
				case STATISTICS:
				case PARTITIONED:
				case EXTERNAL:
				case DEFINED:
				case REVOKE:
				case GRANT:
				case LOCK:
				case UNLOCK:
				case MSCK:
				case REPAIR:
				case RECOVER:
				case EXPORT:
				case IMPORT:
				case LOAD:
				case ROLE:
				case ROLES:
				case COMPACTIONS:
				case PRINCIPALS:
				case TRANSACTIONS:
				case INDEX:
				case INDEXES:
				case LOCKS:
				case OPTION:
				case ANTI:
				case LOCAL:
				case INPATH:
				case CURRENT_DATE:
				case CURRENT_TIMESTAMP:
				case IDENTIFIER:
				case BACKQUOTED_IDENTIFIER:
					{
					setState(1707);
					identifier();
					}
					break;
				case T__0:
					{
					setState(1708);
					identifierList();
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class NamedExpressionSeqContext extends ParserRuleContext {
		public List<NamedExpressionContext> namedExpression() {
			return getRuleContexts(NamedExpressionContext.class);
		}
		public NamedExpressionContext namedExpression(int i) {
			return getRuleContext(NamedExpressionContext.class,i);
		}
		public NamedExpressionSeqContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_namedExpressionSeq; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNamedExpressionSeq(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNamedExpressionSeq(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNamedExpressionSeq(this);
			else return visitor.visitChildren(this);
		}
	}

	public final NamedExpressionSeqContext namedExpressionSeq() throws RecognitionException {
		NamedExpressionSeqContext _localctx = new NamedExpressionSeqContext(_ctx, getState());
		enterRule(_localctx, 116, RULE_namedExpressionSeq);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1713);
			namedExpression();
			setState(1718);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,236,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1714);
					match(T__2);
					setState(1715);
					namedExpression();
					}
					}
				}
				setState(1720);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,236,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ExpressionContext extends ParserRuleContext {
		public BooleanExpressionContext booleanExpression() {
			return getRuleContext(BooleanExpressionContext.class,0);
		}
		public ExpressionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_expression; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterExpression(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitExpression(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitExpression(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ExpressionContext expression() throws RecognitionException {
		ExpressionContext _localctx = new ExpressionContext(_ctx, getState());
		enterRule(_localctx, 118, RULE_expression);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1721);
			booleanExpression(0);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class BooleanExpressionContext extends ParserRuleContext {
		public BooleanExpressionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_booleanExpression; }

		public BooleanExpressionContext() { }
		public void copyFrom(BooleanExpressionContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class LogicalNotContext extends BooleanExpressionContext {
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public BooleanExpressionContext booleanExpression() {
			return getRuleContext(BooleanExpressionContext.class,0);
		}
		public LogicalNotContext(BooleanExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterLogicalNot(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitLogicalNot(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitLogicalNot(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class BooleanDefaultContext extends BooleanExpressionContext {
		public PredicatedContext predicated() {
			return getRuleContext(PredicatedContext.class,0);
		}
		public BooleanDefaultContext(BooleanExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterBooleanDefault(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitBooleanDefault(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitBooleanDefault(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ExistsContext extends BooleanExpressionContext {
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public ExistsContext(BooleanExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterExists(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitExists(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitExists(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class LogicalBinaryContext extends BooleanExpressionContext {
		public BooleanExpressionContext left;
		public Token operator;
		public BooleanExpressionContext right;
		public List<BooleanExpressionContext> booleanExpression() {
			return getRuleContexts(BooleanExpressionContext.class);
		}
		public BooleanExpressionContext booleanExpression(int i) {
			return getRuleContext(BooleanExpressionContext.class,i);
		}
		public TerminalNode AND() { return getToken(SqlBaseParser.AND, 0); }
		public TerminalNode OR() { return getToken(SqlBaseParser.OR, 0); }
		public LogicalBinaryContext(BooleanExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterLogicalBinary(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitLogicalBinary(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitLogicalBinary(this);
			else return visitor.visitChildren(this);
		}
	}

	public final BooleanExpressionContext booleanExpression() throws RecognitionException {
		return booleanExpression(0);
	}

	private BooleanExpressionContext booleanExpression(int _p) throws RecognitionException {
		ParserRuleContext _parentctx = _ctx;
		int _parentState = getState();
		BooleanExpressionContext _localctx = new BooleanExpressionContext(_ctx, _parentState);
		BooleanExpressionContext _prevctx = _localctx;
		int _startState = 120;
		enterRecursionRule(_localctx, 120, RULE_booleanExpression, _p);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1732);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,237,_ctx) ) {
			case 1:
				{
				_localctx = new LogicalNotContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;

				setState(1724);
				match(NOT);
				setState(1725);
				booleanExpression(5);
				}
				break;
			case 2:
				{
				_localctx = new BooleanDefaultContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1726);
				predicated();
				}
				break;
			case 3:
				{
				_localctx = new ExistsContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1727);
				match(EXISTS);
				setState(1728);
				match(T__0);
				setState(1729);
				query();
				setState(1730);
				match(T__1);
				}
				break;
			}
			_ctx.stop = _input.LT(-1);
			setState(1742);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,239,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					if ( _parseListeners!=null ) triggerExitRuleEvent();
					_prevctx = _localctx;
					{
					setState(1740);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,238,_ctx) ) {
					case 1:
						{
						_localctx = new LogicalBinaryContext(new BooleanExpressionContext(_parentctx, _parentState));
						((LogicalBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_booleanExpression);
						setState(1734);
						if (!(precpred(_ctx, 3))) throw new FailedPredicateException(this, "precpred(_ctx, 3)");
						setState(1735);
						((LogicalBinaryContext)_localctx).operator = match(AND);
						setState(1736);
						((LogicalBinaryContext)_localctx).right = booleanExpression(4);
						}
						break;
					case 2:
						{
						_localctx = new LogicalBinaryContext(new BooleanExpressionContext(_parentctx, _parentState));
						((LogicalBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_booleanExpression);
						setState(1737);
						if (!(precpred(_ctx, 2))) throw new FailedPredicateException(this, "precpred(_ctx, 2)");
						setState(1738);
						((LogicalBinaryContext)_localctx).operator = match(OR);
						setState(1739);
						((LogicalBinaryContext)_localctx).right = booleanExpression(3);
						}
						break;
					}
					}
				}
				setState(1744);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,239,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			unrollRecursionContexts(_parentctx);
		}
		return _localctx;
	}

	public static class PredicatedContext extends ParserRuleContext {
		public ValueExpressionContext valueExpression() {
			return getRuleContext(ValueExpressionContext.class,0);
		}
		public PredicateContext predicate() {
			return getRuleContext(PredicateContext.class,0);
		}
		public PredicatedContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_predicated; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterPredicated(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitPredicated(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitPredicated(this);
			else return visitor.visitChildren(this);
		}
	}

	public final PredicatedContext predicated() throws RecognitionException {
		PredicatedContext _localctx = new PredicatedContext(_ctx, getState());
		enterRule(_localctx, 122, RULE_predicated);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1745);
			valueExpression(0);
			setState(1747);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,240,_ctx) ) {
			case 1:
				{
				setState(1746);
				predicate();
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class PredicateContext extends ParserRuleContext {
		public Token kind;
		public ValueExpressionContext lower;
		public ValueExpressionContext upper;
		public ValueExpressionContext pattern;
		public TerminalNode AND() { return getToken(SqlBaseParser.AND, 0); }
		public TerminalNode BETWEEN() { return getToken(SqlBaseParser.BETWEEN, 0); }
		public List<ValueExpressionContext> valueExpression() {
			return getRuleContexts(ValueExpressionContext.class);
		}
		public ValueExpressionContext valueExpression(int i) {
			return getRuleContext(ValueExpressionContext.class,i);
		}
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public TerminalNode IN() { return getToken(SqlBaseParser.IN, 0); }
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public TerminalNode RLIKE() { return getToken(SqlBaseParser.RLIKE, 0); }
		public TerminalNode LIKE() { return getToken(SqlBaseParser.LIKE, 0); }
		public TerminalNode IS() { return getToken(SqlBaseParser.IS, 0); }
		public TerminalNode NULL() { return getToken(SqlBaseParser.NULL, 0); }
		public PredicateContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_predicate; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterPredicate(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitPredicate(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitPredicate(this);
			else return visitor.visitChildren(this);
		}
	}

	public final PredicateContext predicate() throws RecognitionException {
		PredicateContext _localctx = new PredicateContext(_ctx, getState());
		enterRule(_localctx, 124, RULE_predicate);
		int _la;
		try {
			setState(1790);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,247,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(1750);
				_la = _input.LA(1);
				if (_la==NOT) {
					{
					setState(1749);
					match(NOT);
					}
				}

				setState(1752);
				((PredicateContext)_localctx).kind = match(BETWEEN);
				setState(1753);
				((PredicateContext)_localctx).lower = valueExpression(0);
				setState(1754);
				match(AND);
				setState(1755);
				((PredicateContext)_localctx).upper = valueExpression(0);
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(1758);
				_la = _input.LA(1);
				if (_la==NOT) {
					{
					setState(1757);
					match(NOT);
					}
				}

				setState(1760);
				((PredicateContext)_localctx).kind = match(IN);
				setState(1761);
				match(T__0);
				setState(1762);
				expression();
				setState(1767);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==T__2) {
					{
					{
					setState(1763);
					match(T__2);
					setState(1764);
					expression();
					}
					}
					setState(1769);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				setState(1770);
				match(T__1);
				}
				break;
			case 3:
				enterOuterAlt(_localctx, 3);
				{
				setState(1773);
				_la = _input.LA(1);
				if (_la==NOT) {
					{
					setState(1772);
					match(NOT);
					}
				}

				setState(1775);
				((PredicateContext)_localctx).kind = match(IN);
				setState(1776);
				match(T__0);
				setState(1777);
				query();
				setState(1778);
				match(T__1);
				}
				break;
			case 4:
				enterOuterAlt(_localctx, 4);
				{
				setState(1781);
				_la = _input.LA(1);
				if (_la==NOT) {
					{
					setState(1780);
					match(NOT);
					}
				}

				setState(1783);
				((PredicateContext)_localctx).kind = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==LIKE || _la==RLIKE) ) {
					((PredicateContext)_localctx).kind = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(1784);
				((PredicateContext)_localctx).pattern = valueExpression(0);
				}
				break;
			case 5:
				enterOuterAlt(_localctx, 5);
				{
				setState(1785);
				match(IS);
				setState(1787);
				_la = _input.LA(1);
				if (_la==NOT) {
					{
					setState(1786);
					match(NOT);
					}
				}

				setState(1789);
				((PredicateContext)_localctx).kind = match(NULL);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ValueExpressionContext extends ParserRuleContext {
		public ValueExpressionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_valueExpression; }

		public ValueExpressionContext() { }
		public void copyFrom(ValueExpressionContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class ValueExpressionDefaultContext extends ValueExpressionContext {
		public PrimaryExpressionContext primaryExpression() {
			return getRuleContext(PrimaryExpressionContext.class,0);
		}
		public ValueExpressionDefaultContext(ValueExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterValueExpressionDefault(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitValueExpressionDefault(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitValueExpressionDefault(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ComparisonContext extends ValueExpressionContext {
		public ValueExpressionContext left;
		public ValueExpressionContext right;
		public ComparisonOperatorContext comparisonOperator() {
			return getRuleContext(ComparisonOperatorContext.class,0);
		}
		public List<ValueExpressionContext> valueExpression() {
			return getRuleContexts(ValueExpressionContext.class);
		}
		public ValueExpressionContext valueExpression(int i) {
			return getRuleContext(ValueExpressionContext.class,i);
		}
		public ComparisonContext(ValueExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterComparison(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitComparison(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitComparison(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ArithmeticBinaryContext extends ValueExpressionContext {
		public ValueExpressionContext left;
		public Token operator;
		public ValueExpressionContext right;
		public List<ValueExpressionContext> valueExpression() {
			return getRuleContexts(ValueExpressionContext.class);
		}
		public ValueExpressionContext valueExpression(int i) {
			return getRuleContext(ValueExpressionContext.class,i);
		}
		public TerminalNode ASTERISK() { return getToken(SqlBaseParser.ASTERISK, 0); }
		public TerminalNode SLASH() { return getToken(SqlBaseParser.SLASH, 0); }
		public TerminalNode PERCENT() { return getToken(SqlBaseParser.PERCENT, 0); }
		public TerminalNode DIV() { return getToken(SqlBaseParser.DIV, 0); }
		public TerminalNode PLUS() { return getToken(SqlBaseParser.PLUS, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public TerminalNode AMPERSAND() { return getToken(SqlBaseParser.AMPERSAND, 0); }
		public TerminalNode HAT() { return getToken(SqlBaseParser.HAT, 0); }
		public TerminalNode PIPE() { return getToken(SqlBaseParser.PIPE, 0); }
		public TerminalNode RSHIFT() { return getToken(SqlBaseParser.RSHIFT, 0); }
		public ArithmeticBinaryContext(ValueExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterArithmeticBinary(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitArithmeticBinary(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitArithmeticBinary(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ArithmeticUnaryContext extends ValueExpressionContext {
		public Token operator;
		public ValueExpressionContext valueExpression() {
			return getRuleContext(ValueExpressionContext.class,0);
		}
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public TerminalNode PLUS() { return getToken(SqlBaseParser.PLUS, 0); }
		public TerminalNode TILDE() { return getToken(SqlBaseParser.TILDE, 0); }
		public ArithmeticUnaryContext(ValueExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterArithmeticUnary(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitArithmeticUnary(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitArithmeticUnary(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ValueExpressionContext valueExpression() throws RecognitionException {
		return valueExpression(0);
	}

	private ValueExpressionContext valueExpression(int _p) throws RecognitionException {
		ParserRuleContext _parentctx = _ctx;
		int _parentState = getState();
		ValueExpressionContext _localctx = new ValueExpressionContext(_ctx, _parentState);
		ValueExpressionContext _prevctx = _localctx;
		int _startState = 126;
		enterRecursionRule(_localctx, 126, RULE_valueExpression, _p);
		int _la;
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1796);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,248,_ctx) ) {
			case 1:
				{
				_localctx = new ValueExpressionDefaultContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;

				setState(1793);
				primaryExpression(0);
				}
				break;
			case 2:
				{
				_localctx = new ArithmeticUnaryContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1794);
				((ArithmeticUnaryContext)_localctx).operator = _input.LT(1);
				_la = _input.LA(1);
				if ( !(((((_la - 124)) & ~0x3f) == 0 && ((1L << (_la - 124)) & ((1L << (PLUS - 124)) | (1L << (MINUS - 124)) | (1L << (TILDE - 124)))) != 0)) ) {
					((ArithmeticUnaryContext)_localctx).operator = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				setState(1795);
				valueExpression(8);
				}
				break;
			}
			_ctx.stop = _input.LT(-1);
			setState(1822);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,250,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					if ( _parseListeners!=null ) triggerExitRuleEvent();
					_prevctx = _localctx;
					{
					setState(1820);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,249,_ctx) ) {
					case 1:
						{
						_localctx = new ArithmeticBinaryContext(new ValueExpressionContext(_parentctx, _parentState));
						((ArithmeticBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_valueExpression);
						setState(1798);
						if (!(precpred(_ctx, 7))) throw new FailedPredicateException(this, "precpred(_ctx, 7)");
						setState(1799);
						((ArithmeticBinaryContext)_localctx).operator = _input.LT(1);
						_la = _input.LA(1);
						if ( !(((((_la - 126)) & ~0x3f) == 0 && ((1L << (_la - 126)) & ((1L << (ASTERISK - 126)) | (1L << (SLASH - 126)) | (1L << (PERCENT - 126)) | (1L << (DIV - 126)))) != 0)) ) {
							((ArithmeticBinaryContext)_localctx).operator = (Token)_errHandler.recoverInline(this);
						} else {
							consume();
						}
						setState(1800);
						((ArithmeticBinaryContext)_localctx).right = valueExpression(8);
						}
						break;
					case 2:
						{
						_localctx = new ArithmeticBinaryContext(new ValueExpressionContext(_parentctx, _parentState));
						((ArithmeticBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_valueExpression);
						setState(1801);
						if (!(precpred(_ctx, 6))) throw new FailedPredicateException(this, "precpred(_ctx, 6)");
						setState(1802);
						((ArithmeticBinaryContext)_localctx).operator = _input.LT(1);
						_la = _input.LA(1);
						if ( !(_la==PLUS || _la==MINUS) ) {
							((ArithmeticBinaryContext)_localctx).operator = (Token)_errHandler.recoverInline(this);
						} else {
							consume();
						}
						setState(1803);
						((ArithmeticBinaryContext)_localctx).right = valueExpression(7);
						}
						break;
					case 3:
						{
						_localctx = new ArithmeticBinaryContext(new ValueExpressionContext(_parentctx, _parentState));
						((ArithmeticBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_valueExpression);
						setState(1804);
						if (!(precpred(_ctx, 5))) throw new FailedPredicateException(this, "precpred(_ctx, 5)");
						setState(1805);
						((ArithmeticBinaryContext)_localctx).operator = match(AMPERSAND);
						setState(1806);
						((ArithmeticBinaryContext)_localctx).right = valueExpression(6);
						}
						break;
					case 4:
						{
						_localctx = new ArithmeticBinaryContext(new ValueExpressionContext(_parentctx, _parentState));
						((ArithmeticBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_valueExpression);
						setState(1807);
						if (!(precpred(_ctx, 4))) throw new FailedPredicateException(this, "precpred(_ctx, 4)");
						setState(1808);
						((ArithmeticBinaryContext)_localctx).operator = match(HAT);
						setState(1809);
						((ArithmeticBinaryContext)_localctx).right = valueExpression(5);
						}
						break;
					case 5:
						{
						_localctx = new ArithmeticBinaryContext(new ValueExpressionContext(_parentctx, _parentState));
						((ArithmeticBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_valueExpression);
						setState(1810);
						if (!(precpred(_ctx, 3))) throw new FailedPredicateException(this, "precpred(_ctx, 3)");
						setState(1811);
						((ArithmeticBinaryContext)_localctx).operator = match(PIPE);
						setState(1812);
						((ArithmeticBinaryContext)_localctx).right = valueExpression(4);
						}
						break;
					case 6:
						{
						_localctx = new ArithmeticBinaryContext(new ValueExpressionContext(_parentctx, _parentState));
						((ArithmeticBinaryContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_valueExpression);
						setState(1813);
						if (!(precpred(_ctx, 2))) throw new FailedPredicateException(this, "precpred(_ctx, 2)");
						setState(1814);
						((ArithmeticBinaryContext)_localctx).operator = match(RSHIFT);
						setState(1815);
						((ArithmeticBinaryContext)_localctx).right = valueExpression(3);
						}
						break;
					case 7:
						{
						_localctx = new ComparisonContext(new ValueExpressionContext(_parentctx, _parentState));
						((ComparisonContext)_localctx).left = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_valueExpression);
						setState(1816);
						if (!(precpred(_ctx, 1))) throw new FailedPredicateException(this, "precpred(_ctx, 1)");
						setState(1817);
						comparisonOperator();
						setState(1818);
						((ComparisonContext)_localctx).right = valueExpression(2);
						}
						break;
					}
					}
				}
				setState(1824);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,250,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			unrollRecursionContexts(_parentctx);
		}
		return _localctx;
	}

	public static class PrimaryExpressionContext extends ParserRuleContext {
		public PrimaryExpressionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_primaryExpression; }

		public PrimaryExpressionContext() { }
		public void copyFrom(PrimaryExpressionContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class DereferenceContext extends PrimaryExpressionContext {
		public PrimaryExpressionContext base;
		public IdentifierContext fieldName;
		public PrimaryExpressionContext primaryExpression() {
			return getRuleContext(PrimaryExpressionContext.class,0);
		}
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public DereferenceContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDereference(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDereference(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDereference(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SimpleCaseContext extends PrimaryExpressionContext {
		public ExpressionContext value;
		public ExpressionContext elseExpression;
		public TerminalNode CASE() { return getToken(SqlBaseParser.CASE, 0); }
		public TerminalNode END() { return getToken(SqlBaseParser.END, 0); }
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public List<WhenClauseContext> whenClause() {
			return getRuleContexts(WhenClauseContext.class);
		}
		public WhenClauseContext whenClause(int i) {
			return getRuleContext(WhenClauseContext.class,i);
		}
		public TerminalNode ELSE() { return getToken(SqlBaseParser.ELSE, 0); }
		public SimpleCaseContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSimpleCase(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSimpleCase(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSimpleCase(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ColumnReferenceContext extends PrimaryExpressionContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public ColumnReferenceContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterColumnReference(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitColumnReference(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitColumnReference(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class RowConstructorContext extends PrimaryExpressionContext {
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public RowConstructorContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterRowConstructor(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitRowConstructor(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitRowConstructor(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class StarContext extends PrimaryExpressionContext {
		public TerminalNode ASTERISK() { return getToken(SqlBaseParser.ASTERISK, 0); }
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public StarContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterStar(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitStar(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitStar(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SubscriptContext extends PrimaryExpressionContext {
		public PrimaryExpressionContext value;
		public ValueExpressionContext index;
		public PrimaryExpressionContext primaryExpression() {
			return getRuleContext(PrimaryExpressionContext.class,0);
		}
		public ValueExpressionContext valueExpression() {
			return getRuleContext(ValueExpressionContext.class,0);
		}
		public SubscriptContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSubscript(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSubscript(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSubscript(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class TimeFunctionCallContext extends PrimaryExpressionContext {
		public Token name;
		public TerminalNode CURRENT_DATE() { return getToken(SqlBaseParser.CURRENT_DATE, 0); }
		public TerminalNode CURRENT_TIMESTAMP() { return getToken(SqlBaseParser.CURRENT_TIMESTAMP, 0); }
		public TimeFunctionCallContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTimeFunctionCall(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTimeFunctionCall(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTimeFunctionCall(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SubqueryExpressionContext extends PrimaryExpressionContext {
		public QueryContext query() {
			return getRuleContext(QueryContext.class,0);
		}
		public SubqueryExpressionContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSubqueryExpression(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSubqueryExpression(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSubqueryExpression(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class CastContext extends PrimaryExpressionContext {
		public TerminalNode CAST() { return getToken(SqlBaseParser.CAST, 0); }
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public DataTypeContext dataType() {
			return getRuleContext(DataTypeContext.class,0);
		}
		public CastContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterCast(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitCast(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitCast(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ConstantDefaultContext extends PrimaryExpressionContext {
		public ConstantContext constant() {
			return getRuleContext(ConstantContext.class,0);
		}
		public ConstantDefaultContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterConstantDefault(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitConstantDefault(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitConstantDefault(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class ParenthesizedExpressionContext extends PrimaryExpressionContext {
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public ParenthesizedExpressionContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterParenthesizedExpression(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitParenthesizedExpression(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitParenthesizedExpression(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class FunctionCallContext extends PrimaryExpressionContext {
		public QualifiedNameContext qualifiedName() {
			return getRuleContext(QualifiedNameContext.class,0);
		}
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public TerminalNode OVER() { return getToken(SqlBaseParser.OVER, 0); }
		public WindowSpecContext windowSpec() {
			return getRuleContext(WindowSpecContext.class,0);
		}
		public SetQuantifierContext setQuantifier() {
			return getRuleContext(SetQuantifierContext.class,0);
		}
		public FunctionCallContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterFunctionCall(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitFunctionCall(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitFunctionCall(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SearchedCaseContext extends PrimaryExpressionContext {
		public ExpressionContext elseExpression;
		public TerminalNode CASE() { return getToken(SqlBaseParser.CASE, 0); }
		public TerminalNode END() { return getToken(SqlBaseParser.END, 0); }
		public List<WhenClauseContext> whenClause() {
			return getRuleContexts(WhenClauseContext.class);
		}
		public WhenClauseContext whenClause(int i) {
			return getRuleContext(WhenClauseContext.class,i);
		}
		public TerminalNode ELSE() { return getToken(SqlBaseParser.ELSE, 0); }
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public SearchedCaseContext(PrimaryExpressionContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSearchedCase(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSearchedCase(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSearchedCase(this);
			else return visitor.visitChildren(this);
		}
	}

	public final PrimaryExpressionContext primaryExpression() throws RecognitionException {
		return primaryExpression(0);
	}

	private PrimaryExpressionContext primaryExpression(int _p) throws RecognitionException {
		ParserRuleContext _parentctx = _ctx;
		int _parentState = getState();
		PrimaryExpressionContext _localctx = new PrimaryExpressionContext(_ctx, _parentState);
		PrimaryExpressionContext _prevctx = _localctx;
		int _startState = 128;
		enterRecursionRule(_localctx, 128, RULE_primaryExpression, _p);
		int _la;
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1904);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,260,_ctx) ) {
			case 1:
				{
				_localctx = new TimeFunctionCallContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;

				setState(1826);
				((TimeFunctionCallContext)_localctx).name = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==CURRENT_DATE || _la==CURRENT_TIMESTAMP) ) {
					((TimeFunctionCallContext)_localctx).name = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				}
				break;
			case 2:
				{
				_localctx = new SimpleCaseContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1827);
				match(CASE);
				setState(1828);
				((SimpleCaseContext)_localctx).value = expression();
				setState(1830);
				_errHandler.sync(this);
				_la = _input.LA(1);
				do {
					{
					{
					setState(1829);
					whenClause();
					}
					}
					setState(1832);
					_errHandler.sync(this);
					_la = _input.LA(1);
				} while ( _la==WHEN );
				setState(1836);
				_la = _input.LA(1);
				if (_la==ELSE) {
					{
					setState(1834);
					match(ELSE);
					setState(1835);
					((SimpleCaseContext)_localctx).elseExpression = expression();
					}
				}

				setState(1838);
				match(END);
				}
				break;
			case 3:
				{
				_localctx = new SearchedCaseContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1840);
				match(CASE);
				setState(1842);
				_errHandler.sync(this);
				_la = _input.LA(1);
				do {
					{
					{
					setState(1841);
					whenClause();
					}
					}
					setState(1844);
					_errHandler.sync(this);
					_la = _input.LA(1);
				} while ( _la==WHEN );
				setState(1848);
				_la = _input.LA(1);
				if (_la==ELSE) {
					{
					setState(1846);
					match(ELSE);
					setState(1847);
					((SearchedCaseContext)_localctx).elseExpression = expression();
					}
				}

				setState(1850);
				match(END);
				}
				break;
			case 4:
				{
				_localctx = new CastContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1852);
				match(CAST);
				setState(1853);
				match(T__0);
				setState(1854);
				expression();
				setState(1855);
				match(AS);
				setState(1856);
				dataType();
				setState(1857);
				match(T__1);
				}
				break;
			case 5:
				{
				_localctx = new ConstantDefaultContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1859);
				constant();
				}
				break;
			case 6:
				{
				_localctx = new StarContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1860);
				match(ASTERISK);
				}
				break;
			case 7:
				{
				_localctx = new StarContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1861);
				qualifiedName();
				setState(1862);
				match(T__3);
				setState(1863);
				match(ASTERISK);
				}
				break;
			case 8:
				{
				_localctx = new RowConstructorContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1865);
				match(T__0);
				setState(1866);
				expression();
				setState(1869);
				_errHandler.sync(this);
				_la = _input.LA(1);
				do {
					{
					{
					setState(1867);
					match(T__2);
					setState(1868);
					expression();
					}
					}
					setState(1871);
					_errHandler.sync(this);
					_la = _input.LA(1);
				} while ( _la==T__2 );
				setState(1873);
				match(T__1);
				}
				break;
			case 9:
				{
				_localctx = new SubqueryExpressionContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1875);
				match(T__0);
				setState(1876);
				query();
				setState(1877);
				match(T__1);
				}
				break;
			case 10:
				{
				_localctx = new FunctionCallContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1879);
				qualifiedName();
				setState(1880);
				match(T__0);
				setState(1892);
				_la = _input.LA(1);
				if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << JOIN) | (1L << CROSS) | (1L << OUTER) | (1L << INNER) | (1L << LEFT) | (1L << SEMI) | (1L << RIGHT) | (1L << FULL) | (1L << NATURAL) | (1L << ON) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (UNION - 64)) | (1L << (EXCEPT - 64)) | (1L << (SETMINUS - 64)) | (1L << (INTERSECT - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)) | (1L << (PLUS - 64)) | (1L << (MINUS - 64)) | (1L << (ASTERISK - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (TILDE - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (ANTI - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)) | (1L << (STRING - 193)) | (1L << (BIGINT_LITERAL - 193)) | (1L << (SMALLINT_LITERAL - 193)) | (1L << (TINYINT_LITERAL - 193)) | (1L << (INTEGER_VALUE - 193)) | (1L << (DECIMAL_VALUE - 193)) | (1L << (DOUBLE_LITERAL - 193)) | (1L << (BIGDECIMAL_LITERAL - 193)) | (1L << (IDENTIFIER - 193)) | (1L << (BACKQUOTED_IDENTIFIER - 193)))) != 0)) {
					{
					setState(1882);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,256,_ctx) ) {
					case 1:
						{
						setState(1881);
						setQuantifier();
						}
						break;
					}
					setState(1884);
					expression();
					setState(1889);
					_errHandler.sync(this);
					_la = _input.LA(1);
					while (_la==T__2) {
						{
						{
						setState(1885);
						match(T__2);
						setState(1886);
						expression();
						}
						}
						setState(1891);
						_errHandler.sync(this);
						_la = _input.LA(1);
					}
					}
				}

				setState(1894);
				match(T__1);
				setState(1897);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,259,_ctx) ) {
				case 1:
					{
					setState(1895);
					match(OVER);
					setState(1896);
					windowSpec();
					}
					break;
				}
				}
				break;
			case 11:
				{
				_localctx = new ColumnReferenceContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1899);
				identifier();
				}
				break;
			case 12:
				{
				_localctx = new ParenthesizedExpressionContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(1900);
				match(T__0);
				setState(1901);
				expression();
				setState(1902);
				match(T__1);
				}
				break;
			}
			_ctx.stop = _input.LT(-1);
			setState(1916);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,262,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					if ( _parseListeners!=null ) triggerExitRuleEvent();
					_prevctx = _localctx;
					{
					setState(1914);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,261,_ctx) ) {
					case 1:
						{
						_localctx = new SubscriptContext(new PrimaryExpressionContext(_parentctx, _parentState));
						((SubscriptContext)_localctx).value = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_primaryExpression);
						setState(1906);
						if (!(precpred(_ctx, 4))) throw new FailedPredicateException(this, "precpred(_ctx, 4)");
						setState(1907);
						match(T__4);
						setState(1908);
						((SubscriptContext)_localctx).index = valueExpression(0);
						setState(1909);
						match(T__5);
						}
						break;
					case 2:
						{
						_localctx = new DereferenceContext(new PrimaryExpressionContext(_parentctx, _parentState));
						((DereferenceContext)_localctx).base = _prevctx;
						pushNewRecursionContext(_localctx, _startState, RULE_primaryExpression);
						setState(1911);
						if (!(precpred(_ctx, 2))) throw new FailedPredicateException(this, "precpred(_ctx, 2)");
						setState(1912);
						match(T__3);
						setState(1913);
						((DereferenceContext)_localctx).fieldName = identifier();
						}
						break;
					}
					}
				}
				setState(1918);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,262,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			unrollRecursionContexts(_parentctx);
		}
		return _localctx;
	}

	public static class ConstantContext extends ParserRuleContext {
		public ConstantContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_constant; }

		public ConstantContext() { }
		public void copyFrom(ConstantContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class NullLiteralContext extends ConstantContext {
		public TerminalNode NULL() { return getToken(SqlBaseParser.NULL, 0); }
		public NullLiteralContext(ConstantContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNullLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNullLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNullLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class StringLiteralContext extends ConstantContext {
		public List<TerminalNode> STRING() { return getTokens(SqlBaseParser.STRING); }
		public TerminalNode STRING(int i) {
			return getToken(SqlBaseParser.STRING, i);
		}
		public StringLiteralContext(ConstantContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterStringLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitStringLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitStringLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class TypeConstructorContext extends ConstantContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public TypeConstructorContext(ConstantContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTypeConstructor(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTypeConstructor(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTypeConstructor(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class IntervalLiteralContext extends ConstantContext {
		public IntervalContext interval() {
			return getRuleContext(IntervalContext.class,0);
		}
		public IntervalLiteralContext(ConstantContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIntervalLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIntervalLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIntervalLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class NumericLiteralContext extends ConstantContext {
		public NumberContext number() {
			return getRuleContext(NumberContext.class,0);
		}
		public NumericLiteralContext(ConstantContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNumericLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNumericLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNumericLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class BooleanLiteralContext extends ConstantContext {
		public BooleanValueContext booleanValue() {
			return getRuleContext(BooleanValueContext.class,0);
		}
		public BooleanLiteralContext(ConstantContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterBooleanLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitBooleanLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitBooleanLiteral(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ConstantContext constant() throws RecognitionException {
		ConstantContext _localctx = new ConstantContext(_ctx, getState());
		enterRule(_localctx, 130, RULE_constant);
		try {
			int _alt;
			setState(1931);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,264,_ctx) ) {
			case 1:
				_localctx = new NullLiteralContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(1919);
				match(NULL);
				}
				break;
			case 2:
				_localctx = new IntervalLiteralContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(1920);
				interval();
				}
				break;
			case 3:
				_localctx = new TypeConstructorContext(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(1921);
				identifier();
				setState(1922);
				match(STRING);
				}
				break;
			case 4:
				_localctx = new NumericLiteralContext(_localctx);
				enterOuterAlt(_localctx, 4);
				{
				setState(1924);
				number();
				}
				break;
			case 5:
				_localctx = new BooleanLiteralContext(_localctx);
				enterOuterAlt(_localctx, 5);
				{
				setState(1925);
				booleanValue();
				}
				break;
			case 6:
				_localctx = new StringLiteralContext(_localctx);
				enterOuterAlt(_localctx, 6);
				{
				setState(1927);
				_errHandler.sync(this);
				_alt = 1;
				do {
					switch (_alt) {
					case 1:
						{
						{
						setState(1926);
						match(STRING);
						}
						}
						break;
					default:
						throw new NoViableAltException(this);
					}
					setState(1929);
					_errHandler.sync(this);
					_alt = getInterpreter().adaptivePredict(_input,263,_ctx);
				} while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER );
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ComparisonOperatorContext extends ParserRuleContext {
		public TerminalNode EQ() { return getToken(SqlBaseParser.EQ, 0); }
		public TerminalNode NEQ() { return getToken(SqlBaseParser.NEQ, 0); }
		public TerminalNode NEQJ() { return getToken(SqlBaseParser.NEQJ, 0); }
		public TerminalNode LT() { return getToken(SqlBaseParser.LT, 0); }
		public TerminalNode LTE() { return getToken(SqlBaseParser.LTE, 0); }
		public TerminalNode GT() { return getToken(SqlBaseParser.GT, 0); }
		public TerminalNode GTE() { return getToken(SqlBaseParser.GTE, 0); }
		public TerminalNode NSEQ() { return getToken(SqlBaseParser.NSEQ, 0); }
		public ComparisonOperatorContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_comparisonOperator; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterComparisonOperator(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitComparisonOperator(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitComparisonOperator(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ComparisonOperatorContext comparisonOperator() throws RecognitionException {
		ComparisonOperatorContext _localctx = new ComparisonOperatorContext(_ctx, getState());
		enterRule(_localctx, 132, RULE_comparisonOperator);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1933);
			_la = _input.LA(1);
			if ( !(((((_la - 116)) & ~0x3f) == 0 && ((1L << (_la - 116)) & ((1L << (EQ - 116)) | (1L << (NSEQ - 116)) | (1L << (NEQ - 116)) | (1L << (NEQJ - 116)) | (1L << (LT - 116)) | (1L << (LTE - 116)) | (1L << (GT - 116)) | (1L << (GTE - 116)))) != 0)) ) {
			_errHandler.recoverInline(this);
			} else {
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ArithmeticOperatorContext extends ParserRuleContext {
		public TerminalNode PLUS() { return getToken(SqlBaseParser.PLUS, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public TerminalNode ASTERISK() { return getToken(SqlBaseParser.ASTERISK, 0); }
		public TerminalNode SLASH() { return getToken(SqlBaseParser.SLASH, 0); }
		public TerminalNode PERCENT() { return getToken(SqlBaseParser.PERCENT, 0); }
		public TerminalNode DIV() { return getToken(SqlBaseParser.DIV, 0); }
		public TerminalNode TILDE() { return getToken(SqlBaseParser.TILDE, 0); }
		public TerminalNode AMPERSAND() { return getToken(SqlBaseParser.AMPERSAND, 0); }
		public TerminalNode PIPE() { return getToken(SqlBaseParser.PIPE, 0); }
		public TerminalNode HAT() { return getToken(SqlBaseParser.HAT, 0); }
		public TerminalNode RSHIFT() { return getToken(SqlBaseParser.RSHIFT, 0); }
		public ArithmeticOperatorContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_arithmeticOperator; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterArithmeticOperator(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitArithmeticOperator(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitArithmeticOperator(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ArithmeticOperatorContext arithmeticOperator() throws RecognitionException {
		ArithmeticOperatorContext _localctx = new ArithmeticOperatorContext(_ctx, getState());
		enterRule(_localctx, 134, RULE_arithmeticOperator);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1935);
			_la = _input.LA(1);
			if ( !(((((_la - 124)) & ~0x3f) == 0 && ((1L << (_la - 124)) & ((1L << (PLUS - 124)) | (1L << (MINUS - 124)) | (1L << (ASTERISK - 124)) | (1L << (SLASH - 124)) | (1L << (PERCENT - 124)) | (1L << (DIV - 124)) | (1L << (TILDE - 124)) | (1L << (AMPERSAND - 124)) | (1L << (PIPE - 124)) | (1L << (HAT - 124)) | (1L << (RSHIFT - 124)))) != 0)) ) {
			_errHandler.recoverInline(this);
			} else {
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class PredicateOperatorContext extends ParserRuleContext {
		public TerminalNode OR() { return getToken(SqlBaseParser.OR, 0); }
		public TerminalNode AND() { return getToken(SqlBaseParser.AND, 0); }
		public TerminalNode IN() { return getToken(SqlBaseParser.IN, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public PredicateOperatorContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_predicateOperator; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterPredicateOperator(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitPredicateOperator(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitPredicateOperator(this);
			else return visitor.visitChildren(this);
		}
	}

	public final PredicateOperatorContext predicateOperator() throws RecognitionException {
		PredicateOperatorContext _localctx = new PredicateOperatorContext(_ctx, getState());
		enterRule(_localctx, 136, RULE_predicateOperator);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1937);
			_la = _input.LA(1);
			if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT))) != 0)) ) {
			_errHandler.recoverInline(this);
			} else {
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class BooleanValueContext extends ParserRuleContext {
		public TerminalNode TRUE() { return getToken(SqlBaseParser.TRUE, 0); }
		public TerminalNode FALSE() { return getToken(SqlBaseParser.FALSE, 0); }
		public BooleanValueContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_booleanValue; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterBooleanValue(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitBooleanValue(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitBooleanValue(this);
			else return visitor.visitChildren(this);
		}
	}

	public final BooleanValueContext booleanValue() throws RecognitionException {
		BooleanValueContext _localctx = new BooleanValueContext(_ctx, getState());
		enterRule(_localctx, 138, RULE_booleanValue);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1939);
			_la = _input.LA(1);
			if ( !(_la==TRUE || _la==FALSE) ) {
			_errHandler.recoverInline(this);
			} else {
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IntervalContext extends ParserRuleContext {
		public TerminalNode INTERVAL() { return getToken(SqlBaseParser.INTERVAL, 0); }
		public List<IntervalFieldContext> intervalField() {
			return getRuleContexts(IntervalFieldContext.class);
		}
		public IntervalFieldContext intervalField(int i) {
			return getRuleContext(IntervalFieldContext.class,i);
		}
		public IntervalContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_interval; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterInterval(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitInterval(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitInterval(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IntervalContext interval() throws RecognitionException {
		IntervalContext _localctx = new IntervalContext(_ctx, getState());
		enterRule(_localctx, 140, RULE_interval);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1941);
			match(INTERVAL);
			setState(1945);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,265,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1942);
					intervalField();
					}
					}
				}
				setState(1947);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,265,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IntervalFieldContext extends ParserRuleContext {
		public IntervalValueContext value;
		public IdentifierContext unit;
		public IdentifierContext to;
		public IntervalValueContext intervalValue() {
			return getRuleContext(IntervalValueContext.class,0);
		}
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public TerminalNode TO() { return getToken(SqlBaseParser.TO, 0); }
		public IntervalFieldContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_intervalField; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIntervalField(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIntervalField(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIntervalField(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IntervalFieldContext intervalField() throws RecognitionException {
		IntervalFieldContext _localctx = new IntervalFieldContext(_ctx, getState());
		enterRule(_localctx, 142, RULE_intervalField);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(1948);
			((IntervalFieldContext)_localctx).value = intervalValue();
			setState(1949);
			((IntervalFieldContext)_localctx).unit = identifier();
			setState(1952);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,266,_ctx) ) {
			case 1:
				{
				setState(1950);
				match(TO);
				setState(1951);
				((IntervalFieldContext)_localctx).to = identifier();
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IntervalValueContext extends ParserRuleContext {
		public TerminalNode INTEGER_VALUE() { return getToken(SqlBaseParser.INTEGER_VALUE, 0); }
		public TerminalNode DECIMAL_VALUE() { return getToken(SqlBaseParser.DECIMAL_VALUE, 0); }
		public TerminalNode PLUS() { return getToken(SqlBaseParser.PLUS, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public IntervalValueContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_intervalValue; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIntervalValue(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIntervalValue(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIntervalValue(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IntervalValueContext intervalValue() throws RecognitionException {
		IntervalValueContext _localctx = new IntervalValueContext(_ctx, getState());
		enterRule(_localctx, 144, RULE_intervalValue);
		int _la;
		try {
			setState(1959);
			switch (_input.LA(1)) {
			case PLUS:
			case MINUS:
			case INTEGER_VALUE:
			case DECIMAL_VALUE:
				enterOuterAlt(_localctx, 1);
				{
				setState(1955);
				_la = _input.LA(1);
				if (_la==PLUS || _la==MINUS) {
					{
					setState(1954);
					_la = _input.LA(1);
					if ( !(_la==PLUS || _la==MINUS) ) {
					_errHandler.recoverInline(this);
					} else {
						consume();
					}
					}
				}

				setState(1957);
				_la = _input.LA(1);
				if ( !(_la==INTEGER_VALUE || _la==DECIMAL_VALUE) ) {
				_errHandler.recoverInline(this);
				} else {
					consume();
				}
				}
				break;
			case STRING:
				enterOuterAlt(_localctx, 2);
				{
				setState(1958);
				match(STRING);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class DataTypeContext extends ParserRuleContext {
		public DataTypeContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_dataType; }

		public DataTypeContext() { }
		public void copyFrom(DataTypeContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class ComplexDataTypeContext extends DataTypeContext {
		public Token complex;
		public List<DataTypeContext> dataType() {
			return getRuleContexts(DataTypeContext.class);
		}
		public DataTypeContext dataType(int i) {
			return getRuleContext(DataTypeContext.class,i);
		}
		public TerminalNode ARRAY() { return getToken(SqlBaseParser.ARRAY, 0); }
		public TerminalNode MAP() { return getToken(SqlBaseParser.MAP, 0); }
		public TerminalNode STRUCT() { return getToken(SqlBaseParser.STRUCT, 0); }
		public TerminalNode NEQ() { return getToken(SqlBaseParser.NEQ, 0); }
		public ComplexColTypeListContext complexColTypeList() {
			return getRuleContext(ComplexColTypeListContext.class,0);
		}
		public ComplexDataTypeContext(DataTypeContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterComplexDataType(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitComplexDataType(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitComplexDataType(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class PrimitiveDataTypeContext extends DataTypeContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public List<TerminalNode> INTEGER_VALUE() { return getTokens(SqlBaseParser.INTEGER_VALUE); }
		public TerminalNode INTEGER_VALUE(int i) {
			return getToken(SqlBaseParser.INTEGER_VALUE, i);
		}
		public PrimitiveDataTypeContext(DataTypeContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterPrimitiveDataType(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitPrimitiveDataType(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitPrimitiveDataType(this);
			else return visitor.visitChildren(this);
		}
	}

	public final DataTypeContext dataType() throws RecognitionException {
		DataTypeContext _localctx = new DataTypeContext(_ctx, getState());
		enterRule(_localctx, 146, RULE_dataType);
		int _la;
		try {
			setState(1995);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,273,_ctx) ) {
			case 1:
				_localctx = new ComplexDataTypeContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(1961);
				((ComplexDataTypeContext)_localctx).complex = match(ARRAY);
				setState(1962);
				match(LT);
				setState(1963);
				dataType();
				setState(1964);
				match(GT);
				}
				break;
			case 2:
				_localctx = new ComplexDataTypeContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(1966);
				((ComplexDataTypeContext)_localctx).complex = match(MAP);
				setState(1967);
				match(LT);
				setState(1968);
				dataType();
				setState(1969);
				match(T__2);
				setState(1970);
				dataType();
				setState(1971);
				match(GT);
				}
				break;
			case 3:
				_localctx = new ComplexDataTypeContext(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(1973);
				((ComplexDataTypeContext)_localctx).complex = match(STRUCT);
				setState(1980);
				switch (_input.LA(1)) {
				case LT:
					{
					setState(1974);
					match(LT);
					setState(1976);
					_la = _input.LA(1);
					if ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << JOIN) | (1L << CROSS) | (1L << OUTER) | (1L << INNER) | (1L << LEFT) | (1L << SEMI) | (1L << RIGHT) | (1L << FULL) | (1L << NATURAL) | (1L << ON) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (UNION - 64)) | (1L << (EXCEPT - 64)) | (1L << (SETMINUS - 64)) | (1L << (INTERSECT - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (ANTI - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)) | (1L << (IDENTIFIER - 193)) | (1L << (BACKQUOTED_IDENTIFIER - 193)))) != 0)) {
						{
						setState(1975);
						complexColTypeList();
						}
					}

					setState(1978);
					match(GT);
					}
					break;
				case NEQ:
					{
					setState(1979);
					match(NEQ);
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				}
				break;
			case 4:
				_localctx = new PrimitiveDataTypeContext(_localctx);
				enterOuterAlt(_localctx, 4);
				{
				setState(1982);
				identifier();
				setState(1993);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,272,_ctx) ) {
				case 1:
					{
					setState(1983);
					match(T__0);
					setState(1984);
					match(INTEGER_VALUE);
					setState(1989);
					_errHandler.sync(this);
					_la = _input.LA(1);
					while (_la==T__2) {
						{
						{
						setState(1985);
						match(T__2);
						setState(1986);
						match(INTEGER_VALUE);
						}
						}
						setState(1991);
						_errHandler.sync(this);
						_la = _input.LA(1);
					}
					setState(1992);
					match(T__1);
					}
					break;
				}
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ColTypeListContext extends ParserRuleContext {
		public List<ColTypeContext> colType() {
			return getRuleContexts(ColTypeContext.class);
		}
		public ColTypeContext colType(int i) {
			return getRuleContext(ColTypeContext.class,i);
		}
		public ColTypeListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_colTypeList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterColTypeList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitColTypeList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitColTypeList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ColTypeListContext colTypeList() throws RecognitionException {
		ColTypeListContext _localctx = new ColTypeListContext(_ctx, getState());
		enterRule(_localctx, 148, RULE_colTypeList);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(1997);
			colType();
			setState(2002);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,274,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(1998);
					match(T__2);
					setState(1999);
					colType();
					}
					}
				}
				setState(2004);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,274,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ColTypeContext extends ParserRuleContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public DataTypeContext dataType() {
			return getRuleContext(DataTypeContext.class,0);
		}
		public TerminalNode COMMENT() { return getToken(SqlBaseParser.COMMENT, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public ColTypeContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_colType; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterColType(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitColType(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitColType(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ColTypeContext colType() throws RecognitionException {
		ColTypeContext _localctx = new ColTypeContext(_ctx, getState());
		enterRule(_localctx, 150, RULE_colType);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(2005);
			identifier();
			setState(2006);
			dataType();
			setState(2009);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,275,_ctx) ) {
			case 1:
				{
				setState(2007);
				match(COMMENT);
				setState(2008);
				match(STRING);
				}
				break;
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ComplexColTypeListContext extends ParserRuleContext {
		public List<ComplexColTypeContext> complexColType() {
			return getRuleContexts(ComplexColTypeContext.class);
		}
		public ComplexColTypeContext complexColType(int i) {
			return getRuleContext(ComplexColTypeContext.class,i);
		}
		public ComplexColTypeListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_complexColTypeList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterComplexColTypeList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitComplexColTypeList(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitComplexColTypeList(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ComplexColTypeListContext complexColTypeList() throws RecognitionException {
		ComplexColTypeListContext _localctx = new ComplexColTypeListContext(_ctx, getState());
		enterRule(_localctx, 152, RULE_complexColTypeList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(2011);
			complexColType();
			setState(2016);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==T__2) {
				{
				{
				setState(2012);
				match(T__2);
				setState(2013);
				complexColType();
				}
				}
				setState(2018);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ComplexColTypeContext extends ParserRuleContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public DataTypeContext dataType() {
			return getRuleContext(DataTypeContext.class,0);
		}
		public TerminalNode COMMENT() { return getToken(SqlBaseParser.COMMENT, 0); }
		public TerminalNode STRING() { return getToken(SqlBaseParser.STRING, 0); }
		public ComplexColTypeContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_complexColType; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterComplexColType(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitComplexColType(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitComplexColType(this);
			else return visitor.visitChildren(this);
		}
	}

	public final ComplexColTypeContext complexColType() throws RecognitionException {
		ComplexColTypeContext _localctx = new ComplexColTypeContext(_ctx, getState());
		enterRule(_localctx, 154, RULE_complexColType);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(2019);
			identifier();
			setState(2020);
			match(T__6);
			setState(2021);
			dataType();
			setState(2024);
			_la = _input.LA(1);
			if (_la==COMMENT) {
				{
				setState(2022);
				match(COMMENT);
				setState(2023);
				match(STRING);
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class WhenClauseContext extends ParserRuleContext {
		public ExpressionContext condition;
		public ExpressionContext result;
		public TerminalNode WHEN() { return getToken(SqlBaseParser.WHEN, 0); }
		public TerminalNode THEN() { return getToken(SqlBaseParser.THEN, 0); }
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public WhenClauseContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_whenClause; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterWhenClause(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitWhenClause(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitWhenClause(this);
			else return visitor.visitChildren(this);
		}
	}

	public final WhenClauseContext whenClause() throws RecognitionException {
		WhenClauseContext _localctx = new WhenClauseContext(_ctx, getState());
		enterRule(_localctx, 156, RULE_whenClause);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(2026);
			match(WHEN);
			setState(2027);
			((WhenClauseContext)_localctx).condition = expression();
			setState(2028);
			match(THEN);
			setState(2029);
			((WhenClauseContext)_localctx).result = expression();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class WindowsContext extends ParserRuleContext {
		public TerminalNode WINDOW() { return getToken(SqlBaseParser.WINDOW, 0); }
		public List<NamedWindowContext> namedWindow() {
			return getRuleContexts(NamedWindowContext.class);
		}
		public NamedWindowContext namedWindow(int i) {
			return getRuleContext(NamedWindowContext.class,i);
		}
		public WindowsContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_windows; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterWindows(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitWindows(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitWindows(this);
			else return visitor.visitChildren(this);
		}
	}

	public final WindowsContext windows() throws RecognitionException {
		WindowsContext _localctx = new WindowsContext(_ctx, getState());
		enterRule(_localctx, 158, RULE_windows);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(2031);
			match(WINDOW);
			setState(2032);
			namedWindow();
			setState(2037);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,278,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(2033);
					match(T__2);
					setState(2034);
					namedWindow();
					}
					}
				}
				setState(2039);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,278,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class NamedWindowContext extends ParserRuleContext {
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public WindowSpecContext windowSpec() {
			return getRuleContext(WindowSpecContext.class,0);
		}
		public NamedWindowContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_namedWindow; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNamedWindow(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNamedWindow(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNamedWindow(this);
			else return visitor.visitChildren(this);
		}
	}

	public final NamedWindowContext namedWindow() throws RecognitionException {
		NamedWindowContext _localctx = new NamedWindowContext(_ctx, getState());
		enterRule(_localctx, 160, RULE_namedWindow);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(2040);
			identifier();
			setState(2041);
			match(AS);
			setState(2042);
			windowSpec();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class WindowSpecContext extends ParserRuleContext {
		public WindowSpecContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_windowSpec; }

		public WindowSpecContext() { }
		public void copyFrom(WindowSpecContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class WindowRefContext extends WindowSpecContext {
		public IdentifierContext name;
		public IdentifierContext identifier() {
			return getRuleContext(IdentifierContext.class,0);
		}
		public WindowRefContext(WindowSpecContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterWindowRef(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitWindowRef(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitWindowRef(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class WindowDefContext extends WindowSpecContext {
		public ExpressionContext expression;
		public List<ExpressionContext> partition = new ArrayList<ExpressionContext>();
		public TerminalNode CLUSTER() { return getToken(SqlBaseParser.CLUSTER, 0); }
		public List<TerminalNode> BY() { return getTokens(SqlBaseParser.BY); }
		public TerminalNode BY(int i) {
			return getToken(SqlBaseParser.BY, i);
		}
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public WindowFrameContext windowFrame() {
			return getRuleContext(WindowFrameContext.class,0);
		}
		public List<SortItemContext> sortItem() {
			return getRuleContexts(SortItemContext.class);
		}
		public SortItemContext sortItem(int i) {
			return getRuleContext(SortItemContext.class,i);
		}
		public TerminalNode PARTITION() { return getToken(SqlBaseParser.PARTITION, 0); }
		public TerminalNode DISTRIBUTE() { return getToken(SqlBaseParser.DISTRIBUTE, 0); }
		public TerminalNode ORDER() { return getToken(SqlBaseParser.ORDER, 0); }
		public TerminalNode SORT() { return getToken(SqlBaseParser.SORT, 0); }
		public WindowDefContext(WindowSpecContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterWindowDef(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitWindowDef(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitWindowDef(this);
			else return visitor.visitChildren(this);
		}
	}

	public final WindowSpecContext windowSpec() throws RecognitionException {
		WindowSpecContext _localctx = new WindowSpecContext(_ctx, getState());
		enterRule(_localctx, 162, RULE_windowSpec);
		int _la;
		try {
			setState(2086);
			switch (_input.LA(1)) {
			case SELECT:
			case FROM:
			case ADD:
			case AS:
			case ALL:
			case DISTINCT:
			case WHERE:
			case GROUP:
			case BY:
			case GROUPING:
			case SETS:
			case CUBE:
			case ROLLUP:
			case ORDER:
			case HAVING:
			case LIMIT:
			case AT:
			case OR:
			case AND:
			case IN:
			case NOT:
			case NO:
			case EXISTS:
			case BETWEEN:
			case LIKE:
			case RLIKE:
			case IS:
			case NULL:
			case TRUE:
			case FALSE:
			case NULLS:
			case ASC:
			case DESC:
			case FOR:
			case INTERVAL:
			case CASE:
			case WHEN:
			case THEN:
			case ELSE:
			case END:
			case JOIN:
			case CROSS:
			case OUTER:
			case INNER:
			case LEFT:
			case SEMI:
			case RIGHT:
			case FULL:
			case NATURAL:
			case ON:
			case LATERAL:
			case WINDOW:
			case OVER:
			case PARTITION:
			case RANGE:
			case ROWS:
			case UNBOUNDED:
			case PRECEDING:
			case FOLLOWING:
			case CURRENT:
			case FIRST:
			case LAST:
			case ROW:
			case WITH:
			case VALUES:
			case CREATE:
			case TABLE:
			case VIEW:
			case REPLACE:
			case INSERT:
			case DELETE:
			case INTO:
			case DESCRIBE:
			case EXPLAIN:
			case FORMAT:
			case LOGICAL:
			case CODEGEN:
			case CAST:
			case SHOW:
			case TABLES:
			case COLUMNS:
			case COLUMN:
			case USE:
			case PARTITIONS:
			case FUNCTIONS:
			case DROP:
			case UNION:
			case EXCEPT:
			case SETMINUS:
			case INTERSECT:
			case TO:
			case TABLESAMPLE:
			case STRATIFY:
			case ALTER:
			case RENAME:
			case ARRAY:
			case MAP:
			case STRUCT:
			case COMMENT:
			case SET:
			case RESET:
			case DATA:
			case START:
			case TRANSACTION:
			case COMMIT:
			case ROLLBACK:
			case MACRO:
			case IF:
			case DIV:
			case PERCENTLIT:
			case BUCKET:
			case OUT:
			case OF:
			case SORT:
			case CLUSTER:
			case DISTRIBUTE:
			case OVERWRITE:
			case TRANSFORM:
			case REDUCE:
			case USING:
			case SERDE:
			case SERDEPROPERTIES:
			case RECORDREADER:
			case RECORDWRITER:
			case DELIMITED:
			case FIELDS:
			case TERMINATED:
			case COLLECTION:
			case ITEMS:
			case KEYS:
			case ESCAPED:
			case LINES:
			case SEPARATED:
			case FUNCTION:
			case EXTENDED:
			case REFRESH:
			case CLEAR:
			case CACHE:
			case UNCACHE:
			case LAZY:
			case FORMATTED:
			case GLOBAL:
			case TEMPORARY:
			case OPTIONS:
			case UNSET:
			case TBLPROPERTIES:
			case DBPROPERTIES:
			case BUCKETS:
			case SKEWED:
			case STORED:
			case DIRECTORIES:
			case LOCATION:
			case EXCHANGE:
			case ARCHIVE:
			case UNARCHIVE:
			case FILEFORMAT:
			case TOUCH:
			case COMPACT:
			case CONCATENATE:
			case CHANGE:
			case CASCADE:
			case RESTRICT:
			case CLUSTERED:
			case SORTED:
			case PURGE:
			case INPUTFORMAT:
			case OUTPUTFORMAT:
			case DATABASE:
			case DATABASES:
			case DFS:
			case TRUNCATE:
			case ANALYZE:
			case COMPUTE:
			case LIST:
			case STATISTICS:
			case PARTITIONED:
			case EXTERNAL:
			case DEFINED:
			case REVOKE:
			case GRANT:
			case LOCK:
			case UNLOCK:
			case MSCK:
			case REPAIR:
			case RECOVER:
			case EXPORT:
			case IMPORT:
			case LOAD:
			case ROLE:
			case ROLES:
			case COMPACTIONS:
			case PRINCIPALS:
			case TRANSACTIONS:
			case INDEX:
			case INDEXES:
			case LOCKS:
			case OPTION:
			case ANTI:
			case LOCAL:
			case INPATH:
			case CURRENT_DATE:
			case CURRENT_TIMESTAMP:
			case IDENTIFIER:
			case BACKQUOTED_IDENTIFIER:
				_localctx = new WindowRefContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(2044);
				((WindowRefContext)_localctx).name = identifier();
				}
				break;
			case T__0:
				_localctx = new WindowDefContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(2045);
				match(T__0);
				setState(2080);
				switch (_input.LA(1)) {
				case CLUSTER:
					{
					setState(2046);
					match(CLUSTER);
					setState(2047);
					match(BY);
					setState(2048);
					((WindowDefContext)_localctx).expression = expression();
					((WindowDefContext)_localctx).partition.add(((WindowDefContext)_localctx).expression);
					setState(2053);
					_errHandler.sync(this);
					_la = _input.LA(1);
					while (_la==T__2) {
						{
						{
						setState(2049);
						match(T__2);
						setState(2050);
						((WindowDefContext)_localctx).expression = expression();
						((WindowDefContext)_localctx).partition.add(((WindowDefContext)_localctx).expression);
						}
						}
						setState(2055);
						_errHandler.sync(this);
						_la = _input.LA(1);
					}
					}
					break;
				case T__1:
				case ORDER:
				case PARTITION:
				case RANGE:
				case ROWS:
				case SORT:
				case DISTRIBUTE:
					{
					setState(2066);
					_la = _input.LA(1);
					if (_la==PARTITION || _la==DISTRIBUTE) {
						{
						setState(2056);
						_la = _input.LA(1);
						if ( !(_la==PARTITION || _la==DISTRIBUTE) ) {
						_errHandler.recoverInline(this);
						} else {
							consume();
						}
						setState(2057);
						match(BY);
						setState(2058);
						((WindowDefContext)_localctx).expression = expression();
						((WindowDefContext)_localctx).partition.add(((WindowDefContext)_localctx).expression);
						setState(2063);
						_errHandler.sync(this);
						_la = _input.LA(1);
						while (_la==T__2) {
							{
							{
							setState(2059);
							match(T__2);
							setState(2060);
							((WindowDefContext)_localctx).expression = expression();
							((WindowDefContext)_localctx).partition.add(((WindowDefContext)_localctx).expression);
							}
							}
							setState(2065);
							_errHandler.sync(this);
							_la = _input.LA(1);
						}
						}
					}

					setState(2078);
					_la = _input.LA(1);
					if (_la==ORDER || _la==SORT) {
						{
						setState(2068);
						_la = _input.LA(1);
						if ( !(_la==ORDER || _la==SORT) ) {
						_errHandler.recoverInline(this);
						} else {
							consume();
						}
						setState(2069);
						match(BY);
						setState(2070);
						sortItem();
						setState(2075);
						_errHandler.sync(this);
						_la = _input.LA(1);
						while (_la==T__2) {
							{
							{
							setState(2071);
							match(T__2);
							setState(2072);
							sortItem();
							}
							}
							setState(2077);
							_errHandler.sync(this);
							_la = _input.LA(1);
						}
						}
					}

					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				setState(2083);
				_la = _input.LA(1);
				if (_la==RANGE || _la==ROWS) {
					{
					setState(2082);
					windowFrame();
					}
				}

				setState(2085);
				match(T__1);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class WindowFrameContext extends ParserRuleContext {
		public Token frameType;
		public FrameBoundContext start;
		public FrameBoundContext end;
		public TerminalNode RANGE() { return getToken(SqlBaseParser.RANGE, 0); }
		public List<FrameBoundContext> frameBound() {
			return getRuleContexts(FrameBoundContext.class);
		}
		public FrameBoundContext frameBound(int i) {
			return getRuleContext(FrameBoundContext.class,i);
		}
		public TerminalNode ROWS() { return getToken(SqlBaseParser.ROWS, 0); }
		public TerminalNode BETWEEN() { return getToken(SqlBaseParser.BETWEEN, 0); }
		public TerminalNode AND() { return getToken(SqlBaseParser.AND, 0); }
		public WindowFrameContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_windowFrame; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterWindowFrame(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitWindowFrame(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitWindowFrame(this);
			else return visitor.visitChildren(this);
		}
	}

	public final WindowFrameContext windowFrame() throws RecognitionException {
		WindowFrameContext _localctx = new WindowFrameContext(_ctx, getState());
		enterRule(_localctx, 164, RULE_windowFrame);
		try {
			setState(2104);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,287,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(2088);
				((WindowFrameContext)_localctx).frameType = match(RANGE);
				setState(2089);
				((WindowFrameContext)_localctx).start = frameBound();
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(2090);
				((WindowFrameContext)_localctx).frameType = match(ROWS);
				setState(2091);
				((WindowFrameContext)_localctx).start = frameBound();
				}
				break;
			case 3:
				enterOuterAlt(_localctx, 3);
				{
				setState(2092);
				((WindowFrameContext)_localctx).frameType = match(RANGE);
				setState(2093);
				match(BETWEEN);
				setState(2094);
				((WindowFrameContext)_localctx).start = frameBound();
				setState(2095);
				match(AND);
				setState(2096);
				((WindowFrameContext)_localctx).end = frameBound();
				}
				break;
			case 4:
				enterOuterAlt(_localctx, 4);
				{
				setState(2098);
				((WindowFrameContext)_localctx).frameType = match(ROWS);
				setState(2099);
				match(BETWEEN);
				setState(2100);
				((WindowFrameContext)_localctx).start = frameBound();
				setState(2101);
				match(AND);
				setState(2102);
				((WindowFrameContext)_localctx).end = frameBound();
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class FrameBoundContext extends ParserRuleContext {
		public Token boundType;
		public TerminalNode UNBOUNDED() { return getToken(SqlBaseParser.UNBOUNDED, 0); }
		public TerminalNode PRECEDING() { return getToken(SqlBaseParser.PRECEDING, 0); }
		public TerminalNode FOLLOWING() { return getToken(SqlBaseParser.FOLLOWING, 0); }
		public TerminalNode ROW() { return getToken(SqlBaseParser.ROW, 0); }
		public TerminalNode CURRENT() { return getToken(SqlBaseParser.CURRENT, 0); }
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public FrameBoundContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_frameBound; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterFrameBound(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitFrameBound(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitFrameBound(this);
			else return visitor.visitChildren(this);
		}
	}

	public final FrameBoundContext frameBound() throws RecognitionException {
		FrameBoundContext _localctx = new FrameBoundContext(_ctx, getState());
		enterRule(_localctx, 166, RULE_frameBound);
		int _la;
		try {
			setState(2113);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,288,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(2106);
				match(UNBOUNDED);
				setState(2107);
				((FrameBoundContext)_localctx).boundType = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==PRECEDING || _la==FOLLOWING) ) {
					((FrameBoundContext)_localctx).boundType = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(2108);
				((FrameBoundContext)_localctx).boundType = match(CURRENT);
				setState(2109);
				match(ROW);
				}
				break;
			case 3:
				enterOuterAlt(_localctx, 3);
				{
				setState(2110);
				expression();
				setState(2111);
				((FrameBoundContext)_localctx).boundType = _input.LT(1);
				_la = _input.LA(1);
				if ( !(_la==PRECEDING || _la==FOLLOWING) ) {
					((FrameBoundContext)_localctx).boundType = (Token)_errHandler.recoverInline(this);
				} else {
					consume();
				}
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class QualifiedNameContext extends ParserRuleContext {
		public List<IdentifierContext> identifier() {
			return getRuleContexts(IdentifierContext.class);
		}
		public IdentifierContext identifier(int i) {
			return getRuleContext(IdentifierContext.class,i);
		}
		public QualifiedNameContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_qualifiedName; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQualifiedName(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQualifiedName(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQualifiedName(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QualifiedNameContext qualifiedName() throws RecognitionException {
		QualifiedNameContext _localctx = new QualifiedNameContext(_ctx, getState());
		enterRule(_localctx, 168, RULE_qualifiedName);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(2115);
			identifier();
			setState(2120);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,289,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					{
					{
					setState(2116);
					match(T__3);
					setState(2117);
					identifier();
					}
					} 
				}
				setState(2122);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,289,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IdentifierContext extends ParserRuleContext {
		public StrictIdentifierContext strictIdentifier() {
			return getRuleContext(StrictIdentifierContext.class,0);
		}
		public TerminalNode ANTI() { return getToken(SqlBaseParser.ANTI, 0); }
		public TerminalNode FULL() { return getToken(SqlBaseParser.FULL, 0); }
		public TerminalNode INNER() { return getToken(SqlBaseParser.INNER, 0); }
		public TerminalNode LEFT() { return getToken(SqlBaseParser.LEFT, 0); }
		public TerminalNode SEMI() { return getToken(SqlBaseParser.SEMI, 0); }
		public TerminalNode RIGHT() { return getToken(SqlBaseParser.RIGHT, 0); }
		public TerminalNode NATURAL() { return getToken(SqlBaseParser.NATURAL, 0); }
		public TerminalNode JOIN() { return getToken(SqlBaseParser.JOIN, 0); }
		public TerminalNode CROSS() { return getToken(SqlBaseParser.CROSS, 0); }
		public TerminalNode ON() { return getToken(SqlBaseParser.ON, 0); }
		public TerminalNode UNION() { return getToken(SqlBaseParser.UNION, 0); }
		public TerminalNode INTERSECT() { return getToken(SqlBaseParser.INTERSECT, 0); }
		public TerminalNode EXCEPT() { return getToken(SqlBaseParser.EXCEPT, 0); }
		public TerminalNode SETMINUS() { return getToken(SqlBaseParser.SETMINUS, 0); }
		public IdentifierContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_identifier; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIdentifier(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIdentifier(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIdentifier(this);
			else return visitor.visitChildren(this);
		}
	}

	public final IdentifierContext identifier() throws RecognitionException {
		IdentifierContext _localctx = new IdentifierContext(_ctx, getState());
		enterRule(_localctx, 170, RULE_identifier);
		try {
			setState(2138);
			switch (_input.LA(1)) {
			case SELECT:
			case FROM:
			case ADD:
			case AS:
			case ALL:
			case DISTINCT:
			case WHERE:
			case GROUP:
			case BY:
			case GROUPING:
			case SETS:
			case CUBE:
			case ROLLUP:
			case ORDER:
			case HAVING:
			case LIMIT:
			case AT:
			case OR:
			case AND:
			case IN:
			case NOT:
			case NO:
			case EXISTS:
			case BETWEEN:
			case LIKE:
			case RLIKE:
			case IS:
			case NULL:
			case TRUE:
			case FALSE:
			case NULLS:
			case ASC:
			case DESC:
			case FOR:
			case INTERVAL:
			case CASE:
			case WHEN:
			case THEN:
			case ELSE:
			case END:
			case OUTER:
			case LATERAL:
			case WINDOW:
			case OVER:
			case PARTITION:
			case RANGE:
			case ROWS:
			case UNBOUNDED:
			case PRECEDING:
			case FOLLOWING:
			case CURRENT:
			case FIRST:
			case LAST:
			case ROW:
			case WITH:
			case VALUES:
			case CREATE:
			case TABLE:
			case VIEW:
			case REPLACE:
			case INSERT:
			case DELETE:
			case INTO:
			case DESCRIBE:
			case EXPLAIN:
			case FORMAT:
			case LOGICAL:
			case CODEGEN:
			case CAST:
			case SHOW:
			case TABLES:
			case COLUMNS:
			case COLUMN:
			case USE:
			case PARTITIONS:
			case FUNCTIONS:
			case DROP:
			case TO:
			case TABLESAMPLE:
			case STRATIFY:
			case ALTER:
			case RENAME:
			case ARRAY:
			case MAP:
			case STRUCT:
			case COMMENT:
			case SET:
			case RESET:
			case DATA:
			case START:
			case TRANSACTION:
			case COMMIT:
			case ROLLBACK:
			case MACRO:
			case IF:
			case DIV:
			case PERCENTLIT:
			case BUCKET:
			case OUT:
			case OF:
			case SORT:
			case CLUSTER:
			case DISTRIBUTE:
			case OVERWRITE:
			case TRANSFORM:
			case REDUCE:
			case USING:
			case SERDE:
			case SERDEPROPERTIES:
			case RECORDREADER:
			case RECORDWRITER:
			case DELIMITED:
			case FIELDS:
			case TERMINATED:
			case COLLECTION:
			case ITEMS:
			case KEYS:
			case ESCAPED:
			case LINES:
			case SEPARATED:
			case FUNCTION:
			case EXTENDED:
			case REFRESH:
			case CLEAR:
			case CACHE:
			case UNCACHE:
			case LAZY:
			case FORMATTED:
			case GLOBAL:
			case TEMPORARY:
			case OPTIONS:
			case UNSET:
			case TBLPROPERTIES:
			case DBPROPERTIES:
			case BUCKETS:
			case SKEWED:
			case STORED:
			case DIRECTORIES:
			case LOCATION:
			case EXCHANGE:
			case ARCHIVE:
			case UNARCHIVE:
			case FILEFORMAT:
			case TOUCH:
			case COMPACT:
			case CONCATENATE:
			case CHANGE:
			case CASCADE:
			case RESTRICT:
			case CLUSTERED:
			case SORTED:
			case PURGE:
			case INPUTFORMAT:
			case OUTPUTFORMAT:
			case DATABASE:
			case DATABASES:
			case DFS:
			case TRUNCATE:
			case ANALYZE:
			case COMPUTE:
			case LIST:
			case STATISTICS:
			case PARTITIONED:
			case EXTERNAL:
			case DEFINED:
			case REVOKE:
			case GRANT:
			case LOCK:
			case UNLOCK:
			case MSCK:
			case REPAIR:
			case RECOVER:
			case EXPORT:
			case IMPORT:
			case LOAD:
			case ROLE:
			case ROLES:
			case COMPACTIONS:
			case PRINCIPALS:
			case TRANSACTIONS:
			case INDEX:
			case INDEXES:
			case LOCKS:
			case OPTION:
			case LOCAL:
			case INPATH:
			case CURRENT_DATE:
			case CURRENT_TIMESTAMP:
			case IDENTIFIER:
			case BACKQUOTED_IDENTIFIER:
				enterOuterAlt(_localctx, 1);
				{
				setState(2123);
				strictIdentifier();
				}
				break;
			case ANTI:
				enterOuterAlt(_localctx, 2);
				{
				setState(2124);
				match(ANTI);
				}
				break;
			case FULL:
				enterOuterAlt(_localctx, 3);
				{
				setState(2125);
				match(FULL);
				}
				break;
			case INNER:
				enterOuterAlt(_localctx, 4);
				{
				setState(2126);
				match(INNER);
				}
				break;
			case LEFT:
				enterOuterAlt(_localctx, 5);
				{
				setState(2127);
				match(LEFT);
				}
				break;
			case SEMI:
				enterOuterAlt(_localctx, 6);
				{
				setState(2128);
				match(SEMI);
				}
				break;
			case RIGHT:
				enterOuterAlt(_localctx, 7);
				{
				setState(2129);
				match(RIGHT);
				}
				break;
			case NATURAL:
				enterOuterAlt(_localctx, 8);
				{
				setState(2130);
				match(NATURAL);
				}
				break;
			case JOIN:
				enterOuterAlt(_localctx, 9);
				{
				setState(2131);
				match(JOIN);
				}
				break;
			case CROSS:
				enterOuterAlt(_localctx, 10);
				{
				setState(2132);
				match(CROSS);
				}
				break;
			case ON:
				enterOuterAlt(_localctx, 11);
				{
				setState(2133);
				match(ON);
				}
				break;
			case UNION:
				enterOuterAlt(_localctx, 12);
				{
				setState(2134);
				match(UNION);
				}
				break;
			case INTERSECT:
				enterOuterAlt(_localctx, 13);
				{
				setState(2135);
				match(INTERSECT);
				}
				break;
			case EXCEPT:
				enterOuterAlt(_localctx, 14);
				{
				setState(2136);
				match(EXCEPT);
				}
				break;
			case SETMINUS:
				enterOuterAlt(_localctx, 15);
				{
				setState(2137);
				match(SETMINUS);
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class StrictIdentifierContext extends ParserRuleContext {
		public StrictIdentifierContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_strictIdentifier; }
	 
		public StrictIdentifierContext() { }
		public void copyFrom(StrictIdentifierContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class QuotedIdentifierAlternativeContext extends StrictIdentifierContext {
		public QuotedIdentifierContext quotedIdentifier() {
			return getRuleContext(QuotedIdentifierContext.class,0);
		}
		public QuotedIdentifierAlternativeContext(StrictIdentifierContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQuotedIdentifierAlternative(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQuotedIdentifierAlternative(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQuotedIdentifierAlternative(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class UnquotedIdentifierContext extends StrictIdentifierContext {
		public TerminalNode IDENTIFIER() { return getToken(SqlBaseParser.IDENTIFIER, 0); }
		public NonReservedContext nonReserved() {
			return getRuleContext(NonReservedContext.class,0);
		}
		public UnquotedIdentifierContext(StrictIdentifierContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterUnquotedIdentifier(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitUnquotedIdentifier(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitUnquotedIdentifier(this);
			else return visitor.visitChildren(this);
		}
	}

	public final StrictIdentifierContext strictIdentifier() throws RecognitionException {
		StrictIdentifierContext _localctx = new StrictIdentifierContext(_ctx, getState());
		enterRule(_localctx, 172, RULE_strictIdentifier);
		try {
			setState(2143);
			switch (_input.LA(1)) {
			case IDENTIFIER:
				_localctx = new UnquotedIdentifierContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(2140);
				match(IDENTIFIER);
				}
				break;
			case BACKQUOTED_IDENTIFIER:
				_localctx = new QuotedIdentifierAlternativeContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(2141);
				quotedIdentifier();
				}
				break;
			case SELECT:
			case FROM:
			case ADD:
			case AS:
			case ALL:
			case DISTINCT:
			case WHERE:
			case GROUP:
			case BY:
			case GROUPING:
			case SETS:
			case CUBE:
			case ROLLUP:
			case ORDER:
			case HAVING:
			case LIMIT:
			case AT:
			case OR:
			case AND:
			case IN:
			case NOT:
			case NO:
			case EXISTS:
			case BETWEEN:
			case LIKE:
			case RLIKE:
			case IS:
			case NULL:
			case TRUE:
			case FALSE:
			case NULLS:
			case ASC:
			case DESC:
			case FOR:
			case INTERVAL:
			case CASE:
			case WHEN:
			case THEN:
			case ELSE:
			case END:
			case OUTER:
			case LATERAL:
			case WINDOW:
			case OVER:
			case PARTITION:
			case RANGE:
			case ROWS:
			case UNBOUNDED:
			case PRECEDING:
			case FOLLOWING:
			case CURRENT:
			case FIRST:
			case LAST:
			case ROW:
			case WITH:
			case VALUES:
			case CREATE:
			case TABLE:
			case VIEW:
			case REPLACE:
			case INSERT:
			case DELETE:
			case INTO:
			case DESCRIBE:
			case EXPLAIN:
			case FORMAT:
			case LOGICAL:
			case CODEGEN:
			case CAST:
			case SHOW:
			case TABLES:
			case COLUMNS:
			case COLUMN:
			case USE:
			case PARTITIONS:
			case FUNCTIONS:
			case DROP:
			case TO:
			case TABLESAMPLE:
			case STRATIFY:
			case ALTER:
			case RENAME:
			case ARRAY:
			case MAP:
			case STRUCT:
			case COMMENT:
			case SET:
			case RESET:
			case DATA:
			case START:
			case TRANSACTION:
			case COMMIT:
			case ROLLBACK:
			case MACRO:
			case IF:
			case DIV:
			case PERCENTLIT:
			case BUCKET:
			case OUT:
			case OF:
			case SORT:
			case CLUSTER:
			case DISTRIBUTE:
			case OVERWRITE:
			case TRANSFORM:
			case REDUCE:
			case USING:
			case SERDE:
			case SERDEPROPERTIES:
			case RECORDREADER:
			case RECORDWRITER:
			case DELIMITED:
			case FIELDS:
			case TERMINATED:
			case COLLECTION:
			case ITEMS:
			case KEYS:
			case ESCAPED:
			case LINES:
			case SEPARATED:
			case FUNCTION:
			case EXTENDED:
			case REFRESH:
			case CLEAR:
			case CACHE:
			case UNCACHE:
			case LAZY:
			case FORMATTED:
			case GLOBAL:
			case TEMPORARY:
			case OPTIONS:
			case UNSET:
			case TBLPROPERTIES:
			case DBPROPERTIES:
			case BUCKETS:
			case SKEWED:
			case STORED:
			case DIRECTORIES:
			case LOCATION:
			case EXCHANGE:
			case ARCHIVE:
			case UNARCHIVE:
			case FILEFORMAT:
			case TOUCH:
			case COMPACT:
			case CONCATENATE:
			case CHANGE:
			case CASCADE:
			case RESTRICT:
			case CLUSTERED:
			case SORTED:
			case PURGE:
			case INPUTFORMAT:
			case OUTPUTFORMAT:
			case DATABASE:
			case DATABASES:
			case DFS:
			case TRUNCATE:
			case ANALYZE:
			case COMPUTE:
			case LIST:
			case STATISTICS:
			case PARTITIONED:
			case EXTERNAL:
			case DEFINED:
			case REVOKE:
			case GRANT:
			case LOCK:
			case UNLOCK:
			case MSCK:
			case REPAIR:
			case RECOVER:
			case EXPORT:
			case IMPORT:
			case LOAD:
			case ROLE:
			case ROLES:
			case COMPACTIONS:
			case PRINCIPALS:
			case TRANSACTIONS:
			case INDEX:
			case INDEXES:
			case LOCKS:
			case OPTION:
			case LOCAL:
			case INPATH:
			case CURRENT_DATE:
			case CURRENT_TIMESTAMP:
				_localctx = new UnquotedIdentifierContext(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(2142);
				nonReserved();
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class QuotedIdentifierContext extends ParserRuleContext {
		public TerminalNode BACKQUOTED_IDENTIFIER() { return getToken(SqlBaseParser.BACKQUOTED_IDENTIFIER, 0); }
		public QuotedIdentifierContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_quotedIdentifier; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterQuotedIdentifier(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitQuotedIdentifier(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitQuotedIdentifier(this);
			else return visitor.visitChildren(this);
		}
	}

	public final QuotedIdentifierContext quotedIdentifier() throws RecognitionException {
		QuotedIdentifierContext _localctx = new QuotedIdentifierContext(_ctx, getState());
		enterRule(_localctx, 174, RULE_quotedIdentifier);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(2145);
			match(BACKQUOTED_IDENTIFIER);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class NumberContext extends ParserRuleContext {
		public NumberContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_number; }
	 
		public NumberContext() { }
		public void copyFrom(NumberContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class DecimalLiteralContext extends NumberContext {
		public TerminalNode DECIMAL_VALUE() { return getToken(SqlBaseParser.DECIMAL_VALUE, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public DecimalLiteralContext(NumberContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDecimalLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDecimalLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDecimalLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class BigIntLiteralContext extends NumberContext {
		public TerminalNode BIGINT_LITERAL() { return getToken(SqlBaseParser.BIGINT_LITERAL, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public BigIntLiteralContext(NumberContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterBigIntLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitBigIntLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitBigIntLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class TinyIntLiteralContext extends NumberContext {
		public TerminalNode TINYINT_LITERAL() { return getToken(SqlBaseParser.TINYINT_LITERAL, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public TinyIntLiteralContext(NumberContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterTinyIntLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitTinyIntLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitTinyIntLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class BigDecimalLiteralContext extends NumberContext {
		public TerminalNode BIGDECIMAL_LITERAL() { return getToken(SqlBaseParser.BIGDECIMAL_LITERAL, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public BigDecimalLiteralContext(NumberContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterBigDecimalLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitBigDecimalLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitBigDecimalLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class DoubleLiteralContext extends NumberContext {
		public TerminalNode DOUBLE_LITERAL() { return getToken(SqlBaseParser.DOUBLE_LITERAL, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public DoubleLiteralContext(NumberContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterDoubleLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitDoubleLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitDoubleLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class IntegerLiteralContext extends NumberContext {
		public TerminalNode INTEGER_VALUE() { return getToken(SqlBaseParser.INTEGER_VALUE, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public IntegerLiteralContext(NumberContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterIntegerLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitIntegerLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitIntegerLiteral(this);
			else return visitor.visitChildren(this);
		}
	}
	public static class SmallIntLiteralContext extends NumberContext {
		public TerminalNode SMALLINT_LITERAL() { return getToken(SqlBaseParser.SMALLINT_LITERAL, 0); }
		public TerminalNode MINUS() { return getToken(SqlBaseParser.MINUS, 0); }
		public SmallIntLiteralContext(NumberContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterSmallIntLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitSmallIntLiteral(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitSmallIntLiteral(this);
			else return visitor.visitChildren(this);
		}
	}

	public final NumberContext number() throws RecognitionException {
		NumberContext _localctx = new NumberContext(_ctx, getState());
		enterRule(_localctx, 176, RULE_number);
		int _la;
		try {
			setState(2175);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,299,_ctx) ) {
			case 1:
				_localctx = new DecimalLiteralContext(_localctx);
				enterOuterAlt(_localctx, 1);
				{
				setState(2148);
				_la = _input.LA(1);
				if (_la==MINUS) {
					{
					setState(2147);
					match(MINUS);
					}
				}

				setState(2150);
				match(DECIMAL_VALUE);
				}
				break;
			case 2:
				_localctx = new IntegerLiteralContext(_localctx);
				enterOuterAlt(_localctx, 2);
				{
				setState(2152);
				_la = _input.LA(1);
				if (_la==MINUS) {
					{
					setState(2151);
					match(MINUS);
					}
				}

				setState(2154);
				match(INTEGER_VALUE);
				}
				break;
			case 3:
				_localctx = new BigIntLiteralContext(_localctx);
				enterOuterAlt(_localctx, 3);
				{
				setState(2156);
				_la = _input.LA(1);
				if (_la==MINUS) {
					{
					setState(2155);
					match(MINUS);
					}
				}

				setState(2158);
				match(BIGINT_LITERAL);
				}
				break;
			case 4:
				_localctx = new SmallIntLiteralContext(_localctx);
				enterOuterAlt(_localctx, 4);
				{
				setState(2160);
				_la = _input.LA(1);
				if (_la==MINUS) {
					{
					setState(2159);
					match(MINUS);
					}
				}

				setState(2162);
				match(SMALLINT_LITERAL);
				}
				break;
			case 5:
				_localctx = new TinyIntLiteralContext(_localctx);
				enterOuterAlt(_localctx, 5);
				{
				setState(2164);
				_la = _input.LA(1);
				if (_la==MINUS) {
					{
					setState(2163);
					match(MINUS);
					}
				}

				setState(2166);
				match(TINYINT_LITERAL);
				}
				break;
			case 6:
				_localctx = new DoubleLiteralContext(_localctx);
				enterOuterAlt(_localctx, 6);
				{
				setState(2168);
				_la = _input.LA(1);
				if (_la==MINUS) {
					{
					setState(2167);
					match(MINUS);
					}
				}

				setState(2170);
				match(DOUBLE_LITERAL);
				}
				break;
			case 7:
				_localctx = new BigDecimalLiteralContext(_localctx);
				enterOuterAlt(_localctx, 7);
				{
				setState(2172);
				_la = _input.LA(1);
				if (_la==MINUS) {
					{
					setState(2171);
					match(MINUS);
					}
				}

				setState(2174);
				match(BIGDECIMAL_LITERAL);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class NonReservedContext extends ParserRuleContext {
		public TerminalNode SHOW() { return getToken(SqlBaseParser.SHOW, 0); }
		public TerminalNode TABLES() { return getToken(SqlBaseParser.TABLES, 0); }
		public TerminalNode COLUMNS() { return getToken(SqlBaseParser.COLUMNS, 0); }
		public TerminalNode COLUMN() { return getToken(SqlBaseParser.COLUMN, 0); }
		public TerminalNode PARTITIONS() { return getToken(SqlBaseParser.PARTITIONS, 0); }
		public TerminalNode FUNCTIONS() { return getToken(SqlBaseParser.FUNCTIONS, 0); }
		public TerminalNode DATABASES() { return getToken(SqlBaseParser.DATABASES, 0); }
		public TerminalNode ADD() { return getToken(SqlBaseParser.ADD, 0); }
		public TerminalNode OVER() { return getToken(SqlBaseParser.OVER, 0); }
		public TerminalNode PARTITION() { return getToken(SqlBaseParser.PARTITION, 0); }
		public TerminalNode RANGE() { return getToken(SqlBaseParser.RANGE, 0); }
		public TerminalNode ROWS() { return getToken(SqlBaseParser.ROWS, 0); }
		public TerminalNode PRECEDING() { return getToken(SqlBaseParser.PRECEDING, 0); }
		public TerminalNode FOLLOWING() { return getToken(SqlBaseParser.FOLLOWING, 0); }
		public TerminalNode CURRENT() { return getToken(SqlBaseParser.CURRENT, 0); }
		public TerminalNode ROW() { return getToken(SqlBaseParser.ROW, 0); }
		public TerminalNode LAST() { return getToken(SqlBaseParser.LAST, 0); }
		public TerminalNode FIRST() { return getToken(SqlBaseParser.FIRST, 0); }
		public TerminalNode MAP() { return getToken(SqlBaseParser.MAP, 0); }
		public TerminalNode ARRAY() { return getToken(SqlBaseParser.ARRAY, 0); }
		public TerminalNode STRUCT() { return getToken(SqlBaseParser.STRUCT, 0); }
		public TerminalNode LATERAL() { return getToken(SqlBaseParser.LATERAL, 0); }
		public TerminalNode WINDOW() { return getToken(SqlBaseParser.WINDOW, 0); }
		public TerminalNode REDUCE() { return getToken(SqlBaseParser.REDUCE, 0); }
		public TerminalNode TRANSFORM() { return getToken(SqlBaseParser.TRANSFORM, 0); }
		public TerminalNode USING() { return getToken(SqlBaseParser.USING, 0); }
		public TerminalNode SERDE() { return getToken(SqlBaseParser.SERDE, 0); }
		public TerminalNode SERDEPROPERTIES() { return getToken(SqlBaseParser.SERDEPROPERTIES, 0); }
		public TerminalNode RECORDREADER() { return getToken(SqlBaseParser.RECORDREADER, 0); }
		public TerminalNode DELIMITED() { return getToken(SqlBaseParser.DELIMITED, 0); }
		public TerminalNode FIELDS() { return getToken(SqlBaseParser.FIELDS, 0); }
		public TerminalNode TERMINATED() { return getToken(SqlBaseParser.TERMINATED, 0); }
		public TerminalNode COLLECTION() { return getToken(SqlBaseParser.COLLECTION, 0); }
		public TerminalNode ITEMS() { return getToken(SqlBaseParser.ITEMS, 0); }
		public TerminalNode KEYS() { return getToken(SqlBaseParser.KEYS, 0); }
		public TerminalNode ESCAPED() { return getToken(SqlBaseParser.ESCAPED, 0); }
		public TerminalNode LINES() { return getToken(SqlBaseParser.LINES, 0); }
		public TerminalNode SEPARATED() { return getToken(SqlBaseParser.SEPARATED, 0); }
		public TerminalNode EXTENDED() { return getToken(SqlBaseParser.EXTENDED, 0); }
		public TerminalNode REFRESH() { return getToken(SqlBaseParser.REFRESH, 0); }
		public TerminalNode CLEAR() { return getToken(SqlBaseParser.CLEAR, 0); }
		public TerminalNode CACHE() { return getToken(SqlBaseParser.CACHE, 0); }
		public TerminalNode UNCACHE() { return getToken(SqlBaseParser.UNCACHE, 0); }
		public TerminalNode LAZY() { return getToken(SqlBaseParser.LAZY, 0); }
		public TerminalNode GLOBAL() { return getToken(SqlBaseParser.GLOBAL, 0); }
		public TerminalNode TEMPORARY() { return getToken(SqlBaseParser.TEMPORARY, 0); }
		public TerminalNode OPTIONS() { return getToken(SqlBaseParser.OPTIONS, 0); }
		public TerminalNode GROUPING() { return getToken(SqlBaseParser.GROUPING, 0); }
		public TerminalNode CUBE() { return getToken(SqlBaseParser.CUBE, 0); }
		public TerminalNode ROLLUP() { return getToken(SqlBaseParser.ROLLUP, 0); }
		public TerminalNode EXPLAIN() { return getToken(SqlBaseParser.EXPLAIN, 0); }
		public TerminalNode FORMAT() { return getToken(SqlBaseParser.FORMAT, 0); }
		public TerminalNode LOGICAL() { return getToken(SqlBaseParser.LOGICAL, 0); }
		public TerminalNode FORMATTED() { return getToken(SqlBaseParser.FORMATTED, 0); }
		public TerminalNode CODEGEN() { return getToken(SqlBaseParser.CODEGEN, 0); }
		public TerminalNode TABLESAMPLE() { return getToken(SqlBaseParser.TABLESAMPLE, 0); }
		public TerminalNode USE() { return getToken(SqlBaseParser.USE, 0); }
		public List<TerminalNode> TO() { return getTokens(SqlBaseParser.TO); }
		public TerminalNode TO(int i) {
			return getToken(SqlBaseParser.TO, i);
		}
		public TerminalNode BUCKET() { return getToken(SqlBaseParser.BUCKET, 0); }
		public TerminalNode PERCENTLIT() { return getToken(SqlBaseParser.PERCENTLIT, 0); }
		public TerminalNode OUT() { return getToken(SqlBaseParser.OUT, 0); }
		public TerminalNode OF() { return getToken(SqlBaseParser.OF, 0); }
		public TerminalNode SET() { return getToken(SqlBaseParser.SET, 0); }
		public TerminalNode RESET() { return getToken(SqlBaseParser.RESET, 0); }
		public TerminalNode VIEW() { return getToken(SqlBaseParser.VIEW, 0); }
		public TerminalNode REPLACE() { return getToken(SqlBaseParser.REPLACE, 0); }
		public TerminalNode IF() { return getToken(SqlBaseParser.IF, 0); }
		public TerminalNode NO() { return getToken(SqlBaseParser.NO, 0); }
		public TerminalNode DATA() { return getToken(SqlBaseParser.DATA, 0); }
		public TerminalNode START() { return getToken(SqlBaseParser.START, 0); }
		public TerminalNode TRANSACTION() { return getToken(SqlBaseParser.TRANSACTION, 0); }
		public TerminalNode COMMIT() { return getToken(SqlBaseParser.COMMIT, 0); }
		public TerminalNode ROLLBACK() { return getToken(SqlBaseParser.ROLLBACK, 0); }
		public TerminalNode SORT() { return getToken(SqlBaseParser.SORT, 0); }
		public TerminalNode CLUSTER() { return getToken(SqlBaseParser.CLUSTER, 0); }
		public TerminalNode DISTRIBUTE() { return getToken(SqlBaseParser.DISTRIBUTE, 0); }
		public TerminalNode UNSET() { return getToken(SqlBaseParser.UNSET, 0); }
		public TerminalNode TBLPROPERTIES() { return getToken(SqlBaseParser.TBLPROPERTIES, 0); }
		public TerminalNode SKEWED() { return getToken(SqlBaseParser.SKEWED, 0); }
		public TerminalNode STORED() { return getToken(SqlBaseParser.STORED, 0); }
		public TerminalNode DIRECTORIES() { return getToken(SqlBaseParser.DIRECTORIES, 0); }
		public TerminalNode LOCATION() { return getToken(SqlBaseParser.LOCATION, 0); }
		public TerminalNode EXCHANGE() { return getToken(SqlBaseParser.EXCHANGE, 0); }
		public TerminalNode ARCHIVE() { return getToken(SqlBaseParser.ARCHIVE, 0); }
		public TerminalNode UNARCHIVE() { return getToken(SqlBaseParser.UNARCHIVE, 0); }
		public TerminalNode FILEFORMAT() { return getToken(SqlBaseParser.FILEFORMAT, 0); }
		public TerminalNode TOUCH() { return getToken(SqlBaseParser.TOUCH, 0); }
		public TerminalNode COMPACT() { return getToken(SqlBaseParser.COMPACT, 0); }
		public TerminalNode CONCATENATE() { return getToken(SqlBaseParser.CONCATENATE, 0); }
		public TerminalNode CHANGE() { return getToken(SqlBaseParser.CHANGE, 0); }
		public TerminalNode CASCADE() { return getToken(SqlBaseParser.CASCADE, 0); }
		public TerminalNode RESTRICT() { return getToken(SqlBaseParser.RESTRICT, 0); }
		public TerminalNode BUCKETS() { return getToken(SqlBaseParser.BUCKETS, 0); }
		public TerminalNode CLUSTERED() { return getToken(SqlBaseParser.CLUSTERED, 0); }
		public TerminalNode SORTED() { return getToken(SqlBaseParser.SORTED, 0); }
		public TerminalNode PURGE() { return getToken(SqlBaseParser.PURGE, 0); }
		public TerminalNode INPUTFORMAT() { return getToken(SqlBaseParser.INPUTFORMAT, 0); }
		public TerminalNode OUTPUTFORMAT() { return getToken(SqlBaseParser.OUTPUTFORMAT, 0); }
		public TerminalNode DBPROPERTIES() { return getToken(SqlBaseParser.DBPROPERTIES, 0); }
		public TerminalNode DFS() { return getToken(SqlBaseParser.DFS, 0); }
		public TerminalNode TRUNCATE() { return getToken(SqlBaseParser.TRUNCATE, 0); }
		public TerminalNode COMPUTE() { return getToken(SqlBaseParser.COMPUTE, 0); }
		public TerminalNode LIST() { return getToken(SqlBaseParser.LIST, 0); }
		public TerminalNode STATISTICS() { return getToken(SqlBaseParser.STATISTICS, 0); }
		public TerminalNode ANALYZE() { return getToken(SqlBaseParser.ANALYZE, 0); }
		public TerminalNode PARTITIONED() { return getToken(SqlBaseParser.PARTITIONED, 0); }
		public TerminalNode EXTERNAL() { return getToken(SqlBaseParser.EXTERNAL, 0); }
		public TerminalNode DEFINED() { return getToken(SqlBaseParser.DEFINED, 0); }
		public TerminalNode RECORDWRITER() { return getToken(SqlBaseParser.RECORDWRITER, 0); }
		public TerminalNode REVOKE() { return getToken(SqlBaseParser.REVOKE, 0); }
		public TerminalNode GRANT() { return getToken(SqlBaseParser.GRANT, 0); }
		public TerminalNode LOCK() { return getToken(SqlBaseParser.LOCK, 0); }
		public TerminalNode UNLOCK() { return getToken(SqlBaseParser.UNLOCK, 0); }
		public TerminalNode MSCK() { return getToken(SqlBaseParser.MSCK, 0); }
		public TerminalNode REPAIR() { return getToken(SqlBaseParser.REPAIR, 0); }
		public TerminalNode RECOVER() { return getToken(SqlBaseParser.RECOVER, 0); }
		public TerminalNode EXPORT() { return getToken(SqlBaseParser.EXPORT, 0); }
		public TerminalNode IMPORT() { return getToken(SqlBaseParser.IMPORT, 0); }
		public TerminalNode LOAD() { return getToken(SqlBaseParser.LOAD, 0); }
		public TerminalNode VALUES() { return getToken(SqlBaseParser.VALUES, 0); }
		public TerminalNode COMMENT() { return getToken(SqlBaseParser.COMMENT, 0); }
		public TerminalNode ROLE() { return getToken(SqlBaseParser.ROLE, 0); }
		public TerminalNode ROLES() { return getToken(SqlBaseParser.ROLES, 0); }
		public TerminalNode COMPACTIONS() { return getToken(SqlBaseParser.COMPACTIONS, 0); }
		public TerminalNode PRINCIPALS() { return getToken(SqlBaseParser.PRINCIPALS, 0); }
		public TerminalNode TRANSACTIONS() { return getToken(SqlBaseParser.TRANSACTIONS, 0); }
		public TerminalNode INDEX() { return getToken(SqlBaseParser.INDEX, 0); }
		public TerminalNode INDEXES() { return getToken(SqlBaseParser.INDEXES, 0); }
		public TerminalNode LOCKS() { return getToken(SqlBaseParser.LOCKS, 0); }
		public TerminalNode OPTION() { return getToken(SqlBaseParser.OPTION, 0); }
		public TerminalNode LOCAL() { return getToken(SqlBaseParser.LOCAL, 0); }
		public TerminalNode INPATH() { return getToken(SqlBaseParser.INPATH, 0); }
		public TerminalNode ASC() { return getToken(SqlBaseParser.ASC, 0); }
		public TerminalNode DESC() { return getToken(SqlBaseParser.DESC, 0); }
		public TerminalNode LIMIT() { return getToken(SqlBaseParser.LIMIT, 0); }
		public TerminalNode RENAME() { return getToken(SqlBaseParser.RENAME, 0); }
		public TerminalNode SETS() { return getToken(SqlBaseParser.SETS, 0); }
		public TerminalNode AT() { return getToken(SqlBaseParser.AT, 0); }
		public TerminalNode NULLS() { return getToken(SqlBaseParser.NULLS, 0); }
		public TerminalNode OVERWRITE() { return getToken(SqlBaseParser.OVERWRITE, 0); }
		public TerminalNode ALL() { return getToken(SqlBaseParser.ALL, 0); }
		public TerminalNode ALTER() { return getToken(SqlBaseParser.ALTER, 0); }
		public TerminalNode AS() { return getToken(SqlBaseParser.AS, 0); }
		public TerminalNode BETWEEN() { return getToken(SqlBaseParser.BETWEEN, 0); }
		public TerminalNode BY() { return getToken(SqlBaseParser.BY, 0); }
		public TerminalNode CREATE() { return getToken(SqlBaseParser.CREATE, 0); }
		public TerminalNode DELETE() { return getToken(SqlBaseParser.DELETE, 0); }
		public TerminalNode DESCRIBE() { return getToken(SqlBaseParser.DESCRIBE, 0); }
		public TerminalNode DROP() { return getToken(SqlBaseParser.DROP, 0); }
		public TerminalNode EXISTS() { return getToken(SqlBaseParser.EXISTS, 0); }
		public TerminalNode FALSE() { return getToken(SqlBaseParser.FALSE, 0); }
		public TerminalNode FOR() { return getToken(SqlBaseParser.FOR, 0); }
		public TerminalNode GROUP() { return getToken(SqlBaseParser.GROUP, 0); }
		public TerminalNode IN() { return getToken(SqlBaseParser.IN, 0); }
		public TerminalNode INSERT() { return getToken(SqlBaseParser.INSERT, 0); }
		public TerminalNode INTO() { return getToken(SqlBaseParser.INTO, 0); }
		public TerminalNode IS() { return getToken(SqlBaseParser.IS, 0); }
		public TerminalNode LIKE() { return getToken(SqlBaseParser.LIKE, 0); }
		public TerminalNode NULL() { return getToken(SqlBaseParser.NULL, 0); }
		public TerminalNode ORDER() { return getToken(SqlBaseParser.ORDER, 0); }
		public TerminalNode OUTER() { return getToken(SqlBaseParser.OUTER, 0); }
		public List<TerminalNode> TABLE() { return getTokens(SqlBaseParser.TABLE); }
		public TerminalNode TABLE(int i) {
			return getToken(SqlBaseParser.TABLE, i);
		}
		public TerminalNode TRUE() { return getToken(SqlBaseParser.TRUE, 0); }
		public List<TerminalNode> WITH() { return getTokens(SqlBaseParser.WITH); }
		public TerminalNode WITH(int i) {
			return getToken(SqlBaseParser.WITH, i);
		}
		public TerminalNode RLIKE() { return getToken(SqlBaseParser.RLIKE, 0); }
		public TerminalNode AND() { return getToken(SqlBaseParser.AND, 0); }
		public TerminalNode CASE() { return getToken(SqlBaseParser.CASE, 0); }
		public TerminalNode CAST() { return getToken(SqlBaseParser.CAST, 0); }
		public TerminalNode DISTINCT() { return getToken(SqlBaseParser.DISTINCT, 0); }
		public TerminalNode DIV() { return getToken(SqlBaseParser.DIV, 0); }
		public TerminalNode ELSE() { return getToken(SqlBaseParser.ELSE, 0); }
		public TerminalNode END() { return getToken(SqlBaseParser.END, 0); }
		public TerminalNode FUNCTION() { return getToken(SqlBaseParser.FUNCTION, 0); }
		public TerminalNode INTERVAL() { return getToken(SqlBaseParser.INTERVAL, 0); }
		public TerminalNode MACRO() { return getToken(SqlBaseParser.MACRO, 0); }
		public TerminalNode OR() { return getToken(SqlBaseParser.OR, 0); }
		public TerminalNode STRATIFY() { return getToken(SqlBaseParser.STRATIFY, 0); }
		public TerminalNode THEN() { return getToken(SqlBaseParser.THEN, 0); }
		public TerminalNode UNBOUNDED() { return getToken(SqlBaseParser.UNBOUNDED, 0); }
		public TerminalNode WHEN() { return getToken(SqlBaseParser.WHEN, 0); }
		public TerminalNode DATABASE() { return getToken(SqlBaseParser.DATABASE, 0); }
		public TerminalNode SELECT() { return getToken(SqlBaseParser.SELECT, 0); }
		public TerminalNode FROM() { return getToken(SqlBaseParser.FROM, 0); }
		public TerminalNode WHERE() { return getToken(SqlBaseParser.WHERE, 0); }
		public TerminalNode HAVING() { return getToken(SqlBaseParser.HAVING, 0); }
		public TerminalNode NOT() { return getToken(SqlBaseParser.NOT, 0); }
		public TerminalNode CURRENT_DATE() { return getToken(SqlBaseParser.CURRENT_DATE, 0); }
		public TerminalNode CURRENT_TIMESTAMP() { return getToken(SqlBaseParser.CURRENT_TIMESTAMP, 0); }
		public NonReservedContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_nonReserved; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).enterNonReserved(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof SqlBaseListener ) ((SqlBaseListener)listener).exitNonReserved(this);
		}
		@Override
		public <T> T accept(ParseTreeVisitor<? extends T> visitor) {
			if ( visitor instanceof SqlBaseVisitor ) return ((SqlBaseVisitor<? extends T>)visitor).visitNonReserved(this);
			else return visitor.visitChildren(this);
		}
	}

	public final NonReservedContext nonReserved() throws RecognitionException {
		NonReservedContext _localctx = new NonReservedContext(_ctx, getState());
		enterRule(_localctx, 178, RULE_nonReserved);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(2177);
			_la = _input.LA(1);
			if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << SELECT) | (1L << FROM) | (1L << ADD) | (1L << AS) | (1L << ALL) | (1L << DISTINCT) | (1L << WHERE) | (1L << GROUP) | (1L << BY) | (1L << GROUPING) | (1L << SETS) | (1L << CUBE) | (1L << ROLLUP) | (1L << ORDER) | (1L << HAVING) | (1L << LIMIT) | (1L << AT) | (1L << OR) | (1L << AND) | (1L << IN) | (1L << NOT) | (1L << NO) | (1L << EXISTS) | (1L << BETWEEN) | (1L << LIKE) | (1L << RLIKE) | (1L << IS) | (1L << NULL) | (1L << TRUE) | (1L << FALSE) | (1L << NULLS) | (1L << ASC) | (1L << DESC) | (1L << FOR) | (1L << INTERVAL) | (1L << CASE) | (1L << WHEN) | (1L << THEN) | (1L << ELSE) | (1L << END) | (1L << OUTER) | (1L << LATERAL) | (1L << WINDOW) | (1L << OVER) | (1L << PARTITION) | (1L << RANGE) | (1L << ROWS))) != 0) || ((((_la - 64)) & ~0x3f) == 0 && ((1L << (_la - 64)) & ((1L << (UNBOUNDED - 64)) | (1L << (PRECEDING - 64)) | (1L << (FOLLOWING - 64)) | (1L << (CURRENT - 64)) | (1L << (FIRST - 64)) | (1L << (LAST - 64)) | (1L << (ROW - 64)) | (1L << (WITH - 64)) | (1L << (VALUES - 64)) | (1L << (CREATE - 64)) | (1L << (TABLE - 64)) | (1L << (VIEW - 64)) | (1L << (REPLACE - 64)) | (1L << (INSERT - 64)) | (1L << (DELETE - 64)) | (1L << (INTO - 64)) | (1L << (DESCRIBE - 64)) | (1L << (EXPLAIN - 64)) | (1L << (FORMAT - 64)) | (1L << (LOGICAL - 64)) | (1L << (CODEGEN - 64)) | (1L << (CAST - 64)) | (1L << (SHOW - 64)) | (1L << (TABLES - 64)) | (1L << (COLUMNS - 64)) | (1L << (COLUMN - 64)) | (1L << (USE - 64)) | (1L << (PARTITIONS - 64)) | (1L << (FUNCTIONS - 64)) | (1L << (DROP - 64)) | (1L << (TO - 64)) | (1L << (TABLESAMPLE - 64)) | (1L << (STRATIFY - 64)) | (1L << (ALTER - 64)) | (1L << (RENAME - 64)) | (1L << (ARRAY - 64)) | (1L << (MAP - 64)) | (1L << (STRUCT - 64)) | (1L << (COMMENT - 64)) | (1L << (SET - 64)) | (1L << (RESET - 64)) | (1L << (DATA - 64)) | (1L << (START - 64)) | (1L << (TRANSACTION - 64)) | (1L << (COMMIT - 64)) | (1L << (ROLLBACK - 64)) | (1L << (MACRO - 64)) | (1L << (IF - 64)))) != 0) || ((((_la - 129)) & ~0x3f) == 0 && ((1L << (_la - 129)) & ((1L << (DIV - 129)) | (1L << (PERCENTLIT - 129)) | (1L << (BUCKET - 129)) | (1L << (OUT - 129)) | (1L << (OF - 129)) | (1L << (SORT - 129)) | (1L << (CLUSTER - 129)) | (1L << (DISTRIBUTE - 129)) | (1L << (OVERWRITE - 129)) | (1L << (TRANSFORM - 129)) | (1L << (REDUCE - 129)) | (1L << (USING - 129)) | (1L << (SERDE - 129)) | (1L << (SERDEPROPERTIES - 129)) | (1L << (RECORDREADER - 129)) | (1L << (RECORDWRITER - 129)) | (1L << (DELIMITED - 129)) | (1L << (FIELDS - 129)) | (1L << (TERMINATED - 129)) | (1L << (COLLECTION - 129)) | (1L << (ITEMS - 129)) | (1L << (KEYS - 129)) | (1L << (ESCAPED - 129)) | (1L << (LINES - 129)) | (1L << (SEPARATED - 129)) | (1L << (FUNCTION - 129)) | (1L << (EXTENDED - 129)) | (1L << (REFRESH - 129)) | (1L << (CLEAR - 129)) | (1L << (CACHE - 129)) | (1L << (UNCACHE - 129)) | (1L << (LAZY - 129)) | (1L << (FORMATTED - 129)) | (1L << (GLOBAL - 129)) | (1L << (TEMPORARY - 129)) | (1L << (OPTIONS - 129)) | (1L << (UNSET - 129)) | (1L << (TBLPROPERTIES - 129)) | (1L << (DBPROPERTIES - 129)) | (1L << (BUCKETS - 129)) | (1L << (SKEWED - 129)) | (1L << (STORED - 129)) | (1L << (DIRECTORIES - 129)) | (1L << (LOCATION - 129)) | (1L << (EXCHANGE - 129)) | (1L << (ARCHIVE - 129)) | (1L << (UNARCHIVE - 129)) | (1L << (FILEFORMAT - 129)) | (1L << (TOUCH - 129)) | (1L << (COMPACT - 129)) | (1L << (CONCATENATE - 129)) | (1L << (CHANGE - 129)) | (1L << (CASCADE - 129)) | (1L << (RESTRICT - 129)) | (1L << (CLUSTERED - 129)) | (1L << (SORTED - 129)) | (1L << (PURGE - 129)) | (1L << (INPUTFORMAT - 129)) | (1L << (OUTPUTFORMAT - 129)))) != 0) || ((((_la - 193)) & ~0x3f) == 0 && ((1L << (_la - 193)) & ((1L << (DATABASE - 193)) | (1L << (DATABASES - 193)) | (1L << (DFS - 193)) | (1L << (TRUNCATE - 193)) | (1L << (ANALYZE - 193)) | (1L << (COMPUTE - 193)) | (1L << (LIST - 193)) | (1L << (STATISTICS - 193)) | (1L << (PARTITIONED - 193)) | (1L << (EXTERNAL - 193)) | (1L << (DEFINED - 193)) | (1L << (REVOKE - 193)) | (1L << (GRANT - 193)) | (1L << (LOCK - 193)) | (1L << (UNLOCK - 193)) | (1L << (MSCK - 193)) | (1L << (REPAIR - 193)) | (1L << (RECOVER - 193)) | (1L << (EXPORT - 193)) | (1L << (IMPORT - 193)) | (1L << (LOAD - 193)) | (1L << (ROLE - 193)) | (1L << (ROLES - 193)) | (1L << (COMPACTIONS - 193)) | (1L << (PRINCIPALS - 193)) | (1L << (TRANSACTIONS - 193)) | (1L << (INDEX - 193)) | (1L << (INDEXES - 193)) | (1L << (LOCKS - 193)) | (1L << (OPTION - 193)) | (1L << (LOCAL - 193)) | (1L << (INPATH - 193)) | (1L << (CURRENT_DATE - 193)) | (1L << (CURRENT_TIMESTAMP - 193)))) != 0)) ) {
			_errHandler.recoverInline(this);
			} else {
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public boolean sempred(RuleContext _localctx, int ruleIndex, int predIndex) {
		switch (ruleIndex) {
		case 33:
			return queryTerm_sempred((QueryTermContext)_localctx, predIndex);
		case 60:
			return booleanExpression_sempred((BooleanExpressionContext)_localctx, predIndex);
		case 63:
			return valueExpression_sempred((ValueExpressionContext)_localctx, predIndex);
		case 64:
			return primaryExpression_sempred((PrimaryExpressionContext)_localctx, predIndex);
		}
		return true;
	}
	private boolean queryTerm_sempred(QueryTermContext _localctx, int predIndex) {
		switch (predIndex) {
		case 0:
			return precpred(_ctx, 1);
		}
		return true;
	}
	private boolean booleanExpression_sempred(BooleanExpressionContext _localctx, int predIndex) {
		switch (predIndex) {
		case 1:
			return precpred(_ctx, 3);
		case 2:
			return precpred(_ctx, 2);
		}
		return true;
	}
	private boolean valueExpression_sempred(ValueExpressionContext _localctx, int predIndex) {
		switch (predIndex) {
		case 3:
			return precpred(_ctx, 7);
		case 4:
			return precpred(_ctx, 6);
		case 5:
			return precpred(_ctx, 5);
		case 6:
			return precpred(_ctx, 4);
		case 7:
			return precpred(_ctx, 3);
		case 8:
			return precpred(_ctx, 2);
		case 9:
			return precpred(_ctx, 1);
		}
		return true;
	}
	private boolean primaryExpression_sempred(PrimaryExpressionContext _localctx, int predIndex) {
		switch (predIndex) {
		case 10:
			return precpred(_ctx, 4);
		case 11:
			return precpred(_ctx, 2);
		}
		return true;
	}

	public static final String _serializedATN =
		"\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\3\u00f5\u0886\4\2\t"+
		"\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13"+
		"\t\13\4\f\t\f\4\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22"+
		"\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30\4\31\t\31"+
		"\4\32\t\32\4\33\t\33\4\34\t\34\4\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!"+
		"\t!\4\"\t\"\4#\t#\4$\t$\4%\t%\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4"+
		",\t,\4-\t-\4.\t.\4/\t/\4\60\t\60\4\61\t\61\4\62\t\62\4\63\t\63\4\64\t"+
		"\64\4\65\t\65\4\66\t\66\4\67\t\67\48\t8\49\t9\4:\t:\4;\t;\4<\t<\4=\t="+
		"\4>\t>\4?\t?\4@\t@\4A\tA\4B\tB\4C\tC\4D\tD\4E\tE\4F\tF\4G\tG\4H\tH\4I"+
		"\tI\4J\tJ\4K\tK\4L\tL\4M\tM\4N\tN\4O\tO\4P\tP\4Q\tQ\4R\tR\4S\tS\4T\tT"+
		"\4U\tU\4V\tV\4W\tW\4X\tX\4Y\tY\4Z\tZ\4[\t[\3\2\3\2\3\2\3\3\3\3\3\3\3\4"+
		"\3\4\3\4\3\5\3\5\3\5\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u00cb\n\6\3\6"+
		"\3\6\3\6\5\6\u00d0\n\6\3\6\5\6\u00d3\n\6\3\6\3\6\3\6\5\6\u00d8\n\6\3\6"+
		"\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u00e5\n\6\3\6\3\6\5\6\u00e9"+
		"\n\6\3\6\3\6\3\6\3\6\3\6\5\6\u00f0\n\6\3\6\3\6\3\6\5\6\u00f5\n\6\3\6\3"+
		"\6\3\6\5\6\u00fa\n\6\3\6\5\6\u00fd\n\6\3\6\5\6\u0100\n\6\3\6\5\6\u0103"+
		"\n\6\3\6\3\6\3\6\3\6\3\6\5\6\u010a\n\6\3\6\3\6\5\6\u010e\n\6\3\6\3\6\3"+
		"\6\3\6\3\6\3\6\5\6\u0116\n\6\3\6\5\6\u0119\n\6\3\6\5\6\u011c\n\6\3\6\5"+
		"\6\u011f\n\6\3\6\5\6\u0122\n\6\3\6\5\6\u0125\n\6\3\6\3\6\5\6\u0129\n\6"+
		"\3\6\5\6\u012c\n\6\3\6\5\6\u012f\n\6\3\6\3\6\3\6\3\6\3\6\5\6\u0136\n\6"+
		"\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u0140\n\6\3\6\3\6\3\6\3\6\3\6\3\6"+
		"\5\6\u0148\n\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6"+
		"\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u015f\n\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6"+
		"\u0167\n\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u016f\n\6\3\6\3\6\3\6\3\6\5\6\u0175"+
		"\n\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u0182\n\6\3\6\6\6"+
		"\u0185\n\6\r\6\16\6\u0186\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u0190\n\6\3"+
		"\6\6\6\u0193\n\6\r\6\16\6\u0194\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3"+
		"\6\3\6\3\6\3\6\3\6\5\6\u01a5\n\6\3\6\3\6\3\6\7\6\u01aa\n\6\f\6\16\6\u01ad"+
		"\13\6\3\6\5\6\u01b0\n\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u01b8\n\6\3\6\3\6"+
		"\3\6\7\6\u01bd\n\6\f\6\16\6\u01c0\13\6\3\6\3\6\3\6\3\6\5\6\u01c6\n\6\3"+
		"\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u01d5\n\6\3\6\3"+
		"\6\5\6\u01d9\n\6\3\6\3\6\3\6\3\6\5\6\u01df\n\6\3\6\3\6\3\6\3\6\5\6\u01e5"+
		"\n\6\3\6\5\6\u01e8\n\6\3\6\5\6\u01eb\n\6\3\6\3\6\3\6\3\6\5\6\u01f1\n\6"+
		"\3\6\3\6\5\6\u01f5\n\6\3\6\3\6\5\6\u01f9\n\6\3\6\3\6\3\6\5\6\u01fe\n\6"+
		"\3\6\3\6\5\6\u0202\n\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u020a\n\6\3\6\5\6\u020d"+
		"\n\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u0216\n\6\3\6\3\6\3\6\5\6\u021b\n"+
		"\6\3\6\3\6\3\6\3\6\5\6\u0221\n\6\3\6\3\6\3\6\3\6\5\6\u0227\n\6\3\6\3\6"+
		"\3\6\3\6\3\6\3\6\3\6\3\6\7\6\u0231\n\6\f\6\16\6\u0234\13\6\5\6\u0236\n"+
		"\6\3\6\3\6\5\6\u023a\n\6\3\6\3\6\3\6\5\6\u023f\n\6\3\6\3\6\3\6\5\6\u0244"+
		"\n\6\3\6\3\6\3\6\3\6\3\6\5\6\u024b\n\6\3\6\5\6\u024e\n\6\3\6\5\6\u0251"+
		"\n\6\3\6\3\6\3\6\3\6\5\6\u0257\n\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u0260"+
		"\n\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u0268\n\6\3\6\3\6\3\6\3\6\5\6\u026e\n"+
		"\6\3\6\3\6\5\6\u0272\n\6\3\6\3\6\5\6\u0276\n\6\3\6\3\6\5\6\u027a\n\6\5"+
		"\6\u027c\n\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u0285\n\6\3\6\3\6\3\6\3\6"+
		"\5\6\u028b\n\6\3\6\3\6\3\6\5\6\u0290\n\6\3\6\5\6\u0293\n\6\3\6\3\6\5\6"+
		"\u0297\n\6\3\6\5\6\u029a\n\6\3\6\3\6\3\6\3\6\3\6\7\6\u02a1\n\6\f\6\16"+
		"\6\u02a4\13\6\3\6\3\6\5\6\u02a8\n\6\3\6\3\6\3\6\5\6\u02ad\n\6\3\6\5\6"+
		"\u02b0\n\6\3\6\3\6\3\6\3\6\5\6\u02b6\n\6\3\6\3\6\3\6\3\6\3\6\3\6\5\6\u02be"+
		"\n\6\3\6\3\6\3\6\5\6\u02c3\n\6\3\6\3\6\3\6\3\6\5\6\u02c9\n\6\3\6\3\6\3"+
		"\6\3\6\5\6\u02cf\n\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\7\6\u02d8\n\6\f\6\16"+
		"\6\u02db\13\6\3\6\3\6\3\6\7\6\u02e0\n\6\f\6\16\6\u02e3\13\6\3\6\3\6\7"+
		"\6\u02e7\n\6\f\6\16\6\u02ea\13\6\3\6\3\6\3\6\7\6\u02ef\n\6\f\6\16\6\u02f2"+
		"\13\6\5\6\u02f4\n\6\3\7\3\7\3\7\3\7\3\7\3\7\5\7\u02fc\n\7\3\7\3\7\5\7"+
		"\u0300\n\7\3\7\3\7\3\7\3\7\3\7\5\7\u0307\n\7\3\7\3\7\3\7\3\7\3\7\3\7\3"+
		"\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7"+
		"\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3"+
		"\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7"+
		"\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3"+
		"\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7"+
		"\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3"+
		"\7\3\7\3\7\5\7\u037b\n\7\3\7\3\7\3\7\3\7\3\7\3\7\5\7\u0383\n\7\3\7\3\7"+
		"\3\7\3\7\3\7\3\7\5\7\u038b\n\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\5\7\u0394\n"+
		"\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\5\7\u039d\n\7\3\7\3\7\5\7\u03a1\n\7\3\7"+
		"\3\7\3\7\3\7\5\7\u03a7\n\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\7\5\7"+
		"\u03b3\n\7\3\b\3\b\5\b\u03b7\n\b\3\b\5\b\u03ba\n\b\3\b\3\b\3\b\3\b\5\b"+
		"\u03c0\n\b\3\b\3\b\3\t\3\t\3\t\3\t\3\t\3\t\5\t\u03ca\n\t\3\t\3\t\3\t\3"+
		"\t\3\n\3\n\3\n\3\n\3\n\3\n\5\n\u03d6\n\n\3\n\3\n\3\n\5\n\u03db\n\n\3\13"+
		"\3\13\3\13\3\f\5\f\u03e1\n\f\3\f\3\f\3\r\3\r\3\r\3\r\3\r\3\r\3\r\3\r\5"+
		"\r\u03ed\n\r\5\r\u03ef\n\r\3\r\3\r\3\r\5\r\u03f4\n\r\3\r\3\r\5\r\u03f8"+
		"\n\r\5\r\u03fa\n\r\3\16\3\16\5\16\u03fe\n\16\3\17\3\17\3\17\3\17\3\17"+
		"\7\17\u0405\n\17\f\17\16\17\u0408\13\17\3\17\3\17\3\20\3\20\3\20\5\20"+
		"\u040f\n\20\3\21\3\21\3\21\3\21\3\21\5\21\u0416\n\21\3\22\3\22\3\22\3"+
		"\22\5\22\u041c\n\22\7\22\u041e\n\22\f\22\16\22\u0421\13\22\3\23\3\23\3"+
		"\23\3\23\7\23\u0427\n\23\f\23\16\23\u042a\13\23\3\24\3\24\5\24\u042e\n"+
		"\24\3\24\3\24\3\24\3\24\3\25\3\25\3\25\3\26\3\26\3\26\3\26\7\26\u043b"+
		"\n\26\f\26\16\26\u043e\13\26\3\26\3\26\3\27\3\27\5\27\u0444\n\27\3\27"+
		"\5\27\u0447\n\27\3\30\3\30\3\30\7\30\u044c\n\30\f\30\16\30\u044f\13\30"+
		"\3\30\5\30\u0452\n\30\3\31\3\31\3\31\3\31\5\31\u0458\n\31\3\32\3\32\3"+
		"\32\3\32\7\32\u045e\n\32\f\32\16\32\u0461\13\32\3\32\3\32\3\33\3\33\3"+
		"\33\3\33\7\33\u0469\n\33\f\33\16\33\u046c\13\33\3\33\3\33\3\34\3\34\3"+
		"\34\3\34\3\34\3\34\5\34\u0476\n\34\3\35\3\35\3\35\3\35\3\35\5\35\u047d"+
		"\n\35\3\36\3\36\3\36\3\36\5\36\u0483\n\36\3\37\3\37\3\37\3 \5 \u0489\n"+
		" \3 \3 \3 \3 \3 \6 \u0490\n \r \16 \u0491\5 \u0494\n \3!\3!\3!\3!\3!\7"+
		"!\u049b\n!\f!\16!\u049e\13!\5!\u04a0\n!\3!\3!\3!\3!\3!\7!\u04a7\n!\f!"+
		"\16!\u04aa\13!\5!\u04ac\n!\3!\3!\3!\3!\3!\7!\u04b3\n!\f!\16!\u04b6\13"+
		"!\5!\u04b8\n!\3!\3!\3!\3!\3!\7!\u04bf\n!\f!\16!\u04c2\13!\5!\u04c4\n!"+
		"\3!\5!\u04c7\n!\3!\3!\5!\u04cb\n!\3\"\5\"\u04ce\n\"\3\"\3\"\3\"\3#\3#"+
		"\3#\3#\3#\3#\5#\u04d9\n#\3#\7#\u04dc\n#\f#\16#\u04df\13#\3$\3$\3$\3$\3"+
		"$\3$\3$\3$\5$\u04e9\n$\3%\3%\5%\u04ed\n%\3%\3%\5%\u04f1\n%\3&\3&\3&\3"+
		"&\3&\3&\3&\3&\3&\3&\5&\u04fd\n&\3&\5&\u0500\n&\3&\3&\5&\u0504\n&\3&\3"+
		"&\3&\3&\3&\3&\3&\3&\5&\u050e\n&\3&\3&\5&\u0512\n&\5&\u0514\n&\3&\5&\u0517"+
		"\n&\3&\3&\5&\u051b\n&\3&\5&\u051e\n&\3&\3&\5&\u0522\n&\3&\3&\5&\u0526"+
		"\n&\3&\3&\5&\u052a\n&\3&\3&\3&\5&\u052f\n&\3&\5&\u0532\n&\5&\u0534\n&"+
		"\3&\7&\u0537\n&\f&\16&\u053a\13&\3&\3&\5&\u053e\n&\3&\5&\u0541\n&\3&\3"+
		"&\5&\u0545\n&\3&\5&\u0548\n&\5&\u054a\n&\3\'\3\'\3\'\3\'\7\'\u0550\n\'"+
		"\f\'\16\'\u0553\13\'\3\'\7\'\u0556\n\'\f\'\16\'\u0559\13\'\3(\3(\3(\3"+
		"(\3(\7(\u0560\n(\f(\16(\u0563\13(\3(\3(\3(\3(\3(\3(\3(\3(\3(\3(\7(\u056f"+
		"\n(\f(\16(\u0572\13(\3(\3(\5(\u0576\n(\3)\3)\3)\3)\7)\u057c\n)\f)\16)"+
		"\u057f\13)\5)\u0581\n)\3)\3)\5)\u0585\n)\3*\3*\3*\5*\u058a\n*\3*\3*\3"+
		"*\3*\3*\7*\u0591\n*\f*\16*\u0594\13*\5*\u0596\n*\3*\3*\3*\5*\u059b\n*"+
		"\3*\3*\3*\7*\u05a0\n*\f*\16*\u05a3\13*\5*\u05a5\n*\3+\3+\3,\3,\7,\u05ab"+
		"\n,\f,\16,\u05ae\13,\3-\3-\3-\3-\5-\u05b4\n-\3-\3-\3-\3-\3-\5-\u05bb\n"+
		"-\3.\5.\u05be\n.\3.\3.\3.\5.\u05c3\n.\3.\3.\3.\3.\5.\u05c9\n.\3.\3.\5"+
		".\u05cd\n.\3.\5.\u05d0\n.\3.\5.\u05d3\n.\3/\3/\3/\3/\3/\3/\3/\7/\u05dc"+
		"\n/\f/\16/\u05df\13/\3/\3/\5/\u05e3\n/\3\60\3\60\3\60\3\60\3\60\3\60\3"+
		"\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\3\60\5\60\u05f8"+
		"\n\60\5\60\u05fa\n\60\5\60\u05fc\n\60\3\60\3\60\3\61\3\61\3\61\3\61\3"+
		"\62\3\62\3\62\7\62\u0607\n\62\f\62\16\62\u060a\13\62\3\63\3\63\3\63\3"+
		"\63\7\63\u0610\n\63\f\63\16\63\u0613\13\63\3\63\3\63\3\64\3\64\5\64\u0619"+
		"\n\64\3\65\3\65\3\65\3\65\7\65\u061f\n\65\f\65\16\65\u0622\13\65\3\65"+
		"\3\65\3\66\3\66\3\66\5\66\u0629\n\66\3\67\3\67\5\67\u062d\n\67\3\67\5"+
		"\67\u0630\n\67\3\67\5\67\u0633\n\67\3\67\3\67\3\67\3\67\5\67\u0639\n\67"+
		"\3\67\5\67\u063c\n\67\3\67\5\67\u063f\n\67\3\67\3\67\3\67\3\67\5\67\u0645"+
		"\n\67\3\67\5\67\u0648\n\67\3\67\5\67\u064b\n\67\3\67\3\67\3\67\3\67\3"+
		"\67\3\67\7\67\u0653\n\67\f\67\16\67\u0656\13\67\5\67\u0658\n\67\3\67\3"+
		"\67\5\67\u065c\n\67\38\38\38\38\78\u0662\n8\f8\168\u0665\138\38\58\u0668"+
		"\n8\38\38\58\u066c\n8\58\u066e\n8\39\39\39\39\39\39\39\59\u0677\n9\39"+
		"\39\39\39\39\39\39\39\39\39\59\u0683\n9\59\u0685\n9\39\39\39\39\39\59"+
		"\u068c\n9\39\39\39\39\39\59\u0693\n9\39\39\39\39\59\u0699\n9\39\39\39"+
		"\39\59\u069f\n9\59\u06a1\n9\3:\3:\3:\5:\u06a6\n:\3:\3:\3;\3;\5;\u06ac"+
		"\n;\3;\3;\5;\u06b0\n;\5;\u06b2\n;\3<\3<\3<\7<\u06b7\n<\f<\16<\u06ba\13"+
		"<\3=\3=\3>\3>\3>\3>\3>\3>\3>\3>\3>\5>\u06c7\n>\3>\3>\3>\3>\3>\3>\7>\u06cf"+
		"\n>\f>\16>\u06d2\13>\3?\3?\5?\u06d6\n?\3@\5@\u06d9\n@\3@\3@\3@\3@\3@\3"+
		"@\5@\u06e1\n@\3@\3@\3@\3@\3@\7@\u06e8\n@\f@\16@\u06eb\13@\3@\3@\3@\5@"+
		"\u06f0\n@\3@\3@\3@\3@\3@\3@\5@\u06f8\n@\3@\3@\3@\3@\5@\u06fe\n@\3@\5@"+
		"\u0701\n@\3A\3A\3A\3A\5A\u0707\nA\3A\3A\3A\3A\3A\3A\3A\3A\3A\3A\3A\3A"+
		"\3A\3A\3A\3A\3A\3A\3A\3A\3A\3A\7A\u071f\nA\fA\16A\u0722\13A\3B\3B\3B\3"+
		"B\3B\6B\u0729\nB\rB\16B\u072a\3B\3B\5B\u072f\nB\3B\3B\3B\3B\6B\u0735\n"+
		"B\rB\16B\u0736\3B\3B\5B\u073b\nB\3B\3B\3B\3B\3B\3B\3B\3B\3B\3B\3B\3B\3"+
		"B\3B\3B\3B\3B\3B\3B\6B\u0750\nB\rB\16B\u0751\3B\3B\3B\3B\3B\3B\3B\3B\3"+
		"B\5B\u075d\nB\3B\3B\3B\7B\u0762\nB\fB\16B\u0765\13B\5B\u0767\nB\3B\3B"+
		"\3B\5B\u076c\nB\3B\3B\3B\3B\3B\5B\u0773\nB\3B\3B\3B\3B\3B\3B\3B\3B\7B"+
		"\u077d\nB\fB\16B\u0780\13B\3C\3C\3C\3C\3C\3C\3C\3C\6C\u078a\nC\rC\16C"+
		"\u078b\5C\u078e\nC\3D\3D\3E\3E\3F\3F\3G\3G\3H\3H\7H\u079a\nH\fH\16H\u079d"+
		"\13H\3I\3I\3I\3I\5I\u07a3\nI\3J\5J\u07a6\nJ\3J\3J\5J\u07aa\nJ\3K\3K\3"+
		"K\3K\3K\3K\3K\3K\3K\3K\3K\3K\3K\3K\3K\5K\u07bb\nK\3K\3K\5K\u07bf\nK\3"+
		"K\3K\3K\3K\3K\7K\u07c6\nK\fK\16K\u07c9\13K\3K\5K\u07cc\nK\5K\u07ce\nK"+
		"\3L\3L\3L\7L\u07d3\nL\fL\16L\u07d6\13L\3M\3M\3M\3M\5M\u07dc\nM\3N\3N\3"+
		"N\7N\u07e1\nN\fN\16N\u07e4\13N\3O\3O\3O\3O\3O\5O\u07eb\nO\3P\3P\3P\3P"+
		"\3P\3Q\3Q\3Q\3Q\7Q\u07f6\nQ\fQ\16Q\u07f9\13Q\3R\3R\3R\3R\3S\3S\3S\3S\3"+
		"S\3S\3S\7S\u0806\nS\fS\16S\u0809\13S\3S\3S\3S\3S\3S\7S\u0810\nS\fS\16"+
		"S\u0813\13S\5S\u0815\nS\3S\3S\3S\3S\3S\7S\u081c\nS\fS\16S\u081f\13S\5"+
		"S\u0821\nS\5S\u0823\nS\3S\5S\u0826\nS\3S\5S\u0829\nS\3T\3T\3T\3T\3T\3"+
		"T\3T\3T\3T\3T\3T\3T\3T\3T\3T\3T\5T\u083b\nT\3U\3U\3U\3U\3U\3U\3U\5U\u0844"+
		"\nU\3V\3V\3V\7V\u0849\nV\fV\16V\u084c\13V\3W\3W\3W\3W\3W\3W\3W\3W\3W\3"+
		"W\3W\3W\3W\3W\3W\5W\u085d\nW\3X\3X\3X\5X\u0862\nX\3Y\3Y\3Z\5Z\u0867\n"+
		"Z\3Z\3Z\5Z\u086b\nZ\3Z\3Z\5Z\u086f\nZ\3Z\3Z\5Z\u0873\nZ\3Z\3Z\5Z\u0877"+
		"\nZ\3Z\3Z\5Z\u087b\nZ\3Z\3Z\5Z\u087f\nZ\3Z\5Z\u0882\nZ\3[\3[\3[\7\u02a2"+
		"\u02d9\u02e1\u02e8\u02f0\6Dz\u0080\u0082\\\2\4\6\b\n\f\16\20\22\24\26"+
		"\30\32\34\36 \"$&(*,.\60\62\64\668:<>@BDFHJLNPRTVXZ\\^`bdfhjlnprtvxz|"+
		"~\u0080\u0082\u0084\u0086\u0088\u008a\u008c\u008e\u0090\u0092\u0094\u0096"+
		"\u0098\u009a\u009c\u009e\u00a0\u00a2\u00a4\u00a6\u00a8\u00aa\u00ac\u00ae"+
		"\u00b0\u00b2\u00b4\2\33\3\2\u00bc\u00bd\3\2LM\5\2UV\u00a2\u00a2\u00a8"+
		"\u00a8\4\2\13\13\35\35\4\2**RR\4\2\u00a2\u00a2\u00a8\u00a8\4\2\f\f\u00c9"+
		"\u00c9\3\2`c\3\2)*\3\2FG\3\2\16\17\3\2\u00eb\u00ec\3\2\"#\4\2~\177\u0084"+
		"\u0084\3\2\u0080\u0083\3\2~\177\3\2\u00e4\u00e5\3\2v}\3\2~\u0088\3\2\33"+
		"\36\3\2&\'\4\2??\u008f\u008f\4\2\27\27\u008d\u008d\3\2CD\t\2\n\61\64\64"+
		"<_du\u0083\u0083\u0089\u00e0\u00e2\u00e5\u09fb\2\u00b6\3\2\2\2\4\u00b9"+
		"\3\2\2\2\6\u00bc\3\2\2\2\b\u00bf\3\2\2\2\n\u02f3\3\2\2\2\f\u03b2\3\2\2"+
		"\2\16\u03b4\3\2\2\2\20\u03c3\3\2\2\2\22\u03cf\3\2\2\2\24\u03dc\3\2\2\2"+
		"\26\u03e0\3\2\2\2\30\u03f9\3\2\2\2\32\u03fb\3\2\2\2\34\u03ff\3\2\2\2\36"+
		"\u040b\3\2\2\2 \u0415\3\2\2\2\"\u0417\3\2\2\2$\u0422\3\2\2\2&\u042b\3"+
		"\2\2\2(\u0433\3\2\2\2*\u0436\3\2\2\2,\u0441\3\2\2\2.\u0451\3\2\2\2\60"+
		"\u0457\3\2\2\2\62\u0459\3\2\2\2\64\u0464\3\2\2\2\66\u0475\3\2\2\28\u047c"+
		"\3\2\2\2:\u047e\3\2\2\2<\u0484\3\2\2\2>\u0493\3\2\2\2@\u049f\3\2\2\2B"+
		"\u04cd\3\2\2\2D\u04d2\3\2\2\2F\u04e8\3\2\2\2H\u04ea\3\2\2\2J\u0549\3\2"+
		"\2\2L\u054b\3\2\2\2N\u055a\3\2\2\2P\u0584\3\2\2\2R\u0586\3\2\2\2T\u05a6"+
		"\3\2\2\2V\u05a8\3\2\2\2X\u05ba\3\2\2\2Z\u05d2\3\2\2\2\\\u05e2\3\2\2\2"+
		"^\u05e4\3\2\2\2`\u05ff\3\2\2\2b\u0603\3\2\2\2d\u060b\3\2\2\2f\u0616\3"+
		"\2\2\2h\u061a\3\2\2\2j\u0625\3\2\2\2l\u065b\3\2\2\2n\u065d\3\2\2\2p\u06a0"+
		"\3\2\2\2r\u06a5\3\2\2\2t\u06a9\3\2\2\2v\u06b3\3\2\2\2x\u06bb\3\2\2\2z"+
		"\u06c6\3\2\2\2|\u06d3\3\2\2\2~\u0700\3\2\2\2\u0080\u0706\3\2\2\2\u0082"+
		"\u0772\3\2\2\2\u0084\u078d\3\2\2\2\u0086\u078f\3\2\2\2\u0088\u0791\3\2"+
		"\2\2\u008a\u0793\3\2\2\2\u008c\u0795\3\2\2\2\u008e\u0797\3\2\2\2\u0090"+
		"\u079e\3\2\2\2\u0092\u07a9\3\2\2\2\u0094\u07cd\3\2\2\2\u0096\u07cf\3\2"+
		"\2\2\u0098\u07d7\3\2\2\2\u009a\u07dd\3\2\2\2\u009c\u07e5\3\2\2\2\u009e"+
		"\u07ec\3\2\2\2\u00a0\u07f1\3\2\2\2\u00a2\u07fa\3\2\2\2\u00a4\u0828\3\2"+
		"\2\2\u00a6\u083a\3\2\2\2\u00a8\u0843\3\2\2\2\u00aa\u0845\3\2\2\2\u00ac"+
		"\u085c\3\2\2\2\u00ae\u0861\3\2\2\2\u00b0\u0863\3\2\2\2\u00b2\u0881\3\2"+
		"\2\2\u00b4\u0883\3\2\2\2\u00b6\u00b7\5\n\6\2\u00b7\u00b8\7\2\2\3\u00b8"+
		"\3\3\2\2\2\u00b9\u00ba\5t;\2\u00ba\u00bb\7\2\2\3\u00bb\5\3\2\2\2\u00bc"+
		"\u00bd\5r:\2\u00bd\u00be\7\2\2\3\u00be\7\3\2\2\2\u00bf\u00c0\5\u0094K"+
		"\2\u00c0\u00c1\7\2\2\3\u00c1\t\3\2\2\2\u00c2\u02f4\5\26\f\2\u00c3\u00c4"+
		"\7\\\2\2\u00c4\u02f4\5\u00acW\2\u00c5\u00c6\7K\2\2\u00c6\u00ca\7\u00c3"+
		"\2\2\u00c7\u00c8\7u\2\2\u00c8\u00c9\7\36\2\2\u00c9\u00cb\7 \2\2\u00ca"+
		"\u00c7\3\2\2\2\u00ca\u00cb\3\2\2\2\u00cb\u00cc\3\2\2\2\u00cc\u00cf\5\u00ac"+
		"W\2\u00cd\u00ce\7l\2\2\u00ce\u00d0\7\u00e6\2\2\u00cf\u00cd\3\2\2\2\u00cf"+
		"\u00d0\3\2\2\2\u00d0\u00d2\3\2\2\2\u00d1\u00d3\5\24\13\2\u00d2\u00d1\3"+
		"\2\2\2\u00d2\u00d3\3\2\2\2\u00d3\u00d7\3\2\2\2\u00d4\u00d5\7I\2\2\u00d5"+
		"\u00d6\7\u00ae\2\2\u00d6\u00d8\5*\26\2\u00d7\u00d4\3\2\2\2\u00d7\u00d8"+
		"\3\2\2\2\u00d8\u02f4\3\2\2\2\u00d9\u00da\7g\2\2\u00da\u00db\7\u00c3\2"+
		"\2\u00db\u00dc\5\u00acW\2\u00dc\u00dd\7m\2\2\u00dd\u00de\7\u00ae\2\2\u00de"+
		"\u00df\5*\26\2\u00df\u02f4\3\2\2\2\u00e0\u00e1\7_\2\2\u00e1\u00e4\7\u00c3"+
		"\2\2\u00e2\u00e3\7u\2\2\u00e3\u00e5\7 \2\2\u00e4\u00e2\3\2\2\2\u00e4\u00e5"+
		"\3\2\2\2\u00e5\u00e6\3\2\2\2\u00e6\u00e8\5\u00acW\2\u00e7\u00e9\t\2\2"+
		"\2\u00e8\u00e7\3\2\2\2\u00e8\u00e9\3\2\2\2\u00e9\u02f4\3\2\2\2\u00ea\u00ef"+
		"\5\16\b\2\u00eb\u00ec\7\3\2\2\u00ec\u00ed\5\u0096L\2\u00ed\u00ee\7\4\2"+
		"\2\u00ee\u00f0\3\2\2\2\u00ef\u00eb\3\2\2\2\u00ef\u00f0\3\2\2\2\u00f0\u00f1"+
		"\3\2\2\2\u00f1\u00f4\5(\25\2\u00f2\u00f3\7\u00ab\2\2\u00f3\u00f5\5*\26"+
		"\2\u00f4\u00f2\3\2\2\2\u00f4\u00f5\3\2\2\2\u00f5\u00f9\3\2\2\2\u00f6\u00f7"+
		"\7\u00cb\2\2\u00f7\u00f8\7\22\2\2\u00f8\u00fa\5`\61\2\u00f9\u00f6\3\2"+
		"\2\2\u00f9\u00fa\3\2\2\2\u00fa\u00fc\3\2\2\2\u00fb\u00fd\5\20\t\2\u00fc"+
		"\u00fb\3\2\2\2\u00fc\u00fd\3\2\2\2\u00fd\u0102\3\2\2\2\u00fe\u0100\7\r"+
		"\2\2\u00ff\u00fe\3\2\2\2\u00ff\u0100\3\2\2\2\u0100\u0101\3\2\2\2\u0101"+
		"\u0103\5\26\f\2\u0102\u00ff\3\2\2\2\u0102\u0103\3\2\2\2\u0103\u02f4\3"+
		"\2\2\2\u0104\u0109\5\16\b\2\u0105\u0106\7\3\2\2\u0106\u0107\5\u0096L\2"+
		"\u0107\u0108\7\4\2\2\u0108\u010a\3\2\2\2\u0109\u0105\3\2\2\2\u0109\u010a"+
		"\3\2\2\2\u010a\u010d\3\2\2\2\u010b\u010c\7l\2\2\u010c\u010e\7\u00e6\2"+
		"\2\u010d\u010b\3\2\2\2\u010d\u010e\3\2\2\2\u010e\u0115\3\2\2\2\u010f\u0110"+
		"\7\u00cb\2\2\u0110\u0111\7\22\2\2\u0111\u0112\7\3\2\2\u0112\u0113\5\u0096"+
		"L\2\u0113\u0114\7\4\2\2\u0114\u0116\3\2\2\2\u0115\u010f\3\2\2\2\u0115"+
		"\u0116\3\2\2\2\u0116\u0118\3\2\2\2\u0117\u0119\5\20\t\2\u0118\u0117\3"+
		"\2\2\2\u0118\u0119\3\2\2\2\u0119\u011b\3\2\2\2\u011a\u011c\5\22\n\2\u011b"+
		"\u011a\3\2\2\2\u011b\u011c\3\2\2\2\u011c\u011e\3\2\2\2\u011d\u011f\5p"+
		"9\2\u011e\u011d\3\2\2\2\u011e\u011f\3\2\2\2\u011f\u0121\3\2\2\2\u0120"+
		"\u0122\5\66\34\2\u0121\u0120\3\2\2\2\u0121\u0122\3\2\2\2\u0122\u0124\3"+
		"\2\2\2\u0123\u0125\5\24\13\2\u0124\u0123\3\2\2\2\u0124\u0125\3\2\2\2\u0125"+
		"\u0128\3\2\2\2\u0126\u0127\7\u00ad\2\2\u0127\u0129\5*\26\2\u0128\u0126"+
		"\3\2\2\2\u0128\u0129\3\2\2\2\u0129\u012e\3\2\2\2\u012a\u012c\7\r\2\2\u012b"+
		"\u012a\3\2\2\2\u012b\u012c\3\2\2\2\u012c\u012d\3\2\2\2\u012d\u012f\5\26"+
		"\f\2\u012e\u012b\3\2\2\2\u012e\u012f\3\2\2\2\u012f\u02f4\3\2\2\2\u0130"+
		"\u0131\7K\2\2\u0131\u0135\7L\2\2\u0132\u0133\7u\2\2\u0133\u0134\7\36\2"+
		"\2\u0134\u0136\7 \2\2\u0135\u0132\3\2\2\2\u0135\u0136\3\2\2\2\u0136\u0137"+
		"\3\2\2\2\u0137\u0138\5r:\2\u0138\u0139\7\"\2\2\u0139\u013a\5r:\2\u013a"+
		"\u02f4\3\2\2\2\u013b\u013c\7\u00c7\2\2\u013c\u013d\7L\2\2\u013d\u013f"+
		"\5r:\2\u013e\u0140\5\34\17\2\u013f\u013e\3\2\2\2\u013f\u0140\3\2\2\2\u0140"+
		"\u0141\3\2\2\2\u0141\u0142\7\u00c8\2\2\u0142\u0147\7\u00ca\2\2\u0143\u0148"+
		"\5\u00acW\2\u0144\u0145\7+\2\2\u0145\u0146\7Z\2\2\u0146\u0148\5b\62\2"+
		"\u0147\u0143\3\2\2\2\u0147\u0144\3\2\2\2\u0147\u0148\3\2\2\2\u0148\u02f4"+
		"\3\2\2\2\u0149\u014a\7g\2\2\u014a\u014b\t\3\2\2\u014b\u014c\5r:\2\u014c"+
		"\u014d\7h\2\2\u014d\u014e\7d\2\2\u014e\u014f\5r:\2\u014f\u02f4\3\2\2\2"+
		"\u0150\u0151\7g\2\2\u0151\u0152\t\3\2\2\u0152\u0153\5r:\2\u0153\u0154"+
		"\7m\2\2\u0154\u0155\7\u00ad\2\2\u0155\u0156\5*\26\2\u0156\u02f4\3\2\2"+
		"\2\u0157\u0158\7g\2\2\u0158\u0159\t\3\2\2\u0159\u015a\5r:\2\u015a\u015b"+
		"\7\u00ac\2\2\u015b\u015e\7\u00ad\2\2\u015c\u015d\7u\2\2\u015d\u015f\7"+
		" \2\2\u015e\u015c\3\2\2\2\u015e\u015f\3\2\2\2\u015f\u0160\3\2\2\2\u0160"+
		"\u0161\5*\26\2\u0161\u02f4\3\2\2\2\u0162\u0163\7g\2\2\u0163\u0164\7L\2"+
		"\2\u0164\u0166\5r:\2\u0165\u0167\5\34\17\2\u0166\u0165\3\2\2\2\u0166\u0167"+
		"\3\2\2\2\u0167\u0168\3\2\2\2\u0168\u0169\7m\2\2\u0169\u016a\7\u0094\2"+
		"\2\u016a\u016e\7\u00e6\2\2\u016b\u016c\7I\2\2\u016c\u016d\7\u0095\2\2"+
		"\u016d\u016f\5*\26\2\u016e\u016b\3\2\2\2\u016e\u016f\3\2\2\2\u016f\u02f4"+
		"\3\2\2\2\u0170\u0171\7g\2\2\u0171\u0172\7L\2\2\u0172\u0174\5r:\2\u0173"+
		"\u0175\5\34\17\2\u0174\u0173\3\2\2\2\u0174\u0175\3\2\2\2\u0175\u0176\3"+
		"\2\2\2\u0176\u0177\7m\2\2\u0177\u0178\7\u0095\2\2\u0178\u0179\5*\26\2"+
		"\u0179\u02f4\3\2\2\2\u017a\u017b\7g\2\2\u017b\u017c\7L\2\2\u017c\u017d"+
		"\5r:\2\u017d\u0181\7\f\2\2\u017e\u017f\7u\2\2\u017f\u0180\7\36\2\2\u0180"+
		"\u0182\7 \2\2\u0181\u017e\3\2\2\2\u0181\u0182\3\2\2\2\u0182\u0184\3\2"+
		"\2\2\u0183\u0185\5\32\16\2\u0184\u0183\3\2\2\2\u0185\u0186\3\2\2\2\u0186"+
		"\u0184\3\2\2\2\u0186\u0187\3\2\2\2\u0187\u02f4\3\2\2\2\u0188\u0189\7g"+
		"\2\2\u0189\u018a\7M\2\2\u018a\u018b\5r:\2\u018b\u018f\7\f\2\2\u018c\u018d"+
		"\7u\2\2\u018d\u018e\7\36\2\2\u018e\u0190\7 \2\2\u018f\u018c\3\2\2\2\u018f"+
		"\u0190\3\2\2\2\u0190\u0192\3\2\2\2\u0191\u0193\5\34\17\2\u0192\u0191\3"+
		"\2\2\2\u0193\u0194\3\2\2\2\u0194\u0192\3\2\2\2\u0194\u0195\3\2\2\2\u0195"+
		"\u02f4\3\2\2\2\u0196\u0197\7g\2\2\u0197\u0198\7L\2\2\u0198\u0199\5r:\2"+
		"\u0199\u019a\5\34\17\2\u019a\u019b\7h\2\2\u019b\u019c\7d\2\2\u019c\u019d"+
		"\5\34\17\2\u019d\u02f4\3\2\2\2\u019e\u019f\7g\2\2\u019f\u01a0\7L\2\2\u01a0"+
		"\u01a1\5r:\2\u01a1\u01a4\7_\2\2\u01a2\u01a3\7u\2\2\u01a3\u01a5\7 \2\2"+
		"\u01a4\u01a2\3\2\2\2\u01a4\u01a5\3\2\2\2\u01a5\u01a6\3\2\2\2\u01a6\u01ab"+
		"\5\34\17\2\u01a7\u01a8\7\5\2\2\u01a8\u01aa\5\34\17\2\u01a9\u01a7\3\2\2"+
		"\2\u01aa\u01ad\3\2\2\2\u01ab\u01a9\3\2\2\2\u01ab\u01ac\3\2\2\2\u01ac\u01af"+
		"\3\2\2\2\u01ad\u01ab\3\2\2\2\u01ae\u01b0\7\u00c0\2\2\u01af\u01ae\3\2\2"+
		"\2\u01af\u01b0\3\2\2\2\u01b0\u02f4\3\2\2\2\u01b1\u01b2\7g\2\2\u01b2\u01b3"+
		"\7M\2\2\u01b3\u01b4\5r:\2\u01b4\u01b7\7_\2\2\u01b5\u01b6\7u\2\2\u01b6"+
		"\u01b8\7 \2\2\u01b7\u01b5\3\2\2\2\u01b7\u01b8\3\2\2\2\u01b8\u01b9\3\2"+
		"\2\2\u01b9\u01be\5\34\17\2\u01ba\u01bb\7\5\2\2\u01bb\u01bd\5\34\17\2\u01bc"+
		"\u01ba\3\2\2\2\u01bd\u01c0\3\2\2\2\u01be\u01bc\3\2\2\2\u01be\u01bf\3\2"+
		"\2\2\u01bf\u02f4\3\2\2\2\u01c0\u01be\3\2\2\2\u01c1\u01c2\7g\2\2\u01c2"+
		"\u01c3\7L\2\2\u01c3\u01c5\5r:\2\u01c4\u01c6\5\34\17\2\u01c5\u01c4\3\2"+
		"\2\2\u01c5\u01c6\3\2\2\2\u01c6\u01c7\3\2\2\2\u01c7\u01c8\7m\2\2\u01c8"+
		"\u01c9\5\24\13\2\u01c9\u02f4\3\2\2\2\u01ca\u01cb\7g\2\2\u01cb\u01cc\7"+
		"L\2\2\u01cc\u01cd\5r:\2\u01cd\u01ce\7\u00d4\2\2\u01ce\u01cf\7]\2\2\u01cf"+
		"\u02f4\3\2\2\2\u01d0\u01d1\7_\2\2\u01d1\u01d4\7L\2\2\u01d2\u01d3\7u\2"+
		"\2\u01d3\u01d5\7 \2\2\u01d4\u01d2\3\2\2\2\u01d4\u01d5\3\2\2\2\u01d5\u01d6"+
		"\3\2\2\2\u01d6\u01d8\5r:\2\u01d7\u01d9\7\u00c0\2\2\u01d8\u01d7\3\2\2\2"+
		"\u01d8\u01d9\3\2\2\2\u01d9\u02f4\3\2\2\2\u01da\u01db\7_\2\2\u01db\u01de"+
		"\7M\2\2\u01dc\u01dd\7u\2\2\u01dd\u01df\7 \2\2\u01de\u01dc\3\2\2\2\u01de"+
		"\u01df\3\2\2\2\u01df\u01e0\3\2\2\2\u01e0\u02f4\5r:\2\u01e1\u01e4\7K\2"+
		"\2\u01e2\u01e3\7\33\2\2\u01e3\u01e5\7N\2\2\u01e4\u01e2\3\2\2\2\u01e4\u01e5"+
		"\3\2\2\2\u01e5\u01ea\3\2\2\2\u01e6\u01e8\7\u00a9\2\2\u01e7\u01e6\3\2\2"+
		"\2\u01e7\u01e8\3\2\2\2\u01e8\u01e9\3\2\2\2\u01e9\u01eb\7\u00aa\2\2\u01ea"+
		"\u01e7\3\2\2\2\u01ea\u01eb\3\2\2\2\u01eb\u01ec\3\2\2\2\u01ec\u01f0\7M"+
		"\2\2\u01ed\u01ee\7u\2\2\u01ee\u01ef\7\36\2\2\u01ef\u01f1\7 \2\2\u01f0"+
		"\u01ed\3\2\2\2\u01f0\u01f1\3\2\2\2\u01f1\u01f2\3\2\2\2\u01f2\u01f4\5r"+
		":\2\u01f3\u01f5\5h\65\2\u01f4\u01f3\3\2\2\2\u01f4\u01f5\3\2\2\2\u01f5"+
		"\u01f8\3\2\2\2\u01f6\u01f7\7l\2\2\u01f7\u01f9\7\u00e6\2\2\u01f8\u01f6"+
		"\3\2\2\2\u01f8\u01f9\3\2\2\2\u01f9\u01fd\3\2\2\2\u01fa\u01fb\7\u00cb\2"+
		"\2\u01fb\u01fc\7;\2\2\u01fc\u01fe\5`\61\2\u01fd\u01fa\3\2\2\2\u01fd\u01fe"+
		"\3\2\2\2\u01fe\u0201\3\2\2\2\u01ff\u0200\7\u00ad\2\2\u0200\u0202\5*\26"+
		"\2\u0201\u01ff\3\2\2\2\u0201\u0202\3\2\2\2\u0202\u0203\3\2\2\2\u0203\u0204"+
		"\7\r\2\2\u0204\u0205\5\26\f\2\u0205\u02f4\3\2\2\2\u0206\u0209\7K\2\2\u0207"+
		"\u0208\7\33\2\2\u0208\u020a\7N\2\2\u0209\u0207\3\2\2\2\u0209\u020a\3\2"+
		"\2\2\u020a\u020c\3\2\2\2\u020b\u020d\7\u00a9\2\2\u020c\u020b\3\2\2\2\u020c"+
		"\u020d\3\2\2\2\u020d\u020e\3\2\2\2\u020e\u020f\7\u00aa\2\2\u020f\u0210"+
		"\7M\2\2\u0210\u0215\5r:\2\u0211\u0212\7\3\2\2\u0212\u0213\5\u0096L\2\u0213"+
		"\u0214\7\4\2\2\u0214\u0216\3\2\2\2\u0215\u0211\3\2\2\2\u0215\u0216\3\2"+
		"\2\2\u0216\u0217\3\2\2\2\u0217\u021a\5(\25\2\u0218\u0219\7\u00ab\2\2\u0219"+
		"\u021b\5*\26\2\u021a\u0218\3\2\2\2\u021a\u021b\3\2\2\2\u021b\u02f4\3\2"+
		"\2\2\u021c\u021d\7g\2\2\u021d\u021e\7M\2\2\u021e\u0220\5r:\2\u021f\u0221"+
		"\7\r\2\2\u0220\u021f\3\2\2\2\u0220\u0221\3\2\2\2\u0221\u0222\3\2\2\2\u0222"+
		"\u0223\5\26\f\2\u0223\u02f4\3\2\2\2\u0224\u0226\7K\2\2\u0225\u0227\7\u00aa"+
		"\2\2\u0226\u0225\3\2\2\2\u0226\u0227\3\2\2\2\u0227\u0228\3\2\2\2\u0228"+
		"\u0229\7\u00a1\2\2\u0229\u022a\5\u00aaV\2\u022a\u022b\7\r\2\2\u022b\u0235"+
		"\7\u00e6\2\2\u022c\u022d\7\u0093\2\2\u022d\u0232\5<\37\2\u022e\u022f\7"+
		"\5\2\2\u022f\u0231\5<\37\2\u0230\u022e\3\2\2\2\u0231\u0234\3\2\2\2\u0232"+
		"\u0230\3\2\2\2\u0232\u0233\3\2\2\2\u0233\u0236\3\2\2\2\u0234\u0232\3\2"+
		"\2\2\u0235\u022c\3\2\2\2\u0235\u0236\3\2\2\2\u0236\u02f4\3\2\2\2\u0237"+
		"\u0239\7_\2\2\u0238\u023a\7\u00aa\2\2\u0239\u0238\3\2\2\2\u0239\u023a"+
		"\3\2\2\2\u023a\u023b\3\2\2\2\u023b\u023e\7\u00a1\2\2\u023c\u023d\7u\2"+
		"\2\u023d\u023f\7 \2\2\u023e\u023c\3\2\2\2\u023e\u023f\3\2\2\2\u023f\u0240"+
		"\3\2\2\2\u0240\u02f4\5\u00aaV\2\u0241\u0243\7S\2\2\u0242\u0244\t\4\2\2"+
		"\u0243\u0242\3\2\2\2\u0243\u0244\3\2\2\2\u0244\u0245\3\2\2\2\u0245\u02f4"+
		"\5\n\6\2\u0246\u0247\7X\2\2\u0247\u024a\7Y\2\2\u0248\u0249\t\5\2\2\u0249"+
		"\u024b\5\u00acW\2\u024a\u0248\3\2\2\2\u024a\u024b\3\2\2\2\u024b\u0250"+
		"\3\2\2\2\u024c\u024e\7\"\2\2\u024d\u024c\3\2\2\2\u024d\u024e\3\2\2\2\u024e"+
		"\u024f\3\2\2\2\u024f\u0251\7\u00e6\2\2\u0250\u024d\3\2\2\2\u0250\u0251"+
		"\3\2\2\2\u0251\u02f4\3\2\2\2\u0252\u0253\7X\2\2\u0253\u0256\7\u00c4\2"+
		"\2\u0254\u0255\7\"\2\2\u0255\u0257\7\u00e6\2\2\u0256\u0254\3\2\2\2\u0256"+
		"\u0257\3\2\2\2\u0257\u02f4\3\2\2\2\u0258\u0259\7X\2\2\u0259\u025a\7\u00ad"+
		"\2\2\u025a\u025f\5r:\2\u025b\u025c\7\3\2\2\u025c\u025d\5.\30\2\u025d\u025e"+
		"\7\4\2\2\u025e\u0260\3\2\2\2\u025f\u025b\3\2\2\2\u025f\u0260\3\2\2\2\u0260"+
		"\u02f4\3\2\2\2\u0261\u0262\7X\2\2\u0262\u0263\7Z\2\2\u0263\u0264\t\5\2"+
		"\2\u0264\u0267\5r:\2\u0265\u0266\t\5\2\2\u0266\u0268\5\u00acW\2\u0267"+
		"\u0265\3\2\2\2\u0267\u0268\3\2\2\2\u0268\u02f4\3\2\2\2\u0269\u026a\7X"+
		"\2\2\u026a\u026b\7]\2\2\u026b\u026d\5r:\2\u026c\u026e\5\34\17\2\u026d"+
		"\u026c\3\2\2\2\u026d\u026e\3\2\2\2\u026e\u02f4\3\2\2\2\u026f\u0271\7X"+
		"\2\2\u0270\u0272\5\u00acW\2\u0271\u0270\3\2\2\2\u0271\u0272\3\2\2\2\u0272"+
		"\u0273\3\2\2\2\u0273\u027b\7^\2\2\u0274\u0276\7\"\2\2\u0275\u0274\3\2"+
		"\2\2\u0275\u0276\3\2\2\2\u0276\u0279\3\2\2\2\u0277\u027a\5\u00aaV\2\u0278"+
		"\u027a\7\u00e6\2\2\u0279\u0277\3\2\2\2\u0279\u0278\3\2\2\2\u027a\u027c"+
		"\3\2\2\2\u027b\u0275\3\2\2\2\u027b\u027c\3\2\2\2\u027c\u02f4\3\2\2\2\u027d"+
		"\u027e\7X\2\2\u027e\u027f\7K\2\2\u027f\u0280\7L\2\2\u0280\u02f4\5r:\2"+
		"\u0281\u0282\t\6\2\2\u0282\u0284\7\u00a1\2\2\u0283\u0285\7\u00a2\2\2\u0284"+
		"\u0283\3\2\2\2\u0284\u0285\3\2\2\2\u0285\u0286\3\2\2\2\u0286\u02f4\5 "+
		"\21\2\u0287\u0288\t\6\2\2\u0288\u028a\7\u00c3\2\2\u0289\u028b\7\u00a2"+
		"\2\2\u028a\u0289\3\2\2\2\u028a\u028b\3\2\2\2\u028b\u028c\3\2\2\2\u028c"+
		"\u02f4\5\u00acW\2\u028d\u028f\t\6\2\2\u028e\u0290\7L\2\2\u028f\u028e\3"+
		"\2\2\2\u028f\u0290\3\2\2\2\u0290\u0292\3\2\2\2\u0291\u0293\t\7\2\2\u0292"+
		"\u0291\3\2\2\2\u0292\u0293\3\2\2\2\u0293\u0294\3\2\2\2\u0294\u0296\5r"+
		":\2\u0295\u0297\5\34\17\2\u0296\u0295\3\2\2\2\u0296\u0297\3\2\2\2\u0297"+
		"\u0299\3\2\2\2\u0298\u029a\5\"\22\2\u0299\u0298\3\2\2\2\u0299\u029a\3"+
		"\2\2\2\u029a\u02f4\3\2\2\2\u029b\u029c\7\u00a3\2\2\u029c\u029d\7L\2\2"+
		"\u029d\u02f4\5r:\2\u029e\u02a2\7\u00a3\2\2\u029f\u02a1\13\2\2\2\u02a0"+
		"\u029f\3\2\2\2\u02a1\u02a4\3\2\2\2\u02a2\u02a3\3\2\2\2\u02a2\u02a0\3\2"+
		"\2\2\u02a3\u02f4\3\2\2\2\u02a4\u02a2\3\2\2\2\u02a5\u02a7\7\u00a5\2\2\u02a6"+
		"\u02a8\7\u00a7\2\2\u02a7\u02a6\3\2\2\2\u02a7\u02a8\3\2\2\2\u02a8\u02a9"+
		"\3\2\2\2\u02a9\u02aa\7L\2\2\u02aa\u02af\5r:\2\u02ab\u02ad\7\r\2\2\u02ac"+
		"\u02ab\3\2\2\2\u02ac\u02ad\3\2\2\2\u02ad\u02ae\3\2\2\2\u02ae\u02b0\5\26"+
		"\f\2\u02af\u02ac\3\2\2\2\u02af\u02b0\3\2\2\2\u02b0\u02f4\3\2\2\2\u02b1"+
		"\u02b2\7\u00a6\2\2\u02b2\u02b5\7L\2\2\u02b3\u02b4\7u\2\2\u02b4\u02b6\7"+
		" \2\2\u02b5\u02b3\3\2\2\2\u02b5\u02b6\3\2\2\2\u02b6\u02b7\3\2\2\2\u02b7"+
		"\u02f4\5r:\2\u02b8\u02b9\7\u00a4\2\2\u02b9\u02f4\7\u00a5\2\2\u02ba\u02bb"+
		"\7\u00d7\2\2\u02bb\u02bd\7o\2\2\u02bc\u02be\7\u00e2\2\2\u02bd\u02bc\3"+
		"\2\2\2\u02bd\u02be\3\2\2\2\u02be\u02bf\3\2\2\2\u02bf\u02c0\7\u00e3\2\2"+
		"\u02c0\u02c2\7\u00e6\2\2\u02c1\u02c3\7\u0090\2\2\u02c2\u02c1\3\2\2\2\u02c2"+
		"\u02c3\3\2\2\2\u02c3\u02c4\3\2\2\2\u02c4\u02c5\7Q\2\2\u02c5\u02c6\7L\2"+
		"\2\u02c6\u02c8\5r:\2\u02c7\u02c9\5\34\17\2\u02c8\u02c7\3\2\2\2\u02c8\u02c9"+
		"\3\2\2\2\u02c9\u02f4\3\2\2\2\u02ca\u02cb\7\u00c6\2\2\u02cb\u02cc\7L\2"+
		"\2\u02cc\u02ce\5r:\2\u02cd\u02cf\5\34\17\2\u02ce\u02cd\3\2\2\2\u02ce\u02cf"+
		"\3\2\2\2\u02cf\u02f4\3\2\2\2\u02d0\u02d1\7\u00d2\2\2\u02d1\u02d2\7\u00d3"+
		"\2\2\u02d2\u02d3\7L\2\2\u02d3\u02f4\5r:\2\u02d4\u02d5\t\b\2\2\u02d5\u02d9"+
		"\5\u00acW\2\u02d6\u02d8\13\2\2\2\u02d7\u02d6\3\2\2\2\u02d8\u02db\3\2\2"+
		"\2\u02d9\u02da\3\2\2\2\u02d9\u02d7\3\2\2\2\u02da\u02f4\3\2\2\2\u02db\u02d9"+
		"\3\2\2\2\u02dc\u02dd\7m\2\2\u02dd\u02e1\7\u00d8\2\2\u02de\u02e0\13\2\2"+
		"\2\u02df\u02de\3\2\2\2\u02e0\u02e3\3\2\2\2\u02e1\u02e2\3\2\2\2\u02e1\u02df"+
		"\3\2\2\2\u02e2\u02f4\3\2\2\2\u02e3\u02e1\3\2\2\2\u02e4\u02e8\7m\2\2\u02e5"+
		"\u02e7\13\2\2\2\u02e6\u02e5\3\2\2\2\u02e7\u02ea\3\2\2\2\u02e8\u02e9\3"+
		"\2\2\2\u02e8\u02e6\3\2\2\2\u02e9\u02f4\3\2\2\2\u02ea\u02e8\3\2\2\2\u02eb"+
		"\u02f4\7n\2\2\u02ec\u02f0\5\f\7\2\u02ed\u02ef\13\2\2\2\u02ee\u02ed\3\2"+
		"\2\2\u02ef\u02f2\3\2\2\2\u02f0\u02f1\3\2\2\2\u02f0\u02ee\3\2\2\2\u02f1"+
		"\u02f4\3\2\2\2\u02f2\u02f0\3\2\2\2\u02f3\u00c2\3\2\2\2\u02f3\u00c3\3\2"+
		"\2\2\u02f3\u00c5\3\2\2\2\u02f3\u00d9\3\2\2\2\u02f3\u00e0\3\2\2\2\u02f3"+
		"\u00ea\3\2\2\2\u02f3\u0104\3\2\2\2\u02f3\u0130\3\2\2\2\u02f3\u013b\3\2"+
		"\2\2\u02f3\u0149\3\2\2\2\u02f3\u0150\3\2\2\2\u02f3\u0157\3\2\2\2\u02f3"+
		"\u0162\3\2\2\2\u02f3\u0170\3\2\2\2\u02f3\u017a\3\2\2\2\u02f3\u0188\3\2"+
		"\2\2\u02f3\u0196\3\2\2\2\u02f3\u019e\3\2\2\2\u02f3\u01b1\3\2\2\2\u02f3"+
		"\u01c1\3\2\2\2\u02f3\u01ca\3\2\2\2\u02f3\u01d0\3\2\2\2\u02f3\u01da\3\2"+
		"\2\2\u02f3\u01e1\3\2\2\2\u02f3\u0206\3\2\2\2\u02f3\u021c\3\2\2\2\u02f3"+
		"\u0224\3\2\2\2\u02f3\u0237\3\2\2\2\u02f3\u0241\3\2\2\2\u02f3\u0246\3\2"+
		"\2\2\u02f3\u0252\3\2\2\2\u02f3\u0258\3\2\2\2\u02f3\u0261\3\2\2\2\u02f3"+
		"\u0269\3\2\2\2\u02f3\u026f\3\2\2\2\u02f3\u027d\3\2\2\2\u02f3\u0281\3\2"+
		"\2\2\u02f3\u0287\3\2\2\2\u02f3\u028d\3\2\2\2\u02f3\u029b\3\2\2\2\u02f3"+
		"\u029e\3\2\2\2\u02f3\u02a5\3\2\2\2\u02f3\u02b1\3\2\2\2\u02f3\u02b8\3\2"+
		"\2\2\u02f3\u02ba\3\2\2\2\u02f3\u02ca\3\2\2\2\u02f3\u02d0\3\2\2\2\u02f3"+
		"\u02d4\3\2\2\2\u02f3\u02dc\3\2\2\2\u02f3\u02e4\3\2\2\2\u02f3\u02eb\3\2"+
		"\2\2\u02f3\u02ec\3\2\2\2\u02f4\13\3\2\2\2\u02f5\u02f6\7K\2\2\u02f6\u03b3"+
		"\7\u00d8\2\2\u02f7\u02f8\7_\2\2\u02f8\u03b3\7\u00d8\2\2\u02f9\u02fb\7"+
		"\u00cf\2\2\u02fa\u02fc\7\u00d8\2\2\u02fb\u02fa\3\2\2\2\u02fb\u02fc\3\2"+
		"\2\2\u02fc\u03b3\3\2\2\2\u02fd\u02ff\7\u00ce\2\2\u02fe\u0300\7\u00d8\2"+
		"\2\u02ff\u02fe\3\2\2\2\u02ff\u0300\3\2\2\2\u0300\u03b3\3\2\2\2\u0301\u0302"+
		"\7X\2\2\u0302\u03b3\7\u00cf\2\2\u0303\u0304\7X\2\2\u0304\u0306\7\u00d8"+
		"\2\2\u0305\u0307\7\u00cf\2\2\u0306\u0305\3\2\2\2\u0306\u0307\3\2\2\2\u0307"+
		"\u03b3\3\2\2\2\u0308\u0309\7X\2\2\u0309\u03b3\7\u00db\2\2\u030a\u030b"+
		"\7X\2\2\u030b\u03b3\7\u00d9\2\2\u030c\u030d\7X\2\2\u030d\u030e\7E\2\2"+
		"\u030e\u03b3\7\u00d9\2\2\u030f\u0310\7\u00d5\2\2\u0310\u03b3\7L\2\2\u0311"+
		"\u0312\7\u00d6\2\2\u0312\u03b3\7L\2\2\u0313\u0314\7X\2\2\u0314\u03b3\7"+
		"\u00da\2\2\u0315\u0316\7X\2\2\u0316\u0317\7K\2\2\u0317\u03b3\7L\2\2\u0318"+
		"\u0319\7X\2\2\u0319\u03b3\7\u00dc\2\2\u031a\u031b\7X\2\2\u031b\u03b3\7"+
		"\u00de\2\2\u031c\u031d\7X\2\2\u031d\u03b3\7\u00df\2\2\u031e\u031f\7K\2"+
		"\2\u031f\u03b3\7\u00dd\2\2\u0320\u0321\7_\2\2\u0321\u03b3\7\u00dd\2\2"+
		"\u0322\u0323\7g\2\2\u0323\u03b3\7\u00dd\2\2\u0324\u0325\7\u00d0\2\2\u0325"+
		"\u03b3\7L\2\2\u0326\u0327\7\u00d0\2\2\u0327\u03b3\7\u00c3\2\2\u0328\u0329"+
		"\7\u00d1\2\2\u0329\u03b3\7L\2\2\u032a\u032b\7\u00d1\2\2\u032b\u03b3\7"+
		"\u00c3\2\2\u032c\u032d\7K\2\2\u032d\u032e\7\u00aa\2\2\u032e\u03b3\7t\2"+
		"\2\u032f\u0330\7_\2\2\u0330\u0331\7\u00aa\2\2\u0331\u03b3\7t\2\2\u0332"+
		"\u0333\7g\2\2\u0333\u0334\7L\2\2\u0334\u0335\5r:\2\u0335\u0336\7\36\2"+
		"\2\u0336\u0337\7\u00be\2\2\u0337\u03b3\3\2\2\2\u0338\u0339\7g\2\2\u0339"+
		"\u033a\7L\2\2\u033a\u033b\5r:\2\u033b\u033c\7\u00be\2\2\u033c\u033d\7"+
		"\22\2\2\u033d\u03b3\3\2\2\2\u033e\u033f\7g\2\2\u033f\u0340\7L\2\2\u0340"+
		"\u0341\5r:\2\u0341\u0342\7\36\2\2\u0342\u0343\7\u00bf\2\2\u0343\u03b3"+
		"\3\2\2\2\u0344\u0345\7g\2\2\u0345\u0346\7L\2\2\u0346\u0347\5r:\2\u0347"+
		"\u0348\7\u00b0\2\2\u0348\u0349\7\22\2\2\u0349\u03b3\3\2\2\2\u034a\u034b"+
		"\7g\2\2\u034b\u034c\7L\2\2\u034c\u034d\5r:\2\u034d\u034e\7\36\2\2\u034e"+
		"\u034f\7\u00b0\2\2\u034f\u03b3\3\2\2\2\u0350\u0351\7g\2\2\u0351\u0352"+
		"\7L\2\2\u0352\u0353\5r:\2\u0353\u0354\7\36\2\2\u0354\u0355\7\u00b1\2\2"+
		"\u0355\u0356\7\r\2\2\u0356\u0357\7\u00b2\2\2\u0357\u03b3\3\2\2\2\u0358"+
		"\u0359\7g\2\2\u0359\u035a\7L\2\2\u035a\u035b\5r:\2\u035b\u035c\7m\2\2"+
		"\u035c\u035d\7\u00b0\2\2\u035d\u035e\7\u00b3\2\2\u035e\u03b3\3\2\2\2\u035f"+
		"\u0360\7g\2\2\u0360\u0361\7L\2\2\u0361\u0362\5r:\2\u0362\u0363\7\u00b4"+
		"\2\2\u0363\u0364\7?\2\2\u0364\u03b3\3\2\2\2\u0365\u0366\7g\2\2\u0366\u0367"+
		"\7L\2\2\u0367\u0368\5r:\2\u0368\u0369\7\u00b5\2\2\u0369\u036a\7?\2\2\u036a"+
		"\u03b3\3\2\2\2\u036b\u036c\7g\2\2\u036c\u036d\7L\2\2\u036d\u036e\5r:\2"+
		"\u036e\u036f\7\u00b6\2\2\u036f\u0370\7?\2\2\u0370\u03b3\3\2\2\2\u0371"+
		"\u0372\7g\2\2\u0372\u0373\7L\2\2\u0373\u0374\5r:\2\u0374\u0375\7\u00b8"+
		"\2\2\u0375\u03b3\3\2\2\2\u0376\u0377\7g\2\2\u0377\u0378\7L\2\2\u0378\u037a"+
		"\5r:\2\u0379\u037b\5\34\17\2\u037a\u0379\3\2\2\2\u037a\u037b\3\2\2\2\u037b"+
		"\u037c\3\2\2\2\u037c\u037d\7\u00b9\2\2\u037d\u03b3\3\2\2\2\u037e\u037f"+
		"\7g\2\2\u037f\u0380\7L\2\2\u0380\u0382\5r:\2\u0381\u0383\5\34\17\2\u0382"+
		"\u0381\3\2\2\2\u0382\u0383\3\2\2\2\u0383\u0384\3\2\2\2\u0384\u0385\7\u00ba"+
		"\2\2\u0385\u03b3\3\2\2\2\u0386\u0387\7g\2\2\u0387\u0388\7L\2\2\u0388\u038a"+
		"\5r:\2\u0389\u038b\5\34\17\2\u038a\u0389\3\2\2\2\u038a\u038b\3\2\2\2\u038b"+
		"\u038c\3\2\2\2\u038c\u038d\7m\2\2\u038d\u038e\7\u00b7\2\2\u038e\u03b3"+
		"\3\2\2\2\u038f\u0390\7g\2\2\u0390\u0391\7L\2\2\u0391\u0393\5r:\2\u0392"+
		"\u0394\5\34\17\2\u0393\u0392\3\2\2\2\u0393\u0394\3\2\2\2\u0394\u0395\3"+
		"\2\2\2\u0395\u0396\7\f\2\2\u0396\u0397\7Z\2\2\u0397\u03b3\3\2\2\2\u0398"+
		"\u0399\7g\2\2\u0399\u039a\7L\2\2\u039a\u039c\5r:\2\u039b\u039d\5\34\17"+
		"\2\u039c\u039b\3\2\2\2\u039c\u039d\3\2\2\2\u039d\u039e\3\2\2\2\u039e\u03a0"+
		"\7\u00bb\2\2\u039f\u03a1\7[\2\2\u03a0\u039f\3\2\2\2\u03a0\u03a1\3\2\2"+
		"\2\u03a1\u03b3\3\2\2\2\u03a2\u03a3\7g\2\2\u03a3\u03a4\7L\2\2\u03a4\u03a6"+
		"\5r:\2\u03a5\u03a7\5\34\17\2\u03a6\u03a5\3\2\2\2\u03a6\u03a7\3\2\2\2\u03a7"+
		"\u03a8\3\2\2\2\u03a8\u03a9\7N\2\2\u03a9\u03aa\7Z\2\2\u03aa\u03b3\3\2\2"+
		"\2\u03ab\u03ac\7p\2\2\u03ac\u03b3\7q\2\2\u03ad\u03b3\7r\2\2\u03ae\u03b3"+
		"\7s\2\2\u03af\u03b3\7\u00c5\2\2\u03b0\u03b1\7P\2\2\u03b1\u03b3\7\13\2"+
		"\2\u03b2\u02f5\3\2\2\2\u03b2\u02f7\3\2\2\2\u03b2\u02f9\3\2\2\2\u03b2\u02fd"+
		"\3\2\2\2\u03b2\u0301\3\2\2\2\u03b2\u0303\3\2\2\2\u03b2\u0308\3\2\2\2\u03b2"+
		"\u030a\3\2\2\2\u03b2\u030c\3\2\2\2\u03b2\u030f\3\2\2\2\u03b2\u0311\3\2"+
		"\2\2\u03b2\u0313\3\2\2\2\u03b2\u0315\3\2\2\2\u03b2\u0318\3\2\2\2\u03b2"+
		"\u031a\3\2\2\2\u03b2\u031c\3\2\2\2\u03b2\u031e\3\2\2\2\u03b2\u0320\3\2"+
		"\2\2\u03b2\u0322\3\2\2\2\u03b2\u0324\3\2\2\2\u03b2\u0326\3\2\2\2\u03b2"+
		"\u0328\3\2\2\2\u03b2\u032a\3\2\2\2\u03b2\u032c\3\2\2\2\u03b2\u032f\3\2"+
		"\2\2\u03b2\u0332\3\2\2\2\u03b2\u0338\3\2\2\2\u03b2\u033e\3\2\2\2\u03b2"+
		"\u0344\3\2\2\2\u03b2\u034a\3\2\2\2\u03b2\u0350\3\2\2\2\u03b2\u0358\3\2"+
		"\2\2\u03b2\u035f\3\2\2\2\u03b2\u0365\3\2\2\2\u03b2\u036b\3\2\2\2\u03b2"+
		"\u0371\3\2\2\2\u03b2\u0376\3\2\2\2\u03b2\u037e\3\2\2\2\u03b2\u0386\3\2"+
		"\2\2\u03b2\u038f\3\2\2\2\u03b2\u0398\3\2\2\2\u03b2\u03a2\3\2\2\2\u03b2"+
		"\u03ab\3\2\2\2\u03b2\u03ad\3\2\2\2\u03b2\u03ae\3\2\2\2\u03b2\u03af\3\2"+
		"\2\2\u03b2\u03b0\3\2\2\2\u03b3\r\3\2\2\2\u03b4\u03b6\7K\2\2\u03b5\u03b7"+
		"\7\u00aa\2\2\u03b6\u03b5\3\2\2\2\u03b6\u03b7\3\2\2\2\u03b7\u03b9\3\2\2"+
		"\2\u03b8\u03ba\7\u00cc\2\2\u03b9\u03b8\3\2\2\2\u03b9\u03ba\3\2\2\2\u03ba"+
		"\u03bb\3\2\2\2\u03bb\u03bf\7L\2\2\u03bc\u03bd\7u\2\2\u03bd\u03be\7\36"+
		"\2\2\u03be\u03c0\7 \2\2\u03bf\u03bc\3\2\2\2\u03bf\u03c0\3\2\2\2\u03c0"+
		"\u03c1\3\2\2\2\u03c1\u03c2\5r:\2\u03c2\17\3\2\2\2\u03c3\u03c4\7\u00be"+
		"\2\2\u03c4\u03c5\7\22\2\2\u03c5\u03c9\5`\61\2\u03c6\u03c7\7\u00bf\2\2"+
		"\u03c7\u03c8\7\22\2\2\u03c8\u03ca\5d\63\2\u03c9\u03c6\3\2\2\2\u03c9\u03ca"+
		"\3\2\2\2\u03ca\u03cb\3\2\2\2\u03cb\u03cc\7Q\2\2\u03cc\u03cd\7\u00eb\2"+
		"\2\u03cd\u03ce\7\u00af\2\2\u03ce\21\3\2\2\2\u03cf\u03d0\7\u00b0\2\2\u03d0"+
		"\u03d1\7\22\2\2\u03d1\u03d2\5`\61\2\u03d2\u03d5\7;\2\2\u03d3\u03d6\5\62"+
		"\32\2\u03d4\u03d6\5\64\33\2\u03d5\u03d3\3\2\2\2\u03d5\u03d4\3\2\2\2\u03d6"+
		"\u03da\3\2\2\2\u03d7\u03d8\7\u00b1\2\2\u03d8\u03d9\7\r\2\2\u03d9\u03db"+
		"\7\u00b2\2\2\u03da\u03d7\3\2\2\2\u03da\u03db\3\2\2\2\u03db\23\3\2\2\2"+
		"\u03dc\u03dd\7\u00b3\2\2\u03dd\u03de\7\u00e6\2\2\u03de\25\3\2\2\2\u03df"+
		"\u03e1\5$\23\2\u03e0\u03df\3\2\2\2\u03e0\u03e1\3\2\2\2\u03e1\u03e2\3\2"+
		"\2\2\u03e2\u03e3\5> \2\u03e3\27\3\2\2\2\u03e4\u03e5\7O\2\2\u03e5\u03e6"+
		"\7\u0090\2\2\u03e6\u03e7\7L\2\2\u03e7\u03ee\5r:\2\u03e8\u03ec\5\34\17"+
		"\2\u03e9\u03ea\7u\2\2\u03ea\u03eb\7\36\2\2\u03eb\u03ed\7 \2\2\u03ec\u03e9"+
		"\3\2\2\2\u03ec\u03ed\3\2\2\2\u03ed\u03ef\3\2\2\2\u03ee\u03e8\3\2\2\2\u03ee"+
		"\u03ef\3\2\2\2\u03ef\u03fa\3\2\2\2\u03f0\u03f1\7O\2\2\u03f1\u03f3\7Q\2"+
		"\2\u03f2\u03f4\7L\2\2\u03f3\u03f2\3\2\2\2\u03f3\u03f4\3\2\2\2\u03f4\u03f5"+
		"\3\2\2\2\u03f5\u03f7\5r:\2\u03f6\u03f8\5\34\17\2\u03f7\u03f6\3\2\2\2\u03f7"+
		"\u03f8\3\2\2\2\u03f8\u03fa\3\2\2\2\u03f9\u03e4\3\2\2\2\u03f9\u03f0\3\2"+
		"\2\2\u03fa\31\3\2\2\2\u03fb\u03fd\5\34\17\2\u03fc\u03fe\5\24\13\2\u03fd"+
		"\u03fc\3\2\2\2\u03fd\u03fe\3\2\2\2\u03fe\33\3\2\2\2\u03ff\u0400\7?\2\2"+
		"\u0400\u0401\7\3\2\2\u0401\u0406\5\36\20\2\u0402\u0403\7\5\2\2\u0403\u0405"+
		"\5\36\20\2\u0404\u0402\3\2\2\2\u0405\u0408\3\2\2\2\u0406\u0404\3\2\2\2"+
		"\u0406\u0407\3\2\2\2\u0407\u0409\3\2\2\2\u0408\u0406\3\2\2\2\u0409\u040a"+
		"\7\4\2\2\u040a\35\3\2\2\2\u040b\u040e\5\u00acW\2\u040c\u040d\7v\2\2\u040d"+
		"\u040f\5\u0084C\2\u040e\u040c\3\2\2\2\u040e\u040f\3\2\2\2\u040f\37\3\2"+
		"\2\2\u0410\u0416\5\u00aaV\2\u0411\u0416\7\u00e6\2\2\u0412\u0416\5\u0086"+
		"D\2\u0413\u0416\5\u0088E\2\u0414\u0416\5\u008aF\2\u0415\u0410\3\2\2\2"+
		"\u0415\u0411\3\2\2\2\u0415\u0412\3\2\2\2\u0415\u0413\3\2\2\2\u0415\u0414"+
		"\3\2\2\2\u0416!\3\2\2\2\u0417\u041f\5\u00acW\2\u0418\u041b\7\6\2\2\u0419"+
		"\u041c\5\u00acW\2\u041a\u041c\7\u00e6\2\2\u041b\u0419\3\2\2\2\u041b\u041a"+
		"\3\2\2\2\u041c\u041e\3\2\2\2\u041d\u0418\3\2\2\2\u041e\u0421\3\2\2\2\u041f"+
		"\u041d\3\2\2\2\u041f\u0420\3\2\2\2\u0420#\3\2\2\2\u0421\u041f\3\2\2\2"+
		"\u0422\u0423\7I\2\2\u0423\u0428\5&\24\2\u0424\u0425\7\5\2\2\u0425\u0427"+
		"\5&\24\2\u0426\u0424\3\2\2\2\u0427\u042a\3\2\2\2\u0428\u0426\3\2\2\2\u0428"+
		"\u0429\3\2\2\2\u0429%\3\2\2\2\u042a\u0428\3\2\2\2\u042b\u042d\5\u00ac"+
		"W\2\u042c\u042e\7\r\2\2\u042d\u042c\3\2\2\2\u042d\u042e\3\2\2\2\u042e"+
		"\u042f\3\2\2\2\u042f\u0430\7\3\2\2\u0430\u0431\5\26\f\2\u0431\u0432\7"+
		"\4\2\2\u0432\'\3\2\2\2\u0433\u0434\7\u0093\2\2\u0434\u0435\5\u00aaV\2"+
		"\u0435)\3\2\2\2\u0436\u0437\7\3\2\2\u0437\u043c\5,\27\2\u0438\u0439\7"+
		"\5\2\2\u0439\u043b\5,\27\2\u043a\u0438\3\2\2\2\u043b\u043e\3\2\2\2\u043c"+
		"\u043a\3\2\2\2\u043c\u043d\3\2\2\2\u043d\u043f\3\2\2\2\u043e\u043c\3\2"+
		"\2\2\u043f\u0440\7\4\2\2\u0440+\3\2\2\2\u0441\u0446\5.\30\2\u0442\u0444"+
		"\7v\2\2\u0443\u0442\3\2\2\2\u0443\u0444\3\2\2\2\u0444\u0445\3\2\2\2\u0445"+
		"\u0447\5\60\31\2\u0446\u0443\3\2\2\2\u0446\u0447\3\2\2\2\u0447-\3\2\2"+
		"\2\u0448\u044d\5\u00acW\2\u0449\u044a\7\6\2\2\u044a\u044c\5\u00acW\2\u044b"+
		"\u0449\3\2\2\2\u044c\u044f\3\2\2\2\u044d\u044b\3\2\2\2\u044d\u044e\3\2"+
		"\2\2\u044e\u0452\3\2\2\2\u044f\u044d\3\2\2\2\u0450\u0452\7\u00e6\2\2\u0451"+
		"\u0448\3\2\2\2\u0451\u0450\3\2\2\2\u0452/\3\2\2\2\u0453\u0458\7\u00eb"+
		"\2\2\u0454\u0458\7\u00ec\2\2\u0455\u0458\5\u008cG\2\u0456\u0458\7\u00e6"+
		"\2\2\u0457\u0453\3\2\2\2\u0457\u0454\3\2\2\2\u0457\u0455\3\2\2\2\u0457"+
		"\u0456\3\2\2\2\u0458\61\3\2\2\2\u0459\u045a\7\3\2\2\u045a\u045f\5\u0084"+
		"C\2\u045b\u045c\7\5\2\2\u045c\u045e\5\u0084C\2\u045d\u045b\3\2\2\2\u045e"+
		"\u0461\3\2\2\2\u045f\u045d\3\2\2\2\u045f\u0460\3\2\2\2\u0460\u0462\3\2"+
		"\2\2\u0461\u045f\3\2\2\2\u0462\u0463\7\4\2\2\u0463\63\3\2\2\2\u0464\u0465"+
		"\7\3\2\2\u0465\u046a\5\62\32\2\u0466\u0467\7\5\2\2\u0467\u0469\5\62\32"+
		"\2\u0468\u0466\3\2\2\2\u0469\u046c\3\2\2\2\u046a\u0468\3\2\2\2\u046a\u046b"+
		"\3\2\2\2\u046b\u046d\3\2\2\2\u046c\u046a\3\2\2\2\u046d\u046e\7\4\2\2\u046e"+
		"\65\3\2\2\2\u046f\u0470\7\u00b1\2\2\u0470\u0471\7\r\2\2\u0471\u0476\5"+
		"8\35\2\u0472\u0473\7\u00b1\2\2\u0473\u0474\7\22\2\2\u0474\u0476\5:\36"+
		"\2\u0475\u046f\3\2\2\2\u0475\u0472\3\2\2\2\u0476\67\3\2\2\2\u0477\u0478"+
		"\7\u00c1\2\2\u0478\u0479\7\u00e6\2\2\u0479\u047a\7\u00c2\2\2\u047a\u047d"+
		"\7\u00e6\2\2\u047b\u047d\5\u00acW\2\u047c\u0477\3\2\2\2\u047c\u047b\3"+
		"\2\2\2\u047d9\3\2\2\2\u047e\u0482\7\u00e6\2\2\u047f\u0480\7I\2\2\u0480"+
		"\u0481\7\u0095\2\2\u0481\u0483\5*\26\2\u0482\u047f\3\2\2\2\u0482\u0483"+
		"\3\2\2\2\u0483;\3\2\2\2\u0484\u0485\5\u00acW\2\u0485\u0486\7\u00e6\2\2"+
		"\u0486=\3\2\2\2\u0487\u0489\5\30\r\2\u0488\u0487\3\2\2\2\u0488\u0489\3"+
		"\2\2\2\u0489\u048a\3\2\2\2\u048a\u048b\5D#\2\u048b\u048c\5@!\2\u048c\u0494"+
		"\3\2\2\2\u048d\u048f\5L\'\2\u048e\u0490\5B\"\2\u048f\u048e\3\2\2\2\u0490"+
		"\u0491\3\2\2\2\u0491\u048f\3\2\2\2\u0491\u0492\3\2\2\2\u0492\u0494\3\2"+
		"\2\2\u0493\u0488\3\2\2\2\u0493\u048d\3\2\2\2\u0494?\3\2\2\2\u0495\u0496"+
		"\7\27\2\2\u0496\u0497\7\22\2\2\u0497\u049c\5H%\2\u0498\u0499\7\5\2\2\u0499"+
		"\u049b\5H%\2\u049a\u0498\3\2\2\2\u049b\u049e\3\2\2\2\u049c\u049a\3\2\2"+
		"\2\u049c\u049d\3\2\2\2\u049d\u04a0\3\2\2\2\u049e\u049c\3\2\2\2\u049f\u0495"+
		"\3\2\2\2\u049f\u04a0\3\2\2\2\u04a0\u04ab\3\2\2\2\u04a1\u04a2\7\u008e\2"+
		"\2\u04a2\u04a3\7\22\2\2\u04a3\u04a8\5x=\2\u04a4\u04a5\7\5\2\2\u04a5\u04a7"+
		"\5x=\2\u04a6\u04a4\3\2\2\2\u04a7\u04aa\3\2\2\2\u04a8\u04a6\3\2\2\2\u04a8"+
		"\u04a9\3\2\2\2\u04a9\u04ac\3\2\2\2\u04aa\u04a8\3\2\2\2\u04ab\u04a1\3\2"+
		"\2\2\u04ab\u04ac\3\2\2\2\u04ac\u04b7\3\2\2\2\u04ad\u04ae\7\u008f\2\2\u04ae"+
		"\u04af\7\22\2\2\u04af\u04b4\5x=\2\u04b0\u04b1\7\5\2\2\u04b1\u04b3\5x="+
		"\2\u04b2\u04b0\3\2\2\2\u04b3\u04b6\3\2\2\2\u04b4\u04b2\3\2\2\2\u04b4\u04b5"+
		"\3\2\2\2\u04b5\u04b8\3\2\2\2\u04b6\u04b4\3\2\2\2\u04b7\u04ad\3\2\2\2\u04b7"+
		"\u04b8\3\2\2\2\u04b8\u04c3\3\2\2\2\u04b9\u04ba\7\u008d\2\2\u04ba\u04bb"+
		"\7\22\2\2\u04bb\u04c0\5H%\2\u04bc\u04bd\7\5\2\2\u04bd\u04bf\5H%\2\u04be"+
		"\u04bc\3\2\2\2\u04bf\u04c2\3\2\2\2\u04c0\u04be\3\2\2\2\u04c0\u04c1\3\2"+
		"\2\2\u04c1\u04c4\3\2\2\2\u04c2\u04c0\3\2\2\2\u04c3\u04b9\3\2\2\2\u04c3"+
		"\u04c4\3\2\2\2\u04c4\u04c6\3\2\2\2\u04c5\u04c7\5\u00a0Q\2\u04c6\u04c5"+
		"\3\2\2\2\u04c6\u04c7\3\2\2\2\u04c7\u04ca\3\2\2\2\u04c8\u04c9\7\31\2\2"+
		"\u04c9\u04cb\5x=\2\u04ca\u04c8\3\2\2\2\u04ca\u04cb\3\2\2\2\u04cbA\3\2"+
		"\2\2\u04cc\u04ce\5\30\r\2\u04cd\u04cc\3\2\2\2\u04cd\u04ce\3\2\2\2\u04ce"+
		"\u04cf\3\2\2\2\u04cf\u04d0\5J&\2\u04d0\u04d1\5@!\2\u04d1C\3\2\2\2\u04d2"+
		"\u04d3\b#\1\2\u04d3\u04d4\5F$\2\u04d4\u04dd\3\2\2\2\u04d5\u04d6\f\3\2"+
		"\2\u04d6\u04d8\t\t\2\2\u04d7\u04d9\5T+\2\u04d8\u04d7\3\2\2\2\u04d8\u04d9"+
		"\3\2\2\2\u04d9\u04da\3\2\2\2\u04da\u04dc\5D#\4\u04db\u04d5\3\2\2\2\u04dc"+
		"\u04df\3\2\2\2\u04dd\u04db\3\2\2\2\u04dd\u04de\3\2\2\2\u04deE\3\2\2\2"+
		"\u04df\u04dd\3\2\2\2\u04e0\u04e9\5J&\2\u04e1\u04e2\7L\2\2\u04e2\u04e9"+
		"\5r:\2\u04e3\u04e9\5n8\2\u04e4\u04e5\7\3\2\2\u04e5\u04e6\5> \2\u04e6\u04e7"+
		"\7\4\2\2\u04e7\u04e9\3\2\2\2\u04e8\u04e0\3\2\2\2\u04e8\u04e1\3\2\2\2\u04e8"+
		"\u04e3\3\2\2\2\u04e8\u04e4\3\2\2\2\u04e9G\3\2\2\2\u04ea\u04ec\5x=\2\u04eb"+
		"\u04ed\t\n\2\2\u04ec\u04eb\3\2\2\2\u04ec\u04ed\3\2\2\2\u04ed\u04f0\3\2"+
		"\2\2\u04ee\u04ef\7(\2\2\u04ef\u04f1\t\13\2\2\u04f0\u04ee\3\2\2\2\u04f0"+
		"\u04f1\3\2\2\2\u04f1I\3\2\2\2\u04f2\u04f3\7\n\2\2\u04f3\u04f4\7\u0091"+
		"\2\2\u04f4\u04f5\7\3\2\2\u04f5\u04f6\5v<\2\u04f6\u04f7\7\4\2\2\u04f7\u04fd"+
		"\3\2\2\2\u04f8\u04f9\7j\2\2\u04f9\u04fd\5v<\2\u04fa\u04fb\7\u0092\2\2"+
		"\u04fb\u04fd\5v<\2\u04fc\u04f2\3\2\2\2\u04fc\u04f8\3\2\2\2\u04fc\u04fa"+
		"\3\2\2\2\u04fd\u04ff\3\2\2\2\u04fe\u0500\5p9\2\u04ff\u04fe\3\2\2\2\u04ff"+
		"\u0500\3\2\2\2\u0500\u0503\3\2\2\2\u0501\u0502\7\u0097\2\2\u0502\u0504"+
		"\7\u00e6\2\2\u0503\u0501\3\2\2\2\u0503\u0504\3\2\2\2\u0504\u0505\3\2\2"+
		"\2\u0505\u0506\7\u0093\2\2\u0506\u0513\7\u00e6\2\2\u0507\u0511\7\r\2\2"+
		"\u0508\u0512\5b\62\2\u0509\u0512\5\u0096L\2\u050a\u050d\7\3\2\2\u050b"+
		"\u050e\5b\62\2\u050c\u050e\5\u0096L\2\u050d\u050b\3\2\2\2\u050d\u050c"+
		"\3\2\2\2\u050e\u050f\3\2\2\2\u050f\u0510\7\4\2\2\u0510\u0512\3\2\2\2\u0511"+
		"\u0508\3\2\2\2\u0511\u0509\3\2\2\2\u0511\u050a\3\2\2\2\u0512\u0514\3\2"+
		"\2\2\u0513\u0507\3\2\2\2\u0513\u0514\3\2\2\2\u0514\u0516\3\2\2\2\u0515"+
		"\u0517\5p9\2\u0516\u0515\3\2\2\2\u0516\u0517\3\2\2\2\u0517\u051a\3\2\2"+
		"\2\u0518\u0519\7\u0096\2\2\u0519\u051b\7\u00e6\2\2\u051a\u0518\3\2\2\2"+
		"\u051a\u051b\3\2\2\2\u051b\u051d\3\2\2\2\u051c\u051e\5L\'\2\u051d\u051c"+
		"\3\2\2\2\u051d\u051e\3\2\2\2\u051e\u0521\3\2\2\2\u051f\u0520\7\20\2\2"+
		"\u0520\u0522\5z>\2\u0521\u051f\3\2\2\2\u0521\u0522\3\2\2\2\u0522\u054a"+
		"\3\2\2\2\u0523\u0525\7\n\2\2\u0524\u0526\5T+\2\u0525\u0524\3\2\2\2\u0525"+
		"\u0526\3\2\2\2\u0526\u0527\3\2\2\2\u0527\u0529\5v<\2\u0528\u052a\5L\'"+
		"\2\u0529\u0528\3\2\2\2\u0529\u052a\3\2\2\2\u052a\u0534\3\2\2\2\u052b\u0531"+
		"\5L\'\2\u052c\u052e\7\n\2\2\u052d\u052f\5T+\2\u052e\u052d\3\2\2\2\u052e"+
		"\u052f\3\2\2\2\u052f\u0530\3\2\2\2\u0530\u0532\5v<\2\u0531\u052c\3\2\2"+
		"\2\u0531\u0532\3\2\2\2\u0532\u0534\3\2\2\2\u0533\u0523\3\2\2\2\u0533\u052b"+
		"\3\2\2\2\u0534\u0538\3\2\2\2\u0535\u0537\5R*\2\u0536\u0535\3\2\2\2\u0537"+
		"\u053a\3\2\2\2\u0538\u0536\3\2\2\2\u0538\u0539\3\2\2\2\u0539\u053d\3\2"+
		"\2\2\u053a\u0538\3\2\2\2\u053b\u053c\7\20\2\2\u053c\u053e\5z>\2\u053d"+
		"\u053b\3\2\2\2\u053d\u053e\3\2\2\2\u053e\u0540\3\2\2\2\u053f\u0541\5N"+
		"(\2\u0540\u053f\3\2\2\2\u0540\u0541\3\2\2\2\u0541\u0544\3\2\2\2\u0542"+
		"\u0543\7\30\2\2\u0543\u0545\5z>\2\u0544\u0542\3\2\2\2\u0544\u0545\3\2"+
		"\2\2\u0545\u0547\3\2\2\2\u0546\u0548\5\u00a0Q\2\u0547\u0546\3\2\2\2\u0547"+
		"\u0548\3\2\2\2\u0548\u054a\3\2\2\2\u0549\u04fc\3\2\2\2\u0549\u0533\3\2"+
		"\2\2\u054aK\3\2\2\2\u054b\u054c\7\13\2\2\u054c\u0551\5V,\2\u054d\u054e"+
		"\7\5\2\2\u054e\u0550\5V,\2\u054f\u054d\3\2\2\2\u0550\u0553\3\2\2\2\u0551"+
		"\u054f\3\2\2\2\u0551\u0552\3\2\2\2\u0552\u0557\3\2\2\2\u0553\u0551\3\2"+
		"\2\2\u0554\u0556\5R*\2\u0555\u0554\3\2\2\2\u0556\u0559\3\2\2\2\u0557\u0555"+
		"\3\2\2\2\u0557\u0558\3\2\2\2\u0558M\3\2\2\2\u0559\u0557\3\2\2\2\u055a"+
		"\u055b\7\21\2\2\u055b\u055c\7\22\2\2\u055c\u0561\5x=\2\u055d\u055e\7\5"+
		"\2\2\u055e\u0560\5x=\2\u055f\u055d\3\2\2\2\u0560\u0563\3\2\2\2\u0561\u055f"+
		"\3\2\2\2\u0561\u0562\3\2\2\2\u0562\u0575\3\2\2\2\u0563\u0561\3\2\2\2\u0564"+
		"\u0565\7I\2\2\u0565\u0576\7\26\2\2\u0566\u0567\7I\2\2\u0567\u0576\7\25"+
		"\2\2\u0568\u0569\7\23\2\2\u0569\u056a\7\24\2\2\u056a\u056b\7\3\2\2\u056b"+
		"\u0570\5P)\2\u056c\u056d\7\5\2\2\u056d\u056f\5P)\2\u056e\u056c\3\2\2\2"+
		"\u056f\u0572\3\2\2\2\u0570\u056e\3\2\2\2\u0570\u0571\3\2\2\2\u0571\u0573"+
		"\3\2\2\2\u0572\u0570\3\2\2\2\u0573\u0574\7\4\2\2\u0574\u0576\3\2\2\2\u0575"+
		"\u0564\3\2\2\2\u0575\u0566\3\2\2\2\u0575\u0568\3\2\2\2\u0575\u0576\3\2"+
		"\2\2\u0576O\3\2\2\2\u0577\u0580\7\3\2\2\u0578\u057d\5x=\2\u0579\u057a"+
		"\7\5\2\2\u057a\u057c\5x=\2\u057b\u0579\3\2\2\2\u057c\u057f\3\2\2\2\u057d"+
		"\u057b\3\2\2\2\u057d\u057e\3\2\2\2\u057e\u0581\3\2\2\2\u057f\u057d\3\2"+
		"\2\2\u0580\u0578\3\2\2\2\u0580\u0581\3\2\2\2\u0581\u0582\3\2\2\2\u0582"+
		"\u0585\7\4\2\2\u0583\u0585\5x=\2\u0584\u0577\3\2\2\2\u0584\u0583\3\2\2"+
		"\2\u0585Q\3\2\2\2\u0586\u0587\7<\2\2\u0587\u0589\7M\2\2\u0588\u058a\7"+
		"\64\2\2\u0589\u0588\3\2\2\2\u0589\u058a\3\2\2\2\u058a\u058b\3\2\2\2\u058b"+
		"\u058c\5\u00aaV\2\u058c\u0595\7\3\2\2\u058d\u0592\5x=\2\u058e\u058f\7"+
		"\5\2\2\u058f\u0591\5x=\2\u0590\u058e\3\2\2\2\u0591\u0594\3\2\2\2\u0592"+
		"\u0590\3\2\2\2\u0592\u0593\3\2\2\2\u0593\u0596\3\2\2\2\u0594\u0592\3\2"+
		"\2\2\u0595\u058d\3\2\2\2\u0595\u0596\3\2\2\2\u0596\u0597\3\2\2\2\u0597"+
		"\u0598\7\4\2\2\u0598\u05a4\5\u00acW\2\u0599\u059b\7\r\2\2\u059a\u0599"+
		"\3\2\2\2\u059a\u059b\3\2\2\2\u059b\u059c\3\2\2\2\u059c\u05a1\5\u00acW"+
		"\2\u059d\u059e\7\5\2\2\u059e\u05a0\5\u00acW\2\u059f\u059d\3\2\2\2\u05a0"+
		"\u05a3\3\2\2\2\u05a1\u059f\3\2\2\2\u05a1\u05a2\3\2\2\2\u05a2\u05a5\3\2"+
		"\2\2\u05a3\u05a1\3\2\2\2\u05a4\u059a\3\2\2\2\u05a4\u05a5\3\2\2\2\u05a5"+
		"S\3\2\2\2\u05a6\u05a7\t\f\2\2\u05a7U\3\2\2\2\u05a8\u05ac\5l\67\2\u05a9"+
		"\u05ab\5X-\2\u05aa\u05a9\3\2\2\2\u05ab\u05ae\3\2\2\2\u05ac\u05aa\3\2\2"+
		"\2\u05ac\u05ad\3\2\2\2\u05adW\3\2\2\2\u05ae\u05ac\3\2\2\2\u05af\u05b0"+
		"\5Z.\2\u05b0\u05b1\7\62\2\2\u05b1\u05b3\5l\67\2\u05b2\u05b4\5\\/\2\u05b3"+
		"\u05b2\3\2\2\2\u05b3\u05b4\3\2\2\2\u05b4\u05bb\3\2\2\2\u05b5\u05b6\7:"+
		"\2\2\u05b6\u05b7\5Z.\2\u05b7\u05b8\7\62\2\2\u05b8\u05b9\5l\67\2\u05b9"+
		"\u05bb\3\2\2\2\u05ba\u05af\3\2\2\2\u05ba\u05b5\3\2\2\2\u05bbY\3\2\2\2"+
		"\u05bc\u05be\7\65\2\2\u05bd\u05bc\3\2\2\2\u05bd\u05be\3\2\2\2\u05be\u05d3"+
		"\3\2\2\2\u05bf\u05d3\7\63\2\2\u05c0\u05c2\7\66\2\2\u05c1\u05c3\7\64\2"+
		"\2\u05c2\u05c1\3\2\2\2\u05c2\u05c3\3\2\2\2\u05c3\u05d3\3\2\2\2\u05c4\u05c5"+
		"\7\66\2\2\u05c5\u05d3\7\67\2\2\u05c6\u05c8\78\2\2\u05c7\u05c9\7\64\2\2"+
		"\u05c8\u05c7\3\2\2\2\u05c8\u05c9\3\2\2\2\u05c9\u05d3\3\2\2\2\u05ca\u05cc"+
		"\79\2\2\u05cb\u05cd\7\64\2\2\u05cc\u05cb\3\2\2\2\u05cc\u05cd\3\2\2\2\u05cd"+
		"\u05d3\3\2\2\2\u05ce\u05d0\7\66\2\2\u05cf\u05ce\3\2\2\2\u05cf\u05d0\3"+
		"\2\2\2\u05d0\u05d1\3\2\2\2\u05d1\u05d3\7\u00e1\2\2\u05d2\u05bd\3\2\2\2"+
		"\u05d2\u05bf\3\2\2\2\u05d2\u05c0\3\2\2\2\u05d2\u05c4\3\2\2\2\u05d2\u05c6"+
		"\3\2\2\2\u05d2\u05ca\3\2\2\2\u05d2\u05cf\3\2\2\2\u05d3[\3\2\2\2\u05d4"+
		"\u05d5\7;\2\2\u05d5\u05e3\5z>\2\u05d6\u05d7\7\u0093\2\2\u05d7\u05d8\7"+
		"\3\2\2\u05d8\u05dd\5\u00acW\2\u05d9\u05da\7\5\2\2\u05da\u05dc\5\u00ac"+
		"W\2\u05db\u05d9\3\2\2\2\u05dc\u05df\3\2\2\2\u05dd\u05db\3\2\2\2\u05dd"+
		"\u05de\3\2\2\2\u05de\u05e0\3\2\2\2\u05df\u05dd\3\2\2\2\u05e0\u05e1\7\4"+
		"\2\2\u05e1\u05e3\3\2\2\2\u05e2\u05d4\3\2\2\2\u05e2\u05d6\3\2\2\2\u05e3"+
		"]\3\2\2\2\u05e4\u05e5\7e\2\2\u05e5\u05fb\7\3\2\2\u05e6\u05e7\t\r\2\2\u05e7"+
		"\u05fc\7\u0089\2\2\u05e8\u05e9\5x=\2\u05e9\u05ea\7A\2\2\u05ea\u05fc\3"+
		"\2\2\2\u05eb\u05fc\7\u00ea\2\2\u05ec\u05ed\7\u008a\2\2\u05ed\u05ee\7\u00eb"+
		"\2\2\u05ee\u05ef\7\u008b\2\2\u05ef\u05f0\7\u008c\2\2\u05f0\u05f9\7\u00eb"+
		"\2\2\u05f1\u05f7\7;\2\2\u05f2\u05f8\5\u00acW\2\u05f3\u05f4\5\u00aaV\2"+
		"\u05f4\u05f5\7\3\2\2\u05f5\u05f6\7\4\2\2\u05f6\u05f8\3\2\2\2\u05f7\u05f2"+
		"\3\2\2\2\u05f7\u05f3\3\2\2\2\u05f8\u05fa\3\2\2\2\u05f9\u05f1\3\2\2\2\u05f9"+
		"\u05fa\3\2\2\2\u05fa\u05fc\3\2\2\2\u05fb\u05e6\3\2\2\2\u05fb\u05e8\3\2"+
		"\2\2\u05fb\u05eb\3\2\2\2\u05fb\u05ec\3\2\2\2\u05fc\u05fd\3\2\2\2\u05fd"+
		"\u05fe\7\4\2\2\u05fe_\3\2\2\2\u05ff\u0600\7\3\2\2\u0600\u0601\5b\62\2"+
		"\u0601\u0602\7\4\2\2\u0602a\3\2\2\2\u0603\u0608\5\u00acW\2\u0604\u0605"+
		"\7\5\2\2\u0605\u0607\5\u00acW\2\u0606\u0604\3\2\2\2\u0607\u060a\3\2\2"+
		"\2\u0608\u0606\3\2\2\2\u0608\u0609\3\2\2\2\u0609c\3\2\2\2\u060a\u0608"+
		"\3\2\2\2\u060b\u060c\7\3\2\2\u060c\u0611\5f\64\2\u060d\u060e\7\5\2\2\u060e"+
		"\u0610\5f\64\2\u060f\u060d\3\2\2\2\u0610\u0613\3\2\2\2\u0611\u060f\3\2"+
		"\2\2\u0611\u0612\3\2\2\2\u0612\u0614\3\2\2\2\u0613\u0611\3\2\2\2\u0614"+
		"\u0615\7\4\2\2\u0615e\3\2\2\2\u0616\u0618\5\u00acW\2\u0617\u0619\t\n\2"+
		"\2\u0618\u0617\3\2\2\2\u0618\u0619\3\2\2\2\u0619g\3\2\2\2\u061a\u061b"+
		"\7\3\2\2\u061b\u0620\5j\66\2\u061c\u061d\7\5\2\2\u061d\u061f\5j\66\2\u061e"+
		"\u061c\3\2\2\2\u061f\u0622\3\2\2\2\u0620\u061e\3\2\2\2\u0620\u0621\3\2"+
		"\2\2\u0621\u0623\3\2\2\2\u0622\u0620\3\2\2\2\u0623\u0624\7\4\2\2\u0624"+
		"i\3\2\2\2\u0625\u0628\5\u00acW\2\u0626\u0627\7l\2\2\u0627\u0629\7\u00e6"+
		"\2\2\u0628\u0626\3\2\2\2\u0628\u0629\3\2\2\2\u0629k\3\2\2\2\u062a\u062c"+
		"\5r:\2\u062b\u062d\5^\60\2\u062c\u062b\3\2\2\2\u062c\u062d\3\2\2\2\u062d"+
		"\u0632\3\2\2\2\u062e\u0630\7\r\2\2\u062f\u062e\3\2\2\2\u062f\u0630\3\2"+
		"\2\2\u0630\u0631\3\2\2\2\u0631\u0633\5\u00aeX\2\u0632\u062f\3\2\2\2\u0632"+
		"\u0633\3\2\2\2\u0633\u065c\3\2\2\2\u0634\u0635\7\3\2\2\u0635\u0636\5>"+
		" \2\u0636\u0638\7\4\2\2\u0637\u0639\5^\60\2\u0638\u0637\3\2\2\2\u0638"+
		"\u0639\3\2\2\2\u0639\u063e\3\2\2\2\u063a\u063c\7\r\2\2\u063b\u063a\3\2"+
		"\2\2\u063b\u063c\3\2\2\2\u063c\u063d\3\2\2\2\u063d\u063f\5\u00aeX\2\u063e"+
		"\u063b\3\2\2\2\u063e\u063f\3\2\2\2\u063f\u065c\3\2\2\2\u0640\u0641\7\3"+
		"\2\2\u0641\u0642\5V,\2\u0642\u0644\7\4\2\2\u0643\u0645\5^\60\2\u0644\u0643"+
		"\3\2\2\2\u0644\u0645\3\2\2\2\u0645\u064a\3\2\2\2\u0646\u0648\7\r\2\2\u0647"+
		"\u0646\3\2\2\2\u0647\u0648\3\2\2\2\u0648\u0649\3\2\2\2\u0649\u064b\5\u00ae"+
		"X\2\u064a\u0647\3\2\2\2\u064a\u064b\3\2\2\2\u064b\u065c\3\2\2\2\u064c"+
		"\u065c\5n8\2\u064d\u064e\5\u00acW\2\u064e\u0657\7\3\2\2\u064f\u0654\5"+
		"x=\2\u0650\u0651\7\5\2\2\u0651\u0653\5x=\2\u0652\u0650\3\2\2\2\u0653\u0656"+
		"\3\2\2\2\u0654\u0652\3\2\2\2\u0654\u0655\3\2\2\2\u0655\u0658\3\2\2\2\u0656"+
		"\u0654\3\2\2\2\u0657\u064f\3\2\2\2\u0657\u0658\3\2\2\2\u0658\u0659\3\2"+
		"\2\2\u0659\u065a\7\4\2\2\u065a\u065c\3\2\2\2\u065b\u062a\3\2\2\2\u065b"+
		"\u0634\3\2\2\2\u065b\u0640\3\2\2\2\u065b\u064c\3\2\2\2\u065b\u064d\3\2"+
		"\2\2\u065cm\3\2\2\2\u065d\u065e\7J\2\2\u065e\u0663\5x=\2\u065f\u0660\7"+
		"\5\2\2\u0660\u0662\5x=\2\u0661\u065f\3\2\2\2\u0662\u0665\3\2\2\2\u0663"+
		"\u0661\3\2\2\2\u0663\u0664\3\2\2\2\u0664\u066d\3\2\2\2\u0665\u0663\3\2"+
		"\2\2\u0666\u0668\7\r\2\2\u0667\u0666\3\2\2\2\u0667\u0668\3\2\2\2\u0668"+
		"\u0669\3\2\2\2\u0669\u066b\5\u00acW\2\u066a\u066c\5`\61\2\u066b\u066a"+
		"\3\2\2\2\u066b\u066c\3\2\2\2\u066c\u066e\3\2\2\2\u066d\u0667\3\2\2\2\u066d"+
		"\u066e\3\2\2\2\u066eo\3\2\2\2\u066f\u0670\7H\2\2\u0670\u0671\7T\2\2\u0671"+
		"\u0672\7\u0094\2\2\u0672\u0676\7\u00e6\2\2\u0673\u0674\7I\2\2\u0674\u0675"+
		"\7\u0095\2\2\u0675\u0677\5*\26\2\u0676\u0673\3\2\2\2\u0676\u0677\3\2\2"+
		"\2\u0677\u06a1\3\2\2\2\u0678\u0679\7H\2\2\u0679\u067a\7T\2\2\u067a\u0684"+
		"\7\u0098\2\2\u067b\u067c\7\u0099\2\2\u067c\u067d\7\u009a\2\2\u067d\u067e"+
		"\7\22\2\2\u067e\u0682\7\u00e6\2\2\u067f\u0680\7\u009e\2\2\u0680\u0681"+
		"\7\22\2\2\u0681\u0683\7\u00e6\2\2\u0682\u067f\3\2\2\2\u0682\u0683\3\2"+
		"\2\2\u0683\u0685\3\2\2\2\u0684\u067b\3\2\2\2\u0684\u0685\3\2\2\2\u0685"+
		"\u068b\3\2\2\2\u0686\u0687\7\u009b\2\2\u0687\u0688\7\u009c\2\2\u0688\u0689"+
		"\7\u009a\2\2\u0689\u068a\7\22\2\2\u068a\u068c\7\u00e6\2\2\u068b\u0686"+
		"\3\2\2\2\u068b\u068c\3\2\2\2\u068c\u0692\3\2\2\2\u068d\u068e\7j\2\2\u068e"+
		"\u068f\7\u009d\2\2\u068f\u0690\7\u009a\2\2\u0690\u0691\7\22\2\2\u0691"+
		"\u0693\7\u00e6\2\2\u0692\u068d\3\2\2\2\u0692\u0693\3\2\2\2\u0693\u0698"+
		"\3\2\2\2\u0694\u0695\7\u009f\2\2\u0695\u0696\7\u009a\2\2\u0696\u0697\7"+
		"\22\2\2\u0697\u0699\7\u00e6\2\2\u0698\u0694\3\2\2\2\u0698\u0699\3\2\2"+
		"\2\u0699\u069e\3\2\2\2\u069a\u069b\7%\2\2\u069b\u069c\7\u00cd\2\2\u069c"+
		"\u069d\7\r\2\2\u069d\u069f\7\u00e6\2\2\u069e\u069a\3\2\2\2\u069e\u069f"+
		"\3\2\2\2\u069f\u06a1\3\2\2\2\u06a0\u066f\3\2\2\2\u06a0\u0678\3\2\2\2\u06a1"+
		"q\3\2\2\2\u06a2\u06a3\5\u00acW\2\u06a3\u06a4\7\6\2\2\u06a4\u06a6\3\2\2"+
		"\2\u06a5\u06a2\3\2\2\2\u06a5\u06a6\3\2\2\2\u06a6\u06a7\3\2\2\2\u06a7\u06a8"+
		"\5\u00acW\2\u06a8s\3\2\2\2\u06a9\u06b1\5x=\2\u06aa\u06ac\7\r\2\2\u06ab"+
		"\u06aa\3\2\2\2\u06ab\u06ac\3\2\2\2\u06ac\u06af\3\2\2\2\u06ad\u06b0\5\u00ac"+
		"W\2\u06ae\u06b0\5`\61\2\u06af\u06ad\3\2\2\2\u06af\u06ae\3\2\2\2\u06b0"+
		"\u06b2\3\2\2\2\u06b1\u06ab\3\2\2\2\u06b1\u06b2\3\2\2\2\u06b2u\3\2\2\2"+
		"\u06b3\u06b8\5t;\2\u06b4\u06b5\7\5\2\2\u06b5\u06b7\5t;\2\u06b6\u06b4\3"+
		"\2\2\2\u06b7\u06ba\3\2\2\2\u06b8\u06b6\3\2\2\2\u06b8\u06b9\3\2\2\2\u06b9"+
		"w\3\2\2\2\u06ba\u06b8\3\2\2\2\u06bb\u06bc\5z>\2\u06bcy\3\2\2\2\u06bd\u06be"+
		"\b>\1\2\u06be\u06bf\7\36\2\2\u06bf\u06c7\5z>\7\u06c0\u06c7\5|?\2\u06c1"+
		"\u06c2\7 \2\2\u06c2\u06c3\7\3\2\2\u06c3\u06c4\5\26\f\2\u06c4\u06c5\7\4"+
		"\2\2\u06c5\u06c7\3\2\2\2\u06c6\u06bd\3\2\2\2\u06c6\u06c0\3\2\2\2\u06c6"+
		"\u06c1\3\2\2\2\u06c7\u06d0\3\2\2\2\u06c8\u06c9\f\5\2\2\u06c9\u06ca\7\34"+
		"\2\2\u06ca\u06cf\5z>\6\u06cb\u06cc\f\4\2\2\u06cc\u06cd\7\33\2\2\u06cd"+
		"\u06cf\5z>\5\u06ce\u06c8\3\2\2\2\u06ce\u06cb\3\2\2\2\u06cf\u06d2\3\2\2"+
		"\2\u06d0\u06ce\3\2\2\2\u06d0\u06d1\3\2\2\2\u06d1{\3\2\2\2\u06d2\u06d0"+
		"\3\2\2\2\u06d3\u06d5\5\u0080A\2\u06d4\u06d6\5~@\2\u06d5\u06d4\3\2\2\2"+
		"\u06d5\u06d6\3\2\2\2\u06d6}\3\2\2\2\u06d7\u06d9\7\36\2\2\u06d8\u06d7\3"+
		"\2\2\2\u06d8\u06d9\3\2\2\2\u06d9\u06da\3\2\2\2\u06da\u06db\7!\2\2\u06db"+
		"\u06dc\5\u0080A\2\u06dc\u06dd\7\34\2\2\u06dd\u06de\5\u0080A\2\u06de\u0701"+
		"\3\2\2\2\u06df\u06e1\7\36\2\2\u06e0\u06df\3\2\2\2\u06e0\u06e1\3\2\2\2"+
		"\u06e1\u06e2\3\2\2\2\u06e2\u06e3\7\35\2\2\u06e3\u06e4\7\3\2\2\u06e4\u06e9"+
		"\5x=\2\u06e5\u06e6\7\5\2\2\u06e6\u06e8\5x=\2\u06e7\u06e5\3\2\2\2\u06e8"+
		"\u06eb\3\2\2\2\u06e9\u06e7\3\2\2\2\u06e9\u06ea\3\2\2\2\u06ea\u06ec\3\2"+
		"\2\2\u06eb\u06e9\3\2\2\2\u06ec\u06ed\7\4\2\2\u06ed\u0701\3\2\2\2\u06ee"+
		"\u06f0\7\36\2\2\u06ef\u06ee\3\2\2\2\u06ef\u06f0\3\2\2\2\u06f0\u06f1\3"+
		"\2\2\2\u06f1\u06f2\7\35\2\2\u06f2\u06f3\7\3\2\2\u06f3\u06f4\5\26\f\2\u06f4"+
		"\u06f5\7\4\2\2\u06f5\u0701\3\2\2\2\u06f6\u06f8\7\36\2\2\u06f7\u06f6\3"+
		"\2\2\2\u06f7\u06f8\3\2\2\2\u06f8\u06f9\3\2\2\2\u06f9\u06fa\t\16\2\2\u06fa"+
		"\u0701\5\u0080A\2\u06fb\u06fd\7$\2\2\u06fc\u06fe\7\36\2\2\u06fd\u06fc"+
		"\3\2\2\2\u06fd\u06fe\3\2\2\2\u06fe\u06ff\3\2\2\2\u06ff\u0701\7%\2\2\u0700"+
		"\u06d8\3\2\2\2\u0700\u06e0\3\2\2\2\u0700\u06ef\3\2\2\2\u0700\u06f7\3\2"+
		"\2\2\u0700\u06fb\3\2\2\2\u0701\177\3\2\2\2\u0702\u0703\bA\1\2\u0703\u0707"+
		"\5\u0082B\2\u0704\u0705\t\17\2\2\u0705\u0707\5\u0080A\n\u0706\u0702\3"+
		"\2\2\2\u0706\u0704\3\2\2\2\u0707\u0720\3\2\2\2\u0708\u0709\f\t\2\2\u0709"+
		"\u070a\t\20\2\2\u070a\u071f\5\u0080A\n\u070b\u070c\f\b\2\2\u070c\u070d"+
		"\t\21\2\2\u070d\u071f\5\u0080A\t\u070e\u070f\f\7\2\2\u070f\u0710\7\u0085"+
		"\2\2\u0710\u071f\5\u0080A\b\u0711\u0712\f\6\2\2\u0712\u0713\7\u0087\2"+
		"\2\u0713\u071f\5\u0080A\7\u0714\u0715\f\5\2\2\u0715\u0716\7\u0086\2\2"+
		"\u0716\u071f\5\u0080A\6\u0717\u0718\f\4\2\2\u0718\u0719\7\u0088\2\2\u0719"+
		"\u071f\5\u0080A\5\u071a\u071b\f\3\2\2\u071b\u071c\5\u0086D\2\u071c\u071d"+
		"\5\u0080A\4\u071d\u071f\3\2\2\2\u071e\u0708\3\2\2\2\u071e\u070b\3\2\2"+
		"\2\u071e\u070e\3\2\2\2\u071e\u0711\3\2\2\2\u071e\u0714\3\2\2\2\u071e\u0717"+
		"\3\2\2\2\u071e\u071a\3\2\2\2\u071f\u0722\3\2\2\2\u0720\u071e\3\2\2\2\u0720"+
		"\u0721\3\2\2\2\u0721\u0081\3\2\2\2\u0722\u0720\3\2\2\2\u0723\u0724\bB"+
		"\1\2\u0724\u0773\t\22\2\2\u0725\u0726\7-\2\2\u0726\u0728\5x=\2\u0727\u0729"+
		"\5\u009eP\2\u0728\u0727\3\2\2\2\u0729\u072a\3\2\2\2\u072a\u0728\3\2\2"+
		"\2\u072a\u072b\3\2\2\2\u072b\u072e\3\2\2\2\u072c\u072d\7\60\2\2\u072d"+
		"\u072f\5x=\2\u072e\u072c\3\2\2\2\u072e\u072f\3\2\2\2\u072f\u0730\3\2\2"+
		"\2\u0730\u0731\7\61\2\2\u0731\u0773\3\2\2\2\u0732\u0734\7-\2\2\u0733\u0735"+
		"\5\u009eP\2\u0734\u0733\3\2\2\2\u0735\u0736\3\2\2\2\u0736\u0734\3\2\2"+
		"\2\u0736\u0737\3\2\2\2\u0737\u073a\3\2\2\2\u0738\u0739\7\60\2\2\u0739"+
		"\u073b\5x=\2\u073a\u0738\3\2\2\2\u073a\u073b\3\2\2\2\u073b\u073c\3\2\2"+
		"\2\u073c\u073d\7\61\2\2\u073d\u0773\3\2\2\2\u073e\u073f\7W\2\2\u073f\u0740"+
		"\7\3\2\2\u0740\u0741\5x=\2\u0741\u0742\7\r\2\2\u0742\u0743\5\u0094K\2"+
		"\u0743\u0744\7\4\2\2\u0744\u0773\3\2\2\2\u0745\u0773\5\u0084C\2\u0746"+
		"\u0773\7\u0080\2\2\u0747\u0748\5\u00aaV\2\u0748\u0749\7\6\2\2\u0749\u074a"+
		"\7\u0080\2\2\u074a\u0773\3\2\2\2\u074b\u074c\7\3\2\2\u074c\u074f\5x=\2"+
		"\u074d\u074e\7\5\2\2\u074e\u0750\5x=\2\u074f\u074d\3\2\2\2\u0750\u0751"+
		"\3\2\2\2\u0751\u074f\3\2\2\2\u0751\u0752\3\2\2\2\u0752\u0753\3\2\2\2\u0753"+
		"\u0754\7\4\2\2\u0754\u0773\3\2\2\2\u0755\u0756\7\3\2\2\u0756\u0757\5\26"+
		"\f\2\u0757\u0758\7\4\2\2\u0758\u0773\3\2\2\2\u0759\u075a\5\u00aaV\2\u075a"+
		"\u0766\7\3\2\2\u075b\u075d\5T+\2\u075c\u075b\3\2\2\2\u075c\u075d\3\2\2"+
		"\2\u075d\u075e\3\2\2\2\u075e\u0763\5x=\2\u075f\u0760\7\5\2\2\u0760\u0762"+
		"\5x=\2\u0761\u075f\3\2\2\2\u0762\u0765\3\2\2\2\u0763\u0761\3\2\2\2\u0763"+
		"\u0764\3\2\2\2\u0764\u0767\3\2\2\2\u0765\u0763\3\2\2\2\u0766\u075c\3\2"+
		"\2\2\u0766\u0767\3\2\2\2\u0767\u0768\3\2\2\2\u0768\u076b\7\4\2\2\u0769"+
		"\u076a\7>\2\2\u076a\u076c\5\u00a4S\2\u076b\u0769\3\2\2\2\u076b\u076c\3"+
		"\2\2\2\u076c\u0773\3\2\2\2\u076d\u0773\5\u00acW\2\u076e\u076f\7\3\2\2"+
		"\u076f\u0770\5x=\2\u0770\u0771\7\4\2\2\u0771\u0773\3\2\2\2\u0772\u0723"+
		"\3\2\2\2\u0772\u0725\3\2\2\2\u0772\u0732\3\2\2\2\u0772\u073e\3\2\2\2\u0772"+
		"\u0745\3\2\2\2\u0772\u0746\3\2\2\2\u0772\u0747\3\2\2\2\u0772\u074b\3\2"+
		"\2\2\u0772\u0755\3\2\2\2\u0772\u0759\3\2\2\2\u0772\u076d\3\2\2\2\u0772"+
		"\u076e\3\2\2\2\u0773\u077e\3\2\2\2\u0774\u0775\f\6\2\2\u0775\u0776\7\7"+
		"\2\2\u0776\u0777\5\u0080A\2\u0777\u0778\7\b\2\2\u0778\u077d\3\2\2\2\u0779"+
		"\u077a\f\4\2\2\u077a\u077b\7\6\2\2\u077b\u077d\5\u00acW\2\u077c\u0774"+
		"\3\2\2\2\u077c\u0779\3\2\2\2\u077d\u0780\3\2\2\2\u077e\u077c\3\2\2\2\u077e"+
		"\u077f\3\2\2\2\u077f\u0083\3\2\2\2\u0780\u077e\3\2\2\2\u0781\u078e\7%"+
		"\2\2\u0782\u078e\5\u008eH\2\u0783\u0784\5\u00acW\2\u0784\u0785\7\u00e6"+
		"\2\2\u0785\u078e\3\2\2\2\u0786\u078e\5\u00b2Z\2\u0787\u078e\5\u008cG\2"+
		"\u0788\u078a\7\u00e6\2\2\u0789\u0788\3\2\2\2\u078a\u078b\3\2\2\2\u078b"+
		"\u0789\3\2\2\2\u078b\u078c\3\2\2\2\u078c\u078e\3\2\2\2\u078d\u0781\3\2"+
		"\2\2\u078d\u0782\3\2\2\2\u078d\u0783\3\2\2\2\u078d\u0786\3\2\2\2\u078d"+
		"\u0787\3\2\2\2\u078d\u0789\3\2\2\2\u078e\u0085\3\2\2\2\u078f\u0790\t\23"+
		"\2\2\u0790\u0087\3\2\2\2\u0791\u0792\t\24\2\2\u0792\u0089\3\2\2\2\u0793"+
		"\u0794\t\25\2\2\u0794\u008b\3\2\2\2\u0795\u0796\t\26\2\2\u0796\u008d\3"+
		"\2\2\2\u0797\u079b\7,\2\2\u0798\u079a\5\u0090I\2\u0799\u0798\3\2\2\2\u079a"+
		"\u079d\3\2\2\2\u079b\u0799\3\2\2\2\u079b\u079c\3\2\2\2\u079c\u008f\3\2"+
		"\2\2\u079d\u079b\3\2\2\2\u079e\u079f\5\u0092J\2\u079f\u07a2\5\u00acW\2"+
		"\u07a0\u07a1\7d\2\2\u07a1\u07a3\5\u00acW\2\u07a2\u07a0\3\2\2\2\u07a2\u07a3"+
		"\3\2\2\2\u07a3\u0091\3\2\2\2\u07a4\u07a6\t\21\2\2\u07a5\u07a4\3\2\2\2"+
		"\u07a5\u07a6\3\2\2\2\u07a6\u07a7\3\2\2\2\u07a7\u07aa\t\r\2\2\u07a8\u07aa"+
		"\7\u00e6\2\2\u07a9\u07a5\3\2\2\2\u07a9\u07a8\3\2\2\2\u07aa\u0093\3\2\2"+
		"\2\u07ab\u07ac\7i\2\2\u07ac\u07ad\7z\2\2\u07ad\u07ae\5\u0094K\2\u07ae"+
		"\u07af\7|\2\2\u07af\u07ce\3\2\2\2\u07b0\u07b1\7j\2\2\u07b1\u07b2\7z\2"+
		"\2\u07b2\u07b3\5\u0094K\2\u07b3\u07b4\7\5\2\2\u07b4\u07b5\5\u0094K\2\u07b5"+
		"\u07b6\7|\2\2\u07b6\u07ce\3\2\2\2\u07b7\u07be\7k\2\2\u07b8\u07ba\7z\2"+
		"\2\u07b9\u07bb\5\u009aN\2\u07ba\u07b9\3\2\2\2\u07ba\u07bb\3\2\2\2\u07bb"+
		"\u07bc\3\2\2\2\u07bc\u07bf\7|\2\2\u07bd\u07bf\7x\2\2\u07be\u07b8\3\2\2"+
		"\2\u07be\u07bd\3\2\2\2\u07bf\u07ce\3\2\2\2\u07c0\u07cb\5\u00acW\2\u07c1"+
		"\u07c2\7\3\2\2\u07c2\u07c7\7\u00eb\2\2\u07c3\u07c4\7\5\2\2\u07c4\u07c6"+
		"\7\u00eb\2\2\u07c5\u07c3\3\2\2\2\u07c6\u07c9\3\2\2\2\u07c7\u07c5\3\2\2"+
		"\2\u07c7\u07c8\3\2\2\2\u07c8\u07ca\3\2\2\2\u07c9\u07c7\3\2\2\2\u07ca\u07cc"+
		"\7\4\2\2\u07cb\u07c1\3\2\2\2\u07cb\u07cc\3\2\2\2\u07cc\u07ce\3\2\2\2\u07cd"+
		"\u07ab\3\2\2\2\u07cd\u07b0\3\2\2\2\u07cd\u07b7\3\2\2\2\u07cd\u07c0\3\2"+
		"\2\2\u07ce\u0095\3\2\2\2\u07cf\u07d4\5\u0098M\2\u07d0\u07d1\7\5\2\2\u07d1"+
		"\u07d3\5\u0098M\2\u07d2\u07d0\3\2\2\2\u07d3\u07d6\3\2\2\2\u07d4\u07d2"+
		"\3\2\2\2\u07d4\u07d5\3\2\2\2\u07d5\u0097\3\2\2\2\u07d6\u07d4\3\2\2\2\u07d7"+
		"\u07d8\5\u00acW\2\u07d8\u07db\5\u0094K\2\u07d9\u07da\7l\2\2\u07da\u07dc"+
		"\7\u00e6\2\2\u07db\u07d9\3\2\2\2\u07db\u07dc\3\2\2\2\u07dc\u0099\3\2\2"+
		"\2\u07dd\u07e2\5\u009cO\2\u07de\u07df\7\5\2\2\u07df\u07e1\5\u009cO\2\u07e0"+
		"\u07de\3\2\2\2\u07e1\u07e4\3\2\2\2\u07e2\u07e0\3\2\2\2\u07e2\u07e3\3\2"+
		"\2\2\u07e3\u009b\3\2\2\2\u07e4\u07e2\3\2\2\2\u07e5\u07e6\5\u00acW\2\u07e6"+
		"\u07e7\7\t\2\2\u07e7\u07ea\5\u0094K\2\u07e8\u07e9\7l\2\2\u07e9\u07eb\7"+
		"\u00e6\2\2\u07ea\u07e8\3\2\2\2\u07ea\u07eb\3\2\2\2\u07eb\u009d\3\2\2\2"+
		"\u07ec\u07ed\7.\2\2\u07ed\u07ee\5x=\2\u07ee\u07ef\7/\2\2\u07ef\u07f0\5"+
		"x=\2\u07f0\u009f\3\2\2\2\u07f1\u07f2\7=\2\2\u07f2\u07f7\5\u00a2R\2\u07f3"+
		"\u07f4\7\5\2\2\u07f4\u07f6\5\u00a2R\2\u07f5\u07f3\3\2\2\2\u07f6\u07f9"+
		"\3\2\2\2\u07f7\u07f5\3\2\2\2\u07f7\u07f8\3\2\2\2\u07f8\u00a1\3\2\2\2\u07f9"+
		"\u07f7\3\2\2\2\u07fa\u07fb\5\u00acW\2\u07fb\u07fc\7\r\2\2\u07fc\u07fd"+
		"\5\u00a4S\2\u07fd\u00a3\3\2\2\2\u07fe\u0829\5\u00acW\2\u07ff\u0822\7\3"+
		"\2\2\u0800\u0801\7\u008e\2\2\u0801\u0802\7\22\2\2\u0802\u0807\5x=\2\u0803"+
		"\u0804\7\5\2\2\u0804\u0806\5x=\2\u0805\u0803\3\2\2\2\u0806\u0809\3\2\2"+
		"\2\u0807\u0805\3\2\2\2\u0807\u0808\3\2\2\2\u0808\u0823\3\2\2\2\u0809\u0807"+
		"\3\2\2\2\u080a\u080b\t\27\2\2\u080b\u080c\7\22\2\2\u080c\u0811\5x=\2\u080d"+
		"\u080e\7\5\2\2\u080e\u0810\5x=\2\u080f\u080d\3\2\2\2\u0810\u0813\3\2\2"+
		"\2\u0811\u080f\3\2\2\2\u0811\u0812\3\2\2\2\u0812\u0815\3\2\2\2\u0813\u0811"+
		"\3\2\2\2\u0814\u080a\3\2\2\2\u0814\u0815\3\2\2\2\u0815\u0820\3\2\2\2\u0816"+
		"\u0817\t\30\2\2\u0817\u0818\7\22\2\2\u0818\u081d\5H%\2\u0819\u081a\7\5"+
		"\2\2\u081a\u081c\5H%\2\u081b\u0819\3\2\2\2\u081c\u081f\3\2\2\2\u081d\u081b"+
		"\3\2\2\2\u081d\u081e\3\2\2\2\u081e\u0821\3\2\2\2\u081f\u081d\3\2\2\2\u0820"+
		"\u0816\3\2\2\2\u0820\u0821\3\2\2\2\u0821\u0823\3\2\2\2\u0822\u0800\3\2"+
		"\2\2\u0822\u0814\3\2\2\2\u0823\u0825\3\2\2\2\u0824\u0826\5\u00a6T\2\u0825"+
		"\u0824\3\2\2\2\u0825\u0826\3\2\2\2\u0826\u0827\3\2\2\2\u0827\u0829\7\4"+
		"\2\2\u0828\u07fe\3\2\2\2\u0828\u07ff\3\2\2\2\u0829\u00a5\3\2\2\2\u082a"+
		"\u082b\7@\2\2\u082b\u083b\5\u00a8U\2\u082c\u082d\7A\2\2\u082d\u083b\5"+
		"\u00a8U\2\u082e\u082f\7@\2\2\u082f\u0830\7!\2\2\u0830\u0831\5\u00a8U\2"+
		"\u0831\u0832\7\34\2\2\u0832\u0833\5\u00a8U\2\u0833\u083b\3\2\2\2\u0834"+
		"\u0835\7A\2\2\u0835\u0836\7!\2\2\u0836\u0837\5\u00a8U\2\u0837\u0838\7"+
		"\34\2\2\u0838\u0839\5\u00a8U\2\u0839\u083b\3\2\2\2\u083a\u082a\3\2\2\2"+
		"\u083a\u082c\3\2\2\2\u083a\u082e\3\2\2\2\u083a\u0834\3\2\2\2\u083b\u00a7"+
		"\3\2\2\2\u083c\u083d\7B\2\2\u083d\u0844\t\31\2\2\u083e\u083f\7E\2\2\u083f"+
		"\u0844\7H\2\2\u0840\u0841\5x=\2\u0841\u0842\t\31\2\2\u0842\u0844\3\2\2"+
		"\2\u0843\u083c\3\2\2\2\u0843\u083e\3\2\2\2\u0843\u0840\3\2\2\2\u0844\u00a9"+
		"\3\2\2\2\u0845\u084a\5\u00acW\2\u0846\u0847\7\6\2\2\u0847\u0849\5\u00ac"+
		"W\2\u0848\u0846\3\2\2\2\u0849\u084c\3\2\2\2\u084a\u0848\3\2\2\2\u084a"+
		"\u084b\3\2\2\2\u084b\u00ab\3\2\2\2\u084c\u084a\3\2\2\2\u084d\u085d\5\u00ae"+
		"X\2\u084e\u085d\7\u00e1\2\2\u084f\u085d\79\2\2\u0850\u085d\7\65\2\2\u0851"+
		"\u085d\7\66\2\2\u0852\u085d\7\67\2\2\u0853\u085d\78\2\2\u0854\u085d\7"+
		":\2\2\u0855\u085d\7\62\2\2\u0856\u085d\7\63\2\2\u0857\u085d\7;\2\2\u0858"+
		"\u085d\7`\2\2\u0859\u085d\7c\2\2\u085a\u085d\7a\2\2\u085b\u085d\7b\2\2"+
		"\u085c\u084d\3\2\2\2\u085c\u084e\3\2\2\2\u085c\u084f\3\2\2\2\u085c\u0850"+
		"\3\2\2\2\u085c\u0851\3\2\2\2\u085c\u0852\3\2\2\2\u085c\u0853\3\2\2\2\u085c"+
		"\u0854\3\2\2\2\u085c\u0855\3\2\2\2\u085c\u0856\3\2\2\2\u085c\u0857\3\2"+
		"\2\2\u085c\u0858\3\2\2\2\u085c\u0859\3\2\2\2\u085c\u085a\3\2\2\2\u085c"+
		"\u085b\3\2\2\2\u085d\u00ad\3\2\2\2\u085e\u0862\7\u00ef\2\2\u085f\u0862"+
		"\5\u00b0Y\2\u0860\u0862\5\u00b4[\2\u0861\u085e\3\2\2\2\u0861\u085f\3\2"+
		"\2\2\u0861\u0860\3\2\2\2\u0862\u00af\3\2\2\2\u0863\u0864\7\u00f0\2\2\u0864"+
		"\u00b1\3\2\2\2\u0865\u0867\7\177\2\2\u0866\u0865\3\2\2\2\u0866\u0867\3"+
		"\2\2\2\u0867\u0868\3\2\2\2\u0868\u0882\7\u00ec\2\2\u0869\u086b\7\177\2"+
		"\2\u086a\u0869\3\2\2\2\u086a\u086b\3\2\2\2\u086b\u086c\3\2\2\2\u086c\u0882"+
		"\7\u00eb\2\2\u086d\u086f\7\177\2\2\u086e\u086d\3\2\2\2\u086e\u086f\3\2"+
		"\2\2\u086f\u0870\3\2\2\2\u0870\u0882\7\u00e7\2\2\u0871\u0873\7\177\2\2"+
		"\u0872\u0871\3\2\2\2\u0872\u0873\3\2\2\2\u0873\u0874\3\2\2\2\u0874\u0882"+
		"\7\u00e8\2\2\u0875\u0877\7\177\2\2\u0876\u0875\3\2\2\2\u0876\u0877\3\2"+
		"\2\2\u0877\u0878\3\2\2\2\u0878\u0882\7\u00e9\2\2\u0879\u087b\7\177\2\2"+
		"\u087a\u0879\3\2\2\2\u087a\u087b\3\2\2\2\u087b\u087c\3\2\2\2\u087c\u0882"+
		"\7\u00ed\2\2\u087d\u087f\7\177\2\2\u087e\u087d\3\2\2\2\u087e\u087f\3\2"+
		"\2\2\u087f\u0880\3\2\2\2\u0880\u0882\7\u00ee\2\2\u0881\u0866\3\2\2\2\u0881"+
		"\u086a\3\2\2\2\u0881\u086e\3\2\2\2\u0881\u0872\3\2\2\2\u0881\u0876\3\2"+
		"\2\2\u0881\u087a\3\2\2\2\u0881\u087e\3\2\2\2\u0882\u00b3\3\2\2\2\u0883"+
		"\u0884\t\32\2\2\u0884\u00b5\3\2\2\2\u012e\u00ca\u00cf\u00d2\u00d7\u00e4"+
		"\u00e8\u00ef\u00f4\u00f9\u00fc\u00ff\u0102\u0109\u010d\u0115\u0118\u011b"+
		"\u011e\u0121\u0124\u0128\u012b\u012e\u0135\u013f\u0147\u015e\u0166\u016e"+
		"\u0174\u0181\u0186\u018f\u0194\u01a4\u01ab\u01af\u01b7\u01be\u01c5\u01d4"+
		"\u01d8\u01de\u01e4\u01e7\u01ea\u01f0\u01f4\u01f8\u01fd\u0201\u0209\u020c"+
		"\u0215\u021a\u0220\u0226\u0232\u0235\u0239\u023e\u0243\u024a\u024d\u0250"+
		"\u0256\u025f\u0267\u026d\u0271\u0275\u0279\u027b\u0284\u028a\u028f\u0292"+
		"\u0296\u0299\u02a2\u02a7\u02ac\u02af\u02b5\u02bd\u02c2\u02c8\u02ce\u02d9"+
		"\u02e1\u02e8\u02f0\u02f3\u02fb\u02ff\u0306\u037a\u0382\u038a\u0393\u039c"+
		"\u03a0\u03a6\u03b2\u03b6\u03b9\u03bf\u03c9\u03d5\u03da\u03e0\u03ec\u03ee"+
		"\u03f3\u03f7\u03f9\u03fd\u0406\u040e\u0415\u041b\u041f\u0428\u042d\u043c"+
		"\u0443\u0446\u044d\u0451\u0457\u045f\u046a\u0475\u047c\u0482\u0488\u0491"+
		"\u0493\u049c\u049f\u04a8\u04ab\u04b4\u04b7\u04c0\u04c3\u04c6\u04ca\u04cd"+
		"\u04d8\u04dd\u04e8\u04ec\u04f0\u04fc\u04ff\u0503\u050d\u0511\u0513\u0516"+
		"\u051a\u051d\u0521\u0525\u0529\u052e\u0531\u0533\u0538\u053d\u0540\u0544"+
		"\u0547\u0549\u0551\u0557\u0561\u0570\u0575\u057d\u0580\u0584\u0589\u0592"+
		"\u0595\u059a\u05a1\u05a4\u05ac\u05b3\u05ba\u05bd\u05c2\u05c8\u05cc\u05cf"+
		"\u05d2\u05dd\u05e2\u05f7\u05f9\u05fb\u0608\u0611\u0618\u0620\u0628\u062c"+
		"\u062f\u0632\u0638\u063b\u063e\u0644\u0647\u064a\u0654\u0657\u065b\u0663"+
		"\u0667\u066b\u066d\u0676\u0682\u0684\u068b\u0692\u0698\u069e\u06a0\u06a5"+
		"\u06ab\u06af\u06b1\u06b8\u06c6\u06ce\u06d0\u06d5\u06d8\u06e0\u06e9\u06ef"+
		"\u06f7\u06fd\u0700\u0706\u071e\u0720\u072a\u072e\u0736\u073a\u0751\u075c"+
		"\u0763\u0766\u076b\u0772\u077c\u077e\u078b\u078d\u079b\u07a2\u07a5\u07a9"+
		"\u07ba\u07be\u07c7\u07cb\u07cd\u07d4\u07db\u07e2\u07ea\u07f7\u0807\u0811"+
		"\u0814\u081d\u0820\u0822\u0825\u0828\u083a\u0843\u084a\u085c\u0861\u0866"+
		"\u086a\u086e\u0872\u0876\u087a\u087e\u0881";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}