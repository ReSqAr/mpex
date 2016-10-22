from setuptools import setup


setup(
	name = "mpex",
	packages = ["mpex","mpex.lib"],
	version = "0.9",
	description = "git annex helper",
	author = "Yasin Zaehringer",
	author_email = "yasin-mpex@yhjz.de",
	url = "https://github.com/ReSqAr/mpex",
	keywords = ["git-annex"],
	entry_points = {
		'console_scripts': [
			'mpex = mpex.__main__:main'
		]},
	classifiers = [
		"Programming Language :: Python",
		"Programming Language :: Python :: 3",
		"Development Status :: 4 - Beta",
		"Environment :: Other Environment",
		"Intended Audience :: End Users/Desktop",
		"License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
		"Operating System :: POSIX :: Linux",
		"Topic :: Utilities",
		],
	long_description = """\
Git-Annex Multi-Repository Helper
-------------------------------------

This version requires Python 3 or later.
"""
) 
