package cn.piflow.util;

import cn.piflow.Flow;
import org.apache.flink.client.deployment.ClusterDeploymentException;
import org.apache.flink.client.deployment.ClusterSpecification;
import org.apache.flink.client.deployment.application.ApplicationConfiguration;
import org.apache.flink.client.program.ClusterClient;
import org.apache.flink.client.program.ClusterClientProvider;
import org.apache.flink.configuration.*;
import org.apache.flink.yarn.YarnClientYarnClusterInformationRetriever;
import org.apache.flink.yarn.YarnClusterDescriptor;
import org.apache.flink.yarn.YarnClusterInformationRetriever;
import org.apache.flink.yarn.configuration.YarnConfigOptions;
import org.apache.flink.yarn.configuration.YarnDeploymentTarget;

import org.apache.hadoop.fs.Path;
import org.apache.hadoop.yarn.api.records.ApplicationId;
import org.apache.hadoop.yarn.client.api.YarnClient;
import org.apache.hadoop.yarn.conf.YarnConfiguration;

import java.sql.Date;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import static org.apache.flink.configuration.JobManagerOptions.TOTAL_PROCESS_MEMORY;
import static org.apache.flink.configuration.MemorySize.MemoryUnit.MEGA_BYTES;
import  org.apache.hadoop.fs.FSOutputSummer;

public class FlinkYarnClusterLauncher {
    public static String launch(Flow flow) {

        String flowFileName = flow.getFlowName() ;
        String flowFile = FlowFileUtil.getFlowFilePath(flowFileName);
        FileUtil.writeFile(flow.getFlowJson(), flowFile);

        //flink的本地配置目录，为了得到flink的配置
        String configurationDirectory = "/data/flink-1.12.2/conf";
        //存放flink集群相关的jar包目录
        String flinkLibs = PropertyUtil.getPropertyValue("fs.defaultFS") + "/user/flink/lib";
        //用户jar
        String userJarPath = PropertyUtil.getPropertyValue("fs.defaultFS") + "/user/flink/piflow-server-0.9.jar";
        //String userJarPath = "file://" + ConfigureUtil.getPiFlowBundlePath().replace("\\","/");

        //用户依赖的jar
        //String flinkDistJar = "hdfs://dev-ct6-dc-master01:8020/flink/flink-yarn_2.11-1.11.0.jar";
        String flinkDistJar = PropertyUtil.getPropertyValue("fs.defaultFS") + "/user/flink/flink-yarn_2.11-1.12.2.jar";

                YarnClient yarnClient = YarnClient.createYarnClient();
        org.apache.hadoop.conf.Configuration entries = new org.apache.hadoop.conf.Configuration();
        //entries.addResource(new Path("/data/hadoop-2.6.0/etc/hadoop/core-site.xml"));
        //entries.addResource(new Path("/data/hadoop-2.6.0/etc/hadoop/hdfs-site.xml"));
        //entries.addResource(new Path("/data/hadoop-2.6.0/etc/hadoop/yarn-site.xml"));
        entries.set("yarn.resourcemanager.hostname",  PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname"));
        entries.set("fs.defaultFS",PropertyUtil.getPropertyValue("fs.defaultFS"));
        YarnConfiguration yarnConfiguration = new YarnConfiguration(entries);


        yarnClient.init(yarnConfiguration);
        yarnClient.start();

        YarnClusterInformationRetriever clusterInformationRetriever = YarnClientYarnClusterInformationRetriever
                .create(yarnClient);

        //获取flink的配置
        Configuration flinkConfiguration = GlobalConfiguration.loadConfiguration(
                configurationDirectory);
        flinkConfiguration.set(CheckpointingOptions.INCREMENTAL_CHECKPOINTS, true);
        flinkConfiguration.set(
                PipelineOptions.JARS,
                Collections.singletonList(
                        userJarPath));

        Path remoteLib = new Path(flinkLibs);
        flinkConfiguration.set(
                YarnConfigOptions.PROVIDED_LIB_DIRS,
                Collections.singletonList(remoteLib.toString()));

        flinkConfiguration.set(
                YarnConfigOptions.FLINK_DIST_JAR,
                flinkDistJar);

        List<String> shipFiles = new ArrayList<String>();
        shipFiles.add(flowFile);
        flinkConfiguration.set(
                YarnConfigOptions.SHIP_FILES,shipFiles);

        //设置为application模式
        flinkConfiguration.set(
                DeploymentOptions.TARGET,
                YarnDeploymentTarget.APPLICATION.getName());

        //yarn application name
        flinkConfiguration.set(YarnConfigOptions.APPLICATION_NAME, flow.getFlowName());

        flinkConfiguration.set(JobManagerOptions.TOTAL_PROCESS_MEMORY, MemorySize.parse("1024", MEGA_BYTES));
        flinkConfiguration.set(TaskManagerOptions.TOTAL_PROCESS_MEMORY, MemorySize.parse("1024", MEGA_BYTES));

        ClusterSpecification clusterSpecification = new ClusterSpecification.ClusterSpecificationBuilder()
                .createClusterSpecification();

        //设置用户jar的参数和主类
        String [] args = {flow.getFlowName()};
        String applicationClassName = "cn.piflow.api.StartFlinkFlowMain";
        ApplicationConfiguration appConfig = new ApplicationConfiguration(args, applicationClassName);

        YarnClusterDescriptor yarnClusterDescriptor = new YarnClusterDescriptor(
                flinkConfiguration,
                yarnConfiguration,
                yarnClient,
                clusterInformationRetriever,
                true);
        ClusterClientProvider<ApplicationId> clusterClientProvider = null;
        try {
            clusterClientProvider = yarnClusterDescriptor.deployApplicationCluster(
                    clusterSpecification,
                    appConfig);
        } catch (ClusterDeploymentException e) {
            e.printStackTrace();
        }

        ClusterClient<ApplicationId> clusterClient = clusterClientProvider.getClusterClient();
        ApplicationId applicationId = clusterClient.getClusterId();
        System.out.println(applicationId);
        return applicationId.toString();
    }
}