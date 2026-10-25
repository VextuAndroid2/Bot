<?php
error_reporting(0);
ini_set('display_errors', '0');
ob_start();

require __DIR__ . '/config.php';

while (ob_get_level() > 0) {
    ob_end_clean();
}

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');
header('Cache-Control: no-store');

$action = $_POST['action'] ?? $_GET['action'] ?? '';

function write_launch_queue(array $data): void {
    try {
        $queueFile = __DIR__ . DIRECTORY_SEPARATOR . 'launch_queue.json';
        $queue = [];
        if (is_file($queueFile)) {
            $raw = trim((string)@file_get_contents($queueFile));
            if ($raw !== '') {
                $decoded = json_decode($raw, true);
                if (is_array($decoded)) {
                    $queue = $decoded;
                }
            }
        }
        $queue[] = $data;
        if (count($queue) > 50) {
            $queue = array_slice($queue, -50);
        }
        $json = json_encode(array_values($queue), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        if ($json === false) {
            $json = '[]';
        }
        file_put_contents($queueFile, $json, LOCK_EX);
    } catch (Throwable $e) {
    }
}

try {
    if ($action === 'register') {
        if (!check_csrf($_POST['csrf'] ?? null)) {
            json_response(['ok' => false, 'msg' => 'Token inválido. Recarga la página.'], 403);
        }

        $user = strtolower(trim($_POST['username'] ?? ''));
        $pass = $_POST['password'] ?? '';
        $pass2 = $_POST['password2'] ?? '';

        if (strlen($user) < 4 || strlen($user) > 24 || !preg_match('/^[a-z0-9_]+$/', $user)) {
            json_response(['ok' => false, 'msg' => 'Usuario inválido (4-24 caracteres, solo a-z 0-9 _)']);
        }
        if (strlen($pass) < 6) {
            json_response(['ok' => false, 'msg' => 'Contraseña mínimo 6 caracteres']);
        }
        if ($pass !== $pass2) {
            json_response(['ok' => false, 'msg' => 'Las contraseñas no coinciden']);
        }
        if ($user === ADMIN_USER) {
            json_response(['ok' => false, 'msg' => 'Ese usuario está reservado']);
        }

        $hash = password_hash($pass, PASSWORD_DEFAULT);
        try {
            db()->prepare('INSERT INTO users (username, password, credits, created_at) VALUES (?, ?, 0, ?)')
                ->execute([$user, $hash, time()]);
            json_response(['ok' => true, 'msg' => 'Cuenta creada correctamente. Ya puedes entrar.']);
        } catch (PDOException $e) {
            json_response(['ok' => false, 'msg' => 'Ese usuario ya existe']);
        }
    }

    if ($action === 'login') {
        if (!check_csrf($_POST['csrf'] ?? null)) {
            json_response(['ok' => false, 'msg' => 'Token inválido. Recarga la página.'], 403);
        }

        $user = strtolower(trim($_POST['username'] ?? ''));
        $pass = $_POST['password'] ?? '';

        if ($user === '' || $pass === '') {
            json_response(['ok' => false, 'msg' => 'Completa usuario y contraseña']);
        }

        $stmt = db()->prepare('SELECT * FROM users WHERE username = ? LIMIT 1');
        $stmt->execute([$user]);
        $row = $stmt->fetch();

        if (!$row) {
            usleep(random_int(180000, 380000));
            json_response(['ok' => false, 'msg' => 'Usuario o contraseña incorrectos']);
        }

        if (!empty($row['locked_until']) && (int)$row['locked_until'] > time()) {
            $left = (int)ceil(((int)$row['locked_until'] - time()) / 60);
            json_response(['ok' => false, 'msg' => "Cuenta bloqueada temporalmente. Espera {$left} min"]);
        }

        if (!password_verify($pass, $row['password'])) {
            $attempts = (int)$row['login_attempts'] + 1;
            $locked = null;
            if ($attempts >= MAX_LOGIN_ATTEMPTS) {
                $locked = time() + (LOCK_MINUTES * 60);
                $attempts = 0;
            }
            db()->prepare('UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?')
                ->execute([$attempts, $locked, $row['id']]);
            json_response(['ok' => false, 'msg' => 'Usuario o contraseña incorrectos']);
        }

        db()->prepare('UPDATE users SET login_attempts = 0, locked_until = NULL WHERE id = ?')
            ->execute([$row['id']]);

        session_regenerate_id(true);
        $_SESSION['uid'] = (int)$row['id'];

        json_response(['ok' => true, 'admin' => (bool)$row['is_admin']]);
    }

    if ($action === 'logout') {
        $_SESSION = [];
        if (ini_get('session.use_cookies')) {
            $p = session_get_cookie_params();
            setcookie(session_name(), '', time() - 42000, $p['path'], $p['domain'], (bool)$p['secure'], (bool)$p['httponly']);
        }
        session_destroy();
        json_response(['ok' => true]);
    }

    if ($action === 'status') {
        $u = current_user();
        if (!$u) {
            json_response(['ok' => false, 'auth' => false], 401);
        }

        $stmt = db()->prepare('SELECT region, guild_id, bots, expires_at FROM launches WHERE user_id = ? AND expires_at > ? ORDER BY id DESC LIMIT 1');
        $stmt->execute([$u['id'], time()]);
        $launch = $stmt->fetch();

        $isAdmin = (bool)$u['is_admin'] || strtolower((string)$u['username']) === 'vextu';

        $engine = null;
        $savedAccounts = 0;
        if ($isAdmin) {
            $engine = ['online' => false, 'mode' => 'offline', 'msg' => 'Motor apagado. Ejecuta: python app.py', 'stage' => 'offline', 'progress' => 0];
            $engineFile = __DIR__ . DIRECTORY_SEPARATOR . 'engine_status.json';
            if (is_file($engineFile)) {
                $ej = json_decode((string)@file_get_contents($engineFile), true);
                if (is_array($ej)) {
                    $ts = (int)($ej['ts'] ?? 0);
                    $online = $ts > 0 && (time() - $ts) < 45;
                    $engine = [
                        'online' => $online,
                        'mode' => $online ? (string)($ej['mode'] ?? 'idle') : 'offline',
                        'stage' => $online ? (string)($ej['stage'] ?? ($ej['mode'] ?? 'idle')) : 'offline',
                        'msg' => $online ? (string)($ej['msg'] ?? 'ok') : 'Motor apagado. Ejecuta: python app.py',
                        'workers' => (int)($ej['workers'] ?? $ej['active'] ?? 0),
                        'accounts' => (int)($ej['accounts'] ?? 0),
                        'region' => (string)($ej['region'] ?? ''),
                        'guild' => (string)($ej['guild'] ?? ''),
                        'left_min' => (int)($ej['left_min'] ?? 0),
                        'current' => (int)($ej['current'] ?? 0),
                        'total' => (int)($ej['total'] ?? 0),
                        'progress' => (int)($ej['progress'] ?? 0),
                    ];
                }
            }
            $accFile = __DIR__ . DIRECTORY_SEPARATOR . 'accounts.json';
            if (is_file($accFile)) {
                $aj = json_decode((string)@file_get_contents($accFile), true);
                if (is_array($aj)) $savedAccounts = count($aj);
            }
        }

        $job = null;
        try {
            $jq = db()->prepare("SELECT id, region, guild_id, bots, hours, status, progress, stage, msg, created_at, started_at, finished_at FROM bot_queue WHERE user_id = ? ORDER BY created_at DESC LIMIT 1");
            $jq->execute([$u['id']]);
            $jr = $jq->fetch();
            if ($jr) {
                $job = [
                    'id' => $jr['id'],
                    'region' => $jr['region'],
                    'guild' => $jr['guild_id'],
                    'bots' => (int)$jr['bots'],
                    'hours' => (int)$jr['hours'],
                    'status' => $jr['status'],
                    'progress' => (int)($jr['progress'] ?? 0),
                    'stage' => (string)($jr['stage'] ?? ''),
                    'msg' => (string)($jr['msg'] ?? ''),
                ];
            }
        } catch (Throwable $e) {
            $job = null;
        }

        json_response([
            'ok'      => true,
            'user'    => $u['username'],
            'credits' => (int)$u['credits'],
            'admin'   => $isAdmin,
            'engine'  => $engine,
            'saved_accounts' => $isAdmin ? $savedAccounts : null,
            'job'     => $job,
            'launch'  => $launch ? [
                'region'   => $launch['region'],
                'guild'    => $launch['guild_id'],
                'bots'     => (int)$launch['bots'],
                'left_min' => max(0, (int)ceil(($launch['expires_at'] - time()) / 60))
            ] : null
        ]);
    }

    if ($action === 'launch') {
        if (!check_csrf($_POST['csrf'] ?? null)) {
            json_response(['ok' => false, 'msg' => 'Token inválido. Recarga la página.'], 403);
        }

        $u = current_user();
        if (!$u) {
            json_response(['ok' => false, 'msg' => 'No autenticado. Vuelve a entrar.'], 401);
        }

        $region = strtoupper(trim($_POST['region'] ?? ''));
        $guild  = preg_replace('/[^0-9A-Za-z_\-]/', '', trim($_POST['guild'] ?? ''));
        $allowed = ['IND','PK','US','BR','SG','TH','ID','VN','TW','ME','RU','EU'];

        if (!in_array($region, $allowed, true)) {
            json_response(['ok' => false, 'msg' => 'Región no válida']);
        }
        if (strlen($guild) < 3 || strlen($guild) > 32) {
            json_response(['ok' => false, 'msg' => 'Guild ID inválido']);
        }

        $pdo = db();
        $pdo->beginTransaction();
        try {
            $stmt = $pdo->prepare('SELECT credits FROM users WHERE id = ?');
            $stmt->execute([$u['id']]);
            $credits = (int)$stmt->fetchColumn();

            if ($credits < CREDITS_PER_LAUNCH) {
                $pdo->rollBack();
                json_response(['ok' => false, 'msg' => 'No tienes créditos suficientes']);
            }

            $pdo->prepare('UPDATE users SET credits = credits - ? WHERE id = ?')
                ->execute([CREDITS_PER_LAUNCH, $u['id']]);

            $expires = time() + (BOT_HOURS * 3600);
            $pdo->prepare('INSERT INTO launches (user_id, region, guild_id, bots, expires_at, created_at) VALUES (?,?,?,?,?,?)')
                ->execute([$u['id'], $region, $guild, BOTS_PER_CREDIT, $expires, time()]);

            $qid = bin2hex(random_bytes(8));
            $pdo->prepare('INSERT INTO bot_queue (id, user_id, username, region, guild_id, bots, hours, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)')
                ->execute([$qid, $u['id'], $u['username'], $region, $guild, BOTS_PER_CREDIT, BOT_HOURS, 'pending', time()]);

            $pdo->commit();

            // also try json mirror (optional)
            try {
                write_launch_queue([
                    'id' => $qid,
                    'user' => $u['username'],
                    'region' => $region,
                    'guild_id' => $guild,
                    'bots' => BOTS_PER_CREDIT,
                    'hours' => BOT_HOURS,
                    'created_at' => time(),
                    'status' => 'pending'
                ]);
            } catch (Throwable $e) {}

            json_response([
                'ok' => true,
                'msg' => 'Lanzado: ' . BOTS_PER_CREDIT . ' bots · ' . $region . ' · 8 horas',
                'queue_id' => $qid,
                'db' => DB_FILE
            ]);
        } catch (Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            json_response(['ok' => false, 'msg' => 'Error al lanzar: ' . $e->getMessage()], 500);
        }
    }

    if ($action === 'admin_list') {
        $u = current_user();
        if (!$u || !(int)$u['is_admin']) {
            json_response(['ok' => false, 'msg' => 'Acceso denegado'], 403);
        }
        $rows = db()->query('SELECT id, username, credits, created_at FROM users WHERE is_admin = 0 ORDER BY id DESC')->fetchAll();
        json_response(['ok' => true, 'users' => $rows]);
    }

    if ($action === 'admin_add') {
        if (!check_csrf($_POST['csrf'] ?? null)) {
            json_response(['ok' => false, 'msg' => 'Token inválido'], 403);
        }
        $u = current_user();
        if (!$u || !(int)$u['is_admin']) {
            json_response(['ok' => false, 'msg' => 'Acceso denegado'], 403);
        }

        $target = strtolower(trim($_POST['username'] ?? ''));
        $amount = (int)($_POST['amount'] ?? 0);

        if ($amount < 1 || $amount > 9999) {
            json_response(['ok' => false, 'msg' => 'Cantidad inválida (1-9999)']);
        }

        $stmt = db()->prepare('UPDATE users SET credits = credits + ? WHERE username = ? AND is_admin = 0');
        $stmt->execute([$amount, $target]);

        if ($stmt->rowCount() === 0) {
            json_response(['ok' => false, 'msg' => 'Usuario no encontrado']);
        }
        json_response(['ok' => true, 'msg' => "+{$amount} créditos agregados a {$target}"]);
    }

    if ($action === 'ping') {
        json_response(['ok' => true, 'msg' => 'pong', 'time' => time()]);
    }

    json_response(['ok' => false, 'msg' => 'Acción no válida'], 400);

} catch (Throwable $e) {
    while (ob_get_level() > 0) {
        ob_end_clean();
    }
    json_response(['ok' => false, 'msg' => 'Error del servidor: ' . $e->getMessage()], 500);
}
