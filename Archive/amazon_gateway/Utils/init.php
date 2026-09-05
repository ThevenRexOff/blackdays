<?php

namespace Utils;

require __DIR__ . '/../vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Cookie\CookieJar;
use GuzzleHttp\Cookie\SetCookie;

abstract class Core
{

    public static array $COUNTRY_MAP = [
        'ES' => ['code' => 'acbes', 'currency' => 'EUR', 'lc' => 'lc-acbes', 'lc_value' => 'es_ES', 'domain' => 'amazon.es', 'assoc_handle' => 'esflex'],
        'MX' => ['code' => 'acbmx', 'currency' => 'MXN', 'lc' => 'lc-acbmx', 'lc_value' => 'es_MX', 'domain' => 'amazon.com.mx', 'assoc_handle' => 'mxflex'],
        'IT' => ['code' => 'acbit', 'currency' => 'EUR', 'lc' => 'lc-acbit', 'lc_value' => 'it_IT', 'domain' => 'amazon.it', 'assoc_handle' => 'itflex'],
        'US' => ['code' => 'main',  'currency' => 'USD', 'lc' => 'lc-main',  'lc_value' => 'en_US', 'domain' => 'amazon.com', 'assoc_handle' => 'usflex'],
        'DE' => ['code' => 'acbde', 'currency' => 'EUR', 'lc' => 'lc-main',  'lc_value' => 'de_DE', 'domain' => 'amazon.de', 'assoc_handle' => 'deflex'],
        'BR' => ['code' => 'acbbr', 'currency' => 'BRL', 'lc' => 'lc-main',  'lc_value' => 'en_US', 'domain' => 'amazon.com.br', 'assoc_handle' => 'brflex'],
        'AE' => ['code' => 'acbae', 'currency' => 'AED', 'lc' => 'lc-acbae', 'lc_value' => 'en_AE', 'domain' => 'amazon.ae', 'assoc_handle' => 'aeflex'],
        'SG' => ['code' => 'acbsg', 'currency' => 'SGD', 'lc' => 'lc-acbsg', 'lc_value' => 'en_SG', 'domain' => 'amazon.com.sg', 'assoc_handle' => 'sgflex'],
        'SA' => ['code' => 'acbsa', 'currency' => 'SAR', 'lc' => 'lc-acbsa', 'lc_value' => 'ar_AE', 'domain' => 'amazon.sa', 'assoc_handle' => 'saflex'],
        'CA' => ['code' => 'acbca', 'currency' => 'CAD', 'lc' => 'lc-acbca', 'lc_value' => 'en_CA', 'domain' => 'amazon.ca', 'assoc_handle' => 'caflex'],
        'PL' => ['code' => 'acbpl', 'currency' => 'PLN', 'lc' => 'lc-acbpl', 'lc_value' => 'pl_PL', 'domain' => 'amazon.pl', 'assoc_handle' => 'plflex'],
        'AU' => ['code' => 'acbau', 'currency' => 'AUD', 'lc' => 'lc-acbau', 'lc_value' => 'en_AU', 'domain' => 'amazon.com.au', 'assoc_handle' => 'auflex'],
        'JP' => ['code' => 'acbjp', 'currency' => 'JPY', 'lc' => 'lc-acbjp', 'lc_value' => 'ja_JP', 'domain' => 'amazon.co.jp', 'assoc_handle' => 'jpflex'],
        'FR' => ['code' => 'acbfr', 'currency' => 'EUR', 'lc' => 'lc-acbfr', 'lc_value' => 'fr_FR', 'domain' => 'amazon.fr', 'assoc_handle' => 'frflex'],
        'IN' => ['code' => 'acbin', 'currency' => 'INR', 'lc' => 'lc-acbin', 'lc_value' => 'en_IN', 'domain' => 'amazon.in', 'assoc_handle' => 'inflex'],
        'NL' => ['code' => 'acbnl', 'currency' => 'EUR', 'lc' => 'lc-acbnl', 'lc_value' => 'nl_NL', 'domain' => 'amazon.nl', 'assoc_handle' => 'nlflex'],
        'UK' => ['code' => 'acbuk', 'currency' => 'GBP', 'lc' => 'lc-acbuk', 'lc_value' => 'en_GB', 'domain' => 'amazon.co.uk', 'assoc_handle' => 'ukflex'],
        'TR' => ['code' => 'acbtr', 'currency' => 'TRY', 'lc' => 'lc-acbtr', 'lc_value' => 'tr_TR', 'domain' => 'amazon.com.tr', 'assoc_handle' => 'trflex']
    ];


    public static function splitByDelimiters(array $delimiters, string $value): array
    {
        return explode($delimiters[0], str_replace($delimiters, $delimiters[0], $value));
    }


