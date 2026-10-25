<?php
declare(strict_types=1);
error_reporting(0);
ini_set('display_errors', '0');

if (session_status() === PHP_SESSION_NONE) {
    session_start([
        'cookie_httponly' => true,
        'cookie_samesite' => 'Lax',
        'use_strict_mode' => true,
    ]);
}

define('DB_FILE', __DIR__ . DIRECTORY_SEPARATOR . 'vextu.db');
define('ADMIN_USER', 'vextu');
define('ADMIN_PASS', 'proxy');
define('CREDITS_PER_LAUNCH', 1);
define('BOTS_PER_CREDIT', 4);
define('BOT_HOURS', 8);
define('MAX_LOGIN_ATTEMPTS', 7);
define('LOCK_MINUTES', 12);

function db(): PDO {
    static $pdo = null;
    if ($pdo === null) {
        if (!in_array('sqlite', PDO::getAvailableDrivers(), true)) {
            throw new RuntimeException('PHP no tiene pdo_sqlite. Instala php-sqlite3');
        }
        $pdo = new PDO('sqlite:' . DB_FILE, null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
        $pdo->exec('PRAGMA journal_mode = WAL;');
        $pdo->exec('PRAGMA foreign_keys = ON;');
        $pdo->exec('PRAGMA busy_timeout = 5000;');
    }
    return $pdo;
}

function init_db(): void {
    $pdo = db();
    $pdo->exec("
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password TEXT NOT NULL,
            credits INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0,
            login_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER DEFAULT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS launches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            bots INTEGER NOT NULL DEFAULT 4,
            expires_at INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS bot_queue (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            region TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            bots INTEGER NOT NULL DEFAULT 4,
            hours INTEGER NOT NULL DEFAULT 8,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            started_at INTEGER DEFAULT NULL,
            finished_at INTEGER DEFAULT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            stage TEXT DEFAULT '',
            msg TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_launches_user ON launches(user_id);
        CREATE INDEX IF NOT EXISTS idx_launches_exp ON launches(expires_at);
        CREATE INDEX IF NOT EXISTS idx_bot_queue_status ON bot_queue(status);
    ");

    $stmt = $pdo->prepare('SELECT id FROM users WHERE username = ? LIMIT 1');
    $stmt->execute([ADMIN_USER]);
    if (!$stmt->fetch()) {
        $hash = password_hash(ADMIN_PASS, PASSWORD_DEFAULT);
        $pdo->prepare('INSERT INTO users (username, password, credits, is_admin, created_at) VALUES (?, ?, 9999, 1, ?)')
            ->execute([ADMIN_USER, $hash, time()]);
    }
}

function csrf_token(): string {
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function check_csrf(?string $token): bool {
    return !empty($_SESSION['csrf']) && is_string($token) && hash_equals($_SESSION['csrf'], $token);
}

function current_user(): ?array {
    if (empty($_SESSION['uid'])) return null;
    $stmt = db()->prepare('SELECT id, username, credits, is_admin FROM users WHERE id = ? LIMIT 1');
    $stmt->execute([(int)$_SESSION['uid']]);
    $u = $stmt->fetch();
    return $u ?: null;
}

function json_response(array $data, int $code = 200): void {
    while (ob_get_level() > 0) ob_end_clean();
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: DENY');
    header('Referrer-Policy: no-referrer');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function clean(string $s): string {
    return htmlspecialchars(trim($s), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

try { init_db(); } catch (Throwable $e) {}
