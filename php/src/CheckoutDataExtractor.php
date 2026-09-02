<?php

class CheckoutDataExtractor
{
   private array $graphqlData;
   private array|null $negotiateResult;
   private array|null $sessionData;
   private array|null $shopData;
   private string|null $overriddenCurrency = null;

   public function __construct(string $checkoutHtml)
   {
      if (!preg_match('/<meta name="serialized-graphql" content="([^"]*)"/', $checkoutHtml, $gqlMatch)) {
         throw new Exception("serialized-graphql not found in checkout HTML");
      }

      $raw = html_entity_decode($gqlMatch[1]);
      $this->graphqlData = json_decode($raw, true);

      if (!is_array($this->graphqlData)) {
         throw new Exception("Invalid serialized-graphql JSON");
      }

      // Find session with negotiate result
      $this->negotiateResult = null;
      $this->sessionData = null;
      $this->shopData = null;

      foreach ($this->graphqlData as $key => $val) {
         if (!is_array($val)) continue;

         if (isset($val['session']['negotiate']['result'])) {
            $this->negotiateResult = $val['session']['negotiate']['result'];
            $this->sessionData = $val['session'];
         }
         if (isset($val['shop'])) {
            $this->shopData = $val['shop'];
         }
      }

      if (empty($this->negotiateResult)) {
         throw new Exception("session.negotiate.result not found in serialized-graphql");
      }
   }

   public static function meta(string $html, string $name): string
   {
      if (preg_match('/<meta name="' . preg_quote($name, '/') . '" content="([^"]*)"/', $html, $m)) {
         $val = html_entity_decode($m[1]);
         return trim($val, '"');
      }
      return '';
   }

   public function getSessionToken(): string
   {
      return $this->negotiateResult['queueToken'] ?? '';
   }

   public function getQueueToken(): string
   {
      return $this->negotiateResult['queueToken'] ?? '';
   }

   public function getCurrency(): string
   {
      if ($this->overriddenCurrency !== null) {
         return $this->overriddenCurrency;
      }
      $lines = $this->negotiateResult['sellerProposal']['merchandise']['merchandiseLines'] ?? [];
      foreach ($lines as $line) {
         if (!empty($line['merchandise']['price']['currencyCode'])) {
            return $line['merchandise']['price']['currencyCode'];
         }
         if (!empty($line['totalAmount']['value']['currencyCode'])) {
            return $line['totalAmount']['value']['currencyCode'];
         }
      }
      return 'USD';
   }

   public function setCurrency(string $currency): void
   {
      $this->overriddenCurrency = $currency;
   }

   public function isShippingRequired(): bool
   {
      return ($this->negotiateResult['buyerProposal']['isShippingRequired'] ?? true) === true;
   }

   public function getStableIds(): array
   {
      $ids = [];
      $lines = $this->negotiateResult['buyerProposal']['merchandise']['merchandiseLines'] ?? [];
      foreach ($lines as $line) {
         $ids[] = $line['stableId'];
      }
      return $ids;
   }

   public function getPaymentMethodIdentifier(): string
   {
      $lines = $this->negotiateResult['sellerProposal']['payment']['availablePaymentLines'] ?? [];
      foreach ($lines as $pl) {
         $pm = $pl['paymentMethod'] ?? [];
         // Look for PaymentProvider type (Shopify Payments), skip wallets
         if (($pm['__typename'] ?? '') === 'PaymentProvider' && !empty($pm['paymentMethodIdentifier'])) {
            return $pm['paymentMethodIdentifier'];
         }
      }
      // Fallback: first available with identifier
      foreach ($lines as $pl) {
         $pm = $pl['paymentMethod'] ?? [];
         if (!empty($pm['paymentMethodIdentifier'])) {
            return $pm['paymentMethodIdentifier'];
         }
      }
      return '';
   }

   public function getDeliveryHandle(): string
   {
      $lines = $this->negotiateResult['sellerProposal']['delivery']['deliveryLines'] ?? [];
      if (empty($lines)) return '';

      $sdl = $lines[0];

      // Try availableDeliveryStrategies first (shipping)
      $strategies = $sdl['availableDeliveryStrategies'] ?? [];
      if (!empty($strategies[0]['handle'])) {
         return $strategies[0]['handle'];
      }

      // Fallback: selectedDeliveryStrategy (NONE/digital)
      return $sdl['selectedDeliveryStrategy']['handle'] ?? '';
   }

   public function getDeliveryAmount(): string
   {
      $lines = $this->negotiateResult['sellerProposal']['delivery']['deliveryLines'] ?? [];
      if (empty($lines)) return '0.00';

      $strategies = $lines[0]['availableDeliveryStrategies'] ?? [];
      if (!empty($strategies[0]['amount']['value']['amount'])) {
         return $strategies[0]['amount']['value']['amount'];
      }
      return '0.00';
   }

