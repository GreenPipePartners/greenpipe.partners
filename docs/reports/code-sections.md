# Linked report code sections

Reports continue to use a GitHub Gist as their content source. `report.md` or
`Report.md` contains the narrative. Every additional non-image/non-CSV file is
appended automatically as an accordion under **Code and queries**.

Each attached file receives a stable section ID derived from its filename plus
a short digest. The filename is the public identity of that section, so do not
rename a file after sharing its link.

Code sections are collapsed by default. Opening a report URL with the section
fragment expands that block and scrolls it into view:

```text
/reports/{customer}/{gist_id}#report-code-{filename-slug}-{digest}
```

External links can use the stable section fragment directly. Each expanded code
block provides separate icon buttons to copy its code or stable section link.
Release-notice attachments retain their existing expanded presentation.