    public static function extractBetween(?string $haystack, string $start, string $end, int $index = 1): ?string
    {
        if ($haystack === null) return null;
        $parts = explode($start, $haystack);
        if (!isset($parts[$index])) return null;
        $parts2 = explode($end, $parts[$index], 2);
        return $parts2[0] ?? null;
    }


    public static function generateRandomLetters(int $length): string
    {
        $alphabet = 'abcdefghijklmnopqrstuvwxyz';
        $maxIndex = strlen($alphabet) - 1;
        return implode('', array_map(fn() => $alphabet[random_int(0, $maxIndex)], range(1, $length)));
    }


    public static function buildCookieData(string $cookie): array
    {
        $regionCode = self::extractRegionCode(trim($cookie));
        if (!$regionCode) return ['status' => false, 'message' => 'Region code not found in cookie.'];

        $countryMap = array_column(self::$COUNTRY_MAP, null, 'code');

        if (!isset($countryMap[$regionCode])) return ['status' => false, 'message' => 'Unsupported region code in cookie: ' . $regionCode . '.'];

        $country = $countryMap[$regionCode];
        $codes   = array_merge(array_column(self::$COUNTRY_MAP, 'code'), ['acbuc']);
        $cookie  = str_replace($codes, $country['code'], $cookie);
        $cookie  = preg_replace('/(i18n-prefs=)[A-Z]{3}/', '$1' . $country['currency'], $cookie);
        $cookie  = preg_replace('/(' . preg_quote($country['lc'], '/') . '=)[^;]+/', '$1' . $country['lc_value'], $cookie);

        $countryCode = null;
        foreach (self::$COUNTRY_MAP as $code => $data) {
            if ($data === $country) {
                $countryCode = $code;
                break;
            }
        }

        return ['status' => true, 'cookie' => $cookie, 'domain' => $country['domain'], 'country_code' => $countryCode];
    }


    public static function buildCookieAudible(string $cookie, string $country = 'US'): string
    {
        $nonBuildCookieData = self::$COUNTRY_MAP[$country];
        $cookie = preg_replace('/\b(acb[a-z]{2}|main)\b/', $nonBuildCookieData['code'], $cookie);
        $cookie = preg_replace('/(i18n-prefs=)[A-Z]{3}/', '$1' . $nonBuildCookieData['currency'], $cookie);
        return preg_replace('/(' . preg_quote($nonBuildCookieData['lc'], '/') . '=)[a-z]{2}_[A-Z]{2}/', '$1' . $nonBuildCookieData['lc_value'], $cookie);
    }


    public static function parseCardString(string $cardString): ?array
    {
        $parts = self::splitByDelimiters([":", "|", ";", ":", "/", " "], $cardString);
        if (count($parts) < 4) return ['status' => false, 'message' => 'Invalid card format. Expected format: number|exp_month|exp_year|cvv'];
        return ['status' => true, 'number' => trim($parts[0]), 'month' => str_pad(trim($parts[1]), 2, '0', STR_PAD_LEFT), 'year' => trim($parts[2]), 'cvv' => trim($parts[3]),];
    }


    public static function createCookieJarFromString(string $cookie, string $domain): CookieJar
    {
        $jar = new CookieJar();
        foreach (explode(';', $cookie) as $pair) {
            if (!str_contains($pair, '=')) continue;
            [$name, $value] = array_map('trim', explode('=', $pair, 2));
            $jar->setCookie(new SetCookie(['Name' => $name, 'Value' => $value, 'Domain' => $domain, 'Path' => '/',]));
        }
        return $jar;
    }


    public static function buildFlowBillingResult(string $responseAmazon, array $audibleResponse, string $countryCode, array $card, string $finalUrl = ''): array
    {
        $cardStr   = $card['number'] . '|' . $card['month'] . '|' . $card['year'] . '|' . $card['cvv'];
        $cardResp  = $audibleResponse['message'] ?? '';
        $normalized = str_replace(["\xe2\x80\x99", "\xe2\x80\x98"], "\x27", $responseAmazon);
        $check      = $responseAmazon . ' ' . $finalUrl;

        if (stripos($normalized, 'unable to complete your Prime signup') !== false || stripos($normalized, 'sorry') !== false) {
            return ['status' => true, 'success' => true, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'Card successfully linked.', 'apiResponse' => 'Approved ✅'];
        }
        if (strpos($responseAmazon, 'No podemos completar tu registro en Prime') !== false || strpos($responseAmazon, 'Lo lamentamos') !== false) {
            return ['status' => true, 'success' => true, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'Card successfully linked.', 'apiResponse' => 'Approved ✅'];
        }
        if (strpos($check, 'InvalidInput') !== false) {
            return ['status' => true, 'success' => false, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'Invalid card.', 'apiResponse' => 'Declined ❌'];
        }
        if (strpos($responseAmazon, 'If you would still like to join Prime') !== false || strpos($responseAmazon, 'you can sign up during checkout') !== false) {
            return ['status' => true, 'success' => false, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'Attempt limit reached.', 'apiResponse' => 'Declined ❌'];
        }
        if (strpos($check, 'CustomerValidationFailureException') !== false) {
            return ['status' => true, 'success' => true, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'Card successfully linked.', 'apiResponse' => 'Approved ✅'];
        }
        if (strpos($check, 'HARDVET_VERIFICATION_FAILED') !== false) {
            return ['status' => true, 'success' => false, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'Card verification failed.', 'apiResponse' => 'Declined ❌'];
        }
        if (strpos($check, 'HardVetCsrfValidationFailed') !== false) {
            return ['status' => false, 'success' => false, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'CSRF expired - Refresh your cookie.', 'apiResponse' => 'Error ⚠️'];
        }
        return ['status' => false, 'success' => false, 'card' => $cardStr, 'card_response' => $cardResp, 'response' => 'Unknown response from Amazon.', 'apiResponse' => 'Error ⚠️'];
    }