   public function getTaxAmount(): string
   {
      return $this->negotiateResult['sellerProposal']['tax']['totalTaxAmount']['value']['amount'] ?? '0';
   }

   public function getTaxCurrency(): string
   {
      return $this->negotiateResult['sellerProposal']['tax']['totalTaxAmount']['value']['currencyCode'] ?? $this->getCurrency();
   }

   public function getTotalAmount(): string
   {
      return $this->negotiateResult['sellerProposal']['runningTotal']['value']['amount'] ?? '0';
   }

   public function getPaymentMethodName(): string
   {
      $lines = $this->negotiateResult['sellerProposal']['payment']['availablePaymentLines'] ?? [];
      foreach ($lines as $pl) {
         if (isset($pl['paymentMethod']['name'])) {
            return $pl['paymentMethod']['name'];
         }
      }
      return '';
   }

   public function getCheckoutSessionIdentifier(): string
   {
      return $this->sessionData['checkoutSessionIdentifier'] ?? '';
   }

   public function getShopId(): string
   {
      return $this->shopData['id'] ?? '';
   }

   public function updateFromProposalResponse(array $sellerProposal): void
   {
      $this->negotiateResult['sellerProposal'] = $sellerProposal;

      // Sync merchandise prices from sellerProposal -> buyerProposal
      $spLines = $sellerProposal['merchandise']['merchandiseLines'] ?? [];
      $bpLines = &$this->negotiateResult['buyerProposal']['merchandise']['merchandiseLines'];
      if (is_array($bpLines) && !empty($spLines)) {
         foreach ($bpLines as $i => &$bpLine) {
            foreach ($spLines as $spLine) {
               if (($spLine['stableId'] ?? '') === ($bpLine['stableId'] ?? '')) {
                  if (isset($spLine['totalAmount']['value'])) {
                     $bpLine['totalAmount']['value']['amount'] = $spLine['totalAmount']['value']['amount'];
                     $bpLine['totalAmount']['value']['currencyCode'] = $spLine['totalAmount']['value']['currencyCode'];
                  }
                  break;
               }
            }
         }
         unset($bpLine);
      }
   }

   // --- Payload builders ---

   public function buildProposalDelivery(?array $addressData = null): array
   {
      $deliveryLines = [];
      $noDeliveryRequired = [];

      $bpDeliveryLines = $this->negotiateResult['buyerProposal']['delivery']['deliveryLines'] ?? [];

      if (!empty($bpDeliveryLines)) {
         $isShippingOverall = $this->isShippingRequired();

         foreach ($bpDeliveryLines as $dLine) {
            $targetLines = [];
            foreach ($dLine['targetMerchandise']['linesV2'] ?? [] as $line) {
               $targetLines[] = ['stableId' => $line['stableId']];
            }

            $line = [
               'selectedDeliveryStrategy' => [
                  'deliveryStrategyMatchingConditions' => [
                     'estimatedTimeInTransit' => ['any' => true],
                     'shipments' => ['any' => true]
                  ],
                  'options' => (object)[]
               ],
               'targetMerchandiseLines' => ['lines' => $targetLines],
               'deliveryMethodTypes' => $isShippingOverall ? ['SHIPPING'] : ($dLine['deliveryMethodTypes'] ?? []),
               'expectedTotalPrice' => ['any' => true],
               'destinationChanged' => true
            ];

            if ($isShippingOverall && $addressData) {
               $line['destination'] = self::buildDestination($addressData);
            }

            $deliveryLines[] = $line;
         }
      } else {
         $stableIds = $this->getStableIds();
         if (!empty($stableIds)) {
            $targetLines = [];
            foreach ($stableIds as $sid) {
               $targetLines[] = ['stableId' => $sid];
            }

            $isShipping = $this->isShippingRequired();
            $line = [
               'selectedDeliveryStrategy' => [
                  'deliveryStrategyMatchingConditions' => [
                     'estimatedTimeInTransit' => ['any' => true],
                     'shipments' => ['any' => true]
                  ],
                  'options' => (object)[]
               ],
               'targetMerchandiseLines' => ['lines' => $targetLines],
               'deliveryMethodTypes' => [$isShipping ? 'SHIPPING' : 'NONE'],
               'expectedTotalPrice' => ['any' => true],
               'destinationChanged' => true
            ];

            if ($isShipping && $addressData) {
               $line['destination'] = self::buildDestination($addressData);
            }

            $deliveryLines[] = $line;
         }
      }

      return [
         'deliveryLines' => $deliveryLines,
         'noDeliveryRequired' => $noDeliveryRequired,
         'useProgressiveRates' => false,
         'prefetchShippingRatesStrategy' => null,
         'supportsSplitShipping' => true
      ];
   }

