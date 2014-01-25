#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014, Cameron White
import setuptools

if __name__ == "__main__":
    setuptools.setup(
        name="CalagatorBot",
        version='0.1.0',
        description="A IRC bot for @calagator",
        author="Cameron Brandon White",
        author_email="cameronbwhite90@gmail.com",
        provides=[
            "CalagatorBot",
        ],
        packages=[
            "modules",
        ],
        py_modules = [
            "bot",
        ],
        package_data = {
            'PyOLP': ["LICENSE", "README.md", "config.cfg"],
        },
        install_requires = [
            'kitnirc',
            'BotParse',
        ],
        include_package_data=True,
    )
