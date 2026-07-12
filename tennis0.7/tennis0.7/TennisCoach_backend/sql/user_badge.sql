CREATE TABLE IF NOT EXISTS `user_badge` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `badge_code` VARCHAR(80) NOT NULL COMMENT '勋章编码',
  `badge_name` VARCHAR(120) NOT NULL COMMENT '勋章名称',
  `badge_icon` VARCHAR(500) DEFAULT NULL COMMENT '勋章图标URL',
  `description` VARCHAR(255) DEFAULT NULL COMMENT '勋章说明',
  `earned_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '获得时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_badge` (`user_id`, `badge_code`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_badge_code` (`badge_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户荣誉勋章表';
