-- =============================================================================
-- Acme Store — Enterprise Customer Support AI/ML Platform
-- PostgreSQL Database Schema
-- SYNTHETIC DATA — For development and AI/ML experimentation only
-- =============================================================================

-- Enable pgvector extension (for future RAG pipeline)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- customers
-- =============================================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id         VARCHAR(12) PRIMARY KEY,                  -- CUS-XXXX
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255) NOT NULL UNIQUE,
    phone               VARCHAR(30),
    customer_segment    VARCHAR(20) NOT NULL CHECK (customer_segment IN ('standard','premium','business','enterprise')),
    account_status      VARCHAR(20) NOT NULL CHECK (account_status IN ('active','inactive','suspended')),
    country             VARCHAR(3) NOT NULL DEFAULT 'US',
    state               VARCHAR(50),
    city                VARCHAR(100),
    registration_date   DATE NOT NULL,
    preferred_language  VARCHAR(5) NOT NULL DEFAULT 'en',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(customer_segment);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(account_status);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- =============================================================================
-- products
-- =============================================================================
CREATE TABLE IF NOT EXISTS products (
    product_id          VARCHAR(10) PRIMARY KEY,                  -- PROD-XXX
    sku                 VARCHAR(30) NOT NULL UNIQUE,
    product_name        VARCHAR(255) NOT NULL,
    category            VARCHAR(50) NOT NULL,
    subcategory         VARCHAR(50),
    description         TEXT,
    price               NUMERIC(10,2) NOT NULL CHECK (price > 0),
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    stock_status        VARCHAR(20) NOT NULL CHECK (stock_status IN ('in_stock','out_of_stock','discontinued')),
    warranty_months     INTEGER NOT NULL CHECK (warranty_months > 0),
    return_window_days  INTEGER NOT NULL CHECK (return_window_days > 0),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock_status);

-- =============================================================================
-- orders
-- =============================================================================
CREATE TABLE IF NOT EXISTS orders (
    order_id                VARCHAR(12) PRIMARY KEY,              -- ORD-XXXXX
    customer_id             VARCHAR(12) NOT NULL REFERENCES customers(customer_id),
    order_date              DATE NOT NULL,
    product_id              VARCHAR(10) NOT NULL REFERENCES products(product_id),
    quantity                INTEGER NOT NULL CHECK (quantity > 0),
    unit_price              NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    total_amount            NUMERIC(10,2) NOT NULL CHECK (total_amount > 0),
    currency                VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_method          VARCHAR(30) NOT NULL CHECK (payment_method IN ('credit_card','debit_card','paypal','bank_transfer','crypto')),
    payment_status          VARCHAR(30) NOT NULL CHECK (payment_status IN ('pending','paid','failed','refunded','partially_refunded')),
    order_status            VARCHAR(30) NOT NULL CHECK (order_status IN ('placed','confirmed','processing','shipped','out_for_delivery','delivered','delayed','cancelled','returned','refunded')),
    shipping_method         VARCHAR(20) NOT NULL CHECK (shipping_method IN ('standard','express','next_day','international')),
    tracking_number         VARCHAR(50),
    expected_delivery_date  DATE,
    actual_delivery_date    DATE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_delivery_dates CHECK (
        actual_delivery_date IS NULL OR actual_delivery_date >= order_date
    )
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);

-- =============================================================================
-- support_tickets
-- =============================================================================
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id                   VARCHAR(10) PRIMARY KEY,          -- TKT-XXXX
    customer_id                 VARCHAR(12) NOT NULL REFERENCES customers(customer_id),
    order_id                    VARCHAR(12) REFERENCES orders(order_id),
    product_id                  VARCHAR(10) REFERENCES products(product_id),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel                     VARCHAR(10) NOT NULL CHECK (channel IN ('web','email','chat','phone')),
    subject                     VARCHAR(500),
    message                     TEXT NOT NULL,
    category                    VARCHAR(20) NOT NULL CHECK (category IN ('shipping','returns','refunds','payments','orders','products','warranty','account','technical','security')),
    subcategory                 VARCHAR(50),
    intent                      VARCHAR(100),
    priority                    VARCHAR(3) NOT NULL CHECK (priority IN ('P0','P1','P2','P3')),
    sentiment                   VARCHAR(10) CHECK (sentiment IN ('positive','neutral','negative','angry')),
    assigned_team               VARCHAR(30),
    status                      VARCHAR(30) NOT NULL CHECK (status IN ('open','in_progress','waiting_for_customer','resolved','closed')),
    resolution                  TEXT,
    resolution_code             VARCHAR(50),
    resolution_time_minutes     INTEGER,
    escalated                   BOOLEAN NOT NULL DEFAULT FALSE,
    escalation_reason           TEXT,
    customer_satisfaction       SMALLINT CHECK (customer_satisfaction BETWEEN 1 AND 5),
    first_response_time_minutes INTEGER,
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_customer ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_order ON support_tickets(order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON support_tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created ON support_tickets(created_at);

-- =============================================================================
-- conversations
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id         VARCHAR(12) PRIMARY KEY,              -- CONV-XXXX
    customer_id             VARCHAR(12) NOT NULL REFERENCES customers(customer_id),
    channel                 VARCHAR(10) NOT NULL CHECK (channel IN ('web','email','chat','phone')),
    started_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at                TIMESTAMPTZ,
    primary_intent          VARCHAR(100),
    resolution              VARCHAR(20) CHECK (resolution IN ('resolved','escalated','unresolved')),
    escalated               BOOLEAN NOT NULL DEFAULT FALSE,
    customer_satisfaction   SMALLINT CHECK (customer_satisfaction BETWEEN 1 AND 5),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_customer ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversations_started ON conversations(started_at);

-- =============================================================================
-- conversation_messages
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversation_messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id VARCHAR(12) NOT NULL REFERENCES conversations(conversation_id),
    turn_id         INTEGER NOT NULL,
    speaker         VARCHAR(10) NOT NULL CHECK (speaker IN ('customer','agent','system')),
    message         TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB,
    UNIQUE (conversation_id, turn_id)
);

CREATE INDEX IF NOT EXISTS idx_conv_messages_conv ON conversation_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conv_messages_ts ON conversation_messages(timestamp);
