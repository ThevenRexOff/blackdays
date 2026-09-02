<?php

class FakeGenerator
{
   private array $data = [];
   protected array $addresses = [
      ["numd" => "1600", "address1" => "Pennsylvania Ave NW", "city" => "Washington", "state" => "DC", "zip" => "20500"],
      ["numd" => "350", "address1" => "5th Ave", "city" => "New York", "state" => "NY", "zip" => "10118"],
      ["numd" => "1", "address1" => "Infinite Loop", "city" => "Cupertino", "state" => "CA", "zip" => "95014"],
      ["numd" => "221B", "address1" => "Baker Street", "city" => "Los Angeles", "state" => "CA", "zip" => "90001"],
      ["numd" => "600", "address1" => "Montgomery St", "city" => "San Francisco", "state" => "CA", "zip" => "94111"],
      ["numd" => "401", "address1" => "N Michigan Ave", "city" => "Chicago", "state" => "IL", "zip" => "60611"],
      ["numd" => "500", "address1" => "S Capitol Ave", "city" => "Indianapolis", "state" => "IN", "zip" => "46204"],
      ["numd" => "600", "address1" => "Biscayne Blvd", "city" => "Miami", "state" => "FL", "zip" => "33132"],
      ["numd" => "700", "address1" => "Louisiana St", "city" => "Houston", "state" => "TX", "zip" => "77002"],
      ["numd" => "1100", "address1" => "Congress Ave", "city" => "Austin", "state" => "TX", "zip" => "78701"],
      ["numd" => "1601", "address1" => "Bryant St", "city" => "Denver", "state" => "CO", "zip" => "80204"],
      ["numd" => "1500", "address1" => "Market St", "city" => "Philadelphia", "state" => "PA", "zip" => "19102"],
      ["numd" => "100", "address1" => "Peachtree St NE", "city" => "Atlanta", "state" => "GA", "zip" => "30303"],
      ["numd" => "500", "address1" => "Woodward Ave", "city" => "Detroit", "state" => "MI", "zip" => "48226"],
      ["numd" => "200", "address1" => "Boylston St", "city" => "Boston", "state" => "MA", "zip" => "02116"],
      ["numd" => "345", "address1" => "Park Ave S", "city" => "New York", "state" => "NY", "zip" => "10010"],
      ["numd" => "800", "address1" => "N Glebe Rd", "city" => "Arlington", "state" => "VA", "zip" => "22203"],
      ["numd" => "3500", "address1" => "S Las Vegas Blvd", "city" => "Las Vegas", "state" => "NV", "zip" => "89109"],
      ["numd" => "600", "address1" => "Congress St", "city" => "Portland", "state" => "ME", "zip" => "04101"],
      ["numd" => "200", "address1" => "N Broadway", "city" => "Los Angeles", "state" => "CA", "zip" => "90012"],
      ["numd" => "123", "address1" => "Main St", "city" => "Dallas", "state" => "TX", "zip" => "75201"],
      ["numd" => "987", "address1" => "Elm St", "city" => "Charlotte", "state" => "NC", "zip" => "28202"],
      ["numd" => "765", "address1" => "Central Ave", "city" => "Phoenix", "state" => "AZ", "zip" => "85004"],
      ["numd" => "321", "address1" => "Broad St", "city" => "Nashville", "state" => "TN", "zip" => "37203"],
      ["numd" => "444", "address1" => "Oak St", "city" => "Columbus", "state" => "OH", "zip" => "43215"],
      ["numd" => "555", "address1" => "Pine St", "city" => "Seattle", "state" => "WA", "zip" => "98101"],
      ["numd" => "777", "address1" => "Maple Ave", "city" => "Minneapolis", "state" => "MN", "zip" => "55402"],
      ["numd" => "888", "address1" => "River St", "city" => "St. Louis", "state" => "MO", "zip" => "63101"],
      ["numd" => "999", "address1" => "Cedar Rd", "city" => "Kansas City", "state" => "MO", "zip" => "64106"],
      ["numd" => "111", "address1" => "Hickory St", "city" => "New Orleans", "state" => "LA", "zip" => "70130"],
      ["numd" => "222", "address1" => "Sycamore Ln", "city" => "Milwaukee", "state" => "WI", "zip" => "53202"],
      ["numd" => "333", "address1" => "Sunset Blvd", "city" => "Los Angeles", "state" => "CA", "zip" => "90046"],
      ["numd" => "121", "address1" => "Ocean Dr", "city" => "Miami Beach", "state" => "FL", "zip" => "33139"],
      ["numd" => "456", "address1" => "Jefferson Ave", "city" => "Louisville", "state" => "KY", "zip" => "40202"],
      ["numd" => "789", "address1" => "Capitol St", "city" => "Sacramento", "state" => "CA", "zip" => "95814"],
      ["numd" => "654", "address1" => "Union St", "city" => "Portland", "state" => "OR", "zip" => "97204"],
      ["numd" => "321", "address1" => "Franklin St", "city" => "Jacksonville", "state" => "FL", "zip" => "32202"],
      ["numd" => "852", "address1" => "Lexington Ave", "city" => "Baltimore", "state" => "MD", "zip" => "21201"],
      ["numd" => "963", "address1" => "King St", "city" => "Charleston", "state" => "SC", "zip" => "29401"],
   ];

