// Configuração por variáveis de ambiente (TSK-002).
// Lê e valida todas as variáveis obrigatórias de forma lazy (no primeiro uso
// de `getConfig()`), falhando rápido (fail-fast) com mensagem descritiva se
// alguma estiver ausente. A validação NÃO ocorre como side-effect do import,
// para que testes que apenas tocam a cadeia de imports não exijam credenciais.

/** Budget de tokens reservado ao system prompt (ADR-0002). */
export const SYSTEM_PROMPT_TOKEN_BUDGET = 4096;

/** Budget de tokens reservado aos chunks de contexto (ADR-0002). */
export const CHUNKS_TOKEN_BUDGET = 8192;

const REQUIRED_ENV_VARS = [
  "AZURE_OPENAI_ENDPOINT",
  "AZURE_OPENAI_KEY",
  "AZURE_OPENAI_CHAT_DEPLOYMENT",
  "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
  "AZURE_SEARCH_ENDPOINT",
  "AZURE_SEARCH_KEY",
  "AZURE_SEARCH_INDEX",
] as const;

type RequiredEnvVar = (typeof REQUIRED_ENV_VARS)[number];

function loadEnv(): Record<RequiredEnvVar, string> {
  const missing: string[] = [];
  const values = {} as Record<RequiredEnvVar, string>;

  for (const name of REQUIRED_ENV_VARS) {
    const value = process.env[name];
    if (value === undefined || value.trim() === "") {
      missing.push(name);
    } else {
      values[name] = value;
    }
  }

  if (missing.length > 0) {
    throw new Error(
      `Configuração inválida: variáveis de ambiente obrigatórias ausentes: ${missing.join(", ")}`,
    );
  }

  return values;
}

/** Configuração tipada e validada da aplicação. */
export interface Config {
  azureOpenAI: {
    endpoint: string;
    key: string;
    chatDeployment: string;
    embeddingDeployment: string;
  };
  azureSearch: {
    endpoint: string;
    key: string;
    index: string;
  };
  budget: {
    systemPromptTokens: number;
    chunksTokens: number;
  };
}

/** Monta o objeto de configuração a partir das variáveis já validadas. */
function buildConfig(env: Record<RequiredEnvVar, string>): Config {
  return {
    azureOpenAI: {
      endpoint: env.AZURE_OPENAI_ENDPOINT,
      key: env.AZURE_OPENAI_KEY,
      chatDeployment: env.AZURE_OPENAI_CHAT_DEPLOYMENT,
      embeddingDeployment: env.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    },
    azureSearch: {
      endpoint: env.AZURE_SEARCH_ENDPOINT,
      key: env.AZURE_SEARCH_KEY,
      index: env.AZURE_SEARCH_INDEX,
    },
    budget: {
      systemPromptTokens: SYSTEM_PROMPT_TOKEN_BUDGET,
      chunksTokens: CHUNKS_TOKEN_BUDGET,
    },
  };
}

let cached: Config | undefined;

/**
 * Retorna a configuração validada, construindo-a (e validando o env) apenas na
 * primeira chamada. Chame uma vez no bootstrap da Function para preservar o
 * fail-fast no startup real, sem acoplar a validação ao import do módulo.
 * @throws {Error} quando variáveis de ambiente obrigatórias estão ausentes.
 */
export function getConfig(): Config {
  if (!cached) {
    cached = buildConfig(loadEnv());
  }
  return cached;
}
