---
layout: post
title: "Publishing to the VS Code Marketplace with CI"
categories:
  - Posts
tags:
  - DevOps
  - Azure
  - VS Code
  - LanceDB
  - VS Code Extension
---

While setting up CI for [LanceDB Explorer](https://marketplace.visualstudio.com/items?itemName=EmreOzsahin.lancedb-explorer), a VS Code extension I built for browsing LanceDB databases, I wanted `git tag vX.Y.Z && git push` to publish straight to the VS Code Marketplace.

The obvious way is a Personal Access Token: generate one in Azure DevOps, drop it in a GitHub secret, done. But global Azure DevOps PATs are being retired on December 1, 2026, and Microsoft's [own publishing docs](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) now point everyone toward Entra ID instead: OIDC through a managed identity, a federated credential, and one undocumented API call to find the right ID. That page covers the Azure Pipelines version. I spent way more time than I expected getting this to actually work, mostly guessing at IDs the Marketplace would not recognize. This is the GitHub Actions version, spelled out the way I wish I had it going in.

### Requirements

- An Azure account with an active subscription. A free tier subscription is enough, a managed identity is a real Azure resource so it needs somewhere to live.
- A GitHub repo with Actions enabled, and permission to add repo secrets.
- A publisher created on `marketplace.visualstudio.com/manage` (sign in with a Microsoft account, **+ Create publisher**, pick an ID). Nothing else in this post works without this, the managed identity you set up later gets authorized against this specific publisher. Put its ID in your extension's `publisher` field in `package.json`.
- The Azure CLI (`az`) if you want to run the identity lookup in step 4 locally instead of as a throwaway GitHub Actions job.

### Step 1: create a user-assigned managed identity, not an App Registration

Use a managed identity, not an App Registration. An App Registration is free and needs no subscription, so it looks like the right choice, but it authenticates fine and then fails at the actual publish step with `InvalidAccessException: The requested operation is not allowed`. Only a managed identity works here.

1. Go to `portal.azure.com` and sign in.
2. In the search bar at the top, type **Managed Identities** and click the matching result. Do not use the generic "Create a resource" button, it buries this under a category picker.
3. Click **+ Create**.
4. Fill in: your subscription, a resource group (create a new one if you do not have one already), a region (any region is fine), and a name for the identity (for example `vscode-publisher`).
5. Click **Review + create**, then **Create**. Wait for the deployment to finish, then click **Go to resource**.

### Step 2: add a federated credential for GitHub Actions

This step tells Azure to trust GitHub Actions, so it can hand out short-lived tokens without you storing a password anywhere.

1. On the same managed identity resource, in the left menu click **Settings**, then **Federated credentials**.
2. Click **+ Add credential**.
3. Under **Federated credential scenario**, choose **GitHub Actions deploying Azure resources**.
4. Fill in:
   - **Organization**: your GitHub username or org name
   - **Repository**: the name of your repo (just the repo name, not the full URL)
   - **Entity type**: choose **Environment**
   - **GitHub environment name**: type a name for this, for example `marketplace-publish`. Write this down exactly, you will type it again later in your workflow file.
5. Give the credential a **Name** (any label works, for example `github-actions`) and click **Add**.

Use **Environment** here, not **Branch** or **Tag**. If you pick Tag, the trust only matches one exact tag name, and it breaks the moment you push a second release.

### Step 3: add the GitHub Actions secrets

First grab the two values you need. On the managed identity resource, in the left menu click **Settings**, then **Properties**. Copy the values labeled **Client ID** and **Tenant ID**.

Then:

1. Open your repo on GitHub in a browser.
2. Click the **Settings** tab (top of the repo page, not your account settings).
3. In the left menu, click **Secrets and variables**, then **Actions**.
4. Click **New repository secret**.
5. Name it `AZURE_CLIENT_ID`, paste the Client ID, click **Add secret**.
6. Click **New repository secret** again. Name it `AZURE_TENANT_ID`, paste the Tenant ID, click **Add secret**.

Every `azure/login` step later in this post reads these two secrets by these exact names, so they need to exist before anything else here will work.

### Step 4: find the ID the Marketplace actually wants

This is the part that is not documented anywhere I could find. The VS Code Marketplace runs on Azure DevOps under the hood, and Azure DevOps keeps its own internal identity record, separate from both the managed identity's ARM resource ID and its Entra Object ID. A managed identity that has never talked to Azure DevOps before does not have a profile there yet, so trying to add it to your publisher by either of those IDs will just come back "not found."

The fix is one API call, made once, while authenticated as the identity:

```bash
az rest -u https://app.vssps.visualstudio.com/_apis/profile/profiles/me \
  --resource 499b84ac-1321-427f-aa17-267ca6975798
```

That GUID is Azure DevOps's well-known app ID in Microsoft Entra, [documented here](https://learn.microsoft.com/en-us/azure/devops/cli/entra-tokens?view=azure-devops) as the resource ID to use when requesting Entra tokens for Azure DevOps. It is the same for every organization, not something specific to your setup. Calling this endpoint registers the identity with Azure DevOps and returns its ID in Azure DevOps's own terms:

```json
{
  "displayName": "...\\<entra-object-id>",
  "id": "<the ID that actually works>",
  "publicAlias": "<same as id>"
}
```

The easiest way to run this once is a throwaway `workflow_dispatch` job:

```yaml
name: Debug Identity
on: workflow_dispatch
permissions:
  id-token: write
  contents: read
jobs:
  debug:
    runs-on: ubuntu-latest
    environment: marketplace-publish
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          allow-no-subscriptions: true
      - run: az rest -u https://app.vssps.visualstudio.com/_apis/profile/profiles/me --resource 499b84ac-1321-427f-aa17-267ca6975798
```

To run it:

1. Save that YAML as a new file, for example `.github/workflows/debug-identity.yml`, commit it, and push.
2. On GitHub, click the **Actions** tab of your repo.
3. In the left list of workflows, click **Debug Identity**.
4. Click the **Run workflow** button, then confirm.
5. Wait a few seconds, then click into the run that appears, then click the **debug** job.
6. Expand the last step in the log. You will see a block of JSON, find the line that says `"id": "..."` and copy that value.
7. Delete the workflow file and push again, you only need it this once.

### Step 5: authorize the identity on your publisher

1. Go to `marketplace.visualstudio.com/manage`, sign in, and select your publisher.
2. Look for a **Members** section (in some views this is under a settings or gear icon near the publisher name).
3. Click **Add** (or the equivalent button to add a member).
4. Paste the `id` value from step 4 into the search or ID field. Use that value specifically, not the managed identity's Client ID, Tenant ID, or Resource ID, none of those are recognized here.
5. Set the role to **Contributor** and save.

If this does not find the identity, you likely pasted the wrong value. The only ID this search recognizes is the one from step 4's API call.

### Step 6: the actual publish workflow

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: marketplace-publish
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - uses: actions/download-artifact@v4
        with:
          path: artifacts
          merge-multiple: true
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          allow-no-subscriptions: true
      - run: npx vsce publish --packagePath artifacts/*.vsix --skip-duplicate --azure-credential
```

No `VSCE_PAT`, no client secret, nothing to rotate or expire. For the full CI/CD workflow, including the build matrix that produces `artifacts/*.vsix` in the first place, see [`release.yml` in the LanceDB Explorer repo](https://github.com/eozsahin1993/lancedb-explorer/blob/main/.github/workflows/release.yml).

### Resources

- [Publishing Extensions - VS Code API docs](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [Azure DevOps Profile REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/profile/profiles/get)
- [Issue Entra tokens with Azure CLI - Azure DevOps](https://learn.microsoft.com/en-us/azure/devops/cli/entra-tokens?view=azure-devops)
- [azure/login GitHub Action](https://github.com/marketplace/actions/azure-login)

Happy coding!
