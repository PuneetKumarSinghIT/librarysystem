import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Fetching data / restoring the session on mount legitimately sets loading and
      // auth state inside effects. This React-Compiler-era rule is an aggressive
      // performance hint, not a correctness rule; disabled intentionally.
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Test tooling (linted/type-checked by Vitest, not the Next build):
    "src/**/*.test.ts",
    "src/**/*.test.tsx",
    "vitest.config.mts",
    "vitest.setup.ts",
  ]),
]);

export default eslintConfig;
