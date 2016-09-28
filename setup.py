from setuptools import setup

setup(
    name='clamda',
    version='0.0.10',
    description='Work seamlessly with AWS Lambda Jobs',
    url='https://github.com/haydenth/clamda',
    license='MIT',
    author='Tom Hayden',
    author_email='thayden@gmail.com',
    py_modules=['clamda'],
    entry_points={
        'console_scripts': [
            'clamda = clamda:main'
        ]
    },
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
)
