# 🚀 Publishing & Profile Optimization Guide

This guide walks you through deploying your new recruiter-ready GitHub profile README to **https://github.com/SujalKanu-stack/SujalKanu-stack**.

---

## ⚡ Step 1: Create the Special Profile Repository on GitHub

1. Go to [GitHub New Repository](https://github.com/new).
2. Set **Repository name** to exactly: `SujalKanu-stack` (must match your GitHub username character-for-character).
3. Ensure the visibility is set to **Public** (GitHub only displays profile READMEs from public repositories matching the account name).
4. Do **not** initialize with a README, .gitignore, or license (we already have all the production files ready).
5. Click **Create repository**.

---

## 💻 Step 2: Push Your Local Repository to GitHub

Open PowerShell or your terminal in this project folder (`c:\Users\Sujal Gupta\Downloads\gittub`) and run:

```bash
# 1. Initialize git if not already initialized
git init

# 2. Stage all profile files and assets
git add .

# 3. Create initial commit
git commit -m "feat: launch dark-neon engineer profile readme & animated assets"

# 4. Set main branch
git branch -M main

# 5. Link to your GitHub remote repository
git remote add origin https://github.com/SujalKanu-stack/SujalKanu-stack.git

# 6. Push to GitHub
git push -u origin main
```

*(Note: If you use SSH instead of HTTPS, use `git remote add origin git@github.com:SujalKanu-stack/SujalKanu-stack.git`)*

---

## ⚙️ Step 3: Enable GitHub Actions Permissions for Contribution Snake

The contribution snake action needs permission to push the generated SVG to your repository's `output` branch.

1. In your `SujalKanu-stack` repository, click **Settings** (top tab).
2. In the left sidebar, click **Actions** ➔ **General**.
3. Scroll down to **Workflow permissions**.
4. Select **Read and write permissions**.
5. Check **Allow GitHub Actions to approve pull request requests** (if visible).
6. Click **Save**.

### Run the Snake Workflow Once Manually:
1. Go to the **Actions** tab in your repository.
2. In the left list, click **Generate Contribution Snake**.
3. Click the **Run workflow** dropdown on the right ➔ click **Run workflow**.
4. In ~30 seconds, it will create the `output` branch with your custom dark neon snake animation.

---

## ✉️ Step 4: Add Your Contact Email

In `README.md`, find the two occurrences of `mailto:YOUR_EMAIL_HERE` and replace them with your actual preferred contact email (for example, `mailto:sujalguptaa121@gmail.com`).

---

## 🎯 High-Impact Profile Optimization (Next Improvements)

Your profile README now provides a visual experience far superior to standard terminal cards. To maximize your recruiter conversion rate for 2027 placements:

### 1. Merge Duplicate Repositories
Currently, your GitHub shows duplicate repositories:
- `AgriChain` and `AgriChain_block`: Consolidate the smart contracts folder into a monorepo under `AgriChain` or archive `AgriChain_block` with a pointer to `AgriChain`.
- `Heart_Sim` and `Heart-simulator`: Retain `Heart_Sim` as the canonical repository and archive or delete `Heart-simulator`.

### 2. Upgrade Repository Descriptions & Tags
Generic descriptions like *"Agriculture project"* lower recruiter engagement. Update them:
- **AgriChain**: `Decentralized agricultural supply chain & escrow protocol with automated fraud detection (Solidity, Hardhat, React, Node.js)`
  - Topics: `solidity`, `ethereum`, `smart-contracts`, `supply-chain`, `fraud-detection`, `web3`
- **Research_collab_Hub**: `Intelligent academic research synthesis workspace powered by FastAPI, React, and Claude API`
  - Topics: `fastapi`, `claude-api`, `generative-ai`, `react`, `academic-research`
- **Heart_Sim**: `Interactive WebGL 3D cardiac anatomical simulator for medical education and pathology inspection`
  - Topics: `webgl`, `threejs`, `3d-simulation`, `medical-tech`, `javascript`
- **portfolio**: `Personal developer portfolio built with Next.js, TailwindCSS & interactive animations`
  - Topics: `nextjs`, `typescript`, `portfolio`, `web-development`

### 3. Pin Your Canonical 6 Repositories
On your main GitHub profile overview:
1. Click **Customize your pins**.
2. Select your top projects:
   - `AgriChain`
   - `Research_collab_Hub`
   - `Heart_Sim`
   - `portfolio`
   - Hackathon repo (e.g. from IISc CodeForge or CODE RED 3.0)
   - IoT Weather Monitor / MATLAB Statistical Modelling
