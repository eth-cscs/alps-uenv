# Documentation for uenv developers

The documentation here is a collection of best practices and practical how-to for folk writing uenv recipes, specifically for the Alps targets at CSCS.

* A practical [recipe writing guide](pkg-application-tutorial.md);
* A step-by-step guide for [supporting ReFrame tests](pkg-reframe.md) in the CSCS regression testing framework;
* A guide on how to [write uenv documentation](pkg-writing-docs.md) for this site.

## AI review of recipe pull requests

Maintainers can request an automated review of a recipe PR by commenting `/ai-review` on it.
A GitHub Action runs Claude Code against the [CSCS Inference Service](https://docs.cscs.ch/services/inference/api/)
and posts the result as a PR comment.
The review checks the rules in `.github/instructions/recipes.instructions.md` (for example a missing `default-view`, or settings dropped compared to the previous version of a recipe); extend that file when you find a new class of mistake.

The review is advisory only. It is only triggered by repository owners, members and collaborators.
The API key is stored in the repository secret `CSCS_INFERENCE_API_KEY`; the model can be changed with the repository variable `AI_REVIEW_MODEL` (default `zai-org/GLM-5.3`).
As reference material the review reads the Stackinator `CLAUDE.md`, docs and schemas (`main` for version 3 recipes, `releases/v6` for version 2 recipes) and the [cscs-reframe-tests](https://github.com/eth-cscs/cscs-reframe-tests) repository, to check the features in `extra/reframe.yaml`.
