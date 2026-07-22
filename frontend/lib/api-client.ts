/**
 * APIクライアント設定
 */

import { client } from "@/generated/client.gen";

// ベースURL設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

client.setConfig({
  baseUrl: API_BASE_URL,
});

export { client };
