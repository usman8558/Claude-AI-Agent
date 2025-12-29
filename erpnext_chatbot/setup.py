from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="erpnext_chatbot",
    version="0.0.1",
    description="AI-powered chatbot for ERPNext data queries",
    author="ERPNext Chatbot Team",
    author_email="admin@truetechterminal.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
