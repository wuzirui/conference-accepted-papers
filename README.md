# conference-accepted-papers

This repo aims to collect the accepted papers of history conference accepted papers in an unified format, to support potential usage (e.g. [ZoteroMetadataUpdatePlugin](https://github.com/wuzirui/paper-meta-update)).

We publish all the recorded conference in /index.html, with each record a link to the details. For each conference-year record (e.g. CVPR-2025), we store a JSON file in /conf/CONFNAME/year.html. The format is as below:
```JSON
{
    "Conference Name": "2025 IEEE/CVF Conference on Computer Vision and Pattern Recognition",
    "Proceeding Name": "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition",
    "Year": "2025",
    "Publisher": "IEEE",
    "Papers": [
        "Title": {
            "Authors": [
                "Author Name 1",
                ...
            ],
            "Url": "(optional)",
            "DOI": "(optional)",
            "Pages": "(optional)",
        },
        ...
    ]
}
```