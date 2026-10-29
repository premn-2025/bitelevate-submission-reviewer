# AI Opportunity Report for Cynbit Technologies

Prepared for the AI/ML Engineer Intern assessment. Facts about Cynbit come from its public pages (listed at the end), read on 29 October 2026. I could not see anything internal, so every estimate below is my own judgement and is marked as such.

## 1. What Cynbit is, from the outside

Cynbit Technologies Private Limited is a small software company in Jaipur, Rajasthan. It sells three kinds of things.

**Services.** AI agents and workflow automation, LLM integrations, voice AI, CRM automation, web and mobile development, backend and cloud work (AWS, Azure), legacy migration, technical SEO and funnel optimisation.

**Its own products.** Cynbit Studio (coding practice, AI code evaluation, career preparation, mock interviews, AI mentorship), plus TenantEase and Revio. Public descriptions of the last two are thin: from the names, TenantEase looks like property management and Revio like review management, but I could not confirm either from Cynbit's own pages.

**BitElevate.** A training and industry-readiness programme built around projects, technical tasks, mentorship and assessments, covering full-stack development, AI, data science, cloud, cybersecurity and digital marketing. BitElevate 2.0 started its first cohort with the Department of Lifelong Learning at the University of Rajasthan and a local trust.

Two things stand out. First, Cynbit sells AI automation to other businesses, so anything it automates internally doubles as a working reference for clients. Second, a large part of its work with people runs through assessments: students submit tasks, someone reviews them, and feedback goes back. This application followed the same pattern, with a task, a deadline, a repository link submitted through a portal and a review on the other side.

## 2. Industry context

I did not find sourced market figures I trust for this segment, so I am not quoting any. The qualitative picture, as I read it:

- **AI automation services are crowded.** Many small agencies sell agents and chatbots. What separates them is evidence that the work runs in production, and running your own AI products is the strongest evidence.
- **Skills training is moving towards project-based assessment.** Courses that grade real projects produce more review work than courses that grade quizzes, and review work does not scale with cohort size unless something takes the repetitive part.
- **Automated feedback is useful but easy to over-trust.** In education, a tool that silently grades students is risky. A tool that does a first pass, shows its evidence and sends uncertain cases to a person is much safer, and easier to defend to universities and institutional partners.
- **Small teams carry the biggest manual load.** A company this size usually has a few people doing delivery, sales and training at once, so internal time is the real constraint.

## 3. Opportunities considered

Scores are 1 to 5, my own judgement, higher is better. "Data" means how much usable data Cynbit likely has today. "Ease" means how quickly one person could build a credible pilot.

| # | Opportunity | Value | Data | Ease | Notes |
|---|---|---|---|---|---|
| 1 | First-pass review of BitElevate task submissions | 4 | 4 | 4 | Real bottleneck, rubric already implied by the tasks, measurable against reviewer grades |
| 2 | Inbound lead triage and scoring | 4 | 2 | 4 | Fits the CRM automation offer, but little labelled history; the easiest idea to reach for |
| 3 | Voice AI qualifier for inbound calls | 4 | 2 | 2 | Matches a listed service, but speech quality in Indian languages and call recording consent add risk |
| 4 | Proposal and scope drafter from discovery notes | 4 | 3 | 3 | High value per use, needs past proposals as examples |
| 5 | Review analytics and reply drafting for Revio | 3 | 3 | 3 | Product-side upgrade; I know little about Revio's current features |
| 6 | Maintenance request triage for TenantEase | 3 | 2 | 3 | Clear task, but little public detail about the product |
| 7 | Hardening Cynbit Studio's code evaluation | 4 | 3 | 2 | Needs sandboxed execution of untrusted code, which is a larger project |

## 4. Choice: first-pass review of BitElevate submissions

**Why this one.**

1. The pain is concrete. Every cohort produces a batch of repositories that someone has to open, run, read and grade. Much of that first look is mechanical: is there a README, do the tests exist, does the history show real work, is anything copied.
2. It is a real demonstration of Cynbit's own offer. Cynbit sells automation that "does the repetitive part and leaves judgement to people", and this applies that idea inside Cynbit.
3. It can be measured honestly. Reviewers already grade submissions, so agreement between tool and reviewer is a number that can be tracked, and the tool's mistakes can be listed.
4. It is safe to deploy in stages. The tool never decides alone: it shows evidence for every score and sends unclear cases to a person.

**What the proof of concept does.** It reads a submission folder, zip or public GitHub repository, scores it on six rubric criteria (documentation, code quality, testing, structure, git history, and whether the required deliverables exist), checks for committed secrets and for overlap with other submissions, writes draft feedback, and decides whether a person must look. Submitted code is only read, never run.

**What it does not do.** It does not judge whether the idea is good, whether the model is appropriate, or whether the code is correct. Those need a person, or later a carefully checked LLM step.

## 5. Value, with assumptions to replace

I have no figures for Cynbit's cohort sizes or reviewer time, so this is a formula, not a claim:

hours saved per cohort = submissions x minutes per first-pass review x share handled by the tool / 60

For illustration only: 300 submissions x 20 minutes x 40% = 40 hours per cohort. Cynbit should replace each input with its real number. The share the tool can take over is the thing the pilot in the technical approach is designed to measure, and on my small synthetic test the router sent almost everything to a person, so I would not assume a high share until it has been checked on real submissions.

## 6. Risks

- **Fairness.** Code metrics only understand Python and notebooks today. A strong JavaScript submission would score unfairly low until other languages are added. This must be fixed before any real use.
- **Gaming.** Students who learn the rubric can write to it. Some defences exist (README sections must contain content) but they are partial.
- **Over-trust.** A number looks authoritative. The design keeps the evidence visible and keeps the final grade with a person.
- **Student data.** Submissions are personal work. The optional LLM step sends only the structured findings, not the code, and should stay off until Cynbit has decided its policy.
- **Overlap flags are not accusations.** A shared starter template would create false matches. Flags are worded as "needs a human look".

## 7. What I could not verify

Cynbit's actual review process, cohort sizes, reviewer time, grading rubric and which Revio and TenantEase features exist today. The rubric in this project is my reading of the assessment itself and should be replaced by Cynbit's own.

## Sources

- Cynbit Technologies on GitHub (organisation profile): https://github.com/Cynbit-Technologies/.github
- Cynbit Technologies on Crunchbase: https://www.crunchbase.com/organization/cynbit-technologies
- Cynbit website, home, story and contact pages: https://www.cynbit.in/ , https://www.cynbit.in/story , https://www.cynbit.in/contact
- Cynbit and BitElevate 2.0 activity on LinkedIn: https://www.linkedin.com/in/mohak-saini-588991167/