   public function buildSubmitDelivery(
      bool $isShippingRequired,
      string $handle,
      string $delamount,
      string $currency,
      string $stableId,
      ?array $addressData = null
   ): array {
      $line = [
         'selectedDeliveryStrategy' => [
            'deliveryStrategyByHandle' => [
               'handle' => $handle,
               'customDeliveryRate' => false
            ],
            'options' => (object)[]
         ],
         'targetMerchandiseLines' => [
            'lines' => [['stableId' => $stableId]]
         ],
         'deliveryMethodTypes' => [$isShippingRequired ? 'SHIPPING' : 'NONE'],
         'expectedTotalPrice' => [
            'value' => [
               'amount' => $delamount,
               'currencyCode' => $currency
            ]
         ],
         'destinationChanged' => !$isShippingRequired
      ];

      if ($isShippingRequired && $addressData) {
         $line['destination'] = self::buildDestination($addressData);
      }

      return [
         'deliveryLines' => [$line],
         'noDeliveryRequired' => [],
         'useProgressiveRates' => false,
         'prefetchShippingRatesStrategy' => null,
         'supportsSplitShipping' => true
      ];
   }

   public function buildProposalMerchandise(): array
   {
      $lines = [];
      foreach ($this->negotiateResult['buyerProposal']['merchandise']['merchandiseLines'] ?? [] as $line) {
         $merch = $line['merchandise'] ?? [];
         $sellingPlanId = $merch['sellingPlan']['id'] ?? null;
         $sellingPlanDigest = $merch['sellingPlan']['sellingPlanGroupId'] ?? null;

         $lines[] = [
            'stableId' => $line['stableId'],
            'merchandise' => [
               'productVariantReference' => [
                  'id' => $merch['id'] ?? '',
                  'variantId' => $merch['variantId'] ?? '',
                  'properties' => $merch['properties'] ?? [],
                  'sellingPlanId' => $sellingPlanId,
                  'sellingPlanDigest' => $sellingPlanDigest
               ]
            ],
            'quantity' => [
               'items' => ['value' => $line['quantity']['items']['value'] ?? 1]
            ],
            'expectedTotalPrice' => [
               'value' => [
                  'amount' => $line['totalAmount']['value']['amount'] ?? '0',
                  'currencyCode' => $this->getCurrency()
               ]
            ],
            'lineComponentsSource' => null,
            'lineComponents' => []
         ];
      }

      return ['merchandiseLines' => $lines];
   }

   public static function buildAddress(array $addr): array
   {
      return [
         'streetAddress' => [
            'address1' => $addr['address'],
            'city' => $addr['city'],
            'countryCode' => $addr['countryCode'],
            'postalCode' => $addr['zip'],
            'firstName' => $addr['firstName'],
            'lastName' => $addr['lastName'],
            'zoneCode' => $addr['state'],
            'phone' => $addr['phone']
         ]
      ];
   }

   public static function buildDestination(array $addr): array
   {
      return [
         'streetAddress' => [
            'address1' => $addr['address'],
            'city' => $addr['city'],
            'countryCode' => $addr['countryCode'],
            'postalCode' => $addr['zip'],
            'firstName' => $addr['firstName'],
            'lastName' => $addr['lastName'],
            'zoneCode' => $addr['state'],
            'phone' => $addr['phone'],
            'oneTimeUse' => false,
            'coordinates' => [
               'latitude' => $addr['lat'],
               'longitude' => $addr['lon']
            ]
         ]
      ];
   }

   public static function buildBuyerIdentity(string $currency, string $countryCode, string $email): array
   {
      return [
         'customer' => [
            'presentmentCurrency' => $currency,
            'countryCode' => $countryCode
         ],
         'email' => $email,
         'emailChanged' => true,
         'phoneCountryCode' => $countryCode,
         'marketingConsent' => [],
         'shopPayOptInPhone' => ['countryCode' => $countryCode],
         'rememberMe' => false
      ];
   }

   public static function staticFields(): array
   {
      return [
         'discounts' => ['lines' => [], 'acceptUnexpectedDiscounts' => true],
         'deliveryExpectations' => ['deliveryExpectationLines' => []],
         'memberships' => ['memberships' => []],
         'tip' => ['tipLines' => []],
         'note' => ['message' => null, 'customAttributes' => []],
         'localizationExtension' => ['fields' => []],
         'nonNegotiableTerms' => null,
         'scriptFingerprint' => [
            'signature' => null,
            'signatureUuid' => null,
            'lineItemScriptChanges' => [],
            'paymentScriptChanges' => [],
            'shippingScriptChanges' => []
         ],
         'optionalDuties' => ['buyerRefusesDuties' => false],
         'cartMetafields' => []
      ];
   }

