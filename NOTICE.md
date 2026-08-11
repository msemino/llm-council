# Licensing

**This repository ships no license, and that is not an oversight.**

It is a fork of [karpathy/llm-council](https://github.com/karpathy/llm-council). At the time of
writing, upstream publishes **no license file** — GitHub reports its license as `null`, which under
default copyright means all rights reserved. 23 of the 39 files here are upstream's, byte for byte.

You cannot grant rights you were never given. Putting an MIT header over this tree would say
"do what you want with all of it", and for more than half of these files that is not mine to say.
So there is no LICENSE file, and the honest reading of that is: **treat this repository as
all-rights-reserved, and ask upstream before redistributing.**

## What is mine

The 16 files that diverge from upstream are my work: the whole `backend/`, plus `frontend/src/api.js`,
`App.jsx`, and the four stage components — the arena UI, the dynamic free-model selector, and the
retry/fallback layer. If you want to reuse **those specific changes** under MIT, open an issue and
I will split them out into a patch I can license cleanly.

## If upstream adds a license

If `karpathy/llm-council` ships an OSI license, this fork adopts it and this file goes away.

## How to check the split yourself

```bash
gh api repos/karpathy/llm-council/git/trees/HEAD?recursive=1 \
  --jq '.tree[] | select(.type=="blob") | "\(.sha) \(.path)"' | sort -k2 > upstream.txt
gh api repos/msemino/llm-council/git/trees/HEAD?recursive=1 \
  --jq '.tree[] | select(.type=="blob") | "\(.sha) \(.path)"' | sort -k2 > fork.txt
join -1 2 -2 2 -o 1.2,1.1,2.1 upstream.txt fork.txt | awk '$2!=$3{print $1}'
```

Blob SHAs are content-addressed, so equal SHA means identical bytes. The claim in the README is
that command's output.