    public static function extractRegionCode(string $cookie): ?string
    {
        if (preg_match('/\b(main|acb[a-z]{2})\b/i', $cookie, $m)) return strtolower($m[1]);
        return null;
    }


    public static function getBinInfo(string $cc): ?array
    {
        $bin = substr(preg_replace('/\D/', '', $cc), 0, 6);
        if (strlen($bin) < 6) return null;

        try {
            $client = new Client(['http_errors' => false, 'verify' => false, 'timeout' => 10]);
            $response = $client->get('https://bins.antipublic.cc/bins/' . $bin, [
                'headers' => ['accept' => 'application/json', 'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36']
            ]);
            $data = json_decode((string) $response->getBody(), true);
            return is_array($data) ? $data : null;
        } catch (\Throwable $e) {
            return null;
        }
    }
}


abstract class metaData
{

    public static function getBillingAddressId(Client $curl, string $csrfToken, string $domain): ?string
    {
        $headers = [
            'Accept' => 'application/json, text/plain, */*',
            'User-Agent' => 'Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36',
            'client' => 'MYXSettings',
            'Content-Type' => 'application/x-www-form-urlencoded',
            'Origin' => 'https://www.' . $domain,
            'X-Requested-With' => 'com.amazon.dee.app',
            "Referer" => "https://www.$domain/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca"
        ];
        $payload = 'data=%7B%22param%22%3A%7B%22LogPageInfo%22%3A%7B%22pageInfo%22%3A%7B%22subPageType%22%3A%22kinw_total_myk_stb_Perr_paymnt_dlg_cl%22%7D%7D%2C%22GetAllAddresses%22%3A%7B%7D%7D%7D&csrfToken=' . urlencode($csrfToken);
        $request = $curl->post(uri: 'https://www.' . $domain . '/hz/mycd/ajax', options: ["headers" => $headers, 'body' => $payload]);
        $response = (string) $request->getBody();

        return Core::extractBetween($response, 'AddressId":"', '"') ?: null;
    }



