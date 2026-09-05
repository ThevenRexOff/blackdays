<?php

/**
 * Cookie tools bridge for the "Validate" button in index.php.
 * Handles GET ?action=validate&cookie=... and returns JSON:
 *   { status: active|expired|blocked|ratelimit|error|unknown, msg, domain }
 */

require __DIR__ . '/vendor/autoload.php';
require __DIR__ . '/Utils/init.php';

use Utils\Core;
use GuzzleHttp\Client;

header('Content-Type: application/json; charset=utf-8');

$action = $_GET['action'] ?? '';

if ($action === 'validate') {
    $cookie = trim($_GET['cookie'] ?? '');
    $cookie = preg_replace('/^Cookie:\s*/i', '', $cookie);

    if ($cookie === '') {
        echo json_encode(['status' => 'error', 'msg' => 'No cookie', 'domain' => null]);
        exit;
    }

    $country = strtoupper(trim($_GET['country'] ?? ''));
    if ($country === '') {
        $country = detectCountry($cookie);
    }

    echo json_encode(validateCookie($cookie, $country));
    exit;
}

echo json_encode(['status' => 'error', 'msg' => 'Unknown action', 'domain' => null]);
exit;


function detectCountry(string $cookie): string
{
    $region = Core::extractRegionCode($cookie);
    if ($region) {
        foreach (Core::$COUNTRY_MAP as $cc => $info) {
            if ($info['code'] === $region) return $cc;
        }
    }

    if (preg_match('/i18n-prefs=([A-Z]{3})/', $cookie, $m)) {
        foreach (Core::$COUNTRY_MAP as $cc => $info) {
            if ($info['currency'] === $m[1]) return $cc;
        }
    }

    return 'SA';
}


function validateCookie(string $cookie, string $country): array
{
    if (!isset(Core::$COUNTRY_MAP[$country])) {
        return ['status' => 'error', 'msg' => 'Unknown country', 'domain' => null];
    }

    $info    = Core::$COUNTRY_MAP[$country];
    $domain  = $info['domain'];
    $host    = 'www.' . $domain;
    $testUrl = 'https://' . $host . '/cpe/yourpayments/wallet';

    $jar = Core::createCookieJarFromString($cookie, $domain);

    $client = new Client([
        'http_errors'     => false,
        'verify'          => false,
        'timeout'         => 15,
        'cookies'         => $jar,
        'allow_redirects' => ['max' => 10, 'track_redirects' => true],
        'headers'         => [
            'User-Agent'      => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
            'Accept'          => 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language' => 'en-US,en;q=0.9',
        ],
    ]);

    try {
        $response = $client->get($testUrl);
    } catch (\Throwable $e) {
        return ['status' => 'error', 'msg' => 'Connection error', 'domain' => $domain];
    }

    $code = $response->getStatusCode();
    $body = (string) $response->getBody();

    $redirects = $response->getHeader('X-Guzzle-Redirect-History');
    $effUrl    = is_array($redirects) && count($redirects) > 0 ? end($redirects) : $testUrl;

    if (stripos($effUrl, 'signin') !== false) {
        return ['status' => 'expired', 'msg' => 'Cookie expired', 'domain' => $domain];
    }

    if ($code === 200) {
        $isActive =
            strpos($body, 'customerId') !== false ||
            strpos($body, 'csrfToken') !== false ||
            strpos($body, 'YA:MPO') !== false ||
            strpos($body, 'widgetState') !== false;

        if ($isActive) return ['status' => 'active', 'msg' => 'Cookie is ACTIVE', 'domain' => $domain];

        if (stripos($body, 'robot') !== false || stripos($body, 'captcha') !== false) {
            return ['status' => 'blocked', 'msg' => 'Bot detection', 'domain' => $domain];
        }

        return ['status' => 'unknown', 'msg' => 'Session unclear', 'domain' => $domain];
    }

    if ($code === 429) return ['status' => 'ratelimit', 'msg' => 'Rate limited', 'domain' => $domain];

    return ['status' => 'unknown', 'msg' => 'HTTP ' . $code, 'domain' => $domain];
}
