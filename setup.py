from setuptools import setup

setup(
    name='bada',
    version='0.0.4',
    description='Work seamlessly with AWS Lambda Jobs',
    url='https://github.com/haydenth/bada',
    license='MIT',
    author='Tom Hayden',
    author_email='thayden@gmail.com',
    py_modules=['bada'],
    entry_points={
        'console_scripts': [
            'bada = bada:main'
        ]
    },
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
)
