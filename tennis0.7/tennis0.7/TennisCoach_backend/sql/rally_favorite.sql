CREATE TABLE IF NOT EXISTS `rally_favorite` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `video_key` CHAR(64) NOT NULL COMMENT '视频URL的SHA-256，用于去重',
  `video_url` VARCHAR(1000) NOT NULL COMMENT '回合视频地址',
  `poster_url` VARCHAR(1000) DEFAULT NULL COMMENT '首帧封面地址',
  `title` VARCHAR(120) DEFAULT NULL COMMENT '展示标题',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rally_favorite_user_video` (`user_id`, `video_key`),
  KEY `idx_rally_favorite_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏的回合片段';