   protected array $addressesCA = [
      ["numd" => "100", "address1" => "King St W", "city" => "Toronto", "state" => "ON", "zip" => "M5V 1E2"],
      ["numd" => "200", "address1" => "Yonge St", "city" => "Toronto", "state" => "ON", "zip" => "M4W 3G2"],
      ["numd" => "333", "address1" => "Bay St", "city" => "Toronto", "state" => "ON", "zip" => "M5J 2R2"],
      ["numd" => "700", "address1" => "De la Gauchetière St W", "city" => "Montréal", "state" => "QC", "zip" => "H3B 2Y3"],
      ["numd" => "1200", "address1" => "Sainte-Catherine St W", "city" => "Montréal", "state" => "QC", "zip" => "H3G 1P6"],
      ["numd" => "500", "address1" => "Granville St", "city" => "Vancouver", "state" => "BC", "zip" => "V6Z 1Y3"],
      ["numd" => "1050", "address1" => "W Georgia St", "city" => "Vancouver", "state" => "BC", "zip" => "V6E 3P3"],
      ["numd" => "260", "address1" => "Rideau St", "city" => "Ottawa", "state" => "ON", "zip" => "K1N 5Y4"],
      ["numd" => "400", "address1" => "Kent St W", "city" => "Ottawa", "state" => "ON", "zip" => "K2P 2R6"],
      ["numd" => "119", "address1" => "17 Ave SW", "city" => "Calgary", "state" => "AB", "zip" => "T2T 0E3"],
      ["numd" => "800", "address1" => "Stephen Ave NW", "city" => "Calgary", "state" => "AB", "zip" => "T2P 1C4"],
      ["numd" => "101", "address1" => "104 Ave NW", "city" => "Edmonton", "state" => "AB", "zip" => "T5J 4R1"],
      ["numd" => "300", "address1" => "2nd Ave W", "city" => "Edmonton", "state" => "AB", "zip" => "T5J 0R2"],
      ["numd" => "456", "address1" => "Portage Ave", "city" => "Winnipeg", "state" => "MB", "zip" => "R3C 3E2"],
      ["numd" => "165", "address1" => "Market St", "city" => "Halifax", "state" => "NS", "zip" => "B3J 3K4"],
      ["numd" => "240", "address1" => "Waterloo St", "city" => "London", "state" => "ON", "zip" => "N6B 1R3"],
      ["numd" => "150", "address1" => "Johnson St", "city" => "Victoria", "state" => "BC", "zip" => "V8W 2K4"],
      ["numd" => "360", "address1" => "Albert St", "city" => "Saskatoon", "state" => "SK", "zip" => "S7K 1A6"],
      ["numd" => "210", "address1" => "Victoria St", "city" => "Kitchener", "state" => "ON", "zip" => "N2G 2L3"],
      ["numd" => "95", "address1" => "Broadview Ave", "city" => "Toronto", "state" => "ON", "zip" => "M4K 2P6"],
   ];

