# Contributing to Assembly Line

We welcome focused contributions, including AI-assisted pull requests (PRs).
You are responsible for understanding, running, and verifying the code you submit,
whether you wrote it yourself or used AI assistance.

## Keep changes easy to review

AI-assisted PRs from contributors the maintainers do not yet know are welcome
when they are small: aim for approximately **100 changed lines or fewer**
(additions plus deletions). Keep each PR focused on one change. Discuss larger
changes with the maintainers before submitting them.

Include the test files and evidence needed to verify your work, even if they push
the PR past that guideline. Identify supporting test files separately in the PR
description so reviewers can distinguish them from the implementation change.

## Requirements before requesting review

1. **Allow maintainer edits.** For PRs from forks, enable **Allow edits from
   maintainers** so we can make adjustments and manage the merge.
2. **Run the change end to end.** Install your changed code on a running
   docassemble server and exercise the affected workflow through its final result.
   A locally running server is ideal. Automated unit tests or AI assurances alone
   are not enough. Describe the environment, steps, expected behavior, and actual
   result in your PR, including any relevant generated documents.
3. **Include detailed screenshot evidence.** Show the affected steps and final
   result, with captions explaining what each screenshot demonstrates. For a bug
   fix or visual change, include before-and-after screenshots where practical.
   Prefer a linked secret gist to keep the PR readable; screenshots attached to
   the PR are also acceptable. Secret gists are accessible to anyone with the
   link: use fictional test data and omit credentials or personal information.
4. **Include evidence of automated code review.** Have an automated reviewer
   review the proposed diff, preferably using a different model family from the
   one that helped write the code. Link or attach the review, identify the tool
   and model when known, and summarize how you addressed its findings, including
   why you did not adopt any suggestions. A statement that the code was reviewed
   without the review output is not sufficient.

## Make the change easy to reproduce

Prefer including a small, runnable **docassemble test interview YAML file** that
demonstrates the affected behavior. Include any required supporting files,
instructions for launching the interview, sample inputs, and the expected result.
For a bug fix, explain how the interview exposes the original problem and confirms
the fix. Include relevant automated tests and their results as well.

Test interviews and other verification files should accompany the PR so reviewers
can confirm the change. Maintainers may remove unnecessary test files before
merging or later; submitting them does not mean we will retain them permanently.

For changes that cannot be exercised in a docassemble interview, such as
documentation-only edits, explain which runtime or screenshot requirements do not
apply and describe the checks you performed instead.

## PR checklist

- [ ] I explained the problem, the change, and any AI assistance used.
- [ ] The change is focused and approximately 100 changed lines or fewer, or I
      explained the supporting test files or prior discussion for a larger PR.
- [ ] I enabled maintainer edits on my fork PR.
- [ ] I ran the affected workflow end to end and recorded the steps and results.
- [ ] I included detailed screenshot evidence or explained why it does not apply.
- [ ] I included automated review output and my response to its findings.
- [ ] I included a runnable docassemble test YAML where practical, with supporting
      files and reproduction instructions.
- [ ] I reported relevant automated test results and any remaining limitations.
