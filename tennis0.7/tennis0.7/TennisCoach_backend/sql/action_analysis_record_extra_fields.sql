-- 为已有 action_analysis_record 表补充统计友好的字段。
-- 如果你是新建库，可以先执行 action_analysis_record.sql，再执行本文件。

ALTER TABLE `action_analysis_record`
  ADD COLUMN `training_duration_seconds` DOUBLE DEFAULT NULL COMMENT '本次视频/训练时长，秒' AFTER `distance`,
  ADD COLUMN `segment_count` INT NOT NULL DEFAULT 0 COMMENT '识别到的动作片段数' AFTER `training_duration_seconds`,
  ADD COLUMN `score` DOUBLE DEFAULT NULL COMMENT '本次分析换算评分，0-100' AFTER `segment_count`,
  ADD COLUMN `forehand_score` DOUBLE DEFAULT NULL COMMENT '本次正手平均分' AFTER `score`,
  ADD COLUMN `backhand_score` DOUBLE DEFAULT NULL COMMENT '本次反手平均分' AFTER `forehand_score`,
  ADD COLUMN `serve_score` DOUBLE DEFAULT NULL COMMENT '本次发球平均分' AFTER `backhand_score`,
  ADD COLUMN `forehand_count` INT NOT NULL DEFAULT 0 COMMENT '本次正手片段数' AFTER `serve_score`,
  ADD COLUMN `backhand_count` INT NOT NULL DEFAULT 0 COMMENT '本次反手片段数' AFTER `forehand_count`,
  ADD COLUMN `serve_count` INT NOT NULL DEFAULT 0 COMMENT '本次发球片段数' AFTER `backhand_count`,
  ADD COLUMN `pose_video_url` VARCHAR(500) DEFAULT NULL COMMENT '用户骨骼回放视频URL' AFTER `serve_count`,
  ADD COLUMN `standard_video_url` VARCHAR(500) DEFAULT NULL COMMENT '标准骨骼回放视频URL' AFTER `pose_video_url`,
  ADD COLUMN `worst_phase` VARCHAR(80) DEFAULT NULL COMMENT '差异最大的动作阶段' AFTER `standard_video_url`,
  ADD COLUMN `worst_keyframe` VARCHAR(80) DEFAULT NULL COMMENT '差异最大的关键帧' AFTER `worst_phase`;