   protected array $addressesUK = [
      ["numd" => "1", "address1" => "Baker Street", "city" => "London", "state" => "", "zip" => "NW1 6XE"],
      ["numd" => "10", "address1" => "Downing Street", "city" => "London", "state" => "", "zip" => "SW1A 2AA"],
      ["numd" => "221B", "address1" => "Baker Street", "city" => "London", "state" => "", "zip" => "NW1 6XE"],
      ["numd" => "160", "address1" => "Tottenham Ct Rd", "city" => "London", "state" => "", "zip" => "W1T 1JA"],
      ["numd" => "55", "address1" => "Victoria St", "city" => "London", "state" => "", "zip" => "SW1H 0TL"],
      ["numd" => "1", "address1" => "Parliament Square", "city" => "London", "state" => "", "zip" => "SW1A 0AA"],
      ["numd" => "75", "address1" => "Oxford St", "city" => "London", "state" => "", "zip" => "W1D 2DB"],
      ["numd" => "110", "address1" => "Strand", "city" => "London", "state" => "", "zip" => "WC2R 0RL"],
      ["numd" => "40", "address1" => "Fleet St", "city" => "London", "state" => "", "zip" => "EC4Y 1BJ"],
      ["numd" => "30", "address1" => "Fenchurch St", "city" => "London", "state" => "", "zip" => "EC3M 3JF"],
      ["numd" => "100", "address1" => "Deansgate", "city" => "Manchester", "state" => "", "zip" => "M3 2LR"],
      ["numd" => "5", "address1" => "Colmore Circus", "city" => "Birmingham", "state" => "", "zip" => "B1 2EE"],
      ["numd" => "12", "address1" => "Princes St", "city" => "Edinburgh", "state" => "", "zip" => "EH2 2DH"],
      ["numd" => "60", "address1" => "Queen Charlotte St", "city" => "Bristol", "state" => "", "zip" => "BS1 4HJ"],
      ["numd" => "25", "address1" => "Park Row", "city" => "Leeds", "state" => "", "zip" => "LS1 5PW"],
   ];

   protected array $addressesAU = [
      ["numd" => "1", "address1" => "Macquarie St", "city" => "Sydney", "state" => "NSW", "zip" => "2000"],
      ["numd" => "500", "address1" => "George St", "city" => "Sydney", "state" => "NSW", "zip" => "2000"],
      ["numd" => "101", "address1" => "Collins St", "city" => "Melbourne", "state" => "VIC", "zip" => "3000"],
      ["numd" => "360", "address1" => "Collins St", "city" => "Melbourne", "state" => "VIC", "zip" => "3000"],
      ["numd" => "200", "address1" => "Queen St", "city" => "Brisbane", "state" => "QLD", "zip" => "4000"],
      ["numd" => "80", "address1" => "King William St", "city" => "Adelaide", "state" => "SA", "zip" => "5000"],
      ["numd" => "140", "address1" => "St Georges Tce", "city" => "Perth", "state" => "WA", "zip" => "6000"],
      ["numd" => "30", "address1" => "Murray St", "city" => "Hobart", "state" => "TAS", "zip" => "7000"],
      ["numd" => "48", "address1" => "Northbourne Ave", "city" => "Canberra", "state" => "ACT", "zip" => "2601"],
      ["numd" => "120", "address1" => "Hay St", "city" => "Perth", "state" => "WA", "zip" => "6000"],
   ];

   protected $faker;
   protected $userAgent;

