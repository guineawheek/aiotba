import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    reqs = f.read().splitlines()

setuptools.setup(
    name="aiotba",
    version="0.0.3r2",
    author="guineawheek",
    author_email="guineawheek@gmail.com",
    license="MIT",
    description="a lib for the blue alliance (TBA) apiv3 using asyncio/aiohttp",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guineawheek/aiotba",
    packages=setuptools.find_packages(),
    install_requires=reqs,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
