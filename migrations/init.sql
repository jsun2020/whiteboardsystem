-- Initial database setup for Meeting Whiteboard Scribe
-- This script creates the necessary tables for the application

-- Users table with authentication and subscription management
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    email VARCHAR(120) UNIQUE,
    username VARCHAR(80) UNIQUE,
    password_hash VARCHAR(255),
    display_name VARCHAR(120),
    
    -- Account status
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- Session tracking
    session_token VARCHAR(36) UNIQUE,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Usage tracking
    projects_created INTEGER DEFAULT 0,
    images_processed INTEGER DEFAULT 0,
    exports_generated INTEGER DEFAULT 0,
    free_uses_count INTEGER DEFAULT 0,
    
    -- Payment and subscription
    subscription_type VARCHAR(20) DEFAULT 'free',
    subscription_expires_at DATETIME,
    payment_status VARCHAR(20) DEFAULT 'none',
    custom_api_key TEXT,
    
    -- Settings
    preferred_language VARCHAR(10) DEFAULT 'en',
    theme_preference VARCHAR(10) DEFAULT 'light',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id VARCHAR(36),
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    
    -- Analysis results
    analysis_result TEXT, -- JSON
    confidence_score FLOAT DEFAULT 0.0,
    
    -- Sharing
    is_public BOOLEAN DEFAULT FALSE,
    share_token VARCHAR(36) UNIQUE,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Whiteboards table
CREATE TABLE IF NOT EXISTS whiteboards (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    project_id VARCHAR(36),
    user_id VARCHAR(36),
    
    -- File information
    filename VARCHAR(255),
    original_filename VARCHAR(255),
    file_size INTEGER,
    file_type VARCHAR(50),
    
    -- Paths
    original_path TEXT,
    processed_path TEXT,
    
    -- Processing status
    status VARCHAR(20) DEFAULT 'uploaded',
    
    -- Analysis results
    extracted_text TEXT,
    structured_content TEXT, -- JSON
    regions TEXT, -- JSON
    confidence_score FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Exports table
CREATE TABLE IF NOT EXISTS exports (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    project_id VARCHAR(36),
    user_id VARCHAR(36),
    
    -- Export information
    export_type VARCHAR(50), -- markdown, pptx, mindmap, notion, confluence
    filename VARCHAR(255),
    file_path TEXT,
    file_size INTEGER,
    
    -- Export options
    export_options TEXT, -- JSON
    
    -- Status
    status VARCHAR(20) DEFAULT 'generating',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME, -- For cleanup
    
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_session_token ON users(session_token);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_type, payment_status);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_whiteboards_project_id ON whiteboards(project_id);
CREATE INDEX IF NOT EXISTS idx_whiteboards_user_id ON whiteboards(user_id);
CREATE INDEX IF NOT EXISTS idx_exports_project_id ON exports(project_id);
CREATE INDEX IF NOT EXISTS idx_exports_user_id ON exports(user_id);