   public function __construct()
   {
      $this->faker = Faker\Factory::create('en_US');
      $this->userAgent = new userAgent();
   }

   public function getOrSetData(string $key, mixed $value = null): mixed
   {
      return $this->data[$key] ??= $value;
   }


   public function FirstName()
   {
      return $this->getOrSetData('first_name', $this->faker->firstName());
   }

   public function LastName()
   {
      return $this->getOrSetData('last_name', $this->faker->lastName());
   }

   public function Email()
   {
      $email = strtolower($this->FirstName() . $this->LastName()) . rand(1, 100) . '@' . $this->faker->freeEmailDomain();
      return $this->getOrSetData('email', $email);
   }

   public function userAgent()
   {
      return $this->userAgent->generate('windows');
   }

   public static function generatePhoneNumber(string $countryCode = 'US'): string
   {
      if ($countryCode === 'CA') {
         $areaCodes = [416, 647, 905, 289, 613, 514, 438, 519, 226, 902, 604, 778, 236, 587, 403, 780, 306, 204];
         $areaCode = $areaCodes[array_rand($areaCodes)];
         $random3Digit = rand(200, 999);
         $random4Digit = rand(1000, 9999);
         return sprintf("+1%d%03d%04d", $areaCode, $random3Digit, $random4Digit);
      } elseif ($countryCode === 'UK') {
         $areaCodes = ['20', '121', '131', '141', '151', '161', '113', '117', '121', '1273'];
         $areaCode = $areaCodes[array_rand($areaCodes)];
         $random6Digit = rand(100000, 999999);
         return sprintf("+44%s%06d", $areaCode, $random6Digit);
      } elseif ($countryCode === 'AU') {
         $areaCodes = [2, 3, 7, 8];
         $areaCode = $areaCodes[array_rand($areaCodes)];
         $random4Digit = rand(1000, 9999);
         $random4Digit2 = rand(1000, 9999);
         return sprintf("+61%d%04d%04d", $areaCode, $random4Digit, $random4Digit2);
      }
      $areaCodes = [202, 212, 213, 312, 305, 415, 602, 404, 503, 617, 702, 214, 303, 313, 512, 615];
      $areaCode = $areaCodes[array_rand($areaCodes)];
      $random3Digit = rand(200, 999);
      $random4Digit = rand(1000, 9999);

      return sprintf("+1%d%03d%04d", $areaCode, $random3Digit, $random4Digit);
   }

   public function getRandomAddress(string $countryCode = 'US')
   {
      return $this->getRandomAddressByCountry($countryCode);
   }

   public function getRandomAddressByCountry(string $countryCode = 'US')
   {
      $countryCode = strtoupper($countryCode);

      $pool = match ($countryCode) {
         'CA' => $this->addressesCA,
         'UK' => $this->addressesUK,
         'AU' => $this->addressesAU,
         default => $this->addresses,
      };

      $randomAddress = $pool[array_rand($pool)];

      $num = $randomAddress['numd'];
      $address1 = $randomAddress['address1'];
      $address = $num . ' ' . $address1;
      $city = $randomAddress['city'];
      $state = $randomAddress['state'];
      $zip = $randomAddress['zip'];

      return [
         'num' => $num,
         'address1' => $address1,
         'address' => $address,
         'city' => $city,
         'state' => $state,
         'zip' => $zip,
         'country' => $countryCode,
      ];
   }

   public static function detectCountryFromCurrency(string $currency): string
   {
      return match (strtoupper($currency)) {
         'CAD' => 'CA',
         'GBP' => 'UK',
         'AUD' => 'AU',
         'NZD' => 'NZ',
         'EUR' => 'DE',
         'DKK' => 'DK',
         'SEK' => 'SE',
         'NOK' => 'NO',
         'CHF' => 'CH',
         'JPY' => 'JP',
         'MXN' => 'MX',
         default => 'US',
      };
   }
}