    public static function addBillingAddress(Client $curl, string $domain, string $countryCode): array
    {
        $COUNTRY_DATA = [
            'US' => [
                'countryCode' => 'US',
                'fullName' => 'Jesus Jenkins',
                'phone' => '929' . rand(1000000, 9999999),
                'line1' => '42 REMSEN ST APT 41',
                'city' => 'BROOKLYN',
                'state' => 'NY',
                'postalCode' => '11201'
            ],
            'DE' => [
                'countryCode' => 'DE',
                'fullName' => 'Max Müller',
                'phone' => '030' . rand(1000000, 9999999),
                'line1' => 'Unter den Linden 10',
                'city' => 'Berlin',
                'state' => 'BE',
                'postalCode' => '10115'
            ],
            'ES' => [
                'countryCode' => 'ES',
                'fullName' => 'Carlos García',
                'phone' => '91' . rand(1000000, 9999999),
                'line1' => 'Calle de Alcalá 50',
                'city' => 'Madrid',
                'state' => 'MD',
                'postalCode' => '28001'
            ],
            'IT' => [
                'countryCode' => 'IT',
                'fullName' => 'Marco Rossi',
                'phone' => '06' . rand(10000000, 99999999),
                'line1' => 'Via Nazionale 10',
                'city' => 'Roma',
                'state' => 'RM',
                'postalCode' => '00184'
            ],
            'JP' => [
                'countryCode' => 'JP',
                'fullName' => 'Taro Yamada',
                'phone' => '03' . rand(10000000, 99999999),
                'line1' => '1-1 Chiyoda',
                'city' => 'Tokyo',
                'state' => 'Tokyo',
                'postalCode' => '100-0001'
            ],
            'CA' => [
                'countryCode' => 'CA',
                'fullName' => 'John Smith',
                'phone' => '416' . rand(1000000, 9999999),
                'line1' => '100 King St W',
                'city' => 'Toronto',
                'state' => 'ON',
                'postalCode' => 'M5V 2T6'
            ],
            'AU' => [
                'countryCode' => 'AU',
                'fullName' => 'Jack Wilson',
                'phone' => '02' . rand(1000000, 9999999),
                'line1' => '1 George St',
                'city' => 'Sydney',
                'state' => 'NSW',
                'postalCode' => '2000'
            ],
            'BR' => [
                'countryCode' => 'BR',
                'fullName' => 'João Silva',
                'phone' => '11' . rand(100000000, 999999999),
                'line1' => 'Av. Paulista 1000',
                'city' => 'São Paulo',
                'state' => 'SP',
                'postalCode' => '01310-100'
            ],
            'MX' => [
                'countryCode' => 'MX',
                'fullName' => 'Juan Pérez',
                'phone' => '55' . rand(10000000, 99999999),
                'line1' => 'Av. Juárez 10',
                'city' => 'Ciudad de México',
                'state' => 'CDMX',
                'postalCode' => '06000'
            ],
            'IN' => [
                'countryCode' => 'IN',
                'fullName' => 'Aarav Sharma',
                'phone' => '11' . rand(10000000, 99999999),
                'line1' => 'Connaught Pl 10',
                'city' => 'New Delhi',
                'state' => 'DL',
                'postalCode' => '110001'
            ],
            'NL' => [
                'countryCode' => 'NL',
                'fullName' => 'Jan de Vries',
                'phone' => '020' . rand(100000, 999999),
                'line1' => 'Damrak 1',
                'city' => 'Amsterdam',
                'state' => 'NH',
                'postalCode' => '1011'
            ],
            'SG' => [
                'countryCode' => 'SG',
                'fullName' => 'Wei Lim',
                'phone' => '65' . rand(100000, 999999),
                'line1' => '1 Raffles Pl',
                'city' => 'Singapore',
                'state' => 'SG',
                'postalCode' => '018956'
            ],
            'AE' => [
                'countryCode' => 'AE',
                'fullName' => 'Ahmed Al Farsi',
                'phone' => '04' . rand(1000000, 9999999),
                'line1' => 'Sheikh Zayed Rd 1',
                'city' => 'Dubai',
                'state' => 'DU',
                'postalCode' => '00000'
            ],
            'SA' => [
                'countryCode' => 'SA',
                'fullName' => 'Mohammed Al Saud',
                'phone' => '011' . rand(100000, 999999),
                'line1' => 'King Fahd Rd 100',
                'city' => 'Riyadh',
                'state' => 'RU',
                'postalCode' => '12211'
            ],
            'TR' => [
                'countryCode' => 'TR',
                'fullName' => 'Emre Yılmaz',
                'phone' => '212' . rand(1000000, 9999999),
                'line1' => 'İstiklal Cd. 10',
                'city' => 'Istanbul',
                'state' => 'IB',
                'postalCode' => '34110'
            ],
            'SE' => [
                'countryCode' => 'SE',
                'fullName' => 'Erik Andersson',
                'phone' => '08' . rand(1000000, 9999999),
                'line1' => 'Drottninggatan 20',
                'city' => 'Stockholm',
                'state' => 'AB',
                'postalCode' => '111 57'
            ],
            'PL' => [
                'countryCode' => 'PL',
                'fullName' => 'Jan Kowalski',
                'phone' => '22' . rand(1000000, 9999999),
                'line1' => 'Krakowskie Przedmieście 10',
                'city' => 'Warszawa',
                'state' => 'MZ',
                'postalCode' => '00-001'
            ],
            'EG' => [
                'countryCode' => 'EG',
                'fullName' => 'Ahmed Hassan',
                'phone' => '2' . rand(100000000, 999999999),
                'line1' => 'Tahrir Sq 1',
                'city' => 'Cairo',
                'state' => 'C',
                'postalCode' => '11511'
            ],
        ];

        $data = $COUNTRY_DATA[strtoupper($countryCode)] ?? null;
        if (!$data) {
            return ['status' => false, 'message' => 'Country not supported'];
        }

        $headersGet = [
            'Host' => "www.$domain",
            'Referer' => "https://www.$domain/a/addresses?ref_=ya_d_c_addr&claim_type=EmailAddress&new_account=1&",
            'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Viewport-Width' => '1536',
        ];
        $getUrl = "https://www.$domain/a/addresses/add?ref=ya_address_book_add_button";
        $response1 = (string) $curl->get($getUrl, ['headers' => $headersGet])->getBody();

        $csrf = self::extractToken($response1, 'csrfToken');
        $prevState = self::extractToken($response1, 'address-ui-widgets-previous-address-form-state-token');
        $customerId = self::extractToken($response1, 'address-ui-widgets-obfuscated-customerId');
        if (!$customerId && preg_match('/"customerID":"([^"]+)"/', $response1, $m)) {
            $customerId = $m[1];
        }
        $csrfWidget = self::extractToken($response1, 'address-ui-widgets-csrfToken');
        $loadStart = self::extractToken($response1, 'address-ui-widgets-form-load-start-time');
        $clickstream = self::extractToken($response1, 'address-ui-widgets-clickstream-related-request-id');
        $wizardId = self::extractToken($response1, 'address-ui-widgets-address-wizard-interaction-id');
        $ajaxToken = self::extractToken($response1, 'identity-address-ux-ajax-auth-token');

        if (!$csrfWidget) $csrfWidget = $csrf;
        if (!$loadStart) $loadStart = time();

        if (!$csrf || !$prevState || !$customerId || !$wizardId) {
            $missing = [];
            if (!$csrf) $missing[] = 'csrf';
            if (!$prevState) $missing[] = 'prevState';
            if (!$customerId) $missing[] = 'customerId';
            if (!$wizardId) $missing[] = 'wizardId';
            return ['status' => false, 'message' => 'Missing tokens: ' . implode(', ', $missing) . ' (maybe cookie expired)'];
        }

        if (strtoupper($countryCode) === 'MX' && $ajaxToken) {
            $headers2 = [
                'User-Agent' => 'Mozilla/5.0',
                'X-Requested-With' => 'XMLHttpRequest',
                'Content-Type' => 'application/x-www-form-urlencoded',
                'Referer' => "https://www.$domain/a/addresses/add?ref=ya_address_book_add_button"
            ];
            $payload2 = json_encode([
                'JsonPayload' => json_encode([
                    'operation' => 'MexicoAutopopulation',
                    'data' => [
                        'CountryCode' => $data['countryCode'],
                        'PostalCode' => $data['postalCode']
                    ],
                    'ajaxToken' => $ajaxToken
                ])
            ]);
            $curl->post("https://www.$domain/auiws/perform-ajax", ['headers' => $headers2, 'body' => $payload2]);
        }

        $fullName = $data['fullName'];
        $phone = $data['phone'];
        $street = $data['line1'];
        $city = $data['city'];
        $state = $data['state'];
        $postal = $data['postalCode'];
        $countryCodeVal = $data['countryCode'];

        $postData = [
            'csrfToken' => $csrf,
            'addressID' => '',
            'address-ui-widgets-countryCode' => $countryCodeVal,
            'address-ui-widgets-enterAddressFullName' => $fullName,
            'address-ui-widgets-enterAddressPhoneNumber' => $phone,
            'address-ui-widgets-enterAddressLine1' => $street,
            'address-ui-widgets-enterAddressLine2' => '',
            'address-ui-widgets-enterAddressCity' => $city,
            'address-ui-widgets-enterAddressStateOrRegion' => $state,
            'address-ui-widgets-enterAddressPostalCode' => $postal,
            'address-ui-widgets-urbanization' => '',
            'address-ui-widgets-previous-address-form-state-token' => $prevState,
            'address-ui-widgets-use-as-my-default' => 'true',
            'address-ui-widgets-delivery-instructions-desktop-expander-context' => json_encode([
                'deliveryInstructionsDisplayMode' => 'CDP_ONLY',
                'deliveryInstructionsClientName' => 'YourAccountAddressBook',
                'deliveryInstructionsDeviceType' => 'desktop',
                'deliveryInstructionsIsEditAddressFlow' => 'false'
            ]),
            'address-ui-widgets-addressFormButtonText' => 'save',
            'address-ui-widgets-addressFormHideHeading' => 'true',
            'address-ui-widgets-heading-string-id' => '',
            'address-ui-widgets-addressFormHideSubmitButton' => 'false',
            'address-ui-widgets-enableAddressDetails' => 'true',
            'address-ui-widgets-returnLegacyAddressID' => 'false',
            'address-ui-widgets-enableDeliveryInstructions' => 'true',
            'address-ui-widgets-enableAddressWizardInlineSuggestions' => 'true',
            'address-ui-widgets-enableEmailAddress' => 'false',
            'address-ui-widgets-enableAddressTips' => 'true',
            'address-ui-widgets-amazonBusinessGroupId' => '',
            'address-ui-widgets-clientName' => 'YourAccountAddressBook',
            'address-ui-widgets-enableAddressWizardForm' => 'true',
            'address-ui-widgets-delivery-instructions-data' => json_encode(['initialCountryCode' => $countryCodeVal]),
            'address-ui-widgets-ab-delivery-instructions-data' => '',
            'address-ui-widgets-address-wizard-interaction-id' => $wizardId,
            'address-ui-widgets-obfuscated-customerId' => $customerId,
            'address-ui-widgets-locationData' => '',
            'address-ui-widgets-enableLatestAddressWizardForm' => 'false',
            'address-ui-widgets-avsSuppressSoftblock' => 'false',
            'address-ui-widgets-avsSuppressSuggestion' => 'false',
            'address-ui-widgets-csrfToken' => $csrfWidget,
            'address-ui-widgets-form-load-start-time' => $loadStart,
            'address-ui-widgets-clickstream-related-request-id' => $clickstream,
            'address-ui-widgets-deliveryDestinationCity' => $city,
            'address-ui-widgets-deliveryDestinationNonUciPostalCode' => $postal,
            'address-ui-widgets-autofill-location-spinner-loading-text' => 'Loading',
            'address-ui-widgets-locale' => '',
        ];


        // Japan uses a 7-digit postal code split into two fields (e.g. 100-0001 -> 100 / 0001)
        if (strtoupper($countryCode) === 'JP') {
            $pcDigits = preg_replace('/\D/', '', $postal);
            if (strlen($pcDigits) === 7) {
                $postData['address-ui-widgets-enterAddressPostalCodeOne'] = substr($pcDigits, 0, 3);
                $postData['address-ui-widgets-enterAddressPostalCodeTwo'] = substr($pcDigits, 3, 4);
            }
        }

        $postUrl = "https://www.$domain/a/addresses/add?ref=ya_address_book_add_post";

        $headersPost = [
            'Content-Type' => 'application/x-www-form-urlencoded',
            'Host' => "www.$domain",
            'Origin' => "https://www.$domain",
            'Referer' => "https://www.$domain/a/addresses/add?ref=ya_address_book_add_button",
            'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Viewport-Width' => '1536',
        ];

        $response2 = (string) $curl->post($postUrl, [
            'headers' => $headersPost,
            'form_params' => $postData
        ])->getBody();


        $needConfirm = false;
        $confirmKeywords = ['review your address', 'revisar', 'conferma', 'prévisualiser', 'überprüfen', 'revise', 'controlla', 'verifica', 'indirizzo'];
        foreach ($confirmKeywords as $kw) {
            if (stripos($response2, $kw) !== false) {
                $needConfirm = true;
                break;
            }
        }

        if ($needConfirm) {
            $confirmAction = self::extractAttribute($response2, 'form', 'action');
            if (!$confirmAction) {
                $confirmAction = "https://www.$domain/a/addresses/confirm";
            }
            if (strpos($confirmAction, 'http') !== 0) {
                $confirmAction = "https://www.$domain" . (strpos($confirmAction, '/') === 0 ? '' : '/') . $confirmAction;
            }

            $confirmData = self::extractFormInputs($response2);

            $headersConfirm = [
                'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                'Content-Type' => 'application/x-www-form-urlencoded',
                'Referer' => $postUrl,
                'Origin' => "https://www.$domain",
                'Upgrade-Insecure-Requests' => '1',
            ];
            $response3 = (string) $curl->post($confirmAction, [
                'headers' => $headersConfirm,
                'form_params' => $confirmData
            ])->getBody();
            $finalResponse = $response3;
        } else {
            $finalResponse = $response2;
        }

        $successPatterns = [
            'Your address has been added',
            'Tu dirección ha sido añadida',
            'Ihr Adresse wurde hinzugefügt',
            'Il tuo indirizzo è stato aggiunto',
            'Votre adresse a été ajoutée',
            'Indirizzo aggiunto con successo',
            'successfully added',
            'address was successfully added',
            'Your Addresses',
            'Tus direcciones',
            'Indirizzi'
        ];

        $success = false;
        foreach ($successPatterns as $pattern) {
            if (stripos($finalResponse, $pattern) !== false) {
                $success = true;
                break;
            }
        }

        if ($success) {
            return ['status' => true, 'message' => 'Address added successfully'];
        } else {
            // Extraer mensaje de error
            $errorMsg = 'Failed to add address';
            if (preg_match('/<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)<\/div>/i', $finalResponse, $matches)) {
                $errorMsg = 'Amazon error: ' . strip_tags($matches[1]);
            } elseif (preg_match('/<h4[^>]*>(.*?)<\/h4>/i', $finalResponse, $matches)) {
                $errorMsg = 'Amazon error: ' . strip_tags($matches[1]);
            } elseif (preg_match('/<p[^>]*>(.*?)<\/p>/i', $finalResponse, $matches)) {
                $errorMsg = 'Amazon error: ' . strip_tags($matches[1]);
            }
            // Guardar para depuración
            file_put_contents(__DIR__ . '/../address_debug.html', $finalResponse);
            return ['status' => false, 'message' => $errorMsg . ' (response saved to address_debug.html)'];
        }
    }

