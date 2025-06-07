# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.0.0] - 2025-06-07

### Added

- Support for Sphinx 6, 7, 8.
- Support for Python 3.10, 3.11, 3.12, 3.13 and PyPy 3.10.
- Note about using this extension with MyST Markdown.

### Removed

- Support for Sphinx 1, 2, 3.
- Support for Python 2.7, 3.6, 3.7, 3.8 and PyPy 3.7.




## [0.9.4] - 2021-08-09

### Changed

- Updated the included Lightbox2 backend to version 2.11.3 and with it jQuery to
  version 3.4.1.

### Fixed

- Issue where explicit targets for thumbnails were ignored. 
  `.. _my target:` before a thumbnail directive would not make the thumbnail 
  referenceable by `:ref:Title <my target>`.



## [0.9.3] - 2021-04-27

### Fixed

- Issue where adding package configuration options to conf.py 
  (e.g. `images_config={'show_caption'=True}`) would cause incremental builds
  to stop working.
