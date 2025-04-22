package cn.piflow.util;

import org.apache.arrow.vector.VectorSchemaRoot;
import org.apache.arrow.vector.ipc.ArrowFileReader;
import org.apache.arrow.vector.ipc.ArrowFileWriter;
import org.apache.arrow.vector.types.pojo.Schema;
import org.apache.spark.api.java.function.FlatMapFunction;
import org.apache.spark.sql.*;
import org.apache.spark.api.java.function.MapFunction;
import java.util.*;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.types.StructType;
import scala.Function1;
import scala.collection.TraversableOnce;

//public class SciDataFrame implements Iterable<SciDataFrame> {
public class SciDataFrame {
    public enum Level { FOLDER, FILE }
    public enum FileFormat {
        TEXT, JSON, PARQUET;
        public String getFormatString() {
            return this.name().toLowerCase();
        }
    }

    // Fields
    private UUID id;
    private List<Map<String, Object>> schema;
    private Long nbytes;
    private VectorSchemaRoot data;
    private Dataset<Row> df_data;
    private Integer batchSize;
//    private Client client;
    private int counter;
    private ArrowFileReader reader;
    private Level level;
    private String datasetId;
    private Boolean isIterate;
    private Map<String, Object> loadKwargs;





    public SciDataFrame(Dataset<Row> dataFrame) {
        this.df_data = dataFrame;
    }


    // Constructor (Builder 模式处理复杂参数)
    public static class Builder {
        private String datasetId;
        private List<Map<String, Object>> schema;
        private Long nbytes;
        private Level level = Level.FOLDER;
        private VectorSchemaRoot data;
        private Integer batchSize;
//        private Client client = new Client("127.0.0.1", 8815); // 默认客户端
        private Boolean isIterate;
        private Map<String, Object> loadKwargs = new HashMap<>();

        public Builder datasetId(String id) { this.datasetId = id; return this; }
        public Builder schema(List<Map<String, Object>> s) { this.schema = s; return this; }
        // 其他参数类似...

//        public SciDataFrame build() {
//            return new SciDataFrame(this);
//        }
    }



    public void setSparkDf(Dataset<Row> df){
        this.df_data = df;
    }

    public Dataset<Row> getSparkDf(){
        return df_data;
    }

    public void show(){
        df_data.show();
    }
    // 显示指定行数
    public void show(int numRows) {
        df_data.show(numRows);
    }
    // 显示指定行数，并控制字符串截断
    public void show(int numRows, boolean truncate) {
        df_data.show(numRows, truncate);
    }
    // 显示全部行（谨慎使用！）
    public void showAll(boolean truncate) {
        long totalRows = df_data.count();
        df_data.show((int) totalRows, truncate);

    }
    public void save(String path, String format) {
        df_data.write().format(format).save(path);

    }

    public void write(SaveMode saveMode, String url, String dbtable, Properties props) {
        df_data.write().mode(saveMode).jdbc(url, dbtable, props);
    }

    public StructType getSchema() {
        return df_data.schema();
    }

    public <U> SciDataFrame map(MapFunction<Row, U> mapFunction, Encoder<U> encoder){
        Dataset<U> mappedDataset = df_data.map(mapFunction, encoder);
        Dataset<Row> resultDF = mappedDataset.toDF();
        return new SciDataFrame(resultDF);
    }

    public <U> SciDataFrame flatMap(FlatMapFunction<Row, U> flatMapFunction, Encoder<U> encoder){
        Dataset<U> flatMappedDataset = df_data.flatMap(flatMapFunction, encoder);
        return new SciDataFrame(flatMappedDataset.toDF());
    }
    public <U> SciDataFrame flatMap(Function1<Row, TraversableOnce<U>> flatMapFunction, Encoder<U> encoder){
        Dataset<U> flatMappedDataset = df_data.flatMap(flatMapFunction, encoder);
        return new SciDataFrame(flatMappedDataset.toDF());
    }

//    private SciDataFrame(Builder builder) {
//        this.id = UUID.randomUUID();
//        this.datasetId = builder.datasetId;
//        this.schema = builder.schema;
//        this.nbytes = builder.nbytes;
//        this.data = builder.data;
//        this.batchSize = builder.batchSize;
////        this.client = builder.client;
//        this.level = builder.level;
//        this.isIterate = builder.isIterate;
//        this.loadKwargs = builder.loadKwargs;
//    }
    // 实现迭代器接口
//    @Override
//    public Iterator<SciDataFrame> iterator() {
//        if (!isIterate) {
//            throw new UnsupportedOperationException("Batch iteration not enabled");
//        }
//        return new Iterator<>() {
//            @Override
//            public boolean hasNext() {
//                return reader.hasNext();
//            }
//
//            @Override
//            public SciDataFrame next() {
////                VectorSchemaRoot batch = reader.next();
////                return new SciDataFrame.Builder()
////                        .datasetId(datasetId)
////                        .data(batch)
//            }
//        };

    // 流式数据处理初始化
//    public void flatOpen(String paths) {
//        try {
//            this.client.loadInit(loadKwargs);
//            this.reader = client.flatOpen(isPathsFile(paths));
//            if (!isIterate) {
//                this.data = readAllBatches(reader);
//            }
//        } catch (Exception e) {
//            throw new RuntimeException("Flat open failed", e);
//        }
//    }

//    private VectorSchemaRoot readAllBatches(ArrowFileReader reader) {
//        VectorSchemaRoot result = null;
//        while (reader.hasNext()) {
//            VectorSchemaRoot batch = reader.next();
//            if (result == null) {
//                result = VectorSchemaRoot.create(batch.getSchema(), new RootAllocator());
//            }
//            // 合并 batches 到 result（需实现具体合并逻辑）
//        }
//        return result;
//    }
    private Level isPathsFile(String paths) {
        return paths.split(",").length == 1 ? Level.FILE : Level.FOLDER;
    }

}
