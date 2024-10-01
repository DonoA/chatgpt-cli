from setuptools import find_packages, setup

setup(
    name='chatgpt-cli',
    version='1.0',
    packages=['chatgpt'],
    entry_points={
        'console_scripts': [
            'chatgpt=chatgpt.chatgpt:main'
        ]
    },
    install_requires=[
        'openai'
    ],
    include_package_data=True,
)
