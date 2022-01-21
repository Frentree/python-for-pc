-- DROP TABLE IF EXISTS `drm_config`;
-- CREATE TABLE `drm_config` (
--     `mnt_time` datetime DEFAULT NULL COMMENT '모니터 시간',
--     `job_time` datetime DEFAULT NULL COMMENT '일한 시간'
-- );
-- 
-- DROP TABLE IF EXISTS `drm_job`;
-- CREATE TABLE `drm_job` (
--     `index` int(11) NOT NULL AUTO_INCREMENT COMMENT 'index',
--     `path` text DEFAULT NULL COMMENT '경로',
--     `type` varchar(10) DEFAULT NULL COMMENT '암호화 또는 복호화',
--     PRIMARY KEY(`index`) USING BTREE
-- );
-- 
-- DROP TABLE IF EXISTS `drm_resource`;
-- CREATE TABLE `drm_resource` (
--     `index` int(11) NOT NULL AUTO_INCREMENT COMMENT 'drm 리소스 아이디',
--     `timestamp` datetime NOT NULL COMMENT '시간',
--     `hostname` varchar(200) NOT NULL COMMENT '호스트 이름',
--     `total_cpu` varchar(100) DEFAULT NULL COMMENT '전체 cpu',
--     `total_disk` varchar(50) DEFAULT NULL COMMENT '전체 disk',
--     `total_network` varchar(50) DEFAULT NULL COMMENT '전체 network',
--     `specific_cpu` varchar(100) DEFAULT NULL COMMENT '사용 cpu',
--     `specific_memory` varchar(40) DEFAULT NULL COMMENT '사용 memory',
--     `specific_disk` varchar(100) DEFAULT NULL COMMENT '사용 disk',
--     `specific_network` varchar(50) DEFAULT NULL COMMENT '사용 network',
--     PRIMARY KEY(`index`,`hostname`) USING BTREE
-- );
-- 
-- DROP TABLE IF EXISTS `drm_log`;
-- CREATE table `drm_log` (
--     `index` int(11) NOT NULL AUTO_INCREMENT,
--     `timestamp` datetime NOT NULL COMMENT '시간',
--     `hostname` varchar(200) NOT NULL COMMENT '호스트 이름',
--     `path` text DEFAULT NULL COMMENT '경로',
--     PRIMARY KEY(`index`,`hostname`) USING BTREE
-- );

delete from drm_job;
insert into drm_job (`path`, `type`) values('C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\PyClient\\한글.txt', 'decrypt');
insert into drm_job (`path`, `type`) values('C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\PyClient\\한글.txt', 'is_encrypt');

