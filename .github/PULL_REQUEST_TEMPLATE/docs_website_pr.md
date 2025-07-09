# PR Template: Documentation/Website Change

## Description of Changes
Provide a brief description of the documentation or website changes:

* What content was added/modified/removed?
* Why were these changes made?
* How do these changes improve the documentation/website?

## Related Issues
List any related issues or PRs:
* Fixes #123
* Related to #456

## Testing Performed
Describe how you tested your changes:
- [ ] Verified site builds successfully (i.e., `make view-local` runs successfully)
- [ ] Checked links and formatting (run `./check-external-links.sh`, which ensures that all external links have `target="..."` definitions - but it doesn't verify the links are valid...)
- [ ] Tested in local development environment
- [ ] Screenshots of changes (if applicable)

## Code Changes
List all files modified/added:
* docs/foobar.markdown
* ...

## Preview
Provide a link to a preview of the changes (if applicable) or just say that running `make view-local` is sufficient to see them. What should the reviewer check out, specifically?

## Checklist
- [ ] I have read the [CONTRIBUTING.md](CONTRIBUTING.md) guide
- [ ] My changes follow the documentation style guide
- [ ] I have updated any related documentation
- [ ] I have added/updated tests if applicable
- [ ] I have included necessary screenshots or examples

## Additional Context
Add any other context or information that might be helpful for reviewers:
* Related discussions
* Special considerations
* Open questions  