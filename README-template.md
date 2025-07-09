# How to Use `microsite-template`

This repo is used as a template to create and publish AI Alliance &ldquo;microsites&rdquo;. It is setup as a GitHub _template repo_, which you can use to create a new repo. Even if you aren't creating a microsite, you can use this procedure to create a new AI Alliance repo for other purposes. Just delete the `docs` directory after creating the repo and skip the steps that don't apply to you.

See also [`GITHUB_PAGES.md`](https://github.com/The-AI-Alliance/microsite-template/blob/main/GITHUB_PAGES.md), which has more advanced instructions for developers.

## Creating Your Repo

These are the main steps, with details below:

1. Create your repo from the [this template repo](https://github.com/The-AI-Alliance/microsite-template).
1. Convert placeholder _variables_ to the correct values, using the [`finish-microsite.sh`](https://github.com/The-AI-Alliance/microsite-template/blob/main/finish-microsite.sh) script.
1. Push your local changes upstream.
1. Modify the "header buttons" in `docs/_includes/header_buttons_custom.html` to be what you want to appear at the top of each page. See the [OTDI](https://the-ai-alliance.github.io/open-trusted-data-initiative/) site for an example customization. Or if you don't want any buttons, delete the contents of that file (but don't delete the file...).
1. Add your initial custom content for the pages in the `docs` directory.
1. Add your initial custom content to the `README.md`.
1. **If** you plan to publish the website from the `latest` branch, merge changes to that branch from `main`.
1. Edit the repo's _Settings_. 
  1. On the repo's home page in GitHub, click the _Settings_ "gear" on the upper right-hand side. 
  1. Scroll down to _Features_ and click _Discussions_ to enable them (unless you don't want them; in this case, remove the URL on the `docs/contributing.markdown` page!).
  1. On the left-hand side, click the link for _Pages_. Under _Branch_, select the `main` or `latest` branch depending on which one you want to use, then select the `/docs` directory.
  1. On the left-hand side, click the link for _Secrets and variables_ > _Actions_. In the center of the page, make sure the _Secrets_ tab is selected, then click the _New repository secret_ green button and enter five secrets needed for metrics collection. Ask Dean Wampler ([email](mailto:dwampler@thealliance.ai), [Slack](https://ai-alliance-workspace.slack.com/team/U068AL1C30E)), Joe Olson ([email](mailto:Joe.Olson@ibm.com), [Slack](https://ai-alliance-workspace.slack.com/team/U06LFUAM5HN)), or Trevor Grant ([email](mailto:trevor.grant@ibm.com), [Slack](https://ai-alliance-workspace.slack.com/team/U06KCJ31771)) for the list of secrets and the values to use. 
1. Add the website in the appropriate location on the Alliance GitHub organization [README](https://github.com/The-AI-Alliance/) and the Alliance GitHub [website](https://the-ai-alliance.github.io/#the-ai-alliance-projects).
1. Delete the files `README-template.md`, `finish-microsite.sh`, and any of the `LICENSE.*` files that don't apply to your project.
1. Final steps.

> [!NOTE] 
> We are planning to automate as many of the manual steps as we can.

Let's look at these steps in more detail.

### 1. Create your repo from the `microsite-template`.

1. Go to the [`microsite-template`](https://github.com/The-AI-Alliance/microsite-template) repo. 
1. Click the right hand-side green button _Use this template_ and select _Create a new repository_. 
1. Select _The-AI-Alliance_ as the owner account.
1. Enter a unique name for the new repo. I'll use `ai-for-evil-project` as an example here.
1. Enter a description (recommended but optional). 
1. Select _public_ or _private_. You will need the repo to be public to publish a website from it, but you may choose to keep it private initially.
1. click _Create repository_.

See [these GitHub instructions](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) for more details.

### 2. Convert the placeholder _variables_.

> [!NOTE]
> This step is the only one where you need to work locally on your laptop, vs. working through the GitHub UI. It won't be feasible on Windows machines. If you have any problems doing this step, ask Dean Wampler for help.

If you are using this repo for a website, all the website content is under the `docs` directory. However, the script also edits the top-level `README.md` and possibly other files.

Your new repo will have placeholder values for the project name, associated focus area, etc. We'll fix those values using the "shell" script [`finish-microsite.sh`](https://github.com/The-AI-Alliance/microsite-template/blob/main/finish-microsite.sh), which replaces the placeholder _variables_ with appropriate strings for your project.

At the time of this writing, here are the required arguments shown with example values for a repo named `ai-for-evil-project` under the auspices of the _Trust and Safety_ focus area work group:

```shell
./finish-microsite.sh \
  --microsite-title "AI for Evil Project" \
  --work-group fa2
```

> [!NOTE]
> The title has to be in quotes, since it has nested white space.

A custom work group name can be specified, along with a corresponding argument for its URL, `--work-group-url`.

Most of the time, it is sufficient to use a focus area as the work group, in which case you can simply specify a number or `FA#` string, e.g., `2` or `FA2` (case ignored) for _trust and safety_. The value specified is expanded as follows:

| Number | Abbreviation (case ignored)  | Full name |
| :----- | :--------------------------- | :-------- |
| `1`    | `FA1`                        | Skills and Education |
| `2`    | `FA2`                        | Trust and Safety |
| `3`    | `FA3`                        | Applications and Tools |
| `4`    | `FA4`                        | Hardware Enablement |
| `5`    | `FA5`                        | Foundation Models and Datasets |
| `6`    | `FA6`                        | Advocacy |

> [!NOTE]
> 1. The script will try to use `zsh`. If you don't have `zsh`, but you have `bash` V5 or later, then use `bash ./finish-microsite.sh ...`
> 2. To see the current list of required and optional arguments, run the script with the `--help` flag.
> 3. By default, the website will be published from the `main` branch. If you prefer to use a different branch, we have used `latest` as a convention for most of the microsites. In this case, add the flag `--use-latest`. If you prefer to use a different branch, use `--publish-branch BRANCH`.

> [!WARNING]
> The script pushes the changes from the local repo to the upstream repo in GitHub. If you don't want to do that, preferring to push changes upstream later, then add the option `--no-push`. Pushing upstream may fail depending on how your personal GitHub account is configured, etc. Talk to Dean Wampler if you have problems here.

### 3. Edit the website buttons.

> [!NOTE]
> At this point, all the subsequent steps can be done on the GitHub UI for your repo.

There are purple "header buttons" that appear on all pages in the website. You can see examples in existing websites, e.g., [OTDI](https://the-ai-alliance.github.io/open-trusted-data-initiative/). The buttons are defined as HTML _anchor_ tags (`<a href="...">...</a>`) in the file `docs/_includes/header_buttons_custom.html`. 

Edit this file to define buttons that work for you. If you don't want any buttons, delete the contents of the file, but _don't delete the file_.

### 4. Add your initial custom content for the pages in the `docs` directory.

There are various `TODO` and other placeholder texts in the `docs/**/*.markdown`, `README.md`, and other files that you should replace with your real content as soon as possible, e.g.,

1. Find and replace all occurrences of `TODO` with appropriate content.
2. Rename or delete the `second_page.markdown`. Copy it to add more top-level pages, but change the `nav_order` field to control the order of the pages shown in the left-hand side navigation view. 
3. Rename or delete the `nested` folder and its contents, which is an example of how to create nested content.

> [!TIP]
> Start with `10`, `20`, etc. for the `nav_order` of top-level pages, giving yourself room to insert new pages in between existing pages. For nested pages, e.g., under `20`, use `210`, `220`, etc.

4. See the `nested` directory content as an example of how to do nesting. Note that the metadata fields at the top also define the `parent` and `has_children` fields.
5. Make any changes you want to make in the `docs/_config.yml` file. (None are mandatory.)

For more tips and guidance on development tasks, see also the links for more information in the `README.md` in your new repo. Add a project-specific description at the beginning of that file.

### 5. Add your initial custom content to the `README.md` in the repo.

The `README.md` contains useful _boilerplate_ for contributors, but the preamble at the beginning should be customized with useful "welcome" information about the project.

### 6. Merge changes to the `latest` (or another) branch.

By default, the website is published from the `main` branch, for convenience. However, if you chose to use the `latest` branch or another branch (see step 2. above), you'll need to merge the changes in `main` to that branch. We won't provide instructions here, as this is a standard developer practice. However, ask one of the developers on the team for help if needed.

### 7. Edit the repo's _Settings_. 

To publish the website and setup some other repo features, click the _Settings_ "gear" on the upper right-hand side of the repo's top-level page. 

#### 7a. Enable discussions.

Scroll down to _Features_ and click _Discussions_ to enable them. Click the _Set up discussions_ button and edit the first discussion topic to taste, then post it.

However, if you don't want discussions, remove the URL on the `docs/contributing.markdown` page. (Don't forget to merge that edit to any other branches.)

#### 7b. Publish your website.

On the left-hand side of the _Settings_, click the link for _Pages_. Under _Branch_, select your publication branch, either `main`, `latest`, or a custom branch you specified above. Then select the `/docs` directory and finally, click _Save_.

Your website should be published after a few minutes to https://the-ai-alliance.github.io/REPO_NAME/.

> [!TIP]
> At the top of the repo page, click _Actions_ to see the progress of building your website. This action will be executed every time you make a change to a file in your publication branch (i.e., `main` by default). If for some reason building the website fails, this page can provide useful debugging help.

#### 7c. Add secrets for metrics collection, etc.

On the left-hand side, click the link for _Secrets and variables_ > _Actions_. In the center of the page, make sure the _Secrets_ tab is selected, then click the _New repository secret_ green button and enter five secrets needed for metrics collection. (You'll will click the button once per secret...) Ask Dean Wampler ([email](mailto:dwampler@thealliance.ai), [Slack](https://ai-alliance-workspace.slack.com/team/U068AL1C30E)), Joe Olson ([email](mailto:Joe.Olson@ibm.com), [Slack](https://ai-alliance-workspace.slack.com/team/U06LFUAM5HN)), or Trevor Grant ([email](mailto:trevor.grant@ibm.com), [Slack](https://ai-alliance-workspace.slack.com/team/U06KCJ31771)) for the list of secrets and the values to use. 

### 8. Add your website to the Alliance GitHub organization page and the Alliance website.

> [!NOTE]
> This step applies for code repos, not just documentation repos.

Add the website to the Alliance GitHub organization [README](https://github.com/The-AI-Alliance/) and the Alliance GitHub Pages [website](https://the-ai-alliance.github.io/#the-ai-alliance-projects).

When you are ready for broader exposure for your site, there are a few places where we have an index to all the &ldquo;microsites&rdquo;. Add your site in the table shown in each of the following locations. Note how the rows are grouped by focus area. Your new entry will go in the table with the other projects/initiatives for your focus area.

* [https://github.com/The-AI-Alliance/](https://github.com/The-AI-Alliance/) (`README.md` [direct link](https://github.com/The-AI-Alliance/.github/blob/main/profile/README.md))
* [https://the-ai-alliance.github.io/](https://the-ai-alliance.github.io/) (`index.markdown` [direct link](https://github.com/The-AI-Alliance/the-ai-alliance.github.io/blob/main/docs/index.markdown))

You only need to edit the first file, the [`README.md`](https://github.com/The-AI-Alliance/.github/blob/main/profile/README.md). After editing this file, notify Dean Wampler, who will run a tool that copies the change to the other location.

Finally, talk to your focus area leaders about updating the main [AI Alliance website](https://thealliance.ai) with information about your project site.

### 9. Delete the files `README-template.md`, `finish-microsite.sh`, and any of the `LICENSE.*` files that don't apply to your project.

The first two files,`README-template.md` and `finish-microsite.sh`,  are no longer needed, so you can remove them from your repo. Select each one in the GitHub UI and click the `...` menu on the upper right-hand side, then select _Delete file_.

Similarly, you may not need all three `LICENSE.*` files:

* `LICENSE.Apache-2.0`: Recommended for code.
* `LICENSE.CC-BY-4.0`: Recommended for documentation.
* `LICENSE.CDLA-2.0`: Recommended for datasets.

### 10. Final steps.

If you are using a separate publication branch, e.g., `latest`, don't forget to merge all changes from `main` to the branch and push both branches upstream, e.g., `git push --all`.

You should now have a published website and you should know how to edit the content. Reach out to Dean Wampler ([email](mailto:dwampler@thealliance.ai), [Slack](https://ai-alliance-workspace.slack.com/team/U068AL1C30E)), Joe Olson ([email](mailto:Joe.Olson@ibm.com), [Slack](https://ai-alliance-workspace.slack.com/team/U06LFUAM5HN)), or Trevor Grant ([email](mailto:trevor.grant@ibm.com), [Slack](https://ai-alliance-workspace.slack.com/team/U06KCJ31771)) if you need help.
