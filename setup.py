import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="JablotronPy",
    version="0.0.1",
    author="F. de Gier",
    author_email="freddegier@me.com",
    description="A client to interact with the Jablotron API to control Jablotron alarm systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fdegier/JablotronPy",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=["requests>=2.25.0"]
)