    private static function extractToken(string $html, string $name): ?string
    {
        if (preg_match('/<input[^>]*name=["\']' . preg_quote($name, '/') . '["\'][^>]*value=["\']([^"\']*)["\']/i', $html, $matches)) {
            return $matches[1];
        }
        if (preg_match('/data-' . preg_quote($name, '/') . '=["\']([^"\']*)["\']/i', $html, $matches)) {
            return $matches[1];
        }
        if (preg_match('/name=["\']' . preg_quote($name, '/') . '["\'][^>]*value=["\']([^"\']*)["\']/i', $html, $matches)) {
            return $matches[1];
        }
        return null;
    }

    private static function extractAttribute(string $html, string $tag, string $attr): ?string
    {
        if (preg_match('/<' . preg_quote($tag, '/') . '[^>]*' . preg_quote($attr, '/') . '=["\']([^"\']*)["\']/i', $html, $matches)) {
            return $matches[1];
        }
        return null;
    }

    private static function extractFormInputs(string $html): array
    {
        $data = [];
        preg_match_all('/<input[^>]*name=["\']([^"\']*)["\'][^>]*value=["\']([^"\']*)["\']/i', $html, $matches);
        for ($i = 0; $i < count($matches[1]); $i++) {
            $data[$matches[1][$i]] = $matches[2][$i];
        }
        // También extraer selects
        preg_match_all('/<select[^>]*name=["\']([^"\']*)["\'][^>]*>(.*?)<\/select>/is', $html, $selMatches);
        for ($i = 0; $i < count($selMatches[1]); $i++) {
            $name = $selMatches[1][$i];
            if (preg_match('/<option[^>]*selected[^>]*value=["\']([^"\']*)["\']/', $selMatches[2][$i], $optMatches)) {
                $data[$name] = $optMatches[1];
            } elseif (preg_match('/<option[^>]*value=["\']([^"\']*)["\']/', $selMatches[2][$i], $optMatches)) {
                $data[$name] = $optMatches[1];
            }
        }
        return $data;
    }


