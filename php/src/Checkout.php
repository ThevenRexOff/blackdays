<?php

class Checkout
{
   private string $site;
   private ?string $cc = null;
   private ?string $mes = null;
   private ?string $ano = null;
   private ?string $cvv = null;
   private ?array $addressData = null;
   private ?string $email = null;
   private ?array $product = null;
   private ?string $proxy = null;
   private ?ProxyManager $proxyManager = null;
   private ?FakeGenerator $fakeData = null;

   private function __construct(string $site)
   {
      $this->site = $site;
   }

   public static function create(string $site): self
   {
      return new self($site);
   }

   public function card(string $number, string $month, string $year, string $cvv): self
   {
      $this->cc = $number;
      $this->mes = $month;
      $this->ano = $year;
      $this->cvv = $cvv;
      return $this;
   }

   public function address(
      string $street,
      string $city,
      string $state,
      string $zip,
      string $countryCode = 'US',
      ?string $phone = null,
      ?float $lat = null,
      ?float $lon = null
   ): self {
      $this->addressData = [
         'address' => $street,
         'city' => $city,
         'state' => $state,
         'zip' => $zip,
         'countryCode' => $countryCode,
         'phone' => $phone,
         'firstName' => null,
         'lastName' => null,
         'lat' => $lat,
         'lon' => $lon,
      ];
      return $this;
   }

   public function phone(string $phone): self
   {
      if ($this->addressData === null) {
         $this->addressData = [];
      }
      $this->addressData['phone'] = $phone;
      return $this;
   }

   public function name(string $first, string $last): self
   {
      if ($this->addressData === null) {
         $this->addressData = [];
      }
      $this->addressData['firstName'] = $first;
      $this->addressData['lastName'] = $last;
      return $this;
   }

   public function email(string $email): self
   {
      $this->email = $email;
      return $this;
   }

   public function product(array $product): self
   {
      $this->product = $product;
      return $this;
   }

   public function proxy(string $server): self
   {
      $this->proxy = $server;
      return $this;
   }

   public function proxyManager(ProxyManager $manager): self
   {
      $this->proxyManager = $manager;
      return $this;
   }

   public function fakeData(FakeGenerator $fake): self
   {
      $this->fakeData = $fake;
      return $this;
   }

   private function buildAddressData(FakeGenerator $fake, string $countryCode): array
   {
      if ($this->addressData && !empty($this->addressData['address'])) {
         $addr = $this->addressData;
         $parts = explode(' ', $addr['address'], 2);
         return [
            'address' => $addr['address'],
            'city' => $addr['city'],
            'state' => $addr['state'],
            'zip' => $addr['zip'],
            'countryCode' => $addr['countryCode'] ?? $countryCode,
            'phone' => $addr['phone'] ?? $fake->generatePhoneNumber($countryCode),
            'firstName' => $addr['firstName'] ?? $fake->FirstName(),
            'lastName' => $addr['lastName'] ?? $fake->LastName(),
            'lat' => $addr['lat'] ?? 0,
            'lon' => $addr['lon'] ?? 0,
         ];
      }

      $random = $fake->getRandomAddressByCountry($countryCode);
      return [
         'address' => $random['num'] . ' ' . $random['address1'],
         'city' => $random['city'],
         'state' => $random['state'],
         'zip' => $random['zip'],
         'countryCode' => $countryCode,
         'phone' => $fake->generatePhoneNumber($countryCode),
         'firstName' => $fake->FirstName(),
         'lastName' => $fake->LastName(),
         'lat' => 0,
         'lon' => 0,
      ];
   }

   public function execute(): string
   {
      if (empty($this->cc) || empty($this->mes) || empty($this->ano) || empty($this->cvv)) {
         throw new Exception('Card details are required. Use ->card()');
      }

      $fake = $this->fakeData ?? new FakeGenerator();

      // Detect country from TLD
      $domain = parse_url($this->site, PHP_URL_HOST) ?? '';
      $tld = strtolower(substr($domain, strrpos($domain, '.') + 1));
      $countryCode = match ($tld) {
         'ca' => 'CA',
         'co.uk', 'uk' => 'UK',
         'com.au' => 'AU',
         default => 'US',
      };

      // Build address
      $addressData = $this->buildAddressData($fake, $countryCode);

      // Create ShopifyAPi with all config
      $server = $this->proxy ? json_decode($this->proxy, true) : null;
      $shopify = new ShopifyAPi($this->site, $server, $fake, $this->proxyManager);

      $shopify->setCardDetails($this->cc, $this->mes, $this->ano, $this->cvv);
      $shopify->setExternalAddress([
         'street' => $addressData['address'],
         'city' => $addressData['city'],
         'state' => $addressData['state'],
         'zip' => $addressData['zip'],
         'phone' => $addressData['phone'],
      ]);
      $shopify->setExternalEmail($this->email);

      if ($this->product) {
         $shopify->setExternalProduct($this->product);
      }

      return $shopify->checkout();
   }
}
