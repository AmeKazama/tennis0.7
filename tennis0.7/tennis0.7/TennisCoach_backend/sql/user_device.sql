CREATE TABLE IF NOT EXISTS `user_device` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `device_name` VARCHAR(120) NOT NULL COMMENT '设备名称',
  `device_type` VARCHAR(50) DEFAULT NULL COMMENT '设备类型：watch/sensor/racket/phone',
  `device_sn` VARCHAR(120) DEFAULT NULL COMMENT '设备序列号',
  `bind_status` VARCHAR(30) NOT NULL DEFAULT 'active' COMMENT '绑定状态：active/inactive/unbound',
  `last_active_time` DATETIME DEFAULT NULL COMMENT '最近活跃时间',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_device_sn` (`device_sn`),
  KEY `idx_bind_status` (`bind_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户设备表';
