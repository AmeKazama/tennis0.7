-- 朋友圈数据表结构
-- 执行前请确保已创建 tennis0.7 数据库

-- 朋友圈动态表
CREATE TABLE IF NOT EXISTS `moments` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `content` TEXT NOT NULL COMMENT '动态内容',
    `images` TEXT COMMENT '图片JSON数组',
    `video_url` VARCHAR(500) COMMENT '视频URL',
    `location` VARCHAR(200) COMMENT '位置',
    `likes_count` INT DEFAULT 0 COMMENT '点赞数',
    `comments_count` INT DEFAULT 0 COMMENT '评论数',
    `shares_count` INT DEFAULT 0 COMMENT '分享数',
    `is_top` INT DEFAULT 0 COMMENT '是否置顶 0-否 1-是',
    `visibility` VARCHAR(20) DEFAULT 'public' COMMENT '可见性 public/friends/private',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='朋友圈动态表';

-- 动态点赞表
CREATE TABLE IF NOT EXISTS `moment_likes` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `moment_id` BIGINT NOT NULL COMMENT '动态ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
    UNIQUE INDEX `idx_moment_user` (`moment_id`, `user_id`),
    INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态点赞表';

-- 动态评论表
CREATE TABLE IF NOT EXISTS `moment_comments` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `moment_id` BIGINT NOT NULL COMMENT '动态ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `parent_id` BIGINT COMMENT '父评论ID（回复）',
    `content` TEXT NOT NULL COMMENT '评论内容',
    `likes_count` INT DEFAULT 0 COMMENT '点赞数',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_moment_id` (`moment_id`),
    INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态评论表';

-- 动态分享表
CREATE TABLE IF NOT EXISTS `moment_shares` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `moment_id` BIGINT NOT NULL COMMENT '动态ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `share_type` VARCHAR(20) DEFAULT 'internal' COMMENT '分享类型 internal/wechat/friend_circle',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分享时间',
    INDEX `idx_moment_id` (`moment_id`),
    INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态分享表';

-- 朋友圈数据统计表（按日聚合）
CREATE TABLE IF NOT EXISTS `moment_stats` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `stat_date` DATETIME NOT NULL COMMENT '统计日期',
    `posts_count` INT DEFAULT 0 COMMENT '发布动态数',
    `likes_received` INT DEFAULT 0 COMMENT '收到的点赞数',
    `comments_received` INT DEFAULT 0 COMMENT '收到的评论数',
    `shares_received` INT DEFAULT 0 COMMENT '收到的分享数',
    `likes_given` INT DEFAULT 0 COMMENT '发出的点赞数',
    `comments_given` INT DEFAULT 0 COMMENT '发出的评论数',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE INDEX `idx_user_date` (`user_id`, `stat_date`),
    INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='朋友圈数据统计表';
