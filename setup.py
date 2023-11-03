import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()
    print(required)

setuptools.setup(
    name = "senet",
    version = "0.0.0a0",
    author = "Alekos Falagas",
    author_email = "alek.falagas@gmail.com",
    description = "Energy Balance model approach for irrigation (SEN-ET SNAP plugin)",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url="https://gitlab.com/prima-mago/senet",
    packages = setuptools.find_packages(),
    include_package_data=True,
    license="GNU General Public License v3 or later (GPLv3+)",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires = '>=3.6',
    install_requires=['numpy',
                    'wheel',
                    'pypro4sail @ git+https://github.com/hectornieto/pypro4sail@master',
                    'pyTSEB @ git+https://github.com/DHI-GRAS/pyTSEB@master',
                    'pyDMS @ git+https://github.com/alekfal/pyDMS@master',
                    'creodias_finder @ git+https://github.com/DHI-GRAS/creodias-finder@main',
                    required],
)