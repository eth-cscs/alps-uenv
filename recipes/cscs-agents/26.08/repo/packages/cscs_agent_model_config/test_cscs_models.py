import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("cscs_models.py")
SPEC = importlib.util.spec_from_file_location("cscs_models_under_test", SCRIPT)
MODELS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODELS
SPEC.loader.exec_module(MODELS)


class MultiGatewayConfigTest(unittest.TestCase):
    def run_generator(self, cli_args, environment, discovered):
        def list_models(gateway, _api_key):
            return [dict(model) for model in discovered[gateway.provider_key]]

        with tempfile.TemporaryDirectory() as output_dir:
            argv = [
                str(SCRIPT),
                "--out-dir",
                output_dir,
                "--no-docs",
                "--no-pricing",
                "--no-enrich",
                *cli_args,
            ]
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(MODELS, "SECRET_SH", Path("/nonexistent")),
                mock.patch.object(MODELS, "list_models", side_effect=list_models),
                mock.patch.object(sys, "argv", argv),
            ):
                MODELS.main()
            return {
                path.name: path.read_text()
                for path in Path(output_dir).iterdir()
            }

    def test_forno_only_preserves_production_and_selects_forno(self):
        files = self.run_generator(
            ["--format", "opencode"],
            {MODELS.FORNO_KEY_ENV: "forno-secret"},
            {
                MODELS.FORNO_PROVIDER_KEY: [
                    {"id": "experimental/new-model", "owned_by": "test"}
                ]
            },
        )
        config = json.loads(files[MODELS.OPENCODE_FILE])

        self.assertEqual(
            config["model"], "cscs-forno/experimental/new-model"
        )
        self.assertIn("cscs", config["provider"])
        forno = config["provider"]["cscs-forno"]
        self.assertEqual(forno["npm"], "@ai-sdk/openai-compatible")
        self.assertEqual(
            forno["options"]["baseURL"],
            "https://ai-gateway.forno-tds.tds.cscs.ch/v1",
        )
        self.assertEqual(
            forno["options"]["apiKey"],
            "{env:CSCS_INFERENCE_API_KEY_FORNO}",
        )
        self.assertEqual(
            forno["models"]["experimental/new-model"]["limit"],
            {"context": 32768, "output": 16384},
        )

    def test_both_keys_keep_production_default(self):
        files = self.run_generator(
            ["--format", "opencode"],
            {
                MODELS.KEY_ENV: "production-secret",
                MODELS.FORNO_KEY_ENV: "forno-secret",
            },
            {
                "cscs": [{"id": "moonshotai/Kimi-K2.7-Code"}],
                MODELS.FORNO_PROVIDER_KEY: [{"id": "zai-org/GLM-5.3"}],
            },
        )
        config = json.loads(files[MODELS.OPENCODE_FILE])

        self.assertEqual(
            config["model"], "cscs/moonshotai/Kimi-K2.7-Code"
        )
        self.assertEqual(
            set(config["provider"]), {"cscs", "cscs-forno"}
        )

    def test_omp_and_pi_use_openai_for_forno(self):
        files = self.run_generator(
            ["--format", "pi"],
            {MODELS.FORNO_KEY_ENV: "forno-secret"},
            {
                MODELS.FORNO_PROVIDER_KEY: [{"id": "zai-org/GLM-5.3"}]
            },
        )
        omp = files[MODELS.OMP_FILE]
        pi = files[MODELS.PI_FILE]

        self.assertIn("  cscs-forno:\n", omp)
        self.assertIn("    apiKey: CSCS_INFERENCE_API_KEY_FORNO\n", omp)
        self.assertIn("    api: openai-completions\n", omp)
        self.assertIn("      - id: zai-org/GLM-5.3\n", omp)
        self.assertIn('pi.registerProvider("cscs-forno"', pi)
        self.assertIn('api: "openai-completions"', pi)


if __name__ == "__main__":
    unittest.main()