    public static function deletePaymentMethod(string $cookie, string $payment, ?string $proxies = null)
    {
        $cookieData = ['cookie' => $cookie, 'domain' => ''];
        $tokens = array("audible.com", "audible.ca");

        for ($i = 0; $i < count($tokens); $i++) {
            $cookieData['domain'] = $tokens[$i];
            $lastDotPosition = strrpos($cookieData['domain'], '.');
            if ($lastDotPosition !== false) {
                $countryCode = substr($cookieData['domain'], $lastDotPosition + 1);
                if ($countryCode === 'com')  $countryCode = 'US';
            }

            $cookie = Core::buildCookieAudible($cookieData['cookie'], strtoupper($countryCode));
            $ch = curl_init();
            curl_setopt_array($ch, [
                CURLOPT_URL => "https://www." . $cookieData['domain'] . "/account/payments?ref=",
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_SSL_VERIFYPEER => false,
                CURLOPT_FOLLOWLOCATION => true,
                CURLOPT_COOKIE => $cookie,
                CURLOPT_ENCODING => "gzip",
                CURLOPT_POSTFIELDS => "",
                CURLOPT_TIMEOUT => 60,
                CURLOPT_CONNECTTIMEOUT => 15,
                CURLOPT_HTTPHEADER => array("Host: www." . $cookieData['domain'], 'sec-ch-ua: "Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"', 'sec-ch-ua-mobile: ?0', 'sec-ch-ua-platform: "Windows"', 'Upgrade-Insecure-Requests: 1', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8', 'Sec-GPC: 1', 'Accept-Language: ' . ($countryCode == 'AE' || $countryCode  == 'SA' ? 'en-US,en;q=0.9,ar;q=0.8' : ($countryCode == 'JP' ? 'ja-JP,ja;q=0.9,en;q=0.8' : 'en-US,en;q=0.9')))
            ]);
            if ($proxies) curl_setopt($ch, CURLOPT_PROXY, $proxies);
            $r = curl_exec($ch);
            if ($r === false) continue;

            $csrf    = Core::extractBetween($r, 'data-csrf-token="', '"');
            $address = Core::extractBetween($r, 'data-billing-address-id="', '"');

            if ($csrf !== null && stripos($csrf, '///'))
                $csrf = Core::extractBetween(Core::extractBetween($r, 'data-payment-id="', 'payment-type'), 'data-csrf-token="', '"');

            if ($csrf === null || $address === null) continue;

            $ch = curl_init();
            curl_setopt_array($ch, [
                CURLOPT_URL => "https://www." . $cookieData['domain'] . "/unified-payment/deactivate-payment-instrument?requestUrl=https%3A%2F%2Fwww." . $cookieData['domain'] . "%2Faccount%2Fpayments%3Fref%3D&relativeUrl=%2Faccount%2Fpayments&",
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_SSL_VERIFYPEER => false,
                CURLOPT_FOLLOWLOCATION => true,
                CURLOPT_COOKIE => $cookie,
                CURLOPT_ENCODING => "gzip",
                CURLOPT_HEADER => true,
                CURLOPT_TIMEOUT => 60,
                CURLOPT_CONNECTTIMEOUT => 15,
                CURLOPT_POSTFIELDS => "isSubsConfMosaicMigrationEnabled=false&destinationUrl=%2Funified%2Fpayments%2Fmfa&transactionType=Recurring&unifiedPaymentWidgetView=true&paymentPreferenceName=Audible&clientId=audible&isAlcFlow=false&isConsentRequired=false&selectedMembershipBillingPaymentConfirmButton=adbl_accountdetails_mfa_required_credit_card_freetrial_error&selectedMembershipBillingPaymentDescriptionKey=adbl_order_redrive_membership_purchasehistory_mfa_verification&membershipBillingNoBillingDescriptionKey=adbl_order_redrive_membership_no_billing_desc_key&membershipBillingPaymentDescriptionKey=adbl_order_redrive_membership_billing_payments_list_desc_key&keepDialogOpenOnSuccess=false&isMfaCase=false&paymentsListChooseTextKey=adbl_accountdetails_select_default_payment_method&confirmSelectedPaymentDescriptionKey=&confirmButtonTextKey=adbl_paymentswidget_list_confirm_button&paymentsListDescriptionKey=adbl_accountdetails_manage_payment_methods_description&paymentsListTitleKey=adbl_accountdetails_manage_payment_methods&selectedPaymentDescriptionKey=&selectedPaymentTitleKey=adbl_paymentswidget_selected_payment_title&viewAddressDescriptionKey=&viewAddressTitleKey=adbl_paymentswidget_view_address_title&addAddressDescriptionKey=&addAddressTitleKey=adbl_paymentswidget_add_address_title&showEditTelephoneField=false&viewCardCvvField=false&editBankAccountDescriptionKey=&editBankAccountTitleKey=adbl_paymentswidget_edit_bank_account_title&addBankAccountDescriptionKey=&addBankAccountTitleKey=&editPaymentDescriptionKey=&editPaymentTitleKey=&addPaymentDescriptionKey=adbl_paymentswidget_add_payment_description&addPaymentTitleKey=adbl_paymentswidget_add_payment_title&editCardDescriptionKey=&editCardTitleKey=adbl_paymentswidget_edit_card_title&defaultPaymentMethodKey=adbl_accountdetails_default_payment_method&useAsDefaultCardKey=adbl_accountdetails_use_as_default_card&geoBlockAddressErrorKey=adbl_paymentswidget_payment_geoblocked_address&geoBlockErrorMessageKey=adbl_paymentswidget_geoblock_error_message&geoBlockErrorHeaderKey=adbl_paymentswidget_geoblock_error_header&addCardDescriptionKey=adbl_paymentswidget_add_card_description&addCardTitleKey=adbl_paymentswidget_add_card_title&ajaxEndpointPrefix=&geoBlockSupportedCountries=&enableGeoBlock=false&setDefaultOnSelect=true&makeDefaultCheckboxChecked=false&showDefaultCheckbox=false&autoSelectPayment=false&showConfirmButton=false&showAddButton=true&showDeleteButtons=true&showEditButtons=true&showClosePaymentsListButton=false&isDialog=false&isVerifyCvv=false&ref=a_accountPayments_c3_0_delete&paymentId=$payment&billingAddressId=$address&paymentType=CreditCard&tail=0433&accountHolderName=fsdsdgs%20sdffdssdff&isValid=true&isDefault=true&issuerName=MasterCard&displayIssuerName=MasterCard&bankName=&csrfToken=" . urlencode($csrf) . "&index=0",
                CURLOPT_HTTPHEADER => array("Host: www." . $cookieData['domain'], 'sec-ch-ua: "Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"', 'Content-type: application/x-www-form-urlencoded', 'adpToken: ', 'X-Requested-With: XMLHttpRequest', 'sec-ch-ua-mobile: ?0', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36', 'sec-ch-ua-platform: "Windows"', 'Accept: */*', 'Sec-GPC: 1', 'Accept-Language: ' . ($countryCode == 'AE' || $countryCode == 'SA' ? 'en-US,en;q=0.9,ar;q=0.8' : ($countryCode == 'JP' ? 'ja-JP,ja;q=0.9,en;q=0.8' : 'en-US,en;q=0.9')), 'Origin: https://www.' . $cookieData['domain'], "Referer: https://www." . $cookieData['domain'] . "/account/payments?ref=")
            ]);
            if ($proxies) curl_setopt($ch, CURLOPT_PROXY, $proxies);
            $r = curl_exec($ch);
            if ($r === false) continue;

            if (strpos($r, '"statusStringKey":"adbl_paymentswidget_delete_payment_success"'))
                return ['status' => true, 'message' => "Payment method deleted successfully."];
        }
        return ['status' => false, 'message' => 'Failed to delete payment method.'];
    }
}