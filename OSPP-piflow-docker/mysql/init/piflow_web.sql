/*
 Navicat Premium Data Transfer

 Source Server         : hausen1012.caoaman.cn
 Source Server Type    : MySQL
 Source Server Version : 50735
 Source Host           : hausen1012.caoaman.cn:38060
 Source Schema         : piflow_web

 Target Server Type    : MySQL
 Target Server Version : 50735
 File Encoding         : 65001

 Date: 03/09/2022 18:38:25
*/

CREATE DATABASE piflow_web;
USE piflow_web;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for FLOW_STOPS_TEMPLATE_MANAGE
-- ----------------------------
DROP TABLE IF EXISTS `FLOW_STOPS_TEMPLATE_MANAGE`;
CREATE TABLE `FLOW_STOPS_TEMPLATE_MANAGE`  (
  `ID` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `CRT_DTTM` datetime(0) NOT NULL COMMENT 'Create date time',
  `CRT_USER` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `ENABLE_FLAG` bit(1) NOT NULL COMMENT 'Enable flag',
  `LAST_UPDATE_DTTM` datetime(0) NOT NULL COMMENT 'Last update date time',
  `LAST_UPDATE_USER` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `VERSION` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `BUNDLE` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'bundle',
  `STOPS_GROUPS` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'groups name',
  `IS_SHOW` bit(1) NULL DEFAULT NULL COMMENT 'is show',
  PRIMARY KEY (`ID`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of FLOW_STOPS_TEMPLATE_MANAGE
-- ----------------------------

-- ----------------------------
-- Table structure for association_global_params_flow
-- ----------------------------
DROP TABLE IF EXISTS `association_global_params_flow`;
CREATE TABLE `association_global_params_flow`  (
  `global_params_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'FLOW_GLOBAL_PARAMS primary key id',
  `flow_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'FLOW primary key id',
  `process_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'process primary key id',
  INDEX `FK22rp96r4290eons0000000003`(`global_params_id`) USING BTREE,
  CONSTRAINT `FK22rp96r4290eons0000000003` FOREIGN KEY (`global_params_id`) REFERENCES `flow_global_params` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of association_global_params_flow
-- ----------------------------

-- ----------------------------
-- Table structure for association_groups_stops_template
-- ----------------------------
DROP TABLE IF EXISTS `association_groups_stops_template`;
CREATE TABLE `association_groups_stops_template`  (
  `groups_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `stops_template_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  INDEX `FKqwv1iytgkhhgnjdvhqbskncf4`(`stops_template_id`) USING BTREE,
  INDEX `FK5ceurc1karlogl9ppecmkcp7e`(`groups_id`) USING BTREE,
  CONSTRAINT `FK5ceurc1karlogl9ppecmkcp7e` FOREIGN KEY (`groups_id`) REFERENCES `flow_stops_groups` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FKqwv1iytgkhhgnjdvhqbskncf4` FOREIGN KEY (`stops_template_id`) REFERENCES `flow_stops_template` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of association_groups_stops_template
-- ----------------------------

-- ----------------------------
-- Table structure for code_snippet
-- ----------------------------
DROP TABLE IF EXISTS `code_snippet`;
CREATE TABLE `code_snippet`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `fk_note_book_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'fk node_book id',
  `execute_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'execute code id',
  `code_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'code content',
  `code_snippet_sort` bigint(20) NULL DEFAULT NULL COMMENT 'soft',
  INDEX `FK22rp96r4290eons0000000002`(`fk_note_book_id`) USING BTREE,
  CONSTRAINT `FK22rp96r4290eons0000000002` FOREIGN KEY (`fk_note_book_id`) REFERENCES `note_book` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of code_snippet
-- ----------------------------

-- ----------------------------
-- Table structure for data_source
-- ----------------------------
DROP TABLE IF EXISTS `data_source`;
CREATE TABLE `data_source`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `data_source_description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'dataSourceDescription',
  `data_source_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'dataSourceName',
  `data_source_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'dataSourceType',
  `is_template` bit(1) NULL DEFAULT NULL COMMENT 'isTemplate',
  `stops_template_bundle` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKqwv1iytgkhhgnjdvhqbsknas6`(`stops_template_bundle`) USING BTREE,
  CONSTRAINT `FKqwv1iytgkhhgnjdvhqbsknas6` FOREIGN KEY (`stops_template_bundle`) REFERENCES `flow_stops_template` (`bundel`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of data_source
-- ----------------------------
INSERT INTO `data_source` VALUES ('05ce8a4f0ef942098b5bd5610ff8f181', '2019-11-21 00:00:01', 'system', b'1', '2019-11-21 00:00:01', 'Admin', 0, NULL, 'FTP', 'FTP', b'1', NULL);
INSERT INTO `data_source` VALUES ('342a4d45f8f2468194d88ee50ae4cab9', '2019-11-21 00:00:02', 'system', b'1', '2019-11-21 00:00:02', 'Admin', 0, NULL, 'Redis', 'Redis', b'1', NULL);
INSERT INTO `data_source` VALUES ('4776ca565a6542259c17962869538f0c', '2019-11-21 00:00:03', 'system', b'1', '2019-11-21 00:00:03', 'Admin', 0, NULL, 'MongoDB', 'MongoDB', b'1', NULL);
INSERT INTO `data_source` VALUES ('49aeba77472f43bba6245f22723619bf', '2019-11-21 00:00:04', 'system', b'1', '2019-11-21 00:00:04', 'Admin', 0, NULL, 'ElasticSearch', 'ElasticSearch', b'1', NULL);
INSERT INTO `data_source` VALUES ('a9aa6416c43d11ec95bdc8000a005a9b', '2022-09-03 10:38:09', 'system', b'1', '2022-09-03 10:38:09', 'Admin', 0, NULL, 'STOP', 'STOP', b'1', NULL);
INSERT INTO `data_source` VALUES ('abe3113ce02d422aba70e9588ebdfff3', '2019-11-21 00:00:05', 'system', b'1', '2019-11-21 00:00:05', 'Admin', 0, NULL, 'JDBC', 'JDBC', b'1', NULL);

-- ----------------------------
-- Table structure for data_source_property
-- ----------------------------
DROP TABLE IF EXISTS `data_source_property`;
CREATE TABLE `data_source_property`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'name',
  `value` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'value',
  `fk_data_source_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKmu1sbq6pael97442xi5bwdmu0`(`fk_data_source_id`) USING BTREE,
  CONSTRAINT `FKmu1sbq6pael97442xi5bwdmu0` FOREIGN KEY (`fk_data_source_id`) REFERENCES `data_source` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of data_source_property
-- ----------------------------
INSERT INTO `data_source_property` VALUES ('18eff61306a349718dce9c0c6988c8b8', '2019-11-21 00:00:05', 'Admin', b'1', '2019-11-21 00:00:05', 'system', 0, NULL, 'host', NULL, '342a4d45f8f2468194d88ee50ae4cab9');
INSERT INTO `data_source_property` VALUES ('2cf157b6cb05464794cf40d3d9156409', '2019-11-21 00:00:14', 'Admin', b'1', '2019-11-21 00:00:14', 'system', 0, NULL, 'url', NULL, 'abe3113ce02d422aba70e9588ebdfff3');
INSERT INTO `data_source_property` VALUES ('2f2e9d19240a458791282c6eee633f62', '2019-11-21 00:00:01', 'Admin', b'1', '2019-11-21 00:00:01', 'system', 0, NULL, 'url', NULL, '05ce8a4f0ef942098b5bd5610ff8f181');
INSERT INTO `data_source_property` VALUES ('363fa8f831d5410db31e1c15bf74b229', '2019-11-21 00:00:03', 'Admin', b'1', '2019-11-21 00:00:03', 'system', 0, NULL, 'username', NULL, '05ce8a4f0ef942098b5bd5610ff8f181');
INSERT INTO `data_source_property` VALUES ('45b3fd29b8fd45be8c87498c1d764406', '2019-11-21 00:00:02', 'Admin', b'1', '2019-11-21 00:00:02', 'system', 0, NULL, 'port', NULL, '05ce8a4f0ef942098b5bd5610ff8f181');
INSERT INTO `data_source_property` VALUES ('5b88aff65a674814a983b955df2404bf', '2019-11-21 00:00:07', 'Admin', b'1', '2019-11-21 00:00:07', 'system', 0, NULL, 'password', NULL, '342a4d45f8f2468194d88ee50ae4cab9');
INSERT INTO `data_source_property` VALUES ('5f297c6968ca4ba884479b1a43b82198', '2019-11-21 00:00:10', 'Admin', b'1', '2019-11-21 00:00:10', 'system', 0, NULL, 'es_nodes', NULL, '49aeba77472f43bba6245f22723619bf');
INSERT INTO `data_source_property` VALUES ('8516d28f43884252886e908126778ef0', '2019-11-21 00:00:06', 'Admin', b'1', '2019-11-21 00:00:06', 'system', 0, NULL, 'port', NULL, '342a4d45f8f2468194d88ee50ae4cab9');
INSERT INTO `data_source_property` VALUES ('8d1b0acee4be46788ca552b2040b90fc', '2019-11-21 00:00:11', 'Admin', b'1', '2019-11-21 00:00:11', 'system', 0, NULL, 'es_type', NULL, '49aeba77472f43bba6245f22723619bf');
INSERT INTO `data_source_property` VALUES ('947c4d47518c4863b8651cf3d604f4f1', '2019-11-21 00:00:16', 'Admin', b'1', '2019-11-21 00:00:16', 'system', 0, NULL, 'user', NULL, 'abe3113ce02d422aba70e9588ebdfff3');
INSERT INTO `data_source_property` VALUES ('968c061007fa4216b9a0b05d8d68bf2c', '2019-11-21 00:00:12', 'Admin', b'1', '2019-11-21 00:00:12', 'system', 0, NULL, 'es_port', NULL, '49aeba77472f43bba6245f22723619bf');
INSERT INTO `data_source_property` VALUES ('b6463d34ad234a38badfa82d324dcc78', '2019-11-21 00:00:15', 'Admin', b'1', '2019-11-21 00:00:15', 'system', 0, NULL, 'driver', NULL, 'abe3113ce02d422aba70e9588ebdfff3');
INSERT INTO `data_source_property` VALUES ('c72ecaebaaad4ef08a5279f6713f107f', '2019-11-21 00:00:04', 'Admin', b'1', '2019-11-21 00:00:04', 'system', 0, NULL, 'password', NULL, '05ce8a4f0ef942098b5bd5610ff8f181');
INSERT INTO `data_source_property` VALUES ('d28fe75ea4464261b15b9294b82bcb52', '2019-11-21 00:00:08', 'Admin', b'1', '2019-11-21 00:00:08', 'system', 0, NULL, 'address', NULL, '4776ca565a6542259c17962869538f0c');
INSERT INTO `data_source_property` VALUES ('e68116bc9c6c4ebcbfa7e8fb322349f7', '2019-11-21 00:00:09', 'Admin', b'1', '2019-11-21 00:00:09', 'system', 0, NULL, 'database', NULL, '4776ca565a6542259c17962869538f0c');
INSERT INTO `data_source_property` VALUES ('e85bc1643a5e429da693caf461e8f5cd', '2019-11-21 00:00:17', 'Admin', b'1', '2019-11-21 00:00:17', 'system', 0, NULL, 'password', NULL, 'abe3113ce02d422aba70e9588ebdfff3');
INSERT INTO `data_source_property` VALUES ('f386627bb0734ef9a59c0316d4bd7ab7', '2019-11-21 00:00:13', 'Admin', b'1', '2019-11-21 00:00:13', 'system', 0, NULL, 'es_index', NULL, '49aeba77472f43bba6245f22723619bf');

-- ----------------------------
-- Table structure for flow
-- ----------------------------
DROP TABLE IF EXISTS `flow`;
CREATE TABLE `flow`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `driver_memory` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `executor_cores` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `executor_memory` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `executor_number` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_example` bit(1) NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `uuid` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK3e62cxjsjbtola3f8hcp1my1o`(`fk_flow_group_id`) USING BTREE,
  CONSTRAINT `FK3e62cxjsjbtola3f8hcp1my1o` FOREIGN KEY (`fk_flow_group_id`) REFERENCES `flow_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow
-- ----------------------------
INSERT INTO `flow` VALUES ('0641076d5ae840c09d2be5b71fw00001', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'FlowExample', '1g', '1', '1g', '1', b'1', 'FlowExample', '0641076d5ae840c09d2be5b71fw00001', NULL, NULL);
INSERT INTO `flow` VALUES ('0c4fdee973824a999e1569770677c020', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'parse xml and csv file， and put data into csv、json and hive table', '1g', '1', '1g', '1', b'1', 'Example1', '0c4fdee973824a999e1569770677c020', NULL, NULL);
INSERT INTO `flow` VALUES ('c9c77d24b65942fb9665fbdbe8710236', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'dblp parser', '4g', '6', '4g', '3', b'1', 'Example2', 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL);

-- ----------------------------
-- Table structure for flow_global_params
-- ----------------------------
DROP TABLE IF EXISTS `flow_global_params`;
CREATE TABLE `flow_global_params`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'name',
  `type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'type',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'content',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_global_params
-- ----------------------------

-- ----------------------------
-- Table structure for flow_group
-- ----------------------------
DROP TABLE IF EXISTS `flow_group`;
CREATE TABLE `flow_group`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `is_example` bit(1) NULL DEFAULT NULL COMMENT 'isExample',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'flow name',
  `uuid` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'flow uuid',
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKe1i6t5gnt6ys4yqkt5uumr20w`(`fk_flow_group_id`) USING BTREE,
  CONSTRAINT `FKe1i6t5gnt6ys4yqkt5uumr20w` FOREIGN KEY (`fk_flow_group_id`) REFERENCES `flow_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_group
-- ----------------------------

-- ----------------------------
-- Table structure for flow_group_path
-- ----------------------------
DROP TABLE IF EXISTS `flow_group_path`;
CREATE TABLE `flow_group_path`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `filter_condition` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_from` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'line from',
  `line_inport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'line in port',
  `line_outport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'line out port',
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_to` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'line to',
  `fk_flow_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKluqls1o7ynyiinor8ttdc6wdd`(`fk_flow_group_id`) USING BTREE,
  CONSTRAINT `FKluqls1o7ynyiinor8ttdc6wdd` FOREIGN KEY (`fk_flow_group_id`) REFERENCES `flow_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_group_path
-- ----------------------------

-- ----------------------------
-- Table structure for flow_group_template
-- ----------------------------
DROP TABLE IF EXISTS `flow_group_template`;
CREATE TABLE `flow_group_template`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `description` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'description',
  `flow_group_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `path` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `template_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'template type',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_group_template
-- ----------------------------

-- ----------------------------
-- Table structure for flow_path
-- ----------------------------
DROP TABLE IF EXISTS `flow_path`;
CREATE TABLE `flow_path`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `line_from` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_inport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_outport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_to` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `filter_condition` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK33rp96r4290eonsirbwrp8h0f`(`fk_flow_id`) USING BTREE,
  CONSTRAINT `FK33rp96r4290eonsirbwrp8h0f` FOREIGN KEY (`fk_flow_id`) REFERENCES `flow` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_path
-- ----------------------------
INSERT INTO `flow_path` VALUES ('0b5605f63e604a19a0e5e220a9af71fa', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '56', '', '', '111', '65', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('0c9f3b992fc84dcb90ec095447a01d09', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '90', '', '', '108', '68', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('15d8e9957ceb4b60aec7fb6410902203', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '91', '', '', '94', '73', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('1bf7780230ef4541a5952c7a417527fd', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '55', '', '', '95', '58', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('21e1acf9318e4551ac9b70d2f9691306', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '68', '', '', '109', '62', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('223efd6969064a148993a50a08683669', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '87', '', '', '115', '54', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('2dbf623b76954923bc8159476f2afd5c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out6', '127', '70', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('314bb51706c54cb2988bb5f10b9661db', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '59', '', '', '103', '69', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('34201996af3f49798a56205b728b502b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '76', '', '', '116', '88', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('3a0514688eef4344bd3eac5bfd92d444', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '71', '', '', '114', '87', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('46c79bf07c7049ed90caa6f0d1b2d967', '2022-09-03 10:35:56', 'Add', b'1', '2022-09-03 10:35:56', 'admin', 0, '5', 'data2', '', '8', '6', '0c4fdee973824a999e1569770677c020', NULL);
INSERT INTO `flow_path` VALUES ('4da1ea3f8b2f4fddb1d8ce6a11191a0e', '2022-09-03 10:35:56', 'Add', b'1', '2022-09-03 10:35:56', 'admin', 0, '9', '', 'out2', '14', '13', '0c4fdee973824a999e1569770677c020', NULL);
INSERT INTO `flow_path` VALUES ('576473d056a4400fb9b192097c6c9fd3', '2022-09-03 10:35:56', 'Add', b'1', '2022-09-03 10:35:56', 'admin', 0, '2', '', '', '4', '3', '0c4fdee973824a999e1569770677c020', NULL);
INSERT INTO `flow_path` VALUES ('5e3a2eb78e5f4233a7ad220a11f41803', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out3', '124', '60', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('60e600f9428846f2974d11f1b5df4620', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '72', '', '', '97', '50', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('6b13ac7587a1484db1eddb88f11d04ef', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '58', '', '', '96', '72', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('70056f79546844bda306c120ddc00c03', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '64', '', '', '63', '85', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('716706037a17452cbd24e275b648710a', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '74', '', '', '100', '48', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('786bd0df22b3411097a8aaa0017e9d19', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '67', '', '', '92', '57', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('7b1eabcf60a24947952ce6c538f13ab6', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out5', '126', '89', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('84e444bdcf424174b7d0748c0a438d19', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out4', '125', '59', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('854018f885b44a58a2339cf67cfbfe38', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out8', '129', '76', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('963fd72b32f3467281991c53092fa5a2', '2022-09-03 10:35:56', 'Add', b'1', '2022-09-03 10:35:56', 'admin', 0, '3', 'data1', '', '7', '6', '0c4fdee973824a999e1569770677c020', NULL);
INSERT INTO `flow_path` VALUES ('9d3ccb6a1a7e492ab27fa6efd524b201', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '49', '', '', '113', '71', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('a4e9d2e5a4ee4752960b82064e1b68d3', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '70', '', '', '110', '56', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('a61c0fb13904426197e2b90a53b4566f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '57', '', '', '93', '91', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('b40c0e8141b448c9af5d9c9dbfd56f1c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '75', '', '', '118', '51', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('c1d2e3c089814540be4b8594038a6fce', '2022-09-03 10:35:56', 'Add', b'1', '2022-09-03 10:35:56', 'admin', 0, '9', '', 'out1', '12', '11', '0c4fdee973824a999e1569770677c020', NULL);
INSERT INTO `flow_path` VALUES ('c6061804303040fcaab299e7cdfc3468', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '65', '', '', '112', '86', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('cc3a064ef7b84bb9b47b37d5992634af', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '69', '', '', '104', '52', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('cdf235f656cf44bbb7dd201bd1fb2f6b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '66', '', '', '99', '74', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('d32d1ec7083d4d739a5ccdc43c9ed3b1', '2022-09-03 10:35:56', 'Add', b'1', '2022-09-03 10:35:56', 'admin', 0, '6', '', '', '10', '9', '0c4fdee973824a999e1569770677c020', NULL);
INSERT INTO `flow_path` VALUES ('dc167a7e5a1a4a8a8a14aa565cb45897', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '60', '', '', '98', '66', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('e3ac5b6d115b47e4963cca435c9bdae8', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '130', '', '', '138', '64', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('e5a76b801b1d479fb16cb2fe758c2d54', '2022-09-03 10:35:56', 'Add', b'1', '2022-09-03 10:35:56', 'admin', 0, '9', '', 'out3', '16', '15', '0c4fdee973824a999e1569770677c020', NULL);
INSERT INTO `flow_path` VALUES ('e5f05c582ac64f9ab4e1ac342038c386', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '89', '', '', '106', '90', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('e711832415814a87b402fbdaf950a271', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out2', '123', '55', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('f0e344c7b01c45888dfa459f10bb575d', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out1', '122', '67', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('f2f5be9e4f3d4915969e1fe5d98bdd0f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '52', '', '', '105', '61', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('f823c458b74b45e183c117407a9f607c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '88', '', '', '117', '75', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('fb38e3746a0545a099953c1e6d31a432', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '85', '', 'out7', '128', '49', 'c9c77d24b65942fb9665fbdbe8710236', NULL);
INSERT INTO `flow_path` VALUES ('ff808181725b0c8201725b0dc95e0000', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, '11', NULL, NULL, '54', '15', '0641076d5ae840c09d2be5b71fw00001', NULL);
INSERT INTO `flow_path` VALUES ('ff808181725b0c8201725b0dc9680001', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, '20', NULL, 'out3', '53', '24', '0641076d5ae840c09d2be5b71fw00001', NULL);
INSERT INTO `flow_path` VALUES ('ff808181725b0c8201725b0dc9680002', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, '20', NULL, 'out2', '51', '26', '0641076d5ae840c09d2be5b71fw00001', NULL);
INSERT INTO `flow_path` VALUES ('ff808181725b0c8201725b0dc96a0003', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, '20', NULL, 'out1', '50', '22', '0641076d5ae840c09d2be5b71fw00001', NULL);
INSERT INTO `flow_path` VALUES ('ff808181725b0c8201725b0dc96a0004', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, '17', NULL, NULL, '49', '20', '0641076d5ae840c09d2be5b71fw00001', NULL);
INSERT INTO `flow_path` VALUES ('ff808181725b0c8201725b0dc96a0005', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, '6', 'data1', NULL, '48', '17', '0641076d5ae840c09d2be5b71fw00001', NULL);
INSERT INTO `flow_path` VALUES ('ff808181725b0c8201725b0dc96b0006', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, '15', 'data2', NULL, '47', '17', '0641076d5ae840c09d2be5b71fw00001', NULL);

-- ----------------------------
-- Table structure for flow_process
-- ----------------------------
DROP TABLE IF EXISTS `flow_process`;
CREATE TABLE `flow_process`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `app_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'The id returned when calling runProcess',
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `driver_memory` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `end_time` datetime(0) NULL DEFAULT NULL COMMENT 'End time of the process',
  `executor_cores` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `executor_memory` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `executor_number` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `flow_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'flowId',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process name',
  `parent_process_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'third parentProcessId',
  `process_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'third processId',
  `progress` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process progress',
  `start_time` datetime(0) NULL DEFAULT NULL COMMENT 'Process startup time',
  `state` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process status',
  `view_xml` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Process view xml string',
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_process_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `run_mode_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process RunModeType',
  `process_parent_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process parent type',
  `fk_group_schedule_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKgvr5o5p4n6dbfx010h7wbjgku`(`fk_flow_process_group_id`) USING BTREE,
  CONSTRAINT `FKgvr5o5p4n6dbfx010h7wbjgku` FOREIGN KEY (`fk_flow_process_group_id`) REFERENCES `flow_process_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_process
-- ----------------------------

-- ----------------------------
-- Table structure for flow_process_group
-- ----------------------------
DROP TABLE IF EXISTS `flow_process_group`;
CREATE TABLE `flow_process_group`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `app_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'The id returned when calling runProcess',
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `end_time` datetime(0) NULL DEFAULT NULL COMMENT 'End time of the process',
  `flow_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'flowId',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process name',
  `parent_process_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'third parentProcessId',
  `process_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'third processId',
  `progress` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process progress',
  `run_mode_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process RunModeType',
  `start_time` datetime(0) NULL DEFAULT NULL COMMENT 'Process startup time',
  `state` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process status',
  `view_xml` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Process view xml string',
  `process_parent_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Process parent type',
  `fk_flow_process_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKpxf1rth8fs0pld3jlvigkaf2y`(`fk_flow_process_group_id`) USING BTREE,
  CONSTRAINT `FKpxf1rth8fs0pld3jlvigkaf2y` FOREIGN KEY (`fk_flow_process_group_id`) REFERENCES `flow_process_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_process_group
-- ----------------------------

-- ----------------------------
-- Table structure for flow_process_group_path
-- ----------------------------
DROP TABLE IF EXISTS `flow_process_group_path`;
CREATE TABLE `flow_process_group_path`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `line_from` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_inport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_outport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_to` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_process_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKirc18h7dj5ti11wlnifjwiyyh`(`fk_flow_process_group_id`) USING BTREE,
  CONSTRAINT `FKirc18h7dj5ti11wlnifjwiyyh` FOREIGN KEY (`fk_flow_process_group_id`) REFERENCES `flow_process_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_process_group_path
-- ----------------------------

-- ----------------------------
-- Table structure for flow_process_path
-- ----------------------------
DROP TABLE IF EXISTS `flow_process_path`;
CREATE TABLE `flow_process_path`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `line_from` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_inport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_outport` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `line_to` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_process_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKad4n0sl8j977awtec5beyrphy`(`fk_flow_process_id`) USING BTREE,
  CONSTRAINT `FKad4n0sl8j977awtec5beyrphy` FOREIGN KEY (`fk_flow_process_id`) REFERENCES `flow_process` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_process_path
-- ----------------------------

-- ----------------------------
-- Table structure for flow_process_stop
-- ----------------------------
DROP TABLE IF EXISTS `flow_process_stop`;
CREATE TABLE `flow_process_stop`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `bundel` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `end_time` datetime(0) NULL DEFAULT NULL,
  `groups` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `in_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `inports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `out_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `outports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `owner` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `start_time` datetime(0) NULL DEFAULT NULL,
  `state` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_process_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_data_source` bit(1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK6rvjgxm3smnh3jjjnxnqiwl1p`(`fk_flow_process_id`) USING BTREE,
  CONSTRAINT `FK6rvjgxm3smnh3jjjnxnqiwl1p` FOREIGN KEY (`fk_flow_process_id`) REFERENCES `flow_process` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_process_stop
-- ----------------------------

-- ----------------------------
-- Table structure for flow_process_stop_property
-- ----------------------------
DROP TABLE IF EXISTS `flow_process_stop_property`;
CREATE TABLE `flow_process_stop_property`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `allowable_values` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `custom_value` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `display_name` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `name` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `property_required` bit(1) NULL DEFAULT NULL,
  `property_sensitive` bit(1) NULL DEFAULT NULL,
  `fk_flow_process_stop_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK6pqbouerl5dg97la1yqygj5rp`(`fk_flow_process_stop_id`) USING BTREE,
  CONSTRAINT `FK6pqbouerl5dg97la1yqygj5rp` FOREIGN KEY (`fk_flow_process_stop_id`) REFERENCES `flow_process_stop` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_process_stop_property
-- ----------------------------

-- ----------------------------
-- Table structure for flow_stops
-- ----------------------------
DROP TABLE IF EXISTS `flow_stops`;
CREATE TABLE `flow_stops`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `bundel` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `groups` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `in_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `inports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_checkpoint` bit(1) NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `out_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `outports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `owner` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `start_time` datetime(0) NULL DEFAULT NULL,
  `state` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `stop_time` datetime(0) NULL DEFAULT NULL,
  `fk_flow_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_customized` bit(1) NULL DEFAULT NULL,
  `fk_data_source_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_data_source` bit(1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK11mku3yphyjswbtwj9df79k44`(`fk_flow_id`) USING BTREE,
  INDEX `FKr5de1px70o0uj1hlob7ilc90c`(`fk_data_source_id`) USING BTREE,
  CONSTRAINT `FK11mku3yphyjswbtwj9df79k44` FOREIGN KEY (`fk_flow_id`) REFERENCES `flow` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FKr5de1px70o0uj1hlob7ilc90c` FOREIGN KEY (`fk_data_source_id`) REFERENCES `data_source` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_stops
-- ----------------------------
INSERT INTO `flow_stops` VALUES ('00e6321fcb7e414e823841b9d234d6bd', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hdfs.UnzipFilesOnHDFS', 'Unzip files on HDFS', 'Hdfs', 'DEFAULT', 'Default', b'0', 'UnzipFilesOnHDFS137', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '137', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('033e870e49a842e08f08f8f201921b0d', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.Merge', 'Merge data into one stop.', 'CommonGroup', 'ANY', 'Any', b'1', 'Merge', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '6', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('08c040037c4447a09afe56c0a6df45f5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_incollection', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '59', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('14b56561d2314467bfa0cf2c565216f7', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_phdthesis', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '67', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('17e2c1a803d4453a818ae6c8f745b915', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_www', 'NONE', 'None', 'xjzhu@cnic.cn', '48', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('18d23fcb6dda488bade2c2ff6445ac50', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_phdthesis', 'NONE', 'None', 'xjzhu@cnic.cn', '73', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('1f089b0ea2b94ad5b68f5c1e07ae186e', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_inproceedings', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '49', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('229a334908e1441b91391e2983803f91', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.csv.CsvSave', 'Save data into csv file.', 'CsvGroup', 'DEFAULT', 'Default', b'0', 'CsvSave', 'NONE', 'None', 'xjzhu@cnic.cn', '13', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('229a980a8c2541cf817b4f07cb1aeaaf', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_inproceedings', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '87', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('27dd6e671508412789e18daba785d13a', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_proceedings', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '70', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('2857b4727b174c3f825443bd7674d615', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_incollection', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '69', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('30e18a027f4b47d7a504d76fe9672502', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'XmlGroup', 'NONE', 'None', b'0', 'XmlParser', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '2', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('319053908d1a4f6eb0636bea49758a28', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_www', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '66', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('3abb221b73504713a2cdaddd3e1b674b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_article', 'NONE', 'None', 'xjzhu@cnic.cn', '51', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('41a55c9b3b204d42aadfb2b22cbfd1a7', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_article', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '88', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('4e647aa066f44f548eeff0c78d64e9ef', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_proceedings', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '65', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('57cf60f9f7914d1e8c771c2a0865b7e6', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hdfs.UnzipFilesOnHDFS', 'Unzip files on HDFS', 'Hdfs', 'DEFAULT', 'Default', b'0', 'UnzipFilesOnHDFS134', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '134', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('59595573a5554f428389e5469d292894', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_www', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '74', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('6234c3e144bd4fdbb9c171b7c923ced9', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_proceedings', 'NONE', 'None', 'xjzhu@cnic.cn', '86', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('6dc3a6b04d2d4ed988c045d7a0d8e956', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hdfs.UnzipFilesOnHDFS', 'Unzip files on HDFS', 'Hdfs', 'DEFAULT', 'Default', b'0', 'UnzipFilesOnHDFS135', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '135', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('724c4783e52f4b22ad87d9ffc7a520e7', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_book', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '89', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('730826073d3d4fc38880eb731c9d966f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hdfs.UnzipFilesOnHDFS', 'Unzip files on HDFS', 'Hdfs', 'DEFAULT', 'Default', b'0', 'UnzipFilesOnHDFS133', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '133', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('81f100fb0af84e9cae91c43f3a25241b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.Fork', 'Fork data into diffenrent stop.', 'Common', 'DEFAULT', 'Default', b'0', 'Fork', 'ANY', 'Any', 'xjzhu@cnic.cn', '85', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('827637466cf94b95a1ab9cce7105c3b3', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.json.JsonSave', 'Save data into json file.', 'JsonGroup', 'DEFAULT', 'Default', b'0', 'JsonSave', 'NONE', 'None', 'xjzhu@cnic.cn', '15', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('872a894641a440b58ca9f129c5ceff0f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_www', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '60', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('8ec234c86ed74f19bb8875a7c3b0fcd2', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_mastersthesis', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '72', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('9791a63b506948e091bc457ce59c2f34', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_book', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '68', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('9837c8660ebb4a7aa9be3f66a9a9b3df', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_inproceedings', 'NONE', 'None', 'xjzhu@cnic.cn', '54', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('9b66467045bd403699eea6dd5e8e3b01', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hdfs.UnzipFilesOnHDFS', 'Unzip files on HDFS', 'Hdfs', 'DEFAULT', 'Default', b'0', 'UnzipFilesOnHDFS', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '64', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ae5987691aa5495198caa56bb6247802', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_incollection', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '52', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('b109d6a9aed34c48b2377f5f1c5895bf', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_article', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '75', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('b258c2e02fd74e008535cd83284f49a0', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.Fork', 'Fork data into diffenrent stop.', 'CommonGroup', 'DEFAULT', 'Default', b'0', 'Fork', 'ANY', 'Any', 'xjzhu@cnic.cn', '9', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('b283f13b89534e8ba8182833680b4134', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_proceedings', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '56', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ce465f4a525a4d0cac2b7b24bd89e30c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_mastersthesis', 'NONE', 'None', 'xjzhu@cnic.cn', '50', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('d11a78d504d741a6a21b77e3803afd2f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_mastersthesis', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '58', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('d2266c3179de4c5385cef17985c03933', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.csv.CsvParser', 'Parse csv file.', 'CsvGroup', 'NONE', 'None', b'0', 'CsvParser', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '5', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('d5cc3ff19360423696e08d449bd80130', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField_phdthesis', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '91', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('d68f29590a2845e1a8a944bccaf6b311', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'HiveGroup', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming', 'NONE', 'None', 'xjzhu@cnic.cn', '11', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('d9a9adb003b94ce8a30d2c0acf9b7103', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.http.FileDownHDFS', 'Download the network link to HDFS', 'Http', 'NONE', 'None', b'0', 'FileDownHDFS', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '130', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('da9bc38d76ef4c20bcb26cf2f3c62300', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data field.', 'CommonGroup', 'DEFAULT', 'Default', b'1', 'SelectField', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '3', NULL, NULL, NULL, '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('e27dd03beb4a4e31a341efa778e1d8d8', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_book', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '90', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('e40689a3afde4e9b9946a91949d6e9ac', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_book', 'NONE', 'None', 'xjzhu@cnic.cn', '62', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('e6e59ad9d63d4249887c49703fe2f8cd', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_article', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '76', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('edcdbdb75ad24ea5a28d25c3bd594032', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.xml.XmlParser', 'Parse xml file.', 'Xml', 'DEFAULT', 'Default', b'0', 'XmlParser_mastersthesis', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '55', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ee674c0e2c3f48ffb8320251af2457db', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hdfs.UnzipFilesOnHDFS', 'Unzip files on HDFS', 'Hdfs', 'DEFAULT', 'Default', b'0', 'UnzipFilesOnHDFS136', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '136', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('f6634da9669042f0854aa1fb8e7c4a50', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_inproceedings', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '71', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('fc717ae990584851bd34454413c3dd9c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.hive.PutHiveStreaming', 'Save data into hive.', 'Hive', 'DEFAULT', 'Default', b'0', 'PutHiveStreaming_incollection', 'NONE', 'None', 'xjzhu@cnic.cn', '61', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('fddab1b14a404644af6263b33de3b8c8', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'cn.piflow.bundle.common.ConvertSchema', 'Transform field name', 'Common', 'DEFAULT', 'Default', b'0', 'ConvertSchema_phdthesis', 'DEFAULT', 'Default', 'yangqidong@cnic.cn', '57', NULL, NULL, NULL, 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc96b0007', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.Merge', 'Merge data into one stop', 'Common', 'ANY', 'Any', b'0', 'Merge', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '17', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc96b0009', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.Fork', 'Forking data to different stops', 'Common', 'DEFAULT', 'Default', b'0', 'Fork', 'ANY', 'Any', 'xjzhu@cnic.cn', '20', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc96c000b', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.MockData', 'Mock dataframe.', 'Common', 'DEFAULT', 'Default', b'0', 'MockData', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '6', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc96d000e', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.MockData', 'Mock dataframe.', 'Common', 'DEFAULT', 'Default', b'0', 'MockData7', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '11', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc96f0011', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data column', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '15', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc9700013', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data column', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField18', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '22', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc9700015', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data column', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField20', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '24', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);
INSERT INTO `flow_stops` VALUES ('ff808181725b0c8201725b0dc9710017', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'cn.piflow.bundle.common.SelectField', 'Select data column', 'Common', 'DEFAULT', 'Default', b'0', 'SelectField22', 'DEFAULT', 'Default', 'xjzhu@cnic.cn', '26', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71fw00001', b'0', NULL, NULL);

-- ----------------------------
-- Table structure for flow_stops_customized_property
-- ----------------------------
DROP TABLE IF EXISTS `flow_stops_customized_property`;
CREATE TABLE `flow_stops_customized_property`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `custom_value` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'custom value',
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'name',
  `fk_stops_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK92yilfng8y5k7psuevts911c7`(`fk_stops_id`) USING BTREE,
  CONSTRAINT `FK92yilfng8y5k7psuevts911c7` FOREIGN KEY (`fk_stops_id`) REFERENCES `flow_stops` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_stops_customized_property
-- ----------------------------

-- ----------------------------
-- Table structure for flow_stops_groups
-- ----------------------------
DROP TABLE IF EXISTS `flow_stops_groups`;
CREATE TABLE `flow_stops_groups`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `group_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_stops_groups
-- ----------------------------

-- ----------------------------
-- Table structure for flow_stops_property
-- ----------------------------
DROP TABLE IF EXISTS `flow_stops_property`;
CREATE TABLE `flow_stops_property`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `allowable_values` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `custom_value` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'custom value',
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `display_name` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `is_select` bit(1) NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `property_required` bit(1) NULL DEFAULT NULL,
  `property_sensitive` bit(1) NULL DEFAULT NULL,
  `fk_stops_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_locked` bit(1) NULL DEFAULT NULL,
  `property_sort` bigint(20) NULL DEFAULT NULL COMMENT 'property sort',
  `is_old_data` bit(1) NULL DEFAULT NULL COMMENT 'Has it been updated',
  `example` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'property example',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKsjcg9klyumklhkpl8408v6uuq`(`fk_stops_id`) USING BTREE,
  CONSTRAINT `FKsjcg9klyumklhkpl8408v6uuq` FOREIGN KEY (`fk_stops_id`) REFERENCES `flow_stops` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_stops_property
-- ----------------------------
INSERT INTO `flow_stops_property` VALUES ('010dd611535c4dab970636df6a2b8533', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'f6634da9669042f0854aa1fb8e7c4a50', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('032fe151270c4239885f4e2ddfce09be', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', '2857b4727b174c3f825443bd7674d615', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('041892d54e3b4ef8849274cdc0262fa7', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'true', 'isCustomize', 'isCustomize', b'0', 'isCustomize', b'0', b'0', '9b66467045bd403699eea6dd5e8e3b01', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('078230bd33cb4baa93624e8b0c02fdbb', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'proceedings', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', '27dd6e671508412789e18daba785d13a', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('0ab7810a6ed74edcbd2c3872e4d81456', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml.gz', 'savePath', 'savePath', b'0', 'savePath', b'0', b'0', 'd9a9adb003b94ce8a30d2c0acf9b7103', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('0bc641857a48441b9371a705812f97c5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,author,school,title,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', '8ec234c86ed74f19bb8875a7c3b0fcd2', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('0c11cdf8c6694672863b4dc3dc377341', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', '9837c8660ebb4a7aa9be3f66a9a9b3df', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('115a29865bf74e808a3887d1449fc256', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '/web/dblp/dblp.xml.gz', 'filePath', 'filePath', b'0', 'filePath', b'0', b'0', '9b66467045bd403699eea6dd5e8e3b01', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('14aa08c8974645c2a18f0359a6e43c6b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020', 'hdfsUrl', 'hdfsUrl', b'0', 'hdfsUrl', b'0', b'0', '9b66467045bd403699eea6dd5e8e3b01', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('17ac919707a14b2fa545aa2789ec3d97', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'title,author,pages', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'd2266c3179de4c5385cef17985c03933', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('1a98eb8872864f29862807e87af14aa9', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.86.191:9000/xjzhu/dblp.mini.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', '30e18a027f4b47d7a504d76fe9672502', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('1c101f10133b4422bfd94803593fc932', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,author,booktitle,cite,crossref,editor,ee,i,isbn,journal,note,number,pages,publisher,series,sup,title,url,volume,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', '4e647aa066f44f548eeff0c78d64e9ef', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('21e3415835b8466187a007027d17faee', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', '08c040037c4447a09afe56c0a6df45f5', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('243b23a50661486b965fee5951235ce1', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'www', 'Table', 'Table', b'0', 'table', b'0', b'0', '17e2c1a803d4453a818ae6c8f745b915', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('27487bd637c444e48612886df8a712b5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', 'ce465f4a525a4d0cac2b7b24bd89e30c', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('280377a41fc64b9893ce7f0bd5d082c1', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'filePath', 'filePath', b'0', 'filePath', b'0', b'0', '730826073d3d4fc38880eb731c9d966f', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('28a34932134b49a682dc20b507cd448b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'false', 'header', 'header', b'0', 'header', b'0', b'0', 'd2266c3179de4c5385cef17985c03933', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('29b41f51f1c54e4d80d2634d3f5e050c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'isCustomize', 'isCustomize', b'0', 'isCustomize', b'0', b'0', '00e6321fcb7e414e823841b9d234d6bd', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('2a8e7fe373c440f58d519374d6f05411', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'book', 'Table', 'Table', b'0', 'table', b'0', b'0', 'e40689a3afde4e9b9946a91949d6e9ac', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('2ddd0c3c43bf4f398b1dee35c38a99d5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'isCustomize', 'isCustomize', b'0', 'isCustomize', b'0', b'0', '730826073d3d4fc38880eb731c9d966f', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('2fc7d24e7f37436db75dd08f1d5284eb', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'phdthesis', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', '14b56561d2314467bfa0cf2c565216f7', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('366cab581d584b17aa02a55fd8a6fe6b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', 'fc717ae990584851bd34454413c3dd9c', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('3ac11df60a3449408c2dfad5eeef4db3', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'true', 'header', 'header', b'0', 'header', b'0', b'0', '229a334908e1441b91391e2983803f91', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('3bce8f772b954467b9da3c496e6db7ef', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'e27dd03beb4a4e31a341efa778e1d8d8', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('3d98277044c94887ba49ce965d446d50', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', '3abb221b73504713a2cdaddd3e1b674b', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('427db6551aed41be8afb005d5d609cd2', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'savePath', 'savePath', b'0', 'savePath', b'0', b'0', '730826073d3d4fc38880eb731c9d966f', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('430b7bb0bd8c459ca78405c63689d59c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,publtype,author,booktitle,cite,crossref,editor,note,title,url,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', '59595573a5554f428389e5469d292894', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('4512a2b46ef74aa39992c0715247127f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'mastersthesis', 'Table', 'Table', b'0', 'table', b'0', b'0', 'ce465f4a525a4d0cac2b7b24bd89e30c', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('4a34f2a397204f128614f538ef07a433', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'savePath', 'savePath', b'0', 'savePath', b'0', b'0', 'ee674c0e2c3f48ffb8320251af2457db', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('4cb438f1f18448518d96b83668287e6b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', '1f089b0ea2b94ad5b68f5c1e07ae186e', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('4dca7203783049f785a2aa9832a23246', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'isCustomize', 'isCustomize', b'0', 'isCustomize', b'0', b'0', '57cf60f9f7914d1e8c771c2a0865b7e6', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('4f7987a2135240cc8bb6f0dccc701265', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'incollection', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', '08c040037c4447a09afe56c0a6df45f5', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('55a8b556026e43ff8565c5c40495bfbc', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'hdfsUrl', 'hdfsUrl', b'0', 'hdfsUrl', b'0', b'0', '6dc3a6b04d2d4ed988c045d7a0d8e956', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('55aaa330cb554fb692178373c4e52d2e', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'isCustomize', 'isCustomize', b'0', 'isCustomize', b'0', b'0', 'ee674c0e2c3f48ffb8320251af2457db', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('5806e150fc6548f688caafa347f49801', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'hdfsUrl', 'hdfsUrl', b'0', 'hdfsUrl', b'0', b'0', '730826073d3d4fc38880eb731c9d966f', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('5ee51578c82342a1b3f73aea5d605f37', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,publtype,author,booktitle,cdrom,cite,crossref,editor,ee,i,journal,month,note,number,pages,publisher,sub,sup,title,tt,url,volume,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'b109d6a9aed34c48b2377f5f1c5895bf', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('616062f81dee442cbde226860c950983', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'sparktest', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', 'd68f29590a2845e1a8a944bccaf6b311', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('659db8335e5a4c3d88b6f7e5f8531e15', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'hdfsUrl', 'hdfsUrl', b'0', 'hdfsUrl', b'0', b'0', 'ee674c0e2c3f48ffb8320251af2457db', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('66bfeee0be93443b9827bbde7ac2b726', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'savePath', 'savePath', b'0', 'savePath', b'0', b'0', '6dc3a6b04d2d4ed988c045d7a0d8e956', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('69e80ab46c464cc693da551baef20158', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'hdfsUrl', 'hdfsUrl', b'0', 'hdfsUrl', b'0', b'0', '00e6321fcb7e414e823841b9d234d6bd', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('6c04ee856cb1422ea4d76ffa15af526a', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'mastersthesis', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', 'edcdbdb75ad24ea5a28d25c3bd594032', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('6e6f46e814f84fb58f74545f198c5c51', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'inproceedings', 'Table', 'Table', b'0', 'table', b'0', b'0', '9837c8660ebb4a7aa9be3f66a9a9b3df', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('6f74b91d2d3d4f84b0be4679d4eeed39', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', '17e2c1a803d4453a818ae6c8f745b915', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('7ff7a628598842c8b59bb4c241b74448', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'phdthesis', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', '30e18a027f4b47d7a504d76fe9672502', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('82080376269240329f68608bf8c56a62', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'https://dblp.dagstuhl.de/xml/dblp.xml.gz', 'URL', 'URL', b'0', 'url_str', b'0', b'0', 'd9a9adb003b94ce8a30d2c0acf9b7103', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('8684273ce2b043c289d33fa1afc4ea8b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,publtype,author,booktitle,cdrom,cite,crossref,editor,ee,i,note,number,pages,sub,sup,title,tt,url,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', '229a980a8c2541cf817b4f07cb1aeaaf', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('89147909820947a7ab56e3869f15489c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'isCustomize', 'isCustomize', b'0', 'isCustomize', b'0', b'0', '6dc3a6b04d2d4ed988c045d7a0d8e956', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('896b6782dfc34eefa35d79b403285704', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '/web/dblp/', 'savePath', 'savePath', b'0', 'savePath', b'0', b'0', '9b66467045bd403699eea6dd5e8e3b01', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('89c0757750b54c8b97d9bbef8cb4d32a', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', '872a894641a440b58ca9f129c5ceff0f', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('8bfa8a4f6a1043a2ae86229b4d593112', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'filePath', 'filePath', b'0', 'filePath', b'0', b'0', '6dc3a6b04d2d4ed988c045d7a0d8e956', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('8fb32d4d9d4e43cc8440b35d78e5582f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', '41a55c9b3b204d42aadfb2b22cbfd1a7', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('9398a13aaf7c4e888fd83fc0753398ad', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'data1,data2', 'inports', 'inports', b'0', 'inports', b'0', b'0', '033e870e49a842e08f08f8f201921b0d', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('93f315ab3dc0497da89912a4d63ed256', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'savePath', 'savePath', b'0', 'savePath', b'0', b'0', '00e6321fcb7e414e823841b9d234d6bd', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('9a764580459046fab51d3d56699b928d', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'filePath', 'filePath', b'0', 'filePath', b'0', b'0', '57cf60f9f7914d1e8c771c2a0865b7e6', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('a1c3555d59294699a69068e0477d4d53', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'article', 'Table', 'Table', b'0', 'table', b'0', b'0', '3abb221b73504713a2cdaddd3e1b674b', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('ae0d2967278c45349e75690ed1e349fa', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,publtype,author,booktitle,crossref,ee,i,pages,sub,sup,title,url,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'ae5987691aa5495198caa56bb6247802', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('af05ca8bf7634a3a9d903c3d7bd39cf7', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', '6234c3e144bd4fdbb9c171b7c923ced9', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('b09be05c1173493dad5730b160643503', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'out1,out2,out3', 'outports', 'outports', b'0', 'outports', b'0', b'0', 'b258c2e02fd74e008535cd83284f49a0', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('b0e7e6f1be124666b6f9edc220df0b24', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'article', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', 'e6e59ad9d63d4249887c49703fe2f8cd', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('b9f625787b424a1996be60996e756703', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', '319053908d1a4f6eb0636bea49758a28', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c0c262871881417ea7dd6ae821f1945b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'fddab1b14a404644af6263b33de3b8c8', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c189d6b50a40454bb4736ab54a7ea9c5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'inproceedings', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', '1f089b0ea2b94ad5b68f5c1e07ae186e', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c24f69311129498f9def02ac35a36d13', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', '18d23fcb6dda488bade2c2ff6445ac50', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c258b1c39075481897423269a1ccb6b1', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,publtype,author,booktitle,editor,ee,isbn,note,pages,publisher,school,series,sub,sup,title,url,volume,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', '9791a63b506948e091bc457ce59c2f34', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c3cb096e0c384e0a8ee50f4a3b763163', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', '14b56561d2314467bfa0cf2c565216f7', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c57f2d9666674f8e870f82ff3a444786', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'out1,out2,out3,out4,out5,out6,out7,out8', 'outports', 'outports', b'0', 'outports', b'0', b'0', '81f100fb0af84e9cae91c43f3a25241b', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c59696b38708474e9547377dec5cd158', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp', 'DataBase', 'DataBase', b'0', 'database', b'0', b'0', 'e40689a3afde4e9b9946a91949d6e9ac', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('c5f45d48a7a74e0b8ce25e01e5f302a5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'hdfsUrl', 'hdfsUrl', b'0', 'hdfsUrl', b'0', b'0', '57cf60f9f7914d1e8c771c2a0865b7e6', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('ca272aff99044f62ad51be5adce6d3ac', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'incollection', 'Table', 'Table', b'0', 'table', b'0', b'0', 'fc717ae990584851bd34454413c3dd9c', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('cc26b11f24e9409a8cb5fa8ddc472175', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'book', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', '724c4783e52f4b22ad87d9ffc7a520e7', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('cc6eb6517352468eb6f9af56a203910b', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'filePath', 'filePath', b'0', 'filePath', b'0', b'0', '00e6321fcb7e414e823841b9d234d6bd', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('cd1d1663153f4f1a9cca94e8a8617350', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'b283f13b89534e8ba8182833680b4134', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('d60f0d3c6d6d4e0a8e035966b6a7d7ac', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'www', 'rowTag', 'rowTag', b'0', 'rowTag', b'0', b'0', '872a894641a440b58ca9f129c5ceff0f', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('d80d3291cd5a475f8c72904164dbe767', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', '724c4783e52f4b22ad87d9ffc7a520e7', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('da94207c29bf48cd962ff4ccc701a233', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', 'e6e59ad9d63d4249887c49703fe2f8cd', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('db2b7d1c632a4b55a3c2d87b3135a131', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'proceedings', 'Table', 'Table', b'0', 'table', b'0', b'0', '6234c3e144bd4fdbb9c171b7c923ced9', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('ded789f2a7c94fb7b90f9e9762cdc211', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.86.191:9000/xjzhu/phdthesis.csv', 'csvPath', 'csvPath', b'0', 'csvPath', b'0', b'0', 'd2266c3179de4c5385cef17985c03933', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('df4d78d49a5b4d48839b30374c9fae2c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'title,author,pages', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'da9bc38d76ef4c20bcb26cf2f3c62300', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('e0c889f149a547fea414186f52bddbc9', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'dblp_phdthesis', 'Table', 'Table', b'0', 'table', b'0', b'0', 'd68f29590a2845e1a8a944bccaf6b311', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('e35b30dd1aba478d84cb26f3da3a8476', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.86.191:9000/xjzhu/phdthesis_result.csv', 'csvSavePath', 'csvSavePath', b'0', 'csvSavePath', b'0', b'0', '229a334908e1441b91391e2983803f91', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('e6f8ce9416004d5aa3e50afad32d78b5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', ',', 'delimiter', 'delimiter', b'0', 'delimiter', b'0', b'0', '229a334908e1441b91391e2983803f91', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('e7bbf9f4c65a451f827701654aede47d', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', ',', 'delimiter', 'delimiter', b'0', 'delimiter', b'0', b'0', 'd2266c3179de4c5385cef17985c03933', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('f27f9a429ced45ee8993d5917655f6a7', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'phdthesis', 'Table', 'Table', b'0', 'table', b'0', b'0', '18d23fcb6dda488bade2c2ff6445ac50', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('f84227b4a27545e3b8b5041b5bced29c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'filePath', 'filePath', b'0', 'filePath', b'0', b'0', 'ee674c0e2c3f48ffb8320251af2457db', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('fa550f9ec8ef42278a6edada205af9b4', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'corrupt_record,key,mdate,publtype,author,ee,i,isbn,month,note,number,pages,publisher,school,series,sub,sup,title,url,volume,year', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'd5cc3ff19360423696e08d449bd80130', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('fb679cb8ccd149018a50c7d9a2986d02', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.86.191:9000/xjzhu/phdthesis.json', 'jsonSavePath', 'jsonSavePath', b'0', 'jsonSavePath', b'0', b'0', '827637466cf94b95a1ab9cce7105c3b3', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('fc317c34d2e6460d9ca950a65fb96c61', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '', 'savePath', 'savePath', b'0', 'savePath', b'0', b'0', '57cf60f9f7914d1e8c771c2a0865b7e6', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('fd5c79c99a3740499199d602d2580cf6', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', '_corrupt_record->corrupt_record,_key->key,_mdate->mdate,_publtype->publtype', 'schema', 'schema', b'0', 'schema', b'0', b'0', 'd11a78d504d741a6a21b77e3803afd2f', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('fd634ff2bbbe43938bd89228dd3c216f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', 'edcdbdb75ad24ea5a28d25c3bd594032', NULL, NULL, b'0', NULL);
INSERT INTO `flow_stops_property` VALUES ('fe59df7ea7d749699576d57e33e43905', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, '[]', 'hdfs://10.0.88.109:8020/web/dblp/dblp.xml', 'xmlpath', 'xmlpath', b'0', 'xmlpath', b'0', b'0', '27dd6e671508412789e18daba785d13a', NULL, NULL, b'0', NULL);

-- ----------------------------
-- Table structure for flow_stops_property_template
-- ----------------------------
DROP TABLE IF EXISTS `flow_stops_property_template`;
CREATE TABLE `flow_stops_property_template`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `allowable_values` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL,
  `default_value` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL COMMENT 'Defaults',
  `display_name` text CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL COMMENT 'description',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `property_required` bit(1) NULL DEFAULT NULL,
  `property_sensitive` bit(1) NULL DEFAULT NULL,
  `fk_stops_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `property_sort` bigint(20) NULL DEFAULT NULL COMMENT 'property sort',
  `example` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'property example',
  `language` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'language',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKhtnjkpgjkx21r2qf4r3q3mjr9`(`fk_stops_id`) USING BTREE,
  CONSTRAINT `FKhtnjkpgjkx21r2qf4r3q3mjr9` FOREIGN KEY (`fk_stops_id`) REFERENCES `flow_stops_template` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_stops_property_template
-- ----------------------------

-- ----------------------------
-- Table structure for flow_stops_template
-- ----------------------------
DROP TABLE IF EXISTS `flow_stops_template`;
CREATE TABLE `flow_stops_template`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `bundel` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `groups` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `in_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `inports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `out_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `outports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `owner` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `stop_group` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_customized` bit(1) NULL DEFAULT NULL,
  `visualization_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'visualization type',
  `is_data_source` bit(1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `bundel`(`bundel`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_stops_template
-- ----------------------------

-- ----------------------------
-- Table structure for flow_template
-- ----------------------------
DROP TABLE IF EXISTS `flow_template`;
CREATE TABLE `flow_template`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `description` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '描述',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `path` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `value` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `fk_flow_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `source_flow_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'source flow name',
  `template_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'template type',
  `url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKkcg573sjiknyhppuc0q62a0kj`(`fk_flow_id`) USING BTREE,
  CONSTRAINT `FKkcg573sjiknyhppuc0q62a0kj` FOREIGN KEY (`fk_flow_id`) REFERENCES `flow` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of flow_template
-- ----------------------------

-- ----------------------------
-- Table structure for group_schedule
-- ----------------------------
DROP TABLE IF EXISTS `group_schedule`;
CREATE TABLE `group_schedule`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `cron_expression` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'cron expression',
  `plan_end_time` datetime(0) NULL DEFAULT NULL COMMENT 'plan end time',
  `plan_start_time` datetime(0) NULL DEFAULT NULL COMMENT 'plan start time',
  `schedule_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'service schedule id',
  `schedule_process_template_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Template ID for generating Process',
  `schedule_run_template_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Start template ID',
  `status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'schedule task status',
  `type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'schedule content Flow or FlowGroup',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of group_schedule
-- ----------------------------

-- ----------------------------
-- Table structure for hibernate_sequence
-- ----------------------------
DROP TABLE IF EXISTS `hibernate_sequence`;
CREATE TABLE `hibernate_sequence`  (
  `next_val` bigint(20) NULL DEFAULT NULL
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of hibernate_sequence
-- ----------------------------
INSERT INTO `hibernate_sequence` VALUES (1);

-- ----------------------------
-- Table structure for mx_cell
-- ----------------------------
DROP TABLE IF EXISTS `mx_cell`;
CREATE TABLE `mx_cell`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `mx_edge` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_pageid` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_parent` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_source` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_style` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_target` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_value` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'mx_value',
  `mx_vertex` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_mx_graph_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK4s2gnt8t7e5ok1v7r3v99pji5`(`fk_mx_graph_id`) USING BTREE,
  CONSTRAINT `FK4s2gnt8t7e5ok1v7r3v99pji5` FOREIGN KEY (`fk_mx_graph_id`) REFERENCES `mx_graph_model` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mx_cell
-- ----------------------------
INSERT INTO `mx_cell` VALUES ('0641076d5ae840c09d2be5b71d7fbae3', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '106', '1', '89', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '90', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('07d0527b7098458d8f572c861b6df223', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '86', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_proceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('0970bc210a8347db9b95499cab5f175a', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '100', '1', '74', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '48', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('0ab5bd6a6b9b4602b62835d3d4960847', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '108', '1', '90', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '68', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('0e8cd6ec84564605b77967ce8476a267', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '117', '1', '88', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '75', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('1160a55474764d1abe471154161e3254', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '59', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_incollection', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('11ee64825e284977b6d2f9a663c18096', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '109', '1', '68', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '62', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('1b4334a8d23143a49a257b1c9d41c55b', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '113', '1', '49', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;', '71', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('22ca48a05ec7484598bb8ad0f6122dc3', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '66', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_www', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('2654d43c30464a0d901a83fe359532f9', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '3', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('2881d99bfdb44daba014b1466eb64007', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '14', '1', '9', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;noEdgeStyle=1;orthogonal=1;', '13', NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('28ca0710b42e41799fdb5ea210651064', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '61', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_incollection', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('29dd643f61e942e094cfb64678ba8224', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '7', '1', '3', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;noEdgeStyle=1;orthogonal=1;', '6', NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('3467510fa51844e79f4a0267267bc4a7', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '95', '1', '55', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '58', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('34fe9bb7cc0a4e688a3e4ef46877d887', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '50', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_mastersthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('375c30fd318f432882caf2ae8e26d6cf', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '65', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_proceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('395f42be848442b581bfdafff0e4273f', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '60', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_www', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('3b058329ecbd4daf95122c4dc85b9bb3', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '68', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_book', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('3c405dc611f644be923f091fb33d18a6', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '129', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '76', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('3c4e10c0a41c44e581157502d781c1a1', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '103', '1', '59', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '69', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('4289c02b5e0248e2be21ad0be06ded01', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '110', '1', '70', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '56', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('44ad3472208d4697942e8eca0c2b2ca8', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '48', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_www', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('462723c42b2a4062b75eee40b3c2cc85', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '70', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_proceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('487f52a863874fdb99c5678d7bdbc77f', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '126', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '89', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('4ad34d2365d747a1afca5bc353a506e2', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '63', '1', '64', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '85', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('4f5e785b2c71435a88b683c35350bb1d', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '105', '1', '52', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;', '61', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('526c2afd7c3c4d1f959967fd0b3bdbaf', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '8', '1', '5', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;noEdgeStyle=1;orthogonal=1;', '6', NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('5a9886ceed334e9fac966b92588e391b', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '128', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '49', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('5eef4f7e09a34f7e83c946402c8f821c', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '64', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/UnzipFilesOnHDFS_128x128.png', NULL, 'UnzipFilesOnHDFS', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('5f385f2b426b4b84ae01c891e0ba650d', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '4', '1', '2', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;noEdgeStyle=1;orthogonal=1;', '3', NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('6539017b0a2f4f989c6ba5b09bd8fb03', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '12', '1', '9', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;noEdgeStyle=1;orthogonal=1;', '11', NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('6627427da05d4bb380becf49535476fa', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '85', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/Fork_128x128.png', NULL, 'Fork', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('6c435e7466aa42128b3c2dc8392510e6', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '89', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_book', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('6c824369ae194c52ba2827207b021f67', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '118', '1', '75', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '51', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('6d58cc47f3e94a708d5b719e75b06d46', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '11', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('73bce97f54594ff081e99ed3f7f91572', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '0', '', NULL, NULL, NULL, NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('766a0b5df6de4c03b65fe94ead973b83', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '49', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_inproceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('791719f8153e42a7b4549287e12d9e1c', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '98', '1', '60', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;', '66', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('7a10ea3b94784b98869a5ec02058f3ca', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '125', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '59', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('7a3194ce39ff4543845fbfa4c5246a93', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '56', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_proceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('7a3e4d9f12a74675a0ebb8ffc8981b4a', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '1', '0', NULL, NULL, NULL, NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('7b7b3f01ba7341eb8ae14dbea5ba1464', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '76', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_article', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('7ca092885b374898b5570384748078f6', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '94', '1', '91', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '73', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('7dee73b470864facaceb74a253d7e5ca', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '71', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_inproceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('90ce3539c17e40fbae2c41e218af35a8', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '115', '1', '87', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '54', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('910549a2c6e040ddbffff58f877522e5', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '54', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_inproceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('92a66a249a614d72972b3fe79ed0d323', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '58', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_mastersthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('936f342cb22d4ba59f7f15983464801f', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '104', '1', '69', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '52', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('94d88ea4a5df4063a6e51bb4b0d39f94', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '114', '1', '71', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '87', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('96a1b41428ef4bd68f04ec6b5060cc49', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '51', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_article', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('9a241dbbca654766985c49ccb82806b7', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '88', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_article', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('a41d988fd9eb451e97d8ad233d8b2052', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '124', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '60', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('a46a378925ce42db891e153d4db77581', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '62', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_book', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('a5a2552a68b24d4da2c664ec08a4b27c', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '13', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/CsvSave_128x128.png', NULL, 'CsvSave', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('a5da878107cc48a4b3c891eef0f7c126', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '87', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_inproceedings', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('a90f684911d746ed9ca5205a229e8ec0', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '130', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/FileDownHDFS_128x128.png', NULL, 'FileDownHDFS', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('ac19da587f5240d8b4d9fdb8a03288e4', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '5', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/CsvParser_128x128.png', NULL, 'CsvParser', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('b3051ee8ddb44f38b6f937e546f935c8', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '96', '1', '58', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '72', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('b5b5d35c6ee34a17b2582a184046b0b1', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '74', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_www', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('b984a09bf722453185a691aff96f9dd4', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '57', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_phdthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('bc30534cd7ef455f8c4851e0babd6c1f', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '2', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('c3ca1be73f0343c7a9e5145a11957578', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '112', '1', '65', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '86', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('c4009c838e454395a51556c249177309', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '111', '1', '56', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '65', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('c4b113e9f7624b2cbd5b52591ff2e5e1', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '138', '1', '130', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '64', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('c88fe09bb8b34fb98bb5c2053cabe435', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '6', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/Merge_128x128.png', NULL, 'Merge', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('c8b3ea9fae534faeb0fcd78f3bea4502', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '73', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/PutHiveStreaming_128x128.png', NULL, 'PutHiveStreaming_phdthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('c944d3896e054e71820d922d914bf2dd', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '52', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_incollection', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('cb74262c633c4bd695d8c399ce2bec69', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '90', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_book', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('cc3b89587fa847d298467a2622d94560', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '123', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '55', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('cfb258b23b7c421a9190c9070bdd5d26', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '16', '1', '9', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;noEdgeStyle=1;orthogonal=1;', '15', NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('d127cb00f537498e9ee4a79de39e4974', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '75', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_article', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('d36e8589a5bb4a27b5e6e64347935006', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '1', '0', NULL, NULL, NULL, NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('d3c89cda410d4a81a343c5327cb85e4a', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '10', '1', '6', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;noEdgeStyle=1;orthogonal=1;exitX=0.5;exitY=1;', '9', NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('d95042d44e0348dba844bb48b02991cd', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '0', '', NULL, NULL, NULL, NULL, NULL, 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('d9d2dcf51dc044b198d4c05ff7597afc', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '99', '1', '66', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '74', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('da10f4d630594c7bb0ffe000708181f5', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '97', '1', '72', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '50', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('dd108bc6da824a74a00252b7cac139eb', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '72', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_mastersthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('dea87e1aa10f4a5bae4ba80acae5834e', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '122', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '67', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('e11fceb6aae94b9c9f4bbd2d44775f29', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '91', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/SelectField_128x128.png', NULL, 'SelectField_phdthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('e307a1b2635c490da381e87d9ec6f7ac', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '127', '1', '85', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '70', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('e585ace3841d4218983e19e71c9b7194', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '116', '1', '76', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;', '88', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('e76a8df44be34dd5a23e2fd8c3c31889', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '15', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/JsonSave_128x128.png', NULL, 'JsonSave', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('e880292baa404efc97c3754ab024ca2b', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '93', '1', '57', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '91', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('ed5bbedb60a44b69866661d9d46b75b1', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '92', '1', '67', 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;jettySize=auto;orthogonalLoop=1;', '57', NULL, NULL, 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('f10240ef21354494a8112ca1b5e53350', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '55', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_mastersthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('f530a5d3d7be4daaafab9dbc4bc1ce26', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '9', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff;image=/piflow-web/images/Fork_128x128.png', NULL, 'Fork', '1', 'd3bff4840a7444e891ee4bf7daf1bb5b');
INSERT INTO `mx_cell` VALUES ('fcdee0f3f30b47a28eb33cd432d0dfbe', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '69', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/ConvertSchema_128x128.png', NULL, 'ConvertSchema_incollection', '1', 'da664942f1db4ad7a42fa54e667385d9');
INSERT INTO `mx_cell` VALUES ('fea1f59e5e054a7398d54d26dd790608', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, NULL, '67', '1', NULL, 'image;html=1;labelBackgroundColor=#ffffff00;image=/piflow-web/images/XmlParser_128x128.png', NULL, 'XmlParser_phdthesis', '1', 'da664942f1db4ad7a42fa54e667385d9');

-- ----------------------------
-- Table structure for mx_geometry
-- ----------------------------
DROP TABLE IF EXISTS `mx_geometry`;
CREATE TABLE `mx_geometry`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `mx_as` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_height` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_relative` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_width` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_x` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_y` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_mx_cell_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK6elkg2vbxxjrun0qaqaajwgfu`(`fk_mx_cell_id`) USING BTREE,
  CONSTRAINT `FK6elkg2vbxxjrun0qaqaajwgfu` FOREIGN KEY (`fk_mx_cell_id`) REFERENCES `mx_cell` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mx_geometry
-- ----------------------------
INSERT INTO `mx_geometry` VALUES ('0593d3a70bcd4bd6b141412ebf1a2760', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '487f52a863874fdb99c5678d7bdbc77f');
INSERT INTO `mx_geometry` VALUES ('0682e6a6b4cf4d6fb2528b1e5f3b7419', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1300', '800', 'd127cb00f537498e9ee4a79de39e4974');
INSERT INTO `mx_geometry` VALUES ('084835a5c3904a879c910695b835c3e3', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '100', '400', 'fea1f59e5e054a7398d54d26dd790608');
INSERT INTO `mx_geometry` VALUES ('0a666603af6b48b1934e87056d419925', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1000', '990', '07d0527b7098458d8f572c861b6df223');
INSERT INTO `mx_geometry` VALUES ('12ad5ee7ebce483787bcdbe0230b766f', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'a41d988fd9eb451e97d8ad233d8b2052');
INSERT INTO `mx_geometry` VALUES ('17e17f7d4be44a6d903989b5c4ba7e68', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '700', '240', '6627427da05d4bb380becf49535476fa');
INSERT INTO `mx_geometry` VALUES ('1b5816dce7d04cc2a1ac83f8a0072508', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '100', '600', 'b984a09bf722453185a691aff96f9dd4');
INSERT INTO `mx_geometry` VALUES ('26c2541bb7ad4dd386439e3aabc4fdca', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '550', '800', 'c944d3896e054e71820d922d914bf2dd');
INSERT INTO `mx_geometry` VALUES ('26fb9230a95f4703afb8d49a8424c3e5', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '936f342cb22d4ba59f7f15983464801f');
INSERT INTO `mx_geometry` VALUES ('2e345ca3c4c94c76b1cadf6d7237f1f8', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '1b4334a8d23143a49a257b1c9d41c55b');
INSERT INTO `mx_geometry` VALUES ('2fa22e14ca0b43e4aa94039ae8751709', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '0970bc210a8347db9b95499cab5f175a');
INSERT INTO `mx_geometry` VALUES ('3132b4e0016241bb9242b7243f295401', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '0ab5bd6a6b9b4602b62835d3d4960847');
INSERT INTO `mx_geometry` VALUES ('31f55fee2caf4306b3c30ae60738e27a', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1150', '400', '766a0b5df6de4c03b65fe94ead973b83');
INSERT INTO `mx_geometry` VALUES ('31f65a5134494383900a04d2ee5156a5', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '400', '1000', '44ad3472208d4697942e8eca0c2b2ca8');
INSERT INTO `mx_geometry` VALUES ('359fd78b8f8a4f2b9c518ab3125a61a8', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '2881d99bfdb44daba014b1466eb64007');
INSERT INTO `mx_geometry` VALUES ('360c97259ea842bda03a61b49e90d411', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '250', '400', 'f10240ef21354494a8112ca1b5e53350');
INSERT INTO `mx_geometry` VALUES ('38838288c0cc4a98be325b9b43c71f82', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '94d88ea4a5df4063a6e51bb4b0d39f94');
INSERT INTO `mx_geometry` VALUES ('3ce40f442f3f4acb852130db42489f72', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'c4009c838e454395a51556c249177309');
INSERT INTO `mx_geometry` VALUES ('3ce4138abc82408a81c459af835ee9a0', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1000', '800', '375c30fd318f432882caf2ae8e26d6cf');
INSERT INTO `mx_geometry` VALUES ('3cfbc19c56fa4e86b50f055b209368ba', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'cc3b89587fa847d298467a2622d94560');
INSERT INTO `mx_geometry` VALUES ('3eeae3a1ac164f3db602f8975acdabad', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '4289c02b5e0248e2be21ad0be06ded01');
INSERT INTO `mx_geometry` VALUES ('3f31516d123140c48928fa2face3a256', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '4f5e785b2c71435a88b683c35350bb1d');
INSERT INTO `mx_geometry` VALUES ('3faf42be86cf4e6e9059378e0e0b0d6c', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'e585ace3841d4218983e19e71c9b7194');
INSERT INTO `mx_geometry` VALUES ('409a6fa756fa4e04ac47616205673772', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '250', '800', 'dd108bc6da824a74a00252b7cac139eb');
INSERT INTO `mx_geometry` VALUES ('485658615ab94296910fd53fc7a57f8b', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'ed5bbedb60a44b69866661d9d46b75b1');
INSERT INTO `mx_geometry` VALUES ('4b20f607389540d3a586c50260cc9d66', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '6c824369ae194c52ba2827207b021f67');
INSERT INTO `mx_geometry` VALUES ('4f0ff962c53c4eb08926e7e275907e1a', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1300', '990', '96a1b41428ef4bd68f04ec6b5060cc49');
INSERT INTO `mx_geometry` VALUES ('51e39cb50a6042fc94dc45cd7c67d6e2', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'e880292baa404efc97c3754ab024ca2b');
INSERT INTO `mx_geometry` VALUES ('5560e2385a764a429085b3a1c6a12eb7', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1150', '990', '910549a2c6e040ddbffff58f877522e5');
INSERT INTO `mx_geometry` VALUES ('564477f9c82845e3b8673d79d3fffcce', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '3467510fa51844e79f4a0267267bc4a7');
INSERT INTO `mx_geometry` VALUES ('578c1c324cd740eb83d4b78ef535d7ef', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '6539017b0a2f4f989c6ba5b09bd8fb03');
INSERT INTO `mx_geometry` VALUES ('5b7bf044beea4c74a99ada970933006e', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '0641076d5ae840c09d2be5b71d7fbae3');
INSERT INTO `mx_geometry` VALUES ('5e3c8c0c1083477c87e8e66c52fb8f72', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '250', '1000', '34fe9bb7cc0a4e688a3e4ef46877d887');
INSERT INTO `mx_geometry` VALUES ('607db8b7d6214986b414337308eb98db', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '400', '800', 'b5b5d35c6ee34a17b2582a184046b0b1');
INSERT INTO `mx_geometry` VALUES ('6236dde12fc54eae8b7fea2545983c62', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '400', '600', '22ca48a05ec7484598bb8ad0f6122dc3');
INSERT INTO `mx_geometry` VALUES ('62acef6051ff4a4d9a065bf8a9542fc2', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '70', NULL, '70', '698', '120', '5eef4f7e09a34f7e83c946402c8f821c');
INSERT INTO `mx_geometry` VALUES ('63a1f34698694d72b43c14e27678de23', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '376.875', '568', 'f530a5d3d7be4daaafab9dbc4bc1ce26');
INSERT INTO `mx_geometry` VALUES ('63b49ce5f5ea4257934b48ae04b2b552', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '484.5', '754', '6d58cc47f3e94a708d5b719e75b06d46');
INSERT INTO `mx_geometry` VALUES ('66908d7ccbea4b898cb898c688d6ac13', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '5a9886ceed334e9fac966b92588e391b');
INSERT INTO `mx_geometry` VALUES ('6749bab639d049a9bb2c6629792be801', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '70', NULL, '70', '698', '10', 'a90f684911d746ed9ca5205a229e8ec0');
INSERT INTO `mx_geometry` VALUES ('68500f2dec494ed482088b054ec2a08a', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '526c2afd7c3c4d1f959967fd0b3bdbaf');
INSERT INTO `mx_geometry` VALUES ('6942ab72e5aa457ea4b4a2f1a5e0a87c', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '0e8cd6ec84564605b77967ce8476a267');
INSERT INTO `mx_geometry` VALUES ('6a0a269a6ac340f4adac3a77301dc562', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '7a10ea3b94784b98869a5ec02058f3ca');
INSERT INTO `mx_geometry` VALUES ('6b50014cc5d04bef9ad00df5a6967a55', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'b3051ee8ddb44f38b6f937e546f935c8');
INSERT INTO `mx_geometry` VALUES ('71978f4c4bf643b7b94a0995de50018f', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'c4b113e9f7624b2cbd5b52591ff2e5e1');
INSERT INTO `mx_geometry` VALUES ('744724fe22ea46e088d87622996fc8c9', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '550', '400', '1160a55474764d1abe471154161e3254');
INSERT INTO `mx_geometry` VALUES ('745110db92774bc8a47a576085315878', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1000', '600', '7a3194ce39ff4543845fbfa4c5246a93');
INSERT INTO `mx_geometry` VALUES ('7ad138506b65419ea78fb944b02f1e15', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '1150', '800', 'a5da878107cc48a4b3c891eef0f7c126');
INSERT INTO `mx_geometry` VALUES ('7f09bd31aa24495196efaea7f47ee2f3', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, 'geometry', '66', NULL, '66', '400', '400', '395f42be848442b581bfdafff0e4273f');
INSERT INTO `mx_geometry` VALUES ('7fdf03e5718b447eaef65f2f5a52179e', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '29dd643f61e942e094cfb64678ba8224');
INSERT INTO `mx_geometry` VALUES ('82b79cb7179241f080757b11d55faaa5', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'dea87e1aa10f4a5bae4ba80acae5834e');
INSERT INTO `mx_geometry` VALUES ('85ceea7830954b259dfbf1990d77543c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '300.5', '196', 'ac19da587f5240d8b4d9fdb8a03288e4');
INSERT INTO `mx_geometry` VALUES ('8accd107203d42679e8a5aabfc24c731', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '1300', '400', '7b7b3f01ba7341eb8ae14dbea5ba1464');
INSERT INTO `mx_geometry` VALUES ('9271839924ef48f89da8963986e082fa', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '11ee64825e284977b6d2f9a663c18096');
INSERT INTO `mx_geometry` VALUES ('93127a31c1924c4882290fd66469388d', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '100', '1000', 'c8b3ea9fae534faeb0fcd78f3bea4502');
INSERT INTO `mx_geometry` VALUES ('94ee254bb877409ea8e0531a8de34dc8', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '90ce3539c17e40fbae2c41e218af35a8');
INSERT INTO `mx_geometry` VALUES ('9eb26a744a0d48abac6cbea52b8d26a8', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'cfb258b23b7c421a9190c9070bdd5d26');
INSERT INTO `mx_geometry` VALUES ('b3db34fca7394b1b962465c32b50bd85', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'da10f4d630594c7bb0ffe000708181f5');
INSERT INTO `mx_geometry` VALUES ('c0985929e32a447885ab41ece4780f48', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'd9d2dcf51dc044b198d4c05ff7597afc');
INSERT INTO `mx_geometry` VALUES ('c143acd4451148c4b4fc1987dd6f7201', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '550', '1000', '28ca0710b42e41799fdb5ea210651064');
INSERT INTO `mx_geometry` VALUES ('c163d9629b1641e3af182a43b35ca73f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '850', '600', 'cb74262c633c4bd695d8c399ce2bec69');
INSERT INTO `mx_geometry` VALUES ('c278f68dbad64c5396bb241b331b3cca', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '277', '754', 'e76a8df44be34dd5a23e2fd8c3c31889');
INSERT INTO `mx_geometry` VALUES ('c691ea6cc8b14950b887440c02d378db', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '791719f8153e42a7b4549287e12d9e1c');
INSERT INTO `mx_geometry` VALUES ('cbaefe6dd2b04abc8a197558e6456f6e', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '5f385f2b426b4b84ae01c891e0ba650d');
INSERT INTO `mx_geometry` VALUES ('cd8db3179278425b8e0f8126ad6360d9', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '3c405dc611f644be923f091fb33d18a6');
INSERT INTO `mx_geometry` VALUES ('d063b7e4a791464cbb5e7861ac05074e', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'c3ca1be73f0343c7a9e5145a11957578');
INSERT INTO `mx_geometry` VALUES ('d276783c0ec843809079bba20fe863e4', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '436.5', '10', 'bc30534cd7ef455f8c4851e0babd6c1f');
INSERT INTO `mx_geometry` VALUES ('d32e6922fb9c4b3791cc29beeb018127', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '850', '990', 'a46a378925ce42db891e153d4db77581');
INSERT INTO `mx_geometry` VALUES ('d33d53f976d3405d81446978463a61d1', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '250', '600', '92a66a249a614d72972b3fe79ed0d323');
INSERT INTO `mx_geometry` VALUES ('d4b72c0d62c24f18b57d2d0d21da20e1', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '376.625', '382', 'c88fe09bb8b34fb98bb5c2053cabe435');
INSERT INTO `mx_geometry` VALUES ('db794fdb40504da9acf1149e808a9ffc', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '100', '800', 'e11fceb6aae94b9c9f4bbd2d44775f29');
INSERT INTO `mx_geometry` VALUES ('e50c99ed6b30412cb5780cc94eb225f1', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '1300', '600', '9a241dbbca654766985c49ccb82806b7');
INSERT INTO `mx_geometry` VALUES ('e60a576a9c5b4885a105940d5b338952', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '7ca092885b374898b5570384748078f6');
INSERT INTO `mx_geometry` VALUES ('ead9aad42957473a8d13ec48a7f6a00f', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '4ad34d2365d747a1afca5bc353a506e2');
INSERT INTO `mx_geometry` VALUES ('eddd98f74f26409cab314e0be5262403', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '850', '800', '3b058329ecbd4daf95122c4dc85b9bb3');
INSERT INTO `mx_geometry` VALUES ('f1a40e3c72884e33829e09190afab795', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '850', '400', '6c435e7466aa42128b3c2dc8392510e6');
INSERT INTO `mx_geometry` VALUES ('f3ae42b0b0764e5d8d70a6f1fca277c4', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '451.5', '196', '2654d43c30464a0d901a83fe359532f9');
INSERT INTO `mx_geometry` VALUES ('f5773a2caa9743b2bf2b5a9c2cb384ab', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '1150', '600', '7dee73b470864facaceb74a253d7e5ca');
INSERT INTO `mx_geometry` VALUES ('f5ab8cb664b94ed58ef8db3965261558', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, '3c4e10c0a41c44e581157502d781c1a1');
INSERT INTO `mx_geometry` VALUES ('f5cc2b95963a4975a3adf861826375e6', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '1000', '400', '462723c42b2a4062b75eee40b3c2cc85');
INSERT INTO `mx_geometry` VALUES ('fb20dfd2ceff4d97b58f6754358a3142', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '550', '600', 'fcdee0f3f30b47a28eb33cd432d0dfbe');
INSERT INTO `mx_geometry` VALUES ('fbb911a8131349df9f7141486fd1041c', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'e307a1b2635c490da381e87d9ec6f7ac');
INSERT INTO `mx_geometry` VALUES ('fcd1306eb3d2455a9b1addc62803c836', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', NULL, '1', NULL, NULL, NULL, 'd3c89cda410d4a81a343c5327cb85e4a');
INSERT INTO `mx_geometry` VALUES ('fcff349787cc4f85ad4c16e55a5de339', '2022-09-03 10:35:56', 'admin', b'1', '2022-09-03 10:35:56', 'admin', 0, 'geometry', '66', NULL, '66', '373', '754', 'a5a2552a68b24d4da2c664ec08a4b27c');

-- ----------------------------
-- Table structure for mx_graph_model
-- ----------------------------
DROP TABLE IF EXISTS `mx_graph_model`;
CREATE TABLE `mx_graph_model`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `mx_arrows` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_background` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_connect` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_dx` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_dy` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_fold` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_grid` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_gridsize` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_guides` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_page` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_pageheight` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_pagescale` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_pagewidth` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `mx_tooltips` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_flow_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_process_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_process_group_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKktpy5kv5fgya1gn012g7395l9`(`fk_flow_id`) USING BTREE,
  INDEX `FKbwxper47v5e1ii4wjrcrhi63e`(`fk_flow_group_id`) USING BTREE,
  INDEX `FKkw0r9m7r3jm9scab8caoxnnxc`(`fk_process_id`) USING BTREE,
  INDEX `FKnugg3p8uvupfu3mso2iax2g8t`(`fk_process_group_id`) USING BTREE,
  CONSTRAINT `FKbwxper47v5e1ii4wjrcrhi63e` FOREIGN KEY (`fk_flow_group_id`) REFERENCES `flow_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FKktpy5kv5fgya1gn012g7395l9` FOREIGN KEY (`fk_flow_id`) REFERENCES `flow` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FKkw0r9m7r3jm9scab8caoxnnxc` FOREIGN KEY (`fk_process_id`) REFERENCES `flow_process` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FKnugg3p8uvupfu3mso2iax2g8t` FOREIGN KEY (`fk_process_group_id`) REFERENCES `flow_process_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mx_graph_model
-- ----------------------------
INSERT INTO `mx_graph_model` VALUES ('d3bff4840a7444e891ee4bf7daf1bb5b', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '#ffffff', '1', '1353', '681', '1', '1', '10', '1', '1', '1169', '1', '827', '1', '0c4fdee973824a999e1569770677c020', NULL, NULL, NULL);
INSERT INTO `mx_graph_model` VALUES ('da664942f1db4ad7a42fa54e667385d9', '2022-09-03 10:35:55', 'admin', b'1', '2022-09-03 10:35:55', 'admin', 0, '1', '#ffffff', '1', '1353', '681', '1', '1', '10', '1', '1', '1169', '1', '827', '1', 'c9c77d24b65942fb9665fbdbe8710236', NULL, NULL, NULL);

-- ----------------------------
-- Table structure for mx_node_image
-- ----------------------------
DROP TABLE IF EXISTS `mx_node_image`;
CREATE TABLE `mx_node_image`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `image_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `image_path` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `image_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `image_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mx_node_image
-- ----------------------------
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0001', '2020-05-26 00:00:01', 'admin', b'1', '2020-05-26 00:00:01', 'admin', 0, 'task8.png', 'img/task/task8.png', 'TASK', '/img/task/task8.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0002', '2020-05-26 00:00:02', 'admin', b'1', '2020-05-26 00:00:02', 'admin', 0, 'task7.png', 'img/task/task7.png', 'TASK', '/img/task/task7.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0003', '2020-05-26 00:00:03', 'admin', b'1', '2020-05-26 00:00:03', 'admin', 0, 'task6.png', 'img/task/task6.png', 'TASK', '/img/task/task6.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0004', '2020-05-26 00:00:04', 'admin', b'1', '2020-05-26 00:00:04', 'admin', 0, 'task5.png', 'img/task/task5.png', 'TASK', '/img/task/task5.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0005', '2020-05-26 00:00:05', 'admin', b'1', '2020-05-26 00:00:05', 'admin', 0, 'task4.png', 'img/task/task4.png', 'TASK', '/img/task/task4.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0006', '2020-05-26 00:00:06', 'admin', b'1', '2020-05-26 00:00:06', 'admin', 0, 'task3.png', 'img/task/task3.png', 'TASK', '/img/task/task3.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0007', '2020-05-26 00:00:07', 'admin', b'1', '2020-05-26 00:00:07', 'admin', 0, 'task2.png', 'img/task/task2.png', 'TASK', '/img/task/task2.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0008', '2020-05-26 00:00:08', 'admin', b'1', '2020-05-26 00:00:08', 'admin', 0, 'task1.png', 'img/task/task1.png', 'TASK', '/img/task/task1.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da01725040task0009', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'task.png', 'img/task/task.png', 'TASK', '/img/task/task.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0001', '2020-05-26 00:00:09', 'admin', b'1', '2020-05-26 00:00:09', 'admin', 0, 'group.png', 'img/group/group.png', 'GROUP', '/img/group/group.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0002', '2020-05-26 00:00:08', 'admin', b'1', '2020-05-26 00:00:08', 'admin', 0, 'group1.png', 'img/group/group1.png', 'GROUP', '/img/group/group1.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0003', '2020-05-26 00:00:07', 'admin', b'1', '2020-05-26 00:00:07', 'admin', 0, 'group2.png', 'img/group/group2.png', 'GROUP', '/img/group/group2.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0004', '2020-05-26 00:00:06', 'admin', b'1', '2020-05-26 00:00:06', 'admin', 0, 'group3.png', 'img/group/group3.png', 'GROUP', '/img/group/group3.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0005', '2020-05-26 00:00:05', 'admin', b'1', '2020-05-26 00:00:05', 'admin', 0, 'group4.png', 'img/group/group4.png', 'GROUP', '/img/group/group4.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0006', '2020-05-26 00:00:04', 'admin', b'1', '2020-05-26 00:00:04', 'admin', 0, 'group5.png', 'img/group/group5.png', 'GROUP', '/img/group/group5.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0007', '2020-05-26 00:00:03', 'admin', b'1', '2020-05-26 00:00:03', 'admin', 0, 'group6.png', 'img/group/group6.png', 'GROUP', '/img/group/group6.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0008', '2020-05-26 00:00:02', 'admin', b'1', '2020-05-26 00:00:02', 'admin', 0, 'group7.png', 'img/group/group7.png', 'GROUP', '/img/group/group7.png');
INSERT INTO `mx_node_image` VALUES ('ff808181725005da0172504group0009', '2020-05-26 00:00:01', 'admin', b'1', '2020-05-26 00:00:01', 'admin', 0, 'group8.png', 'img/group/group8.png', 'GROUP', '/img/group/group8.png');

-- ----------------------------
-- Table structure for note_book
-- ----------------------------
DROP TABLE IF EXISTS `note_book`;
CREATE TABLE `note_book`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'name',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'description',
  `sessions_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '`sessions id',
  `code_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'code type',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of note_book
-- ----------------------------

-- ----------------------------
-- Table structure for process_stops_customized_property
-- ----------------------------
DROP TABLE IF EXISTS `process_stops_customized_property`;
CREATE TABLE `process_stops_customized_property`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `custom_value` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'custom value',
  `description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'description',
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'name',
  `fk_flow_process_stop_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK1ql9h2ueevqxg1xjnt06repqv`(`fk_flow_process_stop_id`) USING BTREE,
  CONSTRAINT `FK1ql9h2ueevqxg1xjnt06repqv` FOREIGN KEY (`fk_flow_process_stop_id`) REFERENCES `flow_process_stop` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of process_stops_customized_property
-- ----------------------------

-- ----------------------------
-- Table structure for property_template
-- ----------------------------
DROP TABLE IF EXISTS `property_template`;
CREATE TABLE `property_template`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `allowable_values` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `custom_value` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `description` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '描述',
  `display_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `enable_flag` bit(1) NOT NULL,
  `is_select` bit(1) NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `property_required` bit(1) NULL DEFAULT NULL,
  `property_sensitive` bit(1) NULL DEFAULT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `fk_stops_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK35p1h6w0dsmjc33eavnbuiys3`(`fk_stops_id`) USING BTREE,
  CONSTRAINT `FK35p1h6w0dsmjc33eavnbuiys3` FOREIGN KEY (`fk_stops_id`) REFERENCES `stops_template` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of property_template
-- ----------------------------

-- ----------------------------
-- Table structure for spark_jar
-- ----------------------------
DROP TABLE IF EXISTS `spark_jar`;
CREATE TABLE `spark_jar`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `jar_name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'jar name',
  `jar_url` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'jar url',
  `mount_id` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'jar mount id',
  `status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Spark jar status',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of spark_jar
-- ----------------------------

-- ----------------------------
-- Table structure for stops_hub
-- ----------------------------
DROP TABLE IF EXISTS `stops_hub`;
CREATE TABLE `stops_hub`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `jar_name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'jar name',
  `jar_url` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'jar url',
  `mount_id` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'jar mount id',
  `status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'StopsHue status',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of stops_hub
-- ----------------------------

-- ----------------------------
-- Table structure for stops_template
-- ----------------------------
DROP TABLE IF EXISTS `stops_template`;
CREATE TABLE `stops_template`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `bundel` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `description` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `enable_flag` bit(1) NOT NULL,
  `groups` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `in_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `inports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `is_checkpoint` bit(1) NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `out_port_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `outports` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `owner` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `page_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `fk_template_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FKn0wu7i6frf0xp2iypda50vlmh`(`fk_template_id`) USING BTREE,
  CONSTRAINT `FKn0wu7i6frf0xp2iypda50vlmh` FOREIGN KEY (`fk_template_id`) REFERENCES `flow_template` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of stops_template
-- ----------------------------

-- ----------------------------
-- Table structure for sys_init_records
-- ----------------------------
DROP TABLE IF EXISTS `sys_init_records`;
CREATE TABLE `sys_init_records`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `init_date` datetime(0) NOT NULL,
  `is_succeed` bit(1) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_init_records
-- ----------------------------

-- ----------------------------
-- Table structure for sys_menu
-- ----------------------------
DROP TABLE IF EXISTS `sys_menu`;
CREATE TABLE `sys_menu`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `menu_description` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'description',
  `menu_jurisdiction` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'task status',
  `menu_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'menu name',
  `menu_parent` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'task status',
  `menu_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'menu url',
  `menu_sort` int(11) NULL DEFAULT NULL COMMENT 'menu sort',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_menu
-- ----------------------------
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00001', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'Flows', 'USER', 'Flow', 'Flow', '/piflow-web/web/flowList', 100001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00002', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'Processes', 'USER', 'Process', 'Flow', '/piflow-web/web/processList', 100002);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00003', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'Templates', 'USER', 'Template', 'Flow', '/piflow-web/web/template', 100003);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00004', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'FlowGroup', 'USER', 'FlowGroup', 'Group', '/piflow-web/web/flowGroupList', 200001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00005', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'FlowGroupProcess', 'USER', 'FlowGroupProcess', 'Group', '/piflow-web/web/processGroupList', 200002);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00006', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'FlowProcess', 'USER', 'FlowProcess', 'Group', '/piflow-web/web/groupTypeProcessList', 200003);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00007', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'FlowGroupTemplate', 'USER', 'FlowGroupTemplate', 'Group', '/piflow-web/web/flowGroupTemplateList', 200004);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00008', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'Project', 'USER', 'Project', 'Project', '/piflow-web/web/instructionalVideo', 300001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00009', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'ProjectProcess', 'USER', 'ProjectProcess', 'Project', '/piflow-web/web/instructionalVideo', 300002);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00010', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'GroupProcess', 'USER', 'GroupProcess', 'Project', '/piflow-web/web/instructionalVideo', 300003);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00011', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'FlowProcess', 'USER', 'FlowProcess', 'Project', '/piflow-web/web/instructionalVideo', 300004);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00012', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'ProjectTemplate', 'USER', 'ProjectTemplate', 'Project', '/piflow-web/web/instructionalVideo', 300005);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00013', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'DataSource', 'USER', 'DataSource', '', '/piflow-web/web/dataSources', 400001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00014', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'Instruction', 'USER', 'Instruction', 'Example', '/piflow-web/web/instructionalVideo', 500001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00015', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'Example1', 'USER', 'Example1', 'Example', '/piflow-web/grapheditor/home?load=0c4fdee973824a999e1569770677c020', 500002);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be5bmenu00016', '2019-08-15 10:23:20', 'system', b'0', '2019-08-15 10:23:36', 'system', 0, 'Example2', 'USER', 'Example2', 'Example', '/piflow-web/grapheditor/home?load=c9c77d24b65942fb9665fbdbe8710236', 500003);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00001', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'Flows', 'USER', 'Flow', NULL, '/piflow-web/web/flowList', 100001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00002', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'FlowGroup', 'USER', 'Group', NULL, '/piflow-web/web/flowGroupList', 100001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00003', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'Process', 'USER', 'Process', NULL, '/piflow-web/web/processAndProcessGroup', 100002);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00004', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'FlowGroupTemplate', 'USER', 'Template', NULL, '/piflow-web/web/flowTemplateList', 100003);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00005', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'DataSource', 'USER', 'DataSource', NULL, '/piflow-web/web/dataSources', 400001);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00007', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'Example1', 'USER', 'FlowExample', 'Example', '/piflow-web/mxGraph/drawingBoard?drawingBoardType=TASK&load=0641076d5ae840c09d2be5b71fw00001', 500002);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00008', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'Example2', 'USER', 'GroupExample', 'Example', '/piflow-web/mxGraph/drawingBoard?drawingBoardType=GROUP&load=ff808181725050fe017250group10002', 500003);
INSERT INTO `sys_menu` VALUES ('0641076d5ae840c09d2be6wmenu00009', '2019-08-15 10:23:20', 'system', b'1', '2019-08-15 10:23:36', 'system', 0, 'Schedule', 'ADMIN', 'Schedule', 'Admin', '/piflow-web/web/sysScheduleList', 900001);

-- ----------------------------
-- Table structure for sys_operation_log
-- ----------------------------
DROP TABLE IF EXISTS `sys_operation_log`;
CREATE TABLE `sys_operation_log`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '用户名',
  `last_login_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '管理员地址',
  `type` int(11) NULL DEFAULT NULL COMMENT '操作分类',
  `action` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '操作动作',
  `status` tinyint(1) NULL DEFAULT NULL COMMENT '操作状态',
  `result` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '操作结果，或者成功消息，或者失败消息',
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '补充信息',
  `crt_dttm` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `last_update_dttm` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  `enable_flag` bit(1) NULL DEFAULT b'0' COMMENT '逻辑删除',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 95 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_operation_log
-- ----------------------------

-- ----------------------------
-- Table structure for sys_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `fk_sys_user_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK48hlg5qgnejc4xropo99whsyt`(`fk_sys_user_id`) USING BTREE,
  CONSTRAINT `FK48hlg5qgnejc4xropo99whsyt` FOREIGN KEY (`fk_sys_user_id`) REFERENCES `sys_user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_role
-- ----------------------------
INSERT INTO `sys_role` VALUES (1, 'ADMIN', 'bef148e608004bd8a72e658fed2f9c9f');

-- ----------------------------
-- Table structure for sys_schedule
-- ----------------------------
DROP TABLE IF EXISTS `sys_schedule`;
CREATE TABLE `sys_schedule`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `cron_expression` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'cron',
  `job_class` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'job class',
  `job_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'job name',
  `status` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'task status',
  `last_run_result` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'task last run result',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_schedule
-- ----------------------------
INSERT INTO `sys_schedule` VALUES ('ff8081816eaa8a5d016eaa8a77e40000', '2019-11-27 09:47:12', 'system', b'1', '2019-11-27 09:47:12', 'system', 0, '0/5 * * * * ?', 'com.nature.schedule.RunningProcessSync', 'RunningProcessSync', 'RUNNING', 'SUCCEED');
INSERT INTO `sys_schedule` VALUES ('ff8081816eaa9317016eaa932dd50000', '2019-11-27 09:56:43', 'system', b'1', '2019-11-27 09:56:43', 'system', 0, '0/5 * * * * ?', 'com.nature.schedule.RunningProcessGroupSync', 'RunningProcessGroupSync', 'RUNNING', 'SUCCEED');

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user`  (
  `id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL,
  `crt_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `enable_flag` bit(1) NOT NULL,
  `last_update_dttm` datetime(0) NOT NULL,
  `last_update_user` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `version` bigint(20) NULL DEFAULT NULL,
  `age` int(11) NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `sex` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `status` tinyint(3) NULL DEFAULT NULL COMMENT 'user status',
  `last_login_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'last login ip',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_user
-- ----------------------------
INSERT INTO `sys_user` VALUES ('bef148e608004bd8a72e658fed2f9c9f', '2022-09-03 10:35:55', 'system', b'1', '2022-09-03 10:35:55', 'system', 0, NULL, 'admin', '$2a$10$.PvkSt3Dxz7wopF.q.jNIecayq/b7BPB5ozELXFHxAJljN1hWbbmS', NULL, 'admin', 0, NULL);

-- ----------------------------
-- Table structure for test_data
-- ----------------------------
DROP TABLE IF EXISTS `test_data`;
CREATE TABLE `test_data`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'name',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'description',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of test_data
-- ----------------------------

-- ----------------------------
-- Table structure for test_data_schema
-- ----------------------------
DROP TABLE IF EXISTS `test_data_schema`;
CREATE TABLE `test_data_schema`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `fk_test_data_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'fk test_data id',
  `field_name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'field_name',
  `field_type` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'field_type',
  `field_description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'description',
  `field_soft` bigint(20) NULL DEFAULT NULL COMMENT 'soft',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK22rp96r4290eons0000000001`(`fk_test_data_id`) USING BTREE,
  CONSTRAINT `FK22rp96r4290eons0000000001` FOREIGN KEY (`fk_test_data_id`) REFERENCES `test_data` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of test_data_schema
-- ----------------------------

-- ----------------------------
-- Table structure for test_data_schema_values
-- ----------------------------
DROP TABLE IF EXISTS `test_data_schema_values`;
CREATE TABLE `test_data_schema_values`  (
  `id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `crt_dttm` datetime(0) NOT NULL COMMENT 'Create date time',
  `crt_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Create user',
  `enable_flag` bit(1) NOT NULL COMMENT 'Enable flag',
  `last_update_dttm` datetime(0) NOT NULL COMMENT 'Last update date time',
  `last_update_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Last update user',
  `version` bigint(20) NULL DEFAULT NULL COMMENT 'Version',
  `fk_test_data_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'fk test_data id',
  `fk_test_data_schema_id` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'fk test_data_schema id',
  `field_value` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'field type',
  `data_row` bigint(20) NULL DEFAULT NULL COMMENT 'data row',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `FK33rp96r4290eons0000000001`(`fk_test_data_id`) USING BTREE,
  INDEX `FK33rp96r4290eons0000000002`(`fk_test_data_schema_id`) USING BTREE,
  CONSTRAINT `FK33rp96r4290eons0000000001` FOREIGN KEY (`fk_test_data_id`) REFERENCES `test_data` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FK33rp96r4290eons0000000002` FOREIGN KEY (`fk_test_data_schema_id`) REFERENCES `test_data_schema` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of test_data_schema_values
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
