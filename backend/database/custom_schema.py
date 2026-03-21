# 文件位置: backend/database/custom_schema.py
# 🟢 作用：存放当前项目所有专属的、带物理外键的底层流水表/静态表

def execute_custom_static_tables(cursor):
    """在此处编写所有不需要 JSON 驱动的底层表 SQL"""
    # =========================================================
    # 🏗️ 核心业务表 1：收款计划表 (契约层)
    # 作用：记录合同约定的里程碑节点，用于预测未来的现金流和生成催款计划。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_payment_plans (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            main_contract_code VARCHAR(100) NOT NULL,  -- 归属主合同
            milestone_name VARCHAR(255),               -- 款项节点
            payment_ratio NUMERIC(5,2) DEFAULT 0.00,   -- 比例
            planned_amount NUMERIC(15,2) DEFAULT 0.00, -- 计划金额
            operator VARCHAR(50),                      -- 操作人
            planned_date DATE,                         -- 预警日期
            conditions TEXT,                           -- 付款条件
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,         -- 软删除
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 2：发票记录表 (财务层)
    # 作用：记录税务义务的履行，是计算“财务应收账款”和“未开票收入”的核心。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_invoices (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            main_contract_code VARCHAR(100) NOT NULL,  -- 宏观挂靠主合同
            target_plan_code VARCHAR(100),             -- 微观认领收款计划 (对应哪一期付款)
            invoice_amount NUMERIC(15,2) DEFAULT 0.00, -- 开票金额
            invoice_date DATE,                         -- 开票日期
            invoice_number VARCHAR(100),               -- 发票号码
            invoice_type VARCHAR(50),                  -- 发票类型 (如: 专票, 普票)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 3：资金流水表 (执行层)
    # 作用：记录银行实际进出的真金白银。支持多笔流水核销一张发票，或一笔流水对应多个合同。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_collections (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            main_contract_code VARCHAR(100) NOT NULL,  -- 宏观挂靠主合同
            target_plan_code VARCHAR(100),             -- 微观认领收款计划
            related_invoice_code VARCHAR(100),         -- (可选) 关联的特定发票单号
            collected_amount NUMERIC(15,2) DEFAULT 0.00, -- 到账金额
            collected_date DATE,                       -- 到账日期
            update_project_stage VARCHAR(100),         -- 🟢 顺手更新项目阶段 (放在这里最合适)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 4：变更协议表 (演变层)
    # 作用：记录合同生命周期内的增减项，动态推演“最新合同额”。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_change_orders (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,             -- 关联合同编号
            change_no VARCHAR(100) NOT NULL,            -- 变更单/签证单编号
            change_amount NUMERIC(15,2) DEFAULT 0.00,   -- 变更金额 (支持负数表示核减)
            change_date DATE,                           -- 变更发生/确认日期
            approval_status VARCHAR(50) DEFAULT '审批中',-- 审批状态 (草稿 / 审批中 / 已生效)
            change_reason TEXT,                         -- 变更原因说明
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 5：质保/保证金表 (风险层)
    # 作用：管理被扣留的资金池，预警到期未退的保证金。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_retentions (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,             -- 关联合同编号
            retention_type VARCHAR(50),                 -- 保证金类型 (履约保证金 / 质保金 / 农民工工资保证金)
            retention_amount NUMERIC(15,2) DEFAULT 0.00,-- 扣留/缴纳金额
            due_date DATE,                              -- 预计解冻/返还日期
            actual_return_date DATE,                    -- 实际返还日期
            status VARCHAR(50) DEFAULT '未解冻',         -- 状态 (未解冻 / 已到期 / 已全额返还 / 已扣除抵扣)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
     # =========================================================
    # 🏗️ 核心业务表 6：对外付款流水表 
    # 作用：记录分包合合同的付款流水。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_outbound_payments (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            sub_contract_code VARCHAR(100) NOT NULL,   -- 认领分包合同
            payment_amount NUMERIC(15,2) DEFAULT 0.00, -- 实际付款金额
            payment_date DATE,                         -- 付款日期
            payment_method VARCHAR(50),                -- 支付方式(电汇/承兑等)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # =========================================================
    # 🏗️ 核心业务表 7：分包进项发票表 (分包侧 - 纯票据流入)
    # 🟢 新增：独立管理分包商开过来的发票，用于防范“欠票风险”
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_sub_invoices (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            sub_contract_code VARCHAR(100) NOT NULL,   -- 认领分包合同
            invoice_amount NUMERIC(15,2) DEFAULT 0.00, -- 收票金额
            invoice_date DATE,                         -- 收票/开票日期
            invoice_number VARCHAR(100),               -- 发票号码
            invoice_type VARCHAR(50),                  -- 发票类型(如:增值税专用发票)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
   # ==========================================
    # 🚀 [第三战区] 物理性能加速 (高频查询索引)
    # ==========================================
    
    
    # 主合同侧索引
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_plan_main" ON biz_payment_plans(main_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_inv_main" ON biz_invoices(main_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_inv_plan" ON biz_invoices(target_plan_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_col_main" ON biz_collections(main_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_col_plan" ON biz_collections(target_plan_code);')

    # 通用表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_change_biz" ON sys_change_orders(biz_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_retention_biz" ON sys_retentions(biz_code);')

    # 🟢 分包侧索引 (双剑合璧)
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_out_sub" ON biz_outbound_payments(sub_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_sub_inv_sub" ON biz_sub_invoices(sub_contract_code);')