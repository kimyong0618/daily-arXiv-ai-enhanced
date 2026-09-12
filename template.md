# About
This tool will daily crawl https://arxiv.org and use LLMs to summarize them.

See in: https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/

# How to use
This repo will daily crawl arXiv papers about **cs.CV, cs.GR and cs.CL**, and use **DeepSeek** to summarize the papers in **Chinese**.
If you wish to crawl other arXiv categories, use other LLMs or other languages, please follow the bellow instructions.
Otherwise, you can directly use this repo in https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/ . Please star it if you like :)

**Instructions:**
1. Fork this repo to your own account
2. Go to: your-own-repo -> Settings -> Secrets and variables -> Actions
3. Go to Secrets. Secrets are encrypted and are used for sensitive data
4. Create two repository secrets named `OPENAI_API_KEY` and `OPENAI_BASE_URL`, and input corresponding values.
5. Go to Variables. Variables are shown as plain text and are used for non-sensitive data
6. Create the following repository variables:
   1. `CATEGORIES`: separate the categories with ",", recommended: "cs.AI, cs.LG, cs.CL, cs.NE, cs.DS, math.OC"
   2. `LANGUAGE`: such as "Chinese" or "English"
   3. `MODEL_NAME`: such as "deepseek-chat"
   4. `EMAIL`: your email for push to github
   5. `NAME`: your name for push to github
7. Go to your-own-repo -> Actions -> arXiv-daily-ai-enhanced
8. You can manually click **Run workflow** to test if it works well (it may takes about one hour). 
By default, this action will automatically run every day
You can modify it in `.github/workflows/run.yml`
9. If you wish to modify the content in `README.md`, do not directly edit README.md. You should edit `template.md`.

## Research relevance email digest

The workflow uses the configured LLM to classify each AI-enhanced paper by title and abstract, then sends an HTML digest containing papers whose score reaches `RELEVANCE_THRESHOLD` (default `60`). Existing GitHub Pages and Markdown generation continue to use the original AI-enhanced data.

Add these Actions secrets:

- `MAIL_USERNAME`: SMTP login and From address
- `MAIL_PASSWORD`: SMTP app password / authorization code, not the normal mailbox password
- `MAIL_TO`: recipient address (comma-separated addresses are supported)

Add these optional Actions variables:

- `RELEVANCE_THRESHOLD`: default `60`
- `RELEVANCE_MAX_WORKERS`: default `1`
- `MAIL_SMTP_SERVER`: default `smtp.qq.com`
- `MAIL_SMTP_PORT`: default `465`

# To-do list
- [x] Replace markdown with GitHub pages front-end.
- [ ] Bugfix: In the statistics page, the number of papers for a keyword is not correct.
- [ ] Update instructions for fork users about how to use github pages.

# Content
{readme_content}

# Related tools
- ICML, ICLR, NeurIPS list: https://dw-dengwei.github.io/OpenReview-paper-list/index.html

# Star history

[![Star History Chart](https://api.star-history.com/svg?repos=dw-dengwei/daily-arXiv-ai-enhanced&type=Date)](https://www.star-history.com/#dw-dengwei/daily-arXiv-ai-enhanced&Date)
