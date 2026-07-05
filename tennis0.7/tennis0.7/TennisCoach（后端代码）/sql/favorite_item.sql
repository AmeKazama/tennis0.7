CREATE TABLE IF NOT EXISTS `favorite_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `folder_id` BIGINT DEFAULT NULL COMMENT '收藏夹ID',
  `target_type` VARCHAR(30) NOT NULL COMMENT '收藏对象类型：post/video/analysis/course',
  `target_id` BIGINT NOT NULL COMMENT '收藏对象ID',
  `title` VARCHAR(120) DEFAULT NULL COMMENT '展示标题',
  `poster_url` VARCHAR(500) DEFAULT NULL COMMENT '展示封面',
  `author_name` VARCHAR(80) DEFAULT NULL COMMENT '作者名称',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_target` (`user_id`, `target_type`, `target_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_folder_id` (`folder_id`),
  KEY `idx_target` (`target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏内容表';
