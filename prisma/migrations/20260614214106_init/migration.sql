-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "telegram_id" TEXT NOT NULL,
    "rank" TEXT NOT NULL DEFAULT 'user',
    "credits" INTEGER NOT NULL DEFAULT 0,
    "lives" INTEGER NOT NULL DEFAULT 0,
    "deads" INTEGER NOT NULL DEFAULT 0,
    "membership_expires_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "keys" (
    "id" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "credits" INTEGER NOT NULL DEFAULT 0,
    "days" INTEGER NOT NULL DEFAULT 0,
    "rank" TEXT NOT NULL DEFAULT 'user',
    "is_used" BOOLEAN NOT NULL DEFAULT false,
    "used_by_id" TEXT,
    "created_by_id" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "used_at" TIMESTAMP(3),

    CONSTRAINT "keys_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "temp_mails" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "service" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "token" TEXT,
    "password" TEXT,
    "domain" TEXT,
    "sid_token" TEXT,
    "drop_token" TEXT,
    "session_id" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "temp_mails_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "gates" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "description" TEXT NOT NULL DEFAULT '',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "api_url" TEXT NOT NULL DEFAULT '',
    "credits_live" INTEGER NOT NULL DEFAULT 0,
    "credits_dead" INTEGER NOT NULL DEFAULT 0,
    "min_rank" TEXT NOT NULL DEFAULT 'premium',
    "threads" INTEGER NOT NULL DEFAULT 1,
    "stats" JSONB NOT NULL DEFAULT '{"lives":0,"deads":0,"successRate":0,"total":0}',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "gates_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_username_key" ON "users"("username");

-- CreateIndex
CREATE UNIQUE INDEX "keys_key_key" ON "keys"("key");

-- CreateIndex
CREATE INDEX "temp_mails_user_id_idx" ON "temp_mails"("user_id");

-- CreateIndex
CREATE INDEX "gates_category_idx" ON "gates"("category");

-- CreateIndex
CREATE INDEX "gates_is_active_idx" ON "gates"("is_active");

-- CreateIndex
CREATE INDEX "gates_created_at_idx" ON "gates"("created_at" DESC);

-- AddForeignKey
ALTER TABLE "keys" ADD CONSTRAINT "keys_used_by_id_fkey" FOREIGN KEY ("used_by_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "keys" ADD CONSTRAINT "keys_created_by_id_fkey" FOREIGN KEY ("created_by_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
