CREATE TABLE IF NOT EXISTS `training_video_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `title` VARCHAR(120) DEFAULT NULL COMMENT '视频标题',
  `video_url` VARCHAR(500) NOT NULL COMMENT '视频URL或存储路径',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '封面URL',
  `duration_seconds` DOUBLE DEFAULT NULL COMMENT '视频时长，秒',
  `file_size` BIGINT DEFAULT NULL COMMENT '文件大小，字节',
  `source_type` VARCHAR(30) NOT NULL DEFAULT 'upload' COMMENT '来源：camera/album/upload/analysis',
  `analysis_id` VARCHAR(64) DEFAULT NULL COMMENT '关联动作分析任务ID',
  `shot_type` VARCHAR(40) DEFAULT NULL COMMENT '主要动作类型：forehand/backhand/serve/mixed',
  `score` DOUBLE DEFAULT NULL COMMENT '关联分析评分，0-100',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_analysis_id` (`analysis_id`),
  KEY `idx_shot_type` (`shot_type`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='训练视频记录表';
