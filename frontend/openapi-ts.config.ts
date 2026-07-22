import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  client: "@hey-api/client-fetch",
  input: "../backend/openapi.json",
  output: {
    path: "generated",
    format: "prettier",
  },
  types: {
    enums: "javascript",
  },
});
