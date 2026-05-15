-- users table
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub VARCHAR(128) UNIQUE NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- columns table
CREATE TABLE IF NOT EXISTS columns (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title      VARCHAR(100) NOT NULL,
    color      VARCHAR(20)  NOT NULL DEFAULT '#64748b',
    position   INTEGER      NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    column_id   UUID         NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    priority    VARCHAR(10)  NOT NULL DEFAULT 'medium',
    position    INTEGER      NOT NULL DEFAULT 0,
    created_by  UUID         REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- indexes
CREATE INDEX IF NOT EXISTS idx_tasks_column   ON tasks(column_id);
CREATE INDEX IF NOT EXISTS idx_tasks_position ON tasks(column_id, position);

-- seed: default kanban columns
INSERT INTO columns (title, color, position)
SELECT 'To Do',       '#6366f1', 0
WHERE NOT EXISTS (SELECT 1 FROM columns WHERE title = 'To Do');

INSERT INTO columns (title, color, position)
SELECT 'In Progress', '#f59e0b', 1
WHERE NOT EXISTS (SELECT 1 FROM columns WHERE title = 'In Progress');

INSERT INTO columns (title, color, position)
SELECT 'Review',      '#8b5cf6', 2
WHERE NOT EXISTS (SELECT 1 FROM columns WHERE title = 'Review');

INSERT INTO columns (title, color, position)
SELECT 'Done',        '#10b981', 3
WHERE NOT EXISTS (SELECT 1 FROM columns WHERE title = 'Done');
