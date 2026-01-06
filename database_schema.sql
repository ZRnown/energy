-- 能量租赁机器人数据库表结构
-- 执行前请确保数据库已创建：CREATE DATABASE energy_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE energy_bot;

-- 1. 能量AI笔数套餐表
CREATE TABLE energy_ai_bishu (
    rid BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    tg_uid VARCHAR(50) NOT NULL COMMENT 'Telegram用户ID',
    wallet_addr VARCHAR(100) NOT NULL COMMENT '钱包地址',
    bot_token VARCHAR(200) NOT NULL COMMENT '机器人Token',
    per_bishu_energy_quantity BIGINT DEFAULT 0 COMMENT '每笔能量数量',
    bot_username VARCHAR(100) COMMENT '机器人用户名',
    bot_admin_username VARCHAR(100) COMMENT '管理员用户名',
    max_buy_quantity INT DEFAULT 0 COMMENT '最大购买数量',
    total_buy_quantity INT DEFAULT 0 COMMENT '已购买总数量',
    status TINYINT DEFAULT 0 COMMENT '状态：0-正常，1-暂停',
    is_buy VARCHAR(1) DEFAULT 'N' COMMENT '是否购买：Y-是，N-否',
    is_notice VARCHAR(1) DEFAULT 'N' COMMENT '是否通知：Y-是，N-否',
    is_notice_admin VARCHAR(1) DEFAULT 'N' COMMENT '是否通知管理员：Y-是，N-否',
    tg_admin_uid VARCHAR(50) COMMENT '管理员Telegram ID',
    comments TEXT COMMENT '备注',
    tg_notice_obj_send TEXT COMMENT '通知对象',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_wallet_addr (wallet_addr),
    INDEX idx_tg_uid (tg_uid),
    INDEX idx_status (status),
    INDEX idx_is_notice (is_notice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能量AI笔数套餐表';

-- 2. 能量AI托管表
CREATE TABLE energy_ai_trusteeship (
    rid BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    tg_uid VARCHAR(50) NOT NULL COMMENT 'Telegram用户ID',
    wallet_addr VARCHAR(100) NOT NULL COMMENT '钱包地址',
    bot_token VARCHAR(200) NOT NULL COMMENT '机器人Token',
    per_buy_energy_quantity BIGINT DEFAULT 0 COMMENT '每次购买能量数量',
    bot_username VARCHAR(100) COMMENT '机器人用户名',
    bot_admin_username VARCHAR(100) COMMENT '管理员用户名',
    max_buy_quantity INT DEFAULT 0 COMMENT '最大购买数量',
    total_buy_energy_quantity BIGINT DEFAULT 0 COMMENT '总能量购买数量',
    current_energy_quantity BIGINT DEFAULT 0 COMMENT '当前能量数量',
    total_used_trx DECIMAL(20,6) DEFAULT 0 COMMENT '总使用TRX',
    total_buy_quantity INT DEFAULT 0 COMMENT '总购买次数',
    status TINYINT DEFAULT 0 COMMENT '状态：0-正常，1-暂停',
    is_buy VARCHAR(1) DEFAULT 'N' COMMENT '是否购买：Y-是，N-否',
    is_notice VARCHAR(1) DEFAULT 'N' COMMENT '是否通知：Y-是，N-否',
    is_notice_admin VARCHAR(1) DEFAULT 'N' COMMENT '是否通知管理员：Y-是，N-否',
    tg_admin_uid VARCHAR(50) COMMENT '管理员Telegram ID',
    comments TEXT COMMENT '备注',
    tg_notice_obj_send TEXT COMMENT '通知对象',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_wallet_addr (wallet_addr),
    INDEX idx_tg_uid (tg_uid),
    INDEX idx_status (status),
    INDEX idx_is_buy (is_buy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能量AI托管表';

-- 3. 能量平台表
CREATE TABLE energy_platform (
    rid BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    platform_name VARCHAR(100) NOT NULL COMMENT '平台名称',
    platform_balance DECIMAL(20,6) DEFAULT 0 COMMENT '平台余额',
    platform_wallet_addr VARCHAR(100) COMMENT '平台钱包地址',
    api_url VARCHAR(500) COMMENT 'API地址',
    api_key VARCHAR(200) COMMENT 'API密钥',
    status TINYINT DEFAULT 0 COMMENT '状态：0-正常，1-暂停',
    seq_sn INT DEFAULT 0 COMMENT '排序序号',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_status (status),
    INDEX idx_seq_sn (seq_sn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能量平台表';

-- 4. 能量平台机器人表
CREATE TABLE energy_platform_bot (
    rid BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    bot_rid BIGINT NOT NULL COMMENT '机器人ID',
    platform_rid BIGINT NOT NULL COMMENT '平台ID',
    bot_name VARCHAR(100) COMMENT '机器人名称',
    status TINYINT DEFAULT 0 COMMENT '状态：0-正常，1-暂停',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_bot_rid (bot_rid),
    INDEX idx_platform_rid (platform_rid),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能量平台机器人表';

-- 5. 能量平台订单表
CREATE TABLE energy_platform_order (
    rid BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    platform_rid BIGINT NOT NULL COMMENT '平台ID',
    order_no VARCHAR(100) NOT NULL COMMENT '订单号',
    trx_amount DECIMAL(20,6) NOT NULL COMMENT 'TRX金额',
    energy_amount BIGINT NOT NULL COMMENT '能量数量',
    order_status TINYINT DEFAULT 0 COMMENT '订单状态：0-待处理，1-处理中，2-完成，3-失败',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_order_no (order_no),
    INDEX idx_platform_rid (platform_rid),
    INDEX idx_order_status (order_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能量平台订单表';

-- 6. 能量平台套餐表
CREATE TABLE energy_platform_package (
    rid BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    bot_rid BIGINT NOT NULL COMMENT '机器人ID',
    platform_rid BIGINT NOT NULL COMMENT '平台ID',
    trx_price DECIMAL(20,6) NOT NULL COMMENT 'TRX价格',
    energy_amount BIGINT NOT NULL COMMENT '能量数量',
    status TINYINT DEFAULT 0 COMMENT '状态：0-正常，1-暂停',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_bot_rid (bot_rid),
    INDEX idx_platform_rid (platform_rid),
    INDEX idx_trx_price (trx_price),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能量平台套餐表';

-- 7. 能量钱包交易列表表
CREATE TABLE energy_wallet_trade_list (
    rid BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    wallet_addr VARCHAR(100) NOT NULL COMMENT '钱包地址',
    transferto_address VARCHAR(100) NOT NULL COMMENT '转入地址',
    coin_name VARCHAR(20) NOT NULL COMMENT '币种名称',
    amount DECIMAL(30,6) NOT NULL COMMENT '金额',
    tx_hash VARCHAR(100) NOT NULL COMMENT '交易哈希',
    transfer_timestamp BIGINT NOT NULL COMMENT '转账时间戳',
    block_number BIGINT COMMENT '区块号',
    block_timestamp BIGINT COMMENT '区块时间戳',
    process_status TINYINT DEFAULT 1 COMMENT '处理状态：1-待处理，2-处理中，9-完成，99-失败',
    process_comments TEXT COMMENT '处理备注',
    process_time DATETIME COMMENT '处理时间',
    tg_uid VARCHAR(50) COMMENT 'Telegram用户ID',
    tg_notice_status_receive VARCHAR(1) DEFAULT 'N' COMMENT '接收通知状态：Y-已发送，N-未发送',
    tg_notice_status_send VARCHAR(1) DEFAULT 'N' COMMENT '发送通知状态：Y-已发送，N-未发送',
    energy_amount BIGINT DEFAULT 0 COMMENT '能量数量',
    bot_token VARCHAR(200) COMMENT '机器人Token',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_tx_hash (tx_hash),
    INDEX idx_wallet_addr (wallet_addr),
    INDEX idx_transferto_address (transferto_address),
    INDEX idx_process_status (process_status),
    INDEX idx_transfer_timestamp (transfer_timestamp),
    INDEX idx_tg_uid (tg_uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能量钱包交易列表表';

-- 8. 插入基础数据

-- 插入能量平台数据
INSERT INTO energy_platform (platform_name, platform_balance, status, seq_sn) VALUES
('nee.cc', 1000.000000, 0, 1),
('RentEnergysBot', 1000.000000, 0, 2),
('自己质押', 10000.000000, 0, 3);

-- 插入平台机器人关联
INSERT INTO energy_platform_bot (bot_rid, platform_rid, bot_name, status) VALUES
(1, 1, 'nee.cc_bot', 0),
(1, 2, 'rent_energy_bot', 0),
(1, 3, 'self_stake_bot', 0);

-- 插入平台套餐数据
INSERT INTO energy_platform_package (bot_rid, platform_rid, trx_price, energy_amount, status) VALUES
(1, 1, 2.5, 65000, 0),
(1, 1, 5.0, 131000, 0),
(1, 2, 2.5, 65000, 0),
(1, 2, 5.0, 131000, 0),
(1, 3, 0.01, 131000, 0); -- 自己质押成本几乎为0