   public function buildProposalPayload(
      string $sessionToken,
      string $queueToken,
      array $addressData,
      string $email,
      string $proposalQueryId
   ): array {
      $currency = $this->getCurrency();
      $countryCode = $addressData['countryCode'];
      $static = self::staticFields();

      return [
         'variables' => array_merge([
            'sessionInput' => ['sessionToken' => $sessionToken],
            'queueToken' => $queueToken,
            'delivery' => $this->buildProposalDelivery($addressData),
            'merchandise' => $this->buildProposalMerchandise(),
            'payment' => [
               'totalAmount' => ['any' => true],
               'paymentLines' => [],
               'billingAddress' => self::buildAddress($addressData)
            ],
            'buyerIdentity' => self::buildBuyerIdentity($currency, $countryCode, $email),
            'taxes' => [
               'proposedAllocations' => null,
               'proposedTotalAmount' => [
                  'value' => ['amount' => '0', 'currencyCode' => $currency]
               ],
               'proposedTotalIncludedAmount' => null,
               'proposedMixedStateTotalAmount' => null,
               'proposedExemptions' => []
            ],
            'shopPayArtifact' => [
               'optIn' => ['vaultEmail' => '', 'vaultPhone' => '', 'optInSource' => 'REMEMBER_ME']
            ],
         ], $static),
         'operationName' => 'Proposal',
         'id' => $proposalQueryId
      ];
   }

   public function buildSubmitPayload(
      string $sessionToken,
      string $queueToken,
      string $handle,
      string $delamount,
      string $tax,
      string $totalamt,
      string $currency,
      string $cctoken,
      string $paymentMethodIdentifier,
      string $checkoutToken,
      string $stableId,
      string $submitQueryId,
      string $site,
      string $ccFirst6,
      array $addressData,
      string $email
   ): array {
      $countryCode = $addressData['countryCode'];
      $static = self::staticFields();
      $isShippingRequired = $this->isShippingRequired();

      $input = array_merge([
         'sessionInput' => ['sessionToken' => $sessionToken],
         'queueToken' => $queueToken,
         'delivery' => $this->buildSubmitDelivery(
            $isShippingRequired,
            $handle,
            $delamount,
            $currency,
            $stableId,
            $addressData
         ),
         'merchandise' => $this->buildProposalMerchandise(),
         'payment' => [
            'totalAmount' => ['any' => true],
            'paymentLines' => [[
               'paymentMethod' => [
                  'directPaymentMethod' => [
                     'paymentMethodIdentifier' => $paymentMethodIdentifier,
                     'sessionId' => $cctoken,
                     'billingAddress' => self::buildAddress($addressData),
                     'cardSource' => null
                  ],
                  'giftCardPaymentMethod' => null,
                  'redeemablePaymentMethod' => null,
                  'walletPaymentMethod' => null,
                  'walletsPlatformPaymentMethod' => null,
                  'localPaymentMethod' => null,
                  'paymentOnDeliveryMethod' => null,
                  'paymentOnDeliveryMethod2' => null,
                  'manualPaymentMethod' => null,
                  'customPaymentMethod' => null,
                  'offsitePaymentMethod' => null,
                  'customOnsitePaymentMethod' => null,
                  'deferredPaymentMethod' => null,
                  'customerCreditCardPaymentMethod' => null,
                  'paypalBillingAgreementPaymentMethod' => null,
                  'remotePaymentInstrument' => null
               ],
               'amount' => [
                  'value' => ['amount' => $totalamt, 'currencyCode' => $currency]
               ]
            ]],
            'billingAddress' => self::buildAddress($addressData),
            'creditCardBin' => $ccFirst6
         ],
         'buyerIdentity' => self::buildBuyerIdentity($currency, $countryCode, $email),
         'taxes' => [
            'proposedAllocations' => null,
            'proposedTotalAmount' => [
               'value' => ['amount' => $tax, 'currencyCode' => $currency]
            ],
            'proposedTotalIncludedAmount' => null,
            'proposedMixedStateTotalAmount' => null,
            'proposedExemptions' => []
         ],
         'shopPayArtifact' => [
            'optIn' => [
               'vaultEmail' => '',
               'vaultPhone' => $addressData['phone'],
               'optInSource' => 'REMEMBER_ME'
            ]
         ],
      ], $static);

      return [
         'variables' => [
            'input' => $input,
            'attemptToken' => $checkoutToken . '-64ptawtxh65',
            'metafields' => [],
            'analytics' => [
               'requestUrl' => $site . '/checkouts/cn/' . $checkoutToken,
               'pageId' => $stableId
            ]
         ],
         'operationName' => 'SubmitForCompletion',
         'id' => $submitQueryId
      ];
   }
}
