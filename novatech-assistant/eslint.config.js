// Configuração mínima do ESLint (flat config, ESLint 9 + typescript-eslint).
// Referenciada por `npm run lint`. Mantém o gate de lint real (não ilusório).

import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: ["dist/", "node_modules/", "coverage/"],
  },
  ...tseslint.configs.recommended,
  {
    rules: {
      // Nenhum console.log deve existir no codebase (usar o logger pino).
      "no-console": "error",
    },
  },
);
