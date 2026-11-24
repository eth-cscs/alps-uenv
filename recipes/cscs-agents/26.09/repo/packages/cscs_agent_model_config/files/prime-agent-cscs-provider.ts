// CSCS inference service for Prime Agent.
// `apiKey` names an environment variable; no key is stored here.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerProvider("cscs", {
    name: "CSCS Inference",
    baseUrl: "https://api.inference.cscs.ch/v1",
    apiKey: "CSCS_INFERENCE_API_KEY",
    api: "anthropic-messages",
    models: [
      {
        id: "google/gemma-4-31B-it",
        name: "Gemma 4 31B It [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 262144,
        maxTokens: 32768,
      },
      {
        id: "moonshotai/Kimi-K2.7-Code",
        name: "Kimi K2.7 Code [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 262144,
        maxTokens: 32768,
      },
      {
        id: "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
        name: "NVIDIA Nemotron 3 Super 120B A12B BF16 [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 262144,
        maxTokens: 32768,
      },
      {
        id: "swiss-ai/Apertus-70B-Instruct-2509",
        name: "Apertus 70B Instruct 2509 [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 64000,
        maxTokens: 32000,
      },
      {
        id: "swiss-ai/Apertus-8B-Instruct-2509",
        name: "Apertus 8B Instruct 2509 [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 32768,
        maxTokens: 16384,
      },
      {
        id: "swiss-ai/Apertus-v1.5-70B",
        name: "Apertus v1.5 70B [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 262144,
        maxTokens: 32768,
      },
      {
        id: "swiss-ai/Apertus-v1.5-8B",
        name: "Apertus v1.5 8B [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 262144,
        maxTokens: 32768,
      },
      {
        id: "zai-org/GLM-5.2",
        name: "GLM 5.2 [CSCS]",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 976000,
        maxTokens: 32768,
      },
    ],
  });
}
