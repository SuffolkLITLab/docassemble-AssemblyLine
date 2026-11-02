# Contributing to Assembly Line

We welcome focused contributions, including AI-assisted pull requests (PRs).
You are responsible for understanding, running, and verifying the code you submit,
whether you wrote it yourself or used AI assistance.

We prefer contributions from people who are actively engaged with
our community, which includes weekly open meetings. But small, short,
readable PRs are fine from people who follow the guidelines below.

## Keep changes easy to review

AI-assisted PRs from contributors the maintainers do not yet know are welcome
when they are small: aim for approximately **50 changed lines or fewer**
(additions plus deletions). Keep each PR focused on one change. Discuss larger
changes with the maintainers before submitting them.

Include the test files and evidence needed to verify your work, even if they push
the PR past that guideline. Identify supporting test files separately in the PR
description so reviewers can distinguish them from the implementation change.

## Requirements before requesting review

1. **Follow existing code styles and conventions.** Look through existing Docassemble
   interview code in the following repos, and adopt patterns and use existing functions and methods
   before inventing new ones:
      * https://github.com/SuffolkLITLab/docassemble-AssemblyLine/
      * https://github.com/SuffolkLITLab/docassemble-ALToolbox
      * https://github.com/SuffolkLITLab/docassemble-ALDashboard/
1. **Read (or point your AI) at the documentation.** We have a very detailed style guide, including
   a style guide for code changes: https://assemblyline.suffolklitlab.org/docs/coding_style/overview. Follow it. This repo should enforce some style through the `dabuild` action that runs on PRs to this repo. It also
   includes examples of AssemblyLine conventions and standards, and existing functions and methods you
   can adopt instead of inventing new, complex parallel implementations.
1. **Allow maintainer edits.** For PRs from forks, enable **Allow edits from maintainers** 
   so we can make adjustments and manage the merge.
1. **Run the change end to end.** Install your changed code on a running
   docassemble server and exercise the affected workflow through its final result.
   A locally running server is ideal. Automated unit tests or AI assurances alone
   are not enough. Describe the environment, steps, expected behavior, and actual
   result in your PR, including any relevant generated documents.
   If you cannot deploy a local Docassemble server, please use https://pypi.org/project/docassemble-simulator/ instead to verify changes.
1. **Strongly preferred: include detailed screenshot evidence that uses fictional test data.** Show the affected steps and final
   result, with captions explaining what each screenshot demonstrates. For a bug
   fix or visual change, include before-and-after screenshots where practical.
   Prefer a linked unlisted/secret gist to keep the repo clean; screenshots embedded in
   the PR body are also acceptable. Screenshots should not be added to the repo itself.
1. **AI-assisted PRs must include evidence of automated code review.** Have an automated reviewer
   review the proposed diff, preferably using a different model family from the
   one that helped write the code. Link or attach the review, identify the tool
   and model when known, and summarize how you addressed its findings, including
   why you did not adopt any suggestions. A statement that the code was reviewed
   without the review output is not sufficient. **Human-drafted PRs are not required to use AI-assisted review.**

## Make the change easy to reproduce

In your PR comment, include a small, runnable **docassemble test interview YAML** code snippet that
demonstrates the affected behavior if possible. Include any code from required supporting files,
instructions for launching the interview, sample inputs, and the expected result.
For a bug fix, explain how the interview exposes the original problem and confirms
the fix. Include relevant automated tests and their results as well.

Unit tests and other verification files should accompany the PR so reviewers
can confirm the change. Maintainers may remove long-term unnecessary test files before
merging or later; submitting them does not mean we will retain them permanently.

For changes that cannot be exercised in a docassemble interview, such as
documentation-only edits, explain which runtime or screenshot requirements do not
apply and describe the checks you performed instead.

## PR checklist

- [ ] I explained the problem, the change, and any AI assistance used.
- [ ] The change is focused and approximately 50 changed lines or fewer, or I
      explained the supporting test files or prior discussion for a larger PR.
- [ ] I enabled maintainer edits on my fork PR.
- [ ] I ran the affected workflow end to end and recorded the steps and results.
- [ ] I included detailed screenshot evidence or explained why it does not apply.
- [ ] I included automated review output and my response to its findings.
- [ ] I embedded a runnable docassemble test YAML in the PR body where practical, with supporting
      reproduction instructions.
- [ ] I reported relevant automated test results and any remaining limitations.
