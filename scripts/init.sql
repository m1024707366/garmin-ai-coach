-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS garmin_coach CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE garmin_coach;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    garmin_email VARCHAR(255) UNIQUE NOT NULL,
    garmin_password TEXT NOT NULL,
    is_cn BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 活动表
CREATE TABLE IF NOT EXISTS activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    garmin_activity_id VARCHAR(255) UNIQUE,
    type VARCHAR(50),
    name VARCHAR(255),
    activity_date DATE,
    distance_km DECIMAL(10,2),
    duration_seconds INT,
    average_hr INT,
    max_hr INT,
    calories INT,
    average_cadence INT,
    average_stride_length_cm DECIMAL(5,2),
    average_ground_contact_time_ms INT,
    average_vertical_oscillation_cm DECIMAL(5,2),
    average_vertical_ratio_percent DECIMAL(5,2),
    start_time_local DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 活动分段表
CREATE TABLE IF NOT EXISTS activity_laps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activity_id INT NOT NULL,
    lap_index INT,
    distance_km DECIMAL(10,2),
    duration_seconds INT,
    average_hr INT,
    max_hr INT,
    cadence INT,
    stride_length_cm DECIMAL(5,2),
    ground_contact_time_ms INT,
    vertical_oscillation_cm DECIMAL(5,2),
    vertical_ratio_percent DECIMAL(5,2),
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Garmin每日摘要表
CREATE TABLE IF NOT EXISTS garmin_daily_summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    summary_date DATE,
    sleep_time_hours DECIMAL(5,2),
    sleep_time_seconds INT,
    steps INT,
    floors_ascended INT,
    floors_descended INT,
    active_calories INT,
    bmr_calories INT,
    total_calories INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY `unique_user_date` (`user_id`, `summary_date`)
);

-- 首页摘要缓存表
CREATE TABLE IF NOT EXISTS home_summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    latest_run_json JSON,
    week_stats_json JSON,
    month_stats_json JSON,
    ai_brief_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `unique_user` (`user_id`),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 伤病日志表
CREATE TABLE IF NOT EXISTS injury_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    log_date DATE,
    body_part VARCHAR(100),
    injury_type VARCHAR(100),
    pain_level INT,
    description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 教练记忆表（运动员档案）
CREATE TABLE IF NOT EXISTS coach_memory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    max_hr INT,
    rest_hr INT,
    vo2max DECIMAL(5,2),
    lthr INT,
    ftp INT,
    injury_history TEXT,
    training_preference TEXT,
    target_race VARCHAR(255),
    target_race_date DATE,
    pb_5k_seconds INT,
    pb_10k_seconds INT,
    pb_half_seconds INT,
    pb_full_seconds INT,
    weekly_mileage_goal_km DECIMAL(8,2),
    target_finish_time_seconds INT,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY `unique_user_memory` (`user_id`)
);

-- 插入默认测试用户（密码已加密，实际使用时需要替换）
INSERT INTO users (garmin_email, garmin_password, is_cn) VALUES ('test@example.com', 'encrypted_password_placeholder', FALSE) 
ON DUPLICATE KEY UPDATE garmin_email = garmin_email;

-- 插入示例活动数据
INSERT INTO activities (user_id, garmin_activity_id, type, name, activity_date, distance_km, duration_seconds, average_hr, max_hr)
VALUES (1, '123456789', 'Running', 'Morning Run', '2026-01-01', 20.0, 7200, 150, 180)
ON DUPLICATE KEY UPDATE garmin_activity_id = garmin_activity_id;

-- 插入示例睡眠数据
INSERT INTO garmin_daily_summaries (user_id, summary_date, sleep_time_hours, steps)
VALUES (1, '2026-01-01', 7.5, 10000)
ON DUPLICATE KEY UPDATE user_id = user_id;
