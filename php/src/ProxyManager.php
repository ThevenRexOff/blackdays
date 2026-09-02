<?php

class ProxyManager
{
    private array $proxies = [];
    private array $usedSessions = [];

    public function __construct(array $proxies = [])
    {
        if (!empty($proxies)) {
            $this->proxies = $proxies;
        }
    }

    public function loadFromFile(string $filePath): self
    {
        if (!file_exists($filePath)) {
            throw new \RuntimeException("Proxy file not found: $filePath");
        }

        $content = file_get_contents($filePath);
        $lines = array_filter(array_map('trim', explode("\n", $content)));

        foreach ($lines as $line) {
            if ($line === '' || $line[0] === '#') {
                continue;
            }
            $this->proxies[] = $this->parseLine($line);
        }

        return $this;
    }

    private function parseLine(string $line): array
    {
        // user:pass@host:port
        if (preg_match('/^(.+):(.+)@(.+):(\d+)$/', $line, $m)) {
            return [
                'method' => 'custom',
                'server' => $m[3] . ':' . $m[4],
                'auth'   => $m[1] . ':' . $m[2],
            ];
        }

        // host:port|user:pass
        if (preg_match('/^(.+):(\d+)\|(.+):(.+)$/', $line, $m)) {
            return [
                'method' => 'custom',
                'server' => $m[1] . ':' . $m[2],
                'auth'   => $m[3] . ':' . $m[4],
            ];
        }

        // host:port|auth
        if (preg_match('/^(.+):(\d+)\|(.+)$/', $line, $m)) {
            return [
                'method' => 'custom',
                'server' => $m[1] . ':' . $m[2],
                'auth'   => $m[3],
            ];
        }

        // host:port (sin auth)
        if (preg_match('/^(.+):(\d+)$/', $line, $m)) {
            return [
                'method' => 'tunnel',
                'server' => $m[1] . ':' . $m[2],
            ];
        }

        throw new \RuntimeException("Invalid proxy format: $line");
    }

    public function add(string $host, int $port, ?string $user = null, ?string $pass = null): self
    {
        $proxy = [
            'method' => ($user && $pass) ? 'custom' : 'tunnel',
            'server' => "$host:$port",
        ];

        if ($user && $pass) {
            $proxy['auth'] = "$user:$pass";
        }

        $this->proxies[] = $proxy;
        return $this;
    }

    public function addCustom(string $server, string $auth): self
    {
        $this->proxies[] = [
            'method' => 'custom',
            'server' => $server,
            'auth'   => $auth,
        ];
        return $this;
    }

    public function random(): array
    {
        if (empty($this->proxies)) {
            throw new \RuntimeException('No proxies configured');
        }

        return $this->proxies[array_rand($this->proxies)];
    }

    public function withSession(string $baseUser, string $pass, string $host, int $port): array
    {
        $ssid = $this->generateSSID();

        return [
            'method' => 'custom',
            'server' => "$host:$port",
            'auth'   => "{$baseUser}-ssid-{$ssid}:{$pass}",
        ];
    }

    public function randomWithSession(): array
    {
        if (empty($this->proxies)) {
            throw new \RuntimeException('No proxies configured');
        }

        $base = $this->proxies[array_rand($this->proxies)];

        if ($base['method'] !== 'custom' || empty($base['auth'])) {
            return $base;
        }

        $parts = explode(':', $base['auth'], 2);
        $user = $parts[0];
        $pass = $parts[1] ?? '';

        $ssid = $this->generateSSID();
        $newUser = preg_replace('/-ssid-[a-zA-Z0-9]+$/', '', $user) . "-ssid-{$ssid}";

        return [
            'method' => 'custom',
            'server' => $base['server'],
            'auth'   => "{$newUser}:{$pass}",
        ];
    }

    public function unique(int $count): array
    {
        $shuffled = $this->proxies;
        shuffle($shuffled);
        return array_slice($shuffled, 0, min($count, count($this->proxies)));
    }

    private function generateSSID(): string
    {
        $chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        $ssid = '';
        for ($i = 0; $i < 10; $i++) {
            $ssid .= $chars[random_int(0, strlen($chars) - 1)];
        }
        $this->usedSessions[] = $ssid;
        return $ssid;
    }

    public function getUsedSessions(): array
    {
        return $this->usedSessions;
    }

    public function count(): int
    {
        return count($this->proxies);
    }

    public function all(): array
    {
        return $this->proxies;
    }
}
