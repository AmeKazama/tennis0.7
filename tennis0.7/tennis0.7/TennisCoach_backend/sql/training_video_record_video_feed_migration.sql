-- 首页短视频/私人视频库增量字段
-- 如果 training_video_record 已经存在，请让数据库成员按实际数据库情况执行本文件。
-- MySQL 8.0.29+ 支持 ADD COLUMN IF NOT EXISTS；较低版本可先 SHOW COLUMNS 后手动添加。

ALTER TABLE `training_video_record`
  ADD COLUMN IF NOT EXISTS `description` TEXT DEFAULT NULL COMMENT '视频描述/发布文案' AFTER `title`,
  ADD COLUMN IF NOT EXISTS `visibility` VARCHAR(20) NOT NULL DEFAULT 'private' COMMENT '可见性：private/public/friends' AFTER `score`,
  ADD COLUMN IF NOT EXISTS `status` VARCHAR(20) NOT NULL DEFAULT 'uploaded' COMMENT '状态：uploaded/published/deleted' AFTER `visibility`,
  ADD COLUMN IF NOT EXISTS `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数' AFTER `status`,
  ADD COLUMN IF NOT EXISTS `comment_count` INT NOT NULL DEFAULT 0 COMMENT '评论数' AFTER `like_count`,
  ADD COLUMN IF NOT EXISTS `favorite_count` INT NOT NULL DEFAULT 0 COMMENT '收藏数' AFTER `comment_count`,
  ADD COLUMN IF NOT EXISTS `view_count` INT NOT NULL DEFAULT 0 COMMENT '播放/浏览数' AFTER `favorite_count`,
  ADD COLUMN IF NOT EXISTS `publish_time` DATETIME DEFAULT NULL COMMENT '发布时间' AFTER `view_count`,
  ADD COLUMN IF NOT EXISTS `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER `create_time`;

CREATE INDEX `idx_training_video_visibility_status`
  ON `training_video_record` (`visibility`, `status`);

CREATE INDEX `idx_training_video_publish_time`
  ON `training_video_record` (`publish_time`);
