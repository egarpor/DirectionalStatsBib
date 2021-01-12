DirectionalStats.bib
====================
[![License](https://img.shields.io/badge/license-CC_BY--SA_4.0-blue.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

`DirectionalStats.bib` is a curated BibTeX file with the details of virtually all publications on Directional Statistics published to date. It was compiled by Arthur Pewsey and Eduardo García-Portugués to accompany the invited discussion paper *Recent advances in directional statistics* ([arXiv:2005.06889](https://arxiv.org/abs/2005.06889)), to appear in *TEST*.

## Usage

<a href="https://raw.githubusercontent.com/egarpor/DirectionalStatsBib/master/DirectionalStats.bib" download="DirectionalStats.bib">Retrieve the most updated version</a> and use it with `\bibliography{DirectionalStats}` in your LaTeX document. For the compatibility of certain characters, consider adding `\usepackage[T1]{fontenc}` in your LaTeX preamble.

The entries are sorted alphabetically by their type (first `@article`s, second `@book`s, etc), then inverse chronological order, then alphabetical order from the author's surname. The fields of each entry are sorted according to the following order: title, subtitle, author, year, journal, fjournal, booktitle, booksubtitle, publisher, address, series, volume, number, pages, editor, edition, note, url, doi.

## Contribution

You are most welcome to contribute the details of any paper related to Directional Statistics (or relevant to the field) and report typos. Please contribute new entries following the template style and with full publishing information. The simplest way to do so is to search previous entries (`@article`, `@book`, `@collection`, `@incollection`, `@inproceedings`, `@manual`, etc.) and imitate as close as possible. To contribute entries, either open a pull request or reach out by email.

## Citation

If you found `DirectionalStats.bib` useful, you may consider citing the forthcoming *TEST* paper:

```
@article{Pewsey2020,
	title        = {Recent advances in directional statistics},
	author       = {Pewsey, A. and Garc\'ia-Portugu\'es, E.},
	year         = {2020},
	journal      = {TEST},
	fjournal     = {TEST},
	volume       = {to appear},
	url          = {https://arxiv.org/abs/2005.06889}
}
```

## License

All the material in this repository is